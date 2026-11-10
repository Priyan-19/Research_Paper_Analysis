import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.graph.gnn_link_predictor import GNNLinkPredictor

client = TestClient(app)


def test_gnn_link_predictor_embedding_and_prediction():
    """
    Tests GNNLinkPredictor matrix construction, PyTorch GCN forward pass, and top link ranking.
    """
    source_entity = "RAG"
    target_candidates = ["Neo4j", "GraphSAGE", "FastAPI"]
    relationships = [
        ("RAG", "Neo4j", "USES_METHOD"),
        ("GraphSAGE", "Neo4j", "EXTENDS")
    ]

    results = GNNLinkPredictor.predict_top_links(
        source_entity=source_entity,
        target_candidates=target_candidates,
        existing_relationships=relationships,
        top_k=3
    )

    assert len(results) >= 1
    assert "target_entity" in results[0]
    assert "link_probability" in results[0]
    assert "similarity_score" in results[0]
    assert 0.0 <= results[0]["link_probability"] <= 1.0


def test_gnn_predict_links_api_endpoint():
    """
    Tests POST /api/v1/graph/predict-links API endpoint.
    """
    payload = {
        "source_entity": "Retrieval Augmented Generation",
        "target_candidates": ["PyTorch", "Neo4j", "Transformers"],
        "existing_relationships": [
            {"source": "Retrieval Augmented Generation", "target": "Transformers", "relation": "USES_METHOD"}
        ],
        "top_k": 3
    }

    response = client.post("/api/v1/graph/predict-links", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["source_entity"] == "Retrieval Augmented Generation"
    assert data["total_candidates_evaluated"] == 3
    assert len(data["predicted_links"]) >= 1
    assert "link_probability" in data["predicted_links"][0]
