from typing import Optional
from app.embeddings.base import BaseEmbeddingModel
from app.embeddings.sentence_transformer import SentenceTransformerEmbedding
from app.embeddings.gemini_embedding import GeminiEmbedding
from app.core.config import settings
from app.core.logging import logger

_embedding_instance: Optional[BaseEmbeddingModel] = None


def get_embedding_service() -> BaseEmbeddingModel:
    """
    Singleton factory function returning configured embedding service instance.
    """
    global _embedding_instance
    if _embedding_instance is None:
        model_setting = settings.EMBEDDING_MODEL.lower()
        
        if "gemini" in model_setting or settings.LLM_PROVIDER.lower() == "gemini_cloud":
            logger.info("Initializing Gemini Cloud Embedding Service...")
            _embedding_instance = GeminiEmbedding()
        else:
            logger.info(f"Initializing Local SentenceTransformer Embedding Service ('{settings.EMBEDDING_MODEL}')...")
            _embedding_instance = SentenceTransformerEmbedding(model_name=settings.EMBEDDING_MODEL)

    return _embedding_instance
