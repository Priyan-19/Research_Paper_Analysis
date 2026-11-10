import pytest
import torch
from unittest.mock import MagicMock
from app.graph.gnn_link_predictor import GNNLinkPredictor, GCNEncoder


class TestGNNTrainingPipeline:
    """Unit tests for GNN Link Prediction training pipeline, negative sampling, and semantic features."""

    @pytest.fixture(autouse=True)
    def mock_embeddings(self, monkeypatch):
        """Mocks embedding service so unit tests run 100% offline and in under 1 second."""
        mock_service = MagicMock()
        mock_service.embed_batch.side_effect = lambda texts: [[0.1] * 384 for _ in texts]
        monkeypatch.setattr("app.embeddings.embedding_service.get_embedding_service", lambda: mock_service)
        GNNLinkPredictor._embedding_cache.clear()

    def test_semantic_node_feature_matrix(self):
        """Builds semantic feature tensor matching expected 384-dim dimensions."""
        entities = ["RAG", "BERT", "Neo4j"]
        relationships = [("RAG", "BERT", "USES_METHOD")]

        x, adj, ent2idx, idx2ent = GNNLinkPredictor.build_graph_matrices(entities, relationships, feat_dim=384)

        assert x.shape == (3, 384)
        assert adj.shape == (3, 3)
        assert len(ent2idx) == 3
        assert adj[ent2idx["RAG"], ent2idx["BERT"]] == 1.0
        assert adj[ent2idx["BERT"], ent2idx["RAG"]] == 1.0

    def test_gnn_training_with_negative_sampling(self):
        """Executes a genuine training loop with positive edges and negative edge sampling."""
        entities = ["RAG", "BERT", "Neo4j", "PyTorch", "FastAPI", "PostgreSQL"]
        relationships = [
            ("RAG", "BERT", "USES_METHOD"),
            ("BERT", "PyTorch", "USES_METHOD"),
            ("RAG", "Neo4j", "USES_METHOD"),
            ("FastAPI", "PostgreSQL", "USES_METHOD")
        ]

        result = GNNLinkPredictor.train_link_predictor(
            entities=entities,
            relationships=relationships,
            epochs=10,
            save_checkpoint=False
        )

        assert result["trained"] is True
        assert result["epochs_completed"] == 10
        assert "final_loss" in result
        assert result["positive_edges"] >= 3
        assert result["negative_edges"] >= 1

    def test_insufficient_graph_honesty_safeguard(self):
        """Honestly reports insufficient topology rather than faking training when data is scarce."""
        entities = ["EntityA", "EntityB"]
        relationships = [("EntityA", "EntityB", "USES")]

        result = GNNLinkPredictor.train_link_predictor(
            entities=entities,
            relationships=relationships,
            epochs=5,
            save_checkpoint=False
        )

        assert result["trained"] is False
        assert "Insufficient graph topology" in result["reason"]
