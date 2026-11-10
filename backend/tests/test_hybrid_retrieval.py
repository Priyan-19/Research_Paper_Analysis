import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.embeddings.vector_store import VectorSearchResult
from app.rag.hybrid_retriever import HybridRetriever
from app.schemas.search import (
    GraphSearchResponse,
    GraphTripleItem,
    ConnectedPaperItem,
    HybridSearchResponse,
    HybridSearchResultItem
)

client = TestClient(app)


def test_rrf_scoring_calculation():
    """
    Tests Reciprocal Rank Fusion (RRF) score calculation for vector chunks and graph triples.
    RRF_Score(d) = w_v / (k + rank_v) + w_g / (k + rank_g)
    """
    vector_results = [
        VectorSearchResult(
            chunk_id="c001",
            paper_id="paper_001",
            page_number=1,
            section_name="Abstract",
            text="BERT model achieves state of the art results.",
            similarity_score=0.92
        )
    ]
    graph_triples = [
        GraphTripleItem(
            source="BERT",
            relation_type="EVALUATED_ON",
            target="GLUE",
            description="Evaluated on GLUE benchmark",
            paper_id="paper_001"
        )
    ]

    items = HybridRetriever.apply_reciprocal_rank_fusion(
        vector_results=vector_results,
        graph_triples=graph_triples,
        vector_weight=1.0,
        graph_weight=1.0,
        rrf_k=60
    )

    assert len(items) == 2
    # Vector rank 1 RRF score: 1.0 / (60 + 1) = 0.016393
    v_item = next(i for i in items if i.item_type == "vector_chunk")
    assert v_item.vector_rank == 1
    assert v_item.graph_rank is None
    assert pytest.approx(v_item.rrf_score, abs=1e-4) == 0.016393

    # Graph rank 1 RRF score: 1.0 / (60 + 1) = 0.016393
    g_item = next(i for i in items if i.item_type == "graph_triple")
    assert g_item.graph_rank == 1
    assert g_item.vector_rank is None
    assert pytest.approx(g_item.rrf_score, abs=1e-4) == 0.016393


def test_build_unified_hybrid_context():
    """
    Tests unified context string builder combining vector chunks and graph evidence.
    """
    items = [
        HybridSearchResultItem(
            item_id="chunk_c001",
            item_type="vector_chunk",
            content="BERT uses bidirectional transformer architectures.",
            paper_id="paper_001",
            vector_rank=1,
            rrf_score=0.016393,
            metadata={"page_number": 2, "section_name": "Methodology"}
        ),
        HybridSearchResultItem(
            item_id="triple_bert_uses_method_transformer",
            item_type="graph_triple",
            content="(BERT) --[USES_METHOD]--> (Transformer)",
            paper_id="paper_001",
            graph_rank=1,
            rrf_score=0.016393,
            metadata={"source": "BERT", "relation_type": "USES_METHOD", "target": "Transformer"}
        )
    ]

    graph_response = GraphSearchResponse(
        query="BERT Transformer",
        matched_entities=["BERT"],
        total_triples=1,
        triples=[],
        connected_papers=[
            ConnectedPaperItem(
                paper_id="paper_001",
                paper_title="BERT Paper",
                matched_entity_count=1
            )
        ],
        formatted_graph_context=""
    )

    context = HybridRetriever.build_unified_hybrid_context(items, graph_response)

    assert "=== HYBRID RAG CONTEXT (VECTOR RETRIEVAL + KNOWLEDGE GRAPH FUSION) ===" in context
    assert "[CONNECTED RESEARCH PAPERS]" in context
    assert "BERT Paper" in context
    assert "Evidence Item #1 | Vector Chunk" in context
    assert "Evidence Item #2 | Graph Relationship" in context


@pytest.mark.asyncio
async def test_search_hybrid_mocked_execution():
    """
    Tests HybridRetriever.search_hybrid concurrent execution.
    """
    mock_db = MagicMock()

    with patch("app.embeddings.vector_store.VectorStoreService.search_vector_similarity", new_callable=AsyncMock) as mock_vsearch, \
         patch("app.rag.graph_retriever.GraphRetriever.search_graph", new_callable=AsyncMock) as mock_gsearch:

        mock_vsearch.return_value = [
            VectorSearchResult(
                chunk_id="c001",
                paper_id="paper_001",
                page_number=1,
                section_name="Intro",
                text="Text passage",
                similarity_score=0.88
            )
        ]
        mock_gsearch.return_value = GraphSearchResponse(
            query="test",
            matched_entities=["BERT"],
            total_triples=1,
            triples=[
                GraphTripleItem(
                    source="BERT",
                    relation_type="EVALUATED_ON",
                    target="GLUE",
                    paper_id="paper_001"
                )
            ],
            connected_papers=[],
            formatted_graph_context=""
        )

        res = await HybridRetriever.search_hybrid(
            db=mock_db,
            query="How is BERT evaluated on GLUE?",
            top_k=5
        )

        assert res.query == "How is BERT evaluated on GLUE?"
        assert res.total_results == 2
        assert len(res.results) == 2
        assert "HYBRID RAG CONTEXT" in res.unified_hybrid_context


def test_search_hybrid_api_endpoint():
    """
    Tests FastAPI POST /api/v1/search/hybrid REST API endpoint.
    """
    payload = {
        "query": "How is BERT evaluated on GLUE benchmark?",
        "top_k": 5,
        "vector_weight": 1.0,
        "graph_weight": 1.0
    }

    with patch.object(HybridRetriever, "search_hybrid", new_callable=AsyncMock) as mock_hybrid:
        mock_hybrid.return_value = HybridSearchResponse(
            query=payload["query"],
            total_results=1,
            results=[
                HybridSearchResultItem(
                    item_id="chunk_c001",
                    item_type="vector_chunk",
                    content="BERT text",
                    paper_id="paper_001",
                    vector_rank=1,
                    rrf_score=0.016393,
                    metadata={"page_number": 1}
                )
            ],
            matched_graph_entities=["BERT", "GLUE"],
            unified_hybrid_context="Unified Context String"
        )

        res = client.post("/api/v1/search/hybrid", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["query"] == payload["query"]
        assert data["total_results"] == 1
        assert data["matched_graph_entities"] == ["BERT", "GLUE"]
        assert data["unified_hybrid_context"] == "Unified Context String"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
