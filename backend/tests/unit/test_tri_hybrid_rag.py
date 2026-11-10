import pytest
from app.rag.hybrid_retriever import HybridRetriever
from app.embeddings.vector_store import VectorSearchResult
from app.schemas.search import GraphTripleItem, GraphSearchResponse


class TestTriHybridRAG:
    """Unit tests for Tri-Hybrid (Dense + BM25 + Graph) retrieval and RRF rank fusion."""

    def test_rrf_rank_fusion_merges_dense_and_bm25(self):
        """Verifies that RRF properly merges ranks when a chunk appears in both dense and BM25 results."""
        v_results = [
            VectorSearchResult(
                chunk_id="c_001",
                paper_id="paper_A",
                page_number=1,
                section_name="Intro",
                text="Attention mechanism in Transformers",
                similarity_score=0.92
            ),
            VectorSearchResult(
                chunk_id="c_002",
                paper_id="paper_B",
                page_number=2,
                section_name="Method",
                text="Convolutional layers for image classification",
                similarity_score=0.81
            )
        ]

        b_results = [
            VectorSearchResult(
                chunk_id="c_001",  # Same chunk found via exact keyword BM25
                paper_id="paper_A",
                page_number=1,
                section_name="Intro",
                text="Attention mechanism in Transformers",
                similarity_score=0.95
            ),
            VectorSearchResult(
                chunk_id="c_003",
                paper_id="paper_C",
                page_number=1,
                section_name="Abstract",
                text="Reciprocal Rank Fusion for search",
                similarity_score=0.75
            )
        ]

        g_triples = [
            GraphTripleItem(
                source="Transformer",
                relation_type="USES_METHOD",
                target="Attention",
                description="Transformer uses self-attention",
                paper_id="paper_A"
            )
        ]

        fused = HybridRetriever.apply_reciprocal_rank_fusion(
            vector_results=v_results,
            bm25_results=b_results,
            graph_triples=g_triples,
            vector_weight=1.0,
            bm25_weight=0.8,
            graph_weight=1.0,
            rrf_k=60
        )

        assert len(fused) == 4
        # Chunk c_001 appeared in both Dense and BM25, so it must have the highest aggregated RRF score
        assert fused[0].item_id == "chunk_c_001"
        assert "dense_vector" in fused[0].metadata["retrieval_channels"]
        assert "bm25_lexical" in fused[0].metadata["retrieval_channels"]
        assert fused[0].rrf_score > fused[1].rrf_score

    def test_rerank_candidate_passages_fallback(self):
        """Cross-encoder reranking falls back cleanly on exceptions."""
        items = HybridRetriever.apply_reciprocal_rank_fusion(
            vector_results=[
                VectorSearchResult("c1", "p1", 1, "Sec", "Deep learning models", 0.8)
            ]
        )
        reranked = HybridRetriever.rerank_candidate_passages("deep learning", items)
        assert len(reranked) == 1
        assert reranked[0].item_id == "chunk_c1"

