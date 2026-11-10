import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.embeddings.vector_store import VectorSearchResult
from app.schemas.graph import PaperGraphResponse, GraphNodeResponse
from app.analysis.similarity_detector import SimilarityDetector
from app.schemas.analysis import (
    PaperSimilarityRequest,
    PaperSimilarityResponse,
    PaperSimilarityItem,
    SharedEntityBreakdown
)

client = TestClient(app)


def test_jaccard_overlap_calculation():
    """
    Tests Jaccard similarity index calculation and shared entity list extraction.
    """
    set_a = {"bert", "transformer", "attention"}
    set_b = {"bert", "gpt", "attention"}

    ratio, shared = SimilarityDetector._compute_jaccard_overlap(set_a, set_b)

    # Intersection = {"bert", "attention"} (2), Union = {"bert", "transformer", "attention", "gpt"} (4)
    # Ratio = 2 / 4 = 0.5
    assert ratio == 0.5
    assert "Bert" in shared
    assert "Attention" in shared


def test_categorize_graph_entities():
    """
    Tests categorization of Knowledge Graph nodes into concepts, methods, models, datasets.
    """
    graph = PaperGraphResponse(
        paper_id="p1",
        paper_title="Title",
        total_nodes=4,
        total_edges=0,
        nodes=[
            GraphNodeResponse(id="n1", name="RAG", type="CONCEPT"),
            GraphNodeResponse(id="n2", name="PyMuPDF", type="TOOL"),
            GraphNodeResponse(id="n3", name="all-MiniLM-L6-v2", type="MODEL"),
            GraphNodeResponse(id="n4", name="GLUE", type="DATASET")
        ],
        edges=[]
    )

    buckets = SimilarityDetector._categorize_graph_entities(graph)

    assert "rag" in buckets["concepts"]
    assert "pymupdf" in buckets["methods"]
    assert "all-minilm-l6-v2" in buckets["models"]
    assert "glue" in buckets["datasets"]


@pytest.mark.asyncio
async def test_check_paper_similarity_execution():
    """
    Tests end-to-end 4-factor similarity score calculation and classification labeling.
    """
    mock_db = MagicMock()

    with patch("app.services.paper_service.PaperService.get_paper_by_id", new_callable=AsyncMock) as mock_get_paper, \
         patch("app.services.paper_service.PaperService.get_paper_chunks", new_callable=AsyncMock) as mock_get_chunks, \
         patch("app.embeddings.vector_store.VectorStoreService.search_vector_similarity", new_callable=AsyncMock) as mock_vsearch, \
         patch("app.graph.neo4j_builder.Neo4jGraphBuilder.get_paper_graph", new_callable=AsyncMock) as mock_get_graph:

        # Source Paper Model
        source_paper = MagicMock()
        source_paper.id = "paper_001"
        source_paper.title = "BERT Paper"
        
        # Target Paper Model
        target_paper = MagicMock()
        target_paper.id = "paper_002"
        target_paper.title = "RoBERTa Paper"

        def get_paper_side_effect(db, pid):
            if pid == "paper_001":
                return source_paper
            return target_paper

        mock_get_paper.side_effect = get_paper_side_effect
        mock_get_chunks.return_value = []
        mock_vsearch.return_value = [
            VectorSearchResult(
                chunk_id="c2",
                paper_id="paper_002",
                page_number=1,
                section_name="Abstract",
                text="RoBERTa improves BERT.",
                similarity_score=0.90
            )
        ]

        # Graphs with overlapping entities
        graph_p1 = PaperGraphResponse(
            paper_id="paper_001",
            paper_title="BERT",
            total_nodes=3,
            total_edges=0,
            nodes=[
                GraphNodeResponse(id="1", name="BERT", type="MODEL"),
                GraphNodeResponse(id="2", name="GLUE", type="DATASET"),
                GraphNodeResponse(id="3", name="Transformer", type="CONCEPT")
            ],
            edges=[]
        )
        graph_p2 = PaperGraphResponse(
            paper_id="paper_002",
            paper_title="RoBERTa",
            total_nodes=3,
            total_edges=0,
            nodes=[
                GraphNodeResponse(id="1", name="BERT", type="MODEL"),
                GraphNodeResponse(id="2", name="GLUE", type="DATASET"),
                GraphNodeResponse(id="3", name="Transformer", type="CONCEPT")
            ],
            edges=[]
        )

        def get_graph_side_effect(paper_id, paper_title):
            if paper_id == "paper_001":
                return graph_p1
            return graph_p2

        mock_get_graph.side_effect = get_graph_side_effect

        res = await SimilarityDetector.check_paper_similarity(
            db=mock_db,
            source_paper_id="paper_001",
            top_k=5
        )

        assert res.source_paper_id == "paper_001"
        assert res.total_matches == 1
        top_match = res.matches[0]
        assert top_match.paper_id == "paper_002"
        assert top_match.vector_similarity == 0.90
        assert top_match.overall_similarity_score >= 0.75
        assert top_match.classification_label == "Highly Similar Research"


def test_similarity_check_api_endpoint():
    """
    Tests FastAPI REST endpoint POST /api/v1/similarity/check.
    """
    payload = {
        "source_paper_id": "paper_001",
        "top_k": 5
    }

    with patch.object(SimilarityDetector, "check_paper_similarity", new_callable=AsyncMock) as mock_sim:
        mock_sim.return_value = PaperSimilarityResponse(
            source_paper_id=payload["source_paper_id"],
            source_paper_title="BERT Paper",
            total_matches=1,
            matches=[
                PaperSimilarityItem(
                    paper_id="paper_002",
                    paper_title="RoBERTa Paper",
                    overall_similarity_score=0.82,
                    vector_similarity=0.85,
                    concept_overlap=0.80,
                    method_overlap=0.80,
                    dataset_overlap=0.80,
                    classification_label="Highly Similar Research",
                    shared_entities=SharedEntityBreakdown(
                        shared_concepts=["Transformer"],
                        shared_methods=["Attention"],
                        shared_datasets=["GLUE"],
                        shared_models=["BERT"]
                    )
                )
            ]
        )

        res = client.post("/api/v1/similarity/check", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["source_paper_id"] == "paper_001"
        assert data["total_matches"] == 1
        assert data["matches"][0]["paper_id"] == "paper_002"
        assert data["matches"][0]["classification_label"] == "Highly Similar Research"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
