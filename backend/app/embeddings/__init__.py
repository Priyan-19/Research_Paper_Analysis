"""
Embeddings & Vector Storage Package.
"""
from app.embeddings.embedding_service import get_embedding_service
from app.embeddings.vector_store import VectorStoreService

__all__ = ["get_embedding_service", "VectorStoreService"]
