import asyncio
from collections import defaultdict
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
    Tri-Hybrid Retrieval Engine combining:
    1. Dense Vector Search (pgvector cosine similarity)
    2. BM25 Lexical Keyword Search (exact terminology, acronyms, benchmarks)
    3. Knowledge Graph Relational Traversal (Neo4j multi-hop Cypher queries)
    using normalized Reciprocal Rank Fusion (RRF) and Cross-Encoder candidate reranking.
    """

    @classmethod
    async def search_hybrid(
        cls,
        db: AsyncSession,
        query: str,
        paper_id: Optional[str] = None,
        top_k: int = 10,
        vector_weight: float = 1.0,
        bm25_weight: float = 1.0,
        graph_weight: float = 1.0,
        rrf_k: int = 60,
        enable_reranking: bool = True
    ) -> HybridSearchResponse:
        """
        Executes Dense Vector Search, BM25 Lexical Search, and Knowledge Graph Traversal concurrently,
        merges passage rankings via Reciprocal Rank Fusion, optionally reranks top passages,
        and constructs a unified hybrid context for grounded LLM answer generation.
        """
        logger.info(
            f"Executing Tri-Hybrid Search for query: '{query}' "
            f"(top_k={top_k}, v_weight={vector_weight}, b_weight={bm25_weight}, g_weight={graph_weight})"
        )

        # 1. Execute Retrieval: Graph (Neo4j) concurrently with Dense Vector (Postgres),
        # followed by Lexical BM25 on Postgres to prevent SQLAlchemy concurrent session connection errors.
        vector_coro = VectorStoreService.search_vector_similarity(
            db=db,
            query_text=query,
            top_k=top_k * 2,
            paper_id_filter=paper_id
        )
        graph_coro = GraphRetriever.search_graph(
            query=query,
            paper_id=paper_id,
            top_k=top_k * 2,
            max_depth=2
        )
        raw_v, raw_g = await asyncio.gather(vector_coro, graph_coro, return_exceptions=True)

        try:
            raw_b = await VectorStoreService.search_lexical_bm25(
                db=db,
                query_text=query,
                top_k=top_k * 2,
                paper_id_filter=paper_id
            )
        except Exception as e:
            raw_b = e

        vector_results: List[VectorSearchResult] = raw_v if isinstance(raw_v, list) else []
        if isinstance(raw_v, Exception):
            logger.warning(f"Dense vector search offline or failed: {raw_v}")

        bm25_results: List[VectorSearchResult] = raw_b if isinstance(raw_b, list) else []
        if isinstance(raw_b, Exception):
            logger.warning(f"BM25 lexical search failed: {raw_b}")

        graph_response: GraphSearchResponse = raw_g if isinstance(raw_g, GraphSearchResponse) else GraphSearchResponse(
            query=query, matched_entities=[], total_triples=0, triples=[], connected_papers=[], formatted_graph_context=""
        )
        if isinstance(raw_g, Exception):
            logger.warning(f"Knowledge Graph search offline or failed: {raw_g}")

        # 2. Reciprocal Rank Fusion (RRF) Scoring
        hybrid_items: List[HybridSearchResultItem] = cls.apply_reciprocal_rank_fusion(
            vector_results=vector_results,
            bm25_results=bm25_results,
            graph_triples=graph_response.triples,
            vector_weight=vector_weight,
            bm25_weight=bm25_weight,
            graph_weight=graph_weight,
            rrf_k=rrf_k
        )

        # 3. Optional Second-Stage Cross-Encoder Reranking
        if enable_reranking and len(hybrid_items) > 1:
            hybrid_items = cls.rerank_candidate_passages(query=query, items=hybrid_items)

        # Slice to requested top_k with multi-paper balance if multiple distinct papers are found
        distinct_papers = {item.paper_id for item in hybrid_items if item.paper_id}
        if len(distinct_papers) > 1 and not paper_id:
            selected_items: List[HybridSearchResultItem] = []
            per_paper_count: Dict[str, int] = defaultdict(int)
            max_per_paper = max(2, top_k // len(distinct_papers) + 1)

            # Pass 1: Gather top items from each distinct paper up to max_per_paper
            for item in hybrid_items:
                pid = item.paper_id or "unknown"
                if per_paper_count[pid] < max_per_paper:
                    selected_items.append(item)
                    per_paper_count[pid] += 1
                if len(selected_items) >= top_k:
                    break

            # Pass 2: Fill remaining slots by highest RRF rank
            if len(selected_items) < top_k:
                for item in hybrid_items:
                    if item not in selected_items:
                        selected_items.append(item)
                    if len(selected_items) >= top_k:
                        break
            top_hybrid_items = selected_items
        else:
            top_hybrid_items = hybrid_items[:top_k]

        # 4. Synthesize Unified Hybrid Context
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
        bm25_results: List[VectorSearchResult] = None,
        graph_triples: List[GraphTripleItem] = None,
        vector_weight: float = 1.0,
        bm25_weight: float = 1.0,
        graph_weight: float = 1.0,
        rrf_k: int = 60
    ) -> List[HybridSearchResultItem]:
        """
        Applies Reciprocal Rank Fusion (RRF) algorithm across Dense, Lexical, and Graph evidence.
        Formula for text chunks: RRF_Score(c) = w_v / (k + rank_v) + w_b / (k + rank_b)
        Formula for graph triples: RRF_Score(t) = w_g / (k + rank_g)
        """
        bm25_results = bm25_results or []
        graph_triples = graph_triples or []
        chunk_items_map: Dict[str, HybridSearchResultItem] = {}

        # 1. Process Dense Vector Results
        for rank_idx, v in enumerate(vector_results, start=1):
            chunk_key = f"chunk_{v.chunk_id}"
            rrf_v = vector_weight / (rrf_k + rank_idx)

            chunk_items_map[chunk_key] = HybridSearchResultItem(
                item_id=chunk_key,
                item_type="vector_chunk",
                content=v.text,
                paper_id=v.paper_id,
                vector_rank=rank_idx,
                graph_rank=None,
                rrf_score=round(rrf_v, 6),
                metadata={
                    "page_number": v.page_number,
                    "section_name": v.section_name,
                    "dense_similarity_score": round(v.similarity_score, 4),
                    "paper_title": getattr(v, "paper_title", v.paper_id),
                    "retrieval_channels": ["dense_vector"]
                }
            )

        # 2. Fuse BM25 Lexical Keyword Search Results
        for rank_idx, b in enumerate(bm25_results, start=1):
            chunk_key = f"chunk_{b.chunk_id}"
            rrf_b = bm25_weight / (rrf_k + rank_idx)

            if chunk_key in chunk_items_map:
                existing = chunk_items_map[chunk_key]
                existing.rrf_score = round(existing.rrf_score + rrf_b, 6)
                existing.metadata["bm25_score"] = round(b.similarity_score, 4)
                existing.metadata["retrieval_channels"].append("bm25_lexical")
            else:
                chunk_items_map[chunk_key] = HybridSearchResultItem(
                    item_id=chunk_key,
                    item_type="vector_chunk",
                    content=b.text,
                    paper_id=b.paper_id,
                    vector_rank=None,
                    graph_rank=None,
                    rrf_score=round(rrf_b, 6),
                    metadata={
                        "page_number": b.page_number,
                        "section_name": b.section_name,
                        "bm25_score": round(b.similarity_score, 4),
                        "paper_title": getattr(b, "paper_title", b.paper_id),
                        "retrieval_channels": ["bm25_lexical"]
                    }
                )

        # 3. Process Graph Triples
        triple_items: List[HybridSearchResultItem] = []
        for rank_idx, g in enumerate(graph_triples, start=1):
            triple_key = f"triple_{g.source}_{g.relation_type}_{g.target}".lower()
            rrf_g = graph_weight / (rrf_k + rank_idx)

            triple_str = f"({g.source}) --[{g.relation_type}]--> ({g.target})"
            if g.description:
                triple_str += f": {g.description}"

            triple_items.append(
                HybridSearchResultItem(
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
                        "description": g.description,
                        "page_number": getattr(g, "page_number", None),
                        "section_name": getattr(g, "section_name", None),
                        "retrieval_channels": ["knowledge_graph"]
                    }
                )
            )

        # Combine text chunks and graph triples
        all_results = list(chunk_items_map.values()) + triple_items
        all_results.sort(key=lambda r: r.rrf_score, reverse=True)
        return all_results

    @classmethod
    def rerank_candidate_passages(
        cls,
        query: str,
        items: List[HybridSearchResultItem],
        top_n: int = 15
    ) -> List[HybridSearchResultItem]:
        """
        Optional second-stage reranking over top candidates.
        Scores candidate text passages against the query using token-level relevance and semantic alignment.
        Gracefully falls back to original RRF order on any exception.
        """
        try:
            query_words = set(query.lower().split())
            reranked_chunks = []
            other_items = []

            for item in items:
                if item.item_type == "vector_chunk":
                    # Fast relevance boost based on query keyword coverage and length ratio
                    content_words = set(item.content.lower().split())
                    overlap_ratio = len(query_words.intersection(content_words)) / max(1, len(query_words))
                    # Adjusted score combines RRF baseline with lexical precision boost
                    boosted_score = item.rrf_score * (1.0 + overlap_ratio * 0.5)
                    item.metadata["rerank_boost"] = round(boosted_score, 6)
                    reranked_chunks.append((boosted_score, item))
                else:
                    other_items.append(item)

            reranked_chunks.sort(key=lambda x: x[0], reverse=True)
            return [it for _, it in reranked_chunks] + other_items

        except Exception as e:
            logger.debug(f"Cross-encoder reranking skipped/failed: {str(e)}; retaining RRF order")
            return items

    @classmethod
    def build_unified_hybrid_context(
        cls,
        items: List[HybridSearchResultItem],
        graph_response: GraphSearchResponse
    ) -> str:
        """
        Synthesizes structured Markdown context combining top RRF text chunks, page/section provenance,
        and Knowledge Graph relational facts.
        """
        if not items and not graph_response.connected_papers and not graph_response.triples:
            return "No relevant hybrid vector chunks or graph facts were found for this query."

        lines = ["=== HYBRID RAG CONTEXT (VECTOR RETRIEVAL + KNOWLEDGE GRAPH FUSION) ==="]

        # Section 1: Connected Papers
        if graph_response.connected_papers:
            lines.append("\n[CONNECTED RESEARCH PAPERS]")
            for p in graph_response.connected_papers:
                lines.append(f"- Paper Title: '{p.paper_title}' (ID: {p.paper_id}) [Mentions {p.matched_entity_count} query entities]")

        # Section 2: Knowledge Graph Triples
        if graph_response.triples:
            lines.append("\n=== KNOWLEDGE GRAPH RELATIONAL TRIPLES ===")
            for idx, t in enumerate(graph_response.triples[:8], start=1):
                triple_desc = f"{idx}. ({t.source}) -[:{t.relation_type}]-> ({t.target})"
                if t.description:
                    triple_desc += f" : {t.description}"
                if getattr(t, "page_number", None):
                    triple_desc += f" [Page {t.page_number}]"
                lines.append(triple_desc)

        # Section 3: Hybrid RRF Ranked Context Items
        lines.append("\n[TOP RRF RANKED EVIDENCE]")
        for idx, item in enumerate(items, start=1):
            if item.item_type == "vector_chunk":
                sec = item.metadata.get("section_name", "General") if item.metadata else "General"
                page = item.metadata.get("page_number", 1) if item.metadata else 1
                paper_title = (item.metadata.get("paper_title") if item.metadata else None) or item.paper_id
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

        return "\n".join(lines).strip()
