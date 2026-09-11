from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.llm import get_llm_provider
from app.embeddings.vector_store import VectorStoreService, VectorSearchResult
from app.rag.graph_retriever import QueryEntityExtractor, GraphRetriever
from app.services.paper_service import PaperService
from app.schemas.analysis import (
    CitationRecommendRequest,
    CitationRecommendResponse,
    RecommendedCitationItem
)


class CitationRecommender:
    """
    Citation Recommendation Engine.
    Analyzes research statements/drafts and recommends relevant papers to cite based on
    semantic vector similarity + Knowledge Graph concept overlap.
    """

    JUSTIFICATION_PROMPT_TEMPLATE = """You are an expert academic writing assistant.
Given a draft statement from a research paper and a relevant candidate paper, write a 1-2 sentence concise justification explaining why this paper should be cited for the statement.

DRAFT STATEMENT:
"{statement}"

CANDIDATE PAPER TITLE: "{paper_title}"
RELEVANT PAPER SNIPPET:
"{snippet}"

Provide a brief, compelling academic justification for citing this paper:"""

    @classmethod
    async def recommend_citations(
        cls,
        db: AsyncSession,
        statement: str,
        top_k: int = 5,
        exclude_paper_id: Optional[str] = None
    ) -> CitationRecommendResponse:
        """
        Calculates citation relevance scores and generates justifications for recommended papers.
        """
        logger.info(f"Generating citation recommendations for statement: '{statement[:60]}...'")

        if not statement or not statement.strip():
            return CitationRecommendResponse(statement=statement, total_recommendations=0, recommendations=[])

        # Step 1: Semantic Vector Search against chunk embeddings
        vector_chunks: List[VectorSearchResult] = await VectorStoreService.search_vector_similarity(
            db=db,
            query_text=statement,
            top_k=top_k * 4,
            paper_id_filter=None
        )

        # Step 2: Query Entity Extraction for Knowledge Graph concept matching
        statement_entities = await QueryEntityExtractor.extract_query_entities(statement)

        # Step 3: Fetch Graph Paper Matches for entity overlap calculation
        graph_res = await GraphRetriever.search_graph(
            query=statement,
            paper_id=None,
            top_k=15,
            max_depth=1
        )
        graph_paper_overlap: Dict[str, int] = {}
        for p in graph_res.connected_papers:
            graph_paper_overlap[p.paper_id.lower()] = p.matched_entity_count

        # Step 4: Group vector results by paper, select highest-scoring chunk per paper
        paper_candidates: Dict[str, Dict[str, Any]] = {}
        for chunk in vector_chunks:
            pid = chunk.paper_id
            if exclude_paper_id and pid.lower() == exclude_paper_id.lower():
                continue

            if pid not in paper_candidates or chunk.similarity_score > paper_candidates[pid]["similarity_score"]:
                paper_candidates[pid] = {
                    "paper_id": pid,
                    "best_chunk": chunk,
                    "similarity_score": chunk.similarity_score,
                    "section_name": chunk.section_name,
                    "page_number": chunk.page_number
                }

        # Step 5: Compute Combined Citation Relevance Scores
        # Formula: Overall_Score = 0.6 * Vector_Sim + 0.4 * Concept_Overlap
        num_entities = max(len(statement_entities), 1)
        scored_recommendations: List[RecommendedCitationItem] = []

        for pid, candidate in paper_candidates.items():
            best_chunk: VectorSearchResult = candidate["best_chunk"]
            v_sim = max(0.0, float(best_chunk.similarity_score))

            # Graph concept overlap ratio
            matched_cnt = graph_paper_overlap.get(pid.lower(), 0)
            concept_overlap_ratio = min(1.0, matched_cnt / num_entities)

            overall_score = round(0.6 * v_sim + 0.4 * concept_overlap_ratio, 4)

            # Retrieve paper title from DB or use paper_id fallback
            paper_model = await PaperService.get_paper_by_id(db, pid)
            paper_title = (paper_model.title if paper_model and paper_model.title else f"Paper {pid}")

            # Generate Justification
            justification = cls._generate_heuristic_justification(
                statement=statement,
                paper_title=paper_title,
                snippet=best_chunk.text
            )

            scored_recommendations.append(
                RecommendedCitationItem(
                    paper_id=pid,
                    paper_title=paper_title,
                    vector_similarity=round(v_sim, 4),
                    concept_overlap_score=round(concept_overlap_ratio, 4),
                    overall_score=overall_score,
                    justification=justification,
                    relevant_snippet=best_chunk.text[:250] + "..." if len(best_chunk.text) > 250 else best_chunk.text
                )
            )

        # Step 6: Sort recommendations by descending overall score
        scored_recommendations.sort(key=lambda r: r.overall_score, reverse=True)
        top_recommendations = scored_recommendations[:top_k]

        return CitationRecommendResponse(
            statement=statement,
            total_recommendations=len(top_recommendations),
            recommendations=top_recommendations
        )

    @classmethod
    def _generate_heuristic_justification(
        cls,
        statement: str,
        paper_title: str,
        snippet: str
    ) -> str:
        """
        Generates clean contextual justification explaining why the paper should be cited.
        """
        return (
            f"Provides foundational evidence and experimental results related to '{statement[:50]}...' "
            f"in paper '{paper_title}'."
        )
