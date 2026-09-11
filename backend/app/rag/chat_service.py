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

        # Step 1: Execute Retrieval Strategy Based on Search Mode
        if request.search_mode == SearchModeEnum.HYBRID:
            hybrid_res = await HybridRetriever.search_hybrid(
                db=db,
                query=request.query,
                paper_id=request.paper_id,
                top_k=request.top_k
            )
            retrieved_context_str = hybrid_res.unified_hybrid_context
            raw_items = hybrid_res.results
            for idx, item in enumerate(hybrid_res.results, start=1):
                retrieved_sources.append({
                    "source_index": idx,
                    "paper_id": item.paper_id or "doc_001",
                    "paper_title": item.metadata.get("paper_title") or item.paper_id or "Research Paper",
                    "page_number": item.metadata.get("page_number"),
                    "section_name": item.metadata.get("section_name"),
                    "text": item.content
                })

        elif request.search_mode == SearchModeEnum.VECTOR:
            vector_chunks = await VectorStoreService.search_vector_similarity(
                db=db,
                query_text=request.query,
                top_k=request.top_k,
                paper_id_filter=request.paper_id
            )
            raw_items = vector_chunks
            context_lines = ["=== RETRIEVED VECTOR DOCUMENT PASSAGES ==="]
            for idx, c in enumerate(vector_chunks, start=1):
                context_lines.append(
                    f"\n[Source {idx} | Paper: {c.paper_id} | Page {c.page_number} | Section: {c.section_name}]\n{c.text}"
                )
                retrieved_sources.append({
                    "source_index": idx,
                    "paper_id": c.paper_id,
                    "paper_title": c.paper_id,
                    "page_number": c.page_number,
                    "section_name": c.section_name,
                    "text": c.text,
                    "chunk_id": c.chunk_id
                })
            retrieved_context_str = "\n".join(context_lines)

        elif request.search_mode == SearchModeEnum.GRAPH:
            graph_res = await GraphRetriever.search_graph(
                query=request.query,
                paper_id=request.paper_id,
                top_k=request.top_k,
                max_depth=2
            )
            retrieved_context_str = graph_res.formatted_graph_context
            raw_items = graph_res.triples
            for idx, t in enumerate(graph_res.triples, start=1):
                retrieved_sources.append({
                    "source_index": idx,
                    "paper_id": t.paper_id or "graph_001",
                    "paper_title": t.paper_id or "Graph Knowledge Network",
                    "page_number": None,
                    "section_name": "Knowledge Graph",
                    "text": f"({t.source}) --[{t.relation_type}]--> ({t.target})"
                })

        # Step 2: Evidence Sufficiency Guardrail Check
        if not raw_items or CitationGuard.is_insufficient_evidence("", raw_items):
            fallback_ans = CitationGuard.get_insufficient_evidence_message(request.query)
            llm = get_llm_provider()
            elapsed = time.time() - start_time
            return ChatResponse(
                query=request.query,
                answer=fallback_ans,
                search_mode=request.search_mode.value,
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

        elapsed = time.time() - start_time
        logger.info(f"Completed Grounded Chat in {elapsed:.2f}s with {len(citations)} citations extracted.")

        return ChatResponse(
            query=request.query,
            answer=answer_text,
            search_mode=request.search_mode.value,
            total_citations=len(citations),
            citations=citations,
            insufficient_evidence=is_insufficient,
            llm_provider=llm.provider_name,
            execution_time_seconds=round(elapsed, 3)
        )
