import re
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.llm import get_llm_provider
from app.embeddings.vector_store import VectorStoreService, VectorSearchResult
from app.rag.graph_retriever import GraphRetriever
from app.rag.hybrid_retriever import HybridRetriever
from app.rag.prompts import RAGPrompts
from app.rag.citation_guard import CitationGuard
from app.schemas.rag import (
    ChatRequest,
    ChatResponse,
    CitationBadge,
    SearchModeEnum
)


class GroundedChatService:
    """
    Grounded Research Q&A Chat Service (POST /api/v1/chat).
    Orchestrates multi-mode retrieval (hybrid, vector, graph), system prompt grounding,
    LLM response generation, inline citation badge parsing, and hallucination guardrails.
    """

    @classmethod
    async def generate_grounded_chat(
        cls,
        db: AsyncSession,
        request: ChatRequest
    ) -> ChatResponse:
        """
        Executes grounded research chat workflow.
        """
        start_time = time.time()
        logger.info(f"Starting Grounded Chat Query: '{request.query}' (mode={request.search_mode.value})")

        retrieved_context_str = ""
        retrieved_sources: List[Dict[str, Any]] = []
        raw_items: List[Any] = []

        # Step 1: Unified Tri-Hybrid Retrieval (Vector pgvector + BM25 Lexical + Neo4j Graph with RRF)
        effective_top_k = request.top_k
        comp_terms = {"compare", "comparison", "both", "common", "difference", "differences", "versus", "vs", "share"}
        query_words = set(re.findall(r'\b\w+\b', request.query.lower()))
        if comp_terms.intersection(query_words):
            effective_top_k = max(request.top_k, 8)

        hybrid_res = await HybridRetriever.search_hybrid(
            db=db,
            query=request.query,
            paper_id=request.paper_id,
            top_k=effective_top_k
        )
        retrieved_context_str = hybrid_res.unified_hybrid_context
        raw_items = hybrid_res.results
        for idx, item in enumerate(hybrid_res.results, start=1):
            is_graph = item.item_type == "graph_triple"
            retrieved_sources.append({
                "source_index": idx,
                "paper_id": item.paper_id or ("graph_001" if is_graph else "doc_001"),
                "paper_title": item.metadata.get("paper_title") or ("Knowledge Graph Network" if is_graph else (item.paper_id or "Research Paper")),
                "page_number": item.metadata.get("page_number"),
                "section_name": item.metadata.get("section_name") or ("Knowledge Graph" if is_graph else None),
                "text": item.content,
                "source_type": "graph" if is_graph else "hybrid",
                "score": getattr(item, "rrf_score", None),
                "relationship": item.metadata.get("relation_type"),
                "source_entity": item.metadata.get("source_entity"),
                "target_entity": item.metadata.get("target_entity"),
            })

        # Step 2: Evidence Sufficiency Guardrail Check
        if not raw_items or CitationGuard.is_insufficient_evidence("", raw_items):
            fallback_ans = CitationGuard.get_insufficient_evidence_message(request.query)
            llm = get_llm_provider()
            elapsed = time.time() - start_time
            return ChatResponse(
                query=request.query,
                answer=fallback_ans,
                search_mode="hybrid",
                total_citations=0,
                citations=[],
                insufficient_evidence=True,
                llm_provider=llm.provider_name,
                execution_time_seconds=round(elapsed, 3)
            )

        # Step 3: Construct Prompts and Generate LLM Answer
        system_prompt = RAGPrompts.GROUNDED_CHAT_SYSTEM_PROMPT
        user_prompt = RAGPrompts.GROUNDED_CHAT_USER_PROMPT_TEMPLATE.format(
            query=request.query,
            context=retrieved_context_str
        )

        llm = get_llm_provider()
        answer_text = await llm.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=request.temperature
        )

        # Post-process answer text to replace raw UUID paper IDs with clean paper titles
        answer_text = CitationGuard.replace_paper_ids_with_titles(answer_text, retrieved_sources)

        # Step 4: Check if LLM output indicates insufficient evidence
        is_insufficient = CitationGuard.is_insufficient_evidence(answer_text, raw_items)
        if is_insufficient:
            answer_text = CitationGuard.get_insufficient_evidence_message(request.query)

        # Step 5: Extract Inline Citation Badges
        citations: List[CitationBadge] = []
        if not is_insufficient:
            citations = CitationGuard.extract_citation_badges(
                answer_text=answer_text,
                retrieved_sources=retrieved_sources
            )
            # Grounded Evidence Guarantee: If answer was generated from evidence but LLM omitted bracketed tags,
            # ensure evidence appears in the UI Inspector panel using retrieved sources:
            if not citations and retrieved_sources:
                for idx, src in enumerate(retrieved_sources[:request.top_k], start=1):
                    pid = str(src.get("paper_id", f"src_{idx}")).strip()
                    title = src.get("paper_title") or src.get("title") or pid
                    page = src.get("page_number")
                    sec = src.get("section_name")
                    snippet = src.get("text") or src.get("snippet")
                    citations.append(
                        CitationBadge(
                            paper_id=pid,
                            paper_title=title,
                            page_number=page,
                            section_name=sec,
                            citation_tag=f"[Source {idx}]",
                            snippet=snippet[:300] if snippet else None,
                            source_type=src.get("source_type", "hybrid"),
                            relationship=src.get("relationship"),
                            source_entity=src.get("source_entity"),
                            target_entity=src.get("target_entity"),
                            score=src.get("score")
                        )
                    )

        elapsed = time.time() - start_time
        logger.info(f"Completed Grounded Chat in {elapsed:.2f}s with {len(citations)} citations extracted.")

        return ChatResponse(
            query=request.query,
            answer=answer_text,
            search_mode="hybrid",
            total_citations=len(citations),
            citations=citations,
            insufficient_evidence=is_insufficient,
            llm_provider=llm.provider_name,
            execution_time_seconds=round(elapsed, 3)
        )
