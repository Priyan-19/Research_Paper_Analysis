import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.embeddings.vector_store import VectorStoreService, VectorSearchResult
from app.rag.graph_retriever import GraphRetriever
from app.schemas.search import (
    HybridSearchResponse,
    HybridSearchResultItem,
    GraphSearchResponse,
    GraphTripleItem,
    ConnectedPaperItem
)


class HybridRetriever:
    """
    Hybrid Retrieval Engine combining dense Vector Search and Knowledge Graph Traversal
    using Reciprocal Rank Fusion (RRF) and unified context synthesis.
    """

    @classmethod
    async def search_hybrid(
        cls,
        db: AsyncSession,
        query: str,
        paper_id: Optional[str] = None,
        top_k: int = 10,
        vector_weight: float = 1.0,
        graph_weight: float = 1.0,
        rrf_k: int = 60
    ) -> HybridSearchResponse:
        """
        Executes Vector Search and Graph Search concurrently, calculates Reciprocal Rank Fusion (RRF) scores,
        and constructs a unified hybrid context for grounded LLM answer generation.
        """
        logger.info(f"Executing Hybrid Search for query: '{query}' (top_k={top_k}, v_weight={vector_weight}, g_weight={graph_weight})")

        # 1. Execute Vector Search and Graph Search concurrently
        raw_v, raw_g = await asyncio.gather(
            VectorStoreService.search_vector_similarity(
                db=db,
                query_text=query,
                top_k=top_k * 2,  # Retrieve candidate pool
                paper_id_filter=paper_id
            ),
            GraphRetriever.search_graph(
                query=query,
                paper_id=paper_id,
                top_k=top_k * 2,
                max_depth=2
            ),
            return_exceptions=True
        )

        vector_results: List[VectorSearchResult] = raw_v if isinstance(raw_v, list) else []
        if isinstance(raw_v, Exception):
            logger.warning(f"Vector search offline or failed: {raw_v}")

        graph_response: GraphSearchResponse = raw_g if isinstance(raw_g, GraphSearchResponse) else GraphSearchResponse(
            query=query, matched_entities=[], total_triples=0, triples=[], connected_papers=[], formatted_graph_context=""
        )
        if isinstance(raw_g, Exception):
            logger.warning(f"Graph search offline or failed: {raw_g}")

        # 2. Reciprocal Rank Fusion (RRF) Scoring
        hybrid_items: List[HybridSearchResultItem] = cls.apply_reciprocal_rank_fusion(
            vector_results=vector_results,
            graph_triples=graph_response.triples,
            vector_weight=vector_weight,
            graph_weight=graph_weight,
            rrf_k=rrf_k
        )

        # Slice to requested top_k
        top_hybrid_items = hybrid_items[:top_k]

        # 3. Synthesize Unified Hybrid Context
        unified_context = cls.build_unified_hybrid_context(
            items=top_hybrid_items,
            graph_response=graph_response
        )

        return HybridSearchResponse(
            query=query,
            total_results=len(top_hybrid_items),
            results=top_hybrid_items,
            matched_graph_entities=graph_response.matched_entities,
            unified_hybrid_context=unified_context
        )

    @classmethod
    def apply_reciprocal_rank_fusion(
        cls,
        vector_results: List[VectorSearchResult],
        graph_triples: List[GraphTripleItem],
        vector_weight: float = 1.0,
        graph_weight: float = 1.0,
        rrf_k: int = 60
    ) -> List[HybridSearchResultItem]:
        """
        Applies Reciprocal Rank Fusion (RRF) algorithm to rank vector chunks and graph triples.
        Formula: RRF_Score(d) = w_v / (k + rank_v) + w_g / (k + rank_g)
        """
        items_map: Dict[str, HybridSearchResultItem] = {}

        # Process Vector Search Results
        for rank_idx, v in enumerate(vector_results, start=1):
            item_id = f"chunk_{v.chunk_id}"
            rrf_v = vector_weight / (rrf_k + rank_idx)

            items_map[item_id] = HybridSearchResultItem(
                item_id=item_id,
                item_type="vector_chunk",
                content=v.text,
                paper_id=v.paper_id,
                vector_rank=rank_idx,
                graph_rank=None,
                rrf_score=round(rrf_v, 6),
                metadata={
                    "page_number": v.page_number,
                    "section_name": v.section_name,
                    "similarity_score": round(v.similarity_score, 4),
                    "paper_title": getattr(v, "paper_title", v.paper_id)
                }
            )

        # Process Graph Search Results
        for rank_idx, g in enumerate(graph_triples, start=1):
            triple_key = f"triple_{g.source}_{g.relation_type}_{g.target}".lower()
            rrf_g = graph_weight / (rrf_k + rank_idx)

            triple_str = f"({g.source}) --[{g.relation_type}]--> ({g.target})"
            if g.description:
                triple_str += f": {g.description}"

            if triple_key in items_map:
                # Merge ranks if item exists in both
                existing = items_map[triple_key]
                existing.graph_rank = rank_idx
                existing.rrf_score = round(existing.rrf_score + rrf_g, 6)
            else:
                items_map[triple_key] = HybridSearchResultItem(
                    item_id=triple_key,
                    item_type="graph_triple",
                    content=triple_str,
                    paper_id=g.paper_id,
                    vector_rank=None,
                    graph_rank=rank_idx,
                    rrf_score=round(rrf_g, 6),
                    metadata={
                        "source": g.source,
                        "relation_type": g.relation_type,
                        "target": g.target,
                        "description": g.description
                    }
                )

        # Sort all items by descending RRF score
        sorted_items = sorted(items_map.values(), key=lambda x: x.rrf_score, reverse=True)
        return sorted_items

    @classmethod
    def build_unified_hybrid_context(
        cls,
        items: List[HybridSearchResultItem],
        graph_response: GraphSearchResponse
    ) -> str:
        """
        Builds unified structured Markdown context combining top RRF text chunks and graph facts.
        """
        if not items and not graph_response.connected_papers:
            return "No relevant hybrid vector chunks or graph facts were found for this query."

        lines = ["=== HYBRID RAG CONTEXT (VECTOR RETRIEVAL + KNOWLEDGE GRAPH FUSION) ==="]

        # Section 1: Connected Papers
        if graph_response.connected_papers:
            lines.append("\n[CONNECTED RESEARCH PAPERS]")
            for p in graph_response.connected_papers:
                lines.append(f"- Paper Title: '{p.paper_title}' (ID: {p.paper_id}) [Mentions {p.matched_entity_count} query entities]")

        # Section 2: Hybrid RRF Ranked Context Items
        lines.append("\n[TOP RRF RANKED EVIDENCE]")
        for idx, item in enumerate(items, start=1):
            if item.item_type == "vector_chunk":
                sec = item.metadata.get("section_name", "General")
                page = item.metadata.get("page_number", 1)
                paper_title = item.metadata.get("paper_title") or item.paper_id
                lines.append(
                    f"\n[Evidence Item #{idx} | Vector Chunk | Paper: {paper_title} | Page {page} | Section: {sec} | RRF Score: {item.rrf_score}]\n"
                    f"{item.content}"
                )
            elif item.item_type == "graph_triple":
                pid = f" | Paper: {item.paper_id}" if item.paper_id else ""
                lines.append(
                    f"\n[Evidence Item #{idx} | Graph Relationship{pid} | RRF Score: {item.rrf_score}]\n"
                    f"- {item.content}"
                )

        return "\n".join(lines)
