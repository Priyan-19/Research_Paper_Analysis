from typing import List, Optional
from app.embeddings.base import BaseEmbeddingModel
from app.core.logging import logger


class SentenceTransformerEmbedding(BaseEmbeddingModel):
    """
    Local Embedding Model using SentenceTransformers (default: all-MiniLM-L6-v2, 384 dimensions).
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._dimension = 384

    @property
    def dimension(self) -> int:
        return self._dimension

    def _load_model(self):
        """Lazy loads sentence-transformers model on first request."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading SentenceTransformer model '{self.model_name}'...")
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Successfully loaded '{self.model_name}' (Vector dim: {self._dimension})")
            except Exception as e:
                logger.error(f"Failed to load SentenceTransformer model {self.model_name}: {str(e)}")
                raise e

    def embed_text(self, text: str) -> List[float]:
        self._load_model()
        cleaned_text = text.replace("\n", " ").strip()
        embedding = self._model.encode(cleaned_text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        self._load_model()
        cleaned_texts = [t.replace("\n", " ").strip() for t in texts]
        embeddings = self._model.encode(cleaned_texts, batch_size=32, convert_to_numpy=True)
        return [emb.tolist() for emb in embeddings]
