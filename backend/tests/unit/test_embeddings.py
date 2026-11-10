import pytest
from unittest.mock import MagicMock, patch
import numpy as np

from app.embeddings.base import BaseEmbeddingModel
from app.embeddings.sentence_transformer import SentenceTransformerEmbedding
from app.embeddings.embedding_service import get_embedding_service


class TestEmbeddingService:
    """Unit tests for sentence transformer embedding dimensions and error handling."""

    def test_sentence_transformer_dimension(self):
        """Verifies default model dimension is 384 for all-MiniLM-L6-v2."""
        service = SentenceTransformerEmbedding(model_name="all-MiniLM-L6-v2")
        assert service.dimension == 384

    def test_embed_batch_empty_list(self):
        """Embedding empty list immediately returns empty list without model invocation."""
        service = SentenceTransformerEmbedding()
        result = service.embed_batch([])
        assert result == []

    def test_mocked_embed_text_and_batch(self):
        """Verifies embedding output shape with mocked underlying SentenceTransformer model."""
        service = SentenceTransformerEmbedding()
        mock_model = MagicMock()
        mock_model.encode.side_effect = lambda text, **kwargs: (
            np.ones((len(text), 384)) if isinstance(text, list) else np.ones(384)
        )
        service._model = mock_model

        vec = service.embed_text("Sample academic research text.")
        assert len(vec) == 384
        assert isinstance(vec, list)

        batch_vecs = service.embed_batch(["Sentence one", "Sentence two"])
        assert len(batch_vecs) == 2
        assert len(batch_vecs[0]) == 384
        assert len(batch_vecs[1]) == 384

    def test_singleton_factory_returns_instance(self):
        """Verifies get_embedding_service returns a valid BaseEmbeddingModel."""
        instance = get_embedding_service()
        assert isinstance(instance, BaseEmbeddingModel)

