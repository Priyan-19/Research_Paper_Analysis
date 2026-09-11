import time
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.logging import logger
from app.models.paper import Paper
from app.embeddings.vector_store import VectorStoreService, VectorSearchResult
from app.rag.prompts import RAGPrompts
from app.rag.context_builder import ContextBuilder, FormattedContext


class VectorRAGService:
    """
    Vector-based Retrieval-Augmented Generation (RAG) Service.
    Integrates Vector Retrieval + Context Formatting + LLM Generation.
    """
    @staticmethod
    async def generate_grounded_answer(
        db: AsyncSession,
        query: str,
        top_k: int = 5,
        paper_id: Optional[str] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        start_time = time.time()

        # 1. Retrieve Top-K Vector Search Results
        search_results: List[VectorSearchResult] = await VectorStoreService.search_vector_similarity(
            db=db,
            query_text=query,
            top_k=top_k,
            paper_id_filter=paper_id
        )

        if not search_results:
            execution_time = round(time.time() - start_time, 3)
            return {
                "query": query,
                "answer": "Based on the available research papers, there is insufficient evidence to answer this question as no relevant document passages were found.",
                "total_sources": 0,
                "sources": [],
                "llm_provider": settings.LLM_PROVIDER,
                "execution_time_seconds": execution_time
            }

        # 2. Lookup Paper Titles for Source Citation Metadata
        paper_ids = list(set(r.paper_id for r in search_results))
        paper_titles_query = select(Paper.id, Paper.title).where(Paper.id.in_(paper_ids))
        paper_titles_res = await db.execute(paper_titles_query)
        paper_titles: Dict[str, str] = {
            pid: (title or "Untitled Paper") for pid, title in paper_titles_res.all()
        }

        # 3. Build Formatted Context
        formatted_context: FormattedContext = ContextBuilder.build_vector_context(
            search_results=search_results,
            paper_titles=paper_titles
        )

        # 4. Generate LLM Answer
        answer_text = await VectorRAGService._invoke_llm(
            query=query,
            context_text=formatted_context.context_text,
            temperature=temperature
        )

        execution_time = round(time.time() - start_time, 3)

        return {
            "query": query,
            "answer": answer_text,
            "total_sources": len(formatted_context.sources_metadata),
            "sources": formatted_context.sources_metadata,
            "llm_provider": settings.LLM_PROVIDER,
            "execution_time_seconds": execution_time
        }

    @staticmethod
    async def _invoke_llm(query: str, context_text: str, temperature: float = 0.2) -> str:
        """
        Invokes configured LLM Provider (Gemini or Llama) with system prompt and context.
        """
        prompt = RAGPrompts.VECTOR_RAG_USER_PROMPT_TEMPLATE.format(
            query=query,
            context=context_text
        )

        try:
            from app.llm import get_llm_provider
            llm = get_llm_provider()
            return await llm.generate_text(
                prompt=prompt,
                system_prompt=RAGPrompts.VECTOR_RAG_SYSTEM_PROMPT,
                temperature=temperature
            )
        except Exception as e:
            logger.error(f"LLM Provider invocation failed ({settings.LLM_PROVIDER}): {str(e)}")
            # Fallthrough to fallback evidence synthesis
            return VectorRAGService._build_fallback_answer(query, context_text)

        # Fallback Evidence Synthesis (When API key is not configured or fails)
        logger.info("Using Fallback Evidence Synthesis Engine for grounded answer...")
        return VectorRAGService._build_fallback_answer(query, context_text)

    @staticmethod
    def _build_fallback_answer(query: str, context_text: str) -> str:
        """
        Generates a structured, evidence-grounded summary answer directly from retrieved passages.
        """
        lines = [
            f"### Grounded Evidence Summary for: '{query}'\n",
            "Based on the retrieved research paper passages:\n"
        ]

        # Extract source blocks
        blocks = context_text.split("\n---\n")
        for idx, block in enumerate(blocks[:3], start=1):
            first_line = block.split("\n")[0]
            passage_lines = [l for l in block.split("\n") if l.startswith("Passage:")]
            passage_snippet = passage_lines[0].replace("Passage:", "").strip() if passage_lines else block[:150]
            
            lines.append(f"* **[{idx}]** {passage_snippet[:250]}...")

        lines.append("\n*(Note: Configure `GEMINI_API_KEY` in `.env` to enable real-time Gemini LLM narrative synthesis)*")
        return "\n".join(lines)
