from typing import List
from app.embeddings.base import BaseEmbeddingModel
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import LLMProviderError


class GeminiEmbedding(BaseEmbeddingModel):
    """
    Cloud Embedding Model using Google Gemini API (models/text-embedding-004).
    """
    def __init__(self, model_name: str = "models/text-embedding-004"):
        self.model_name = model_name
        self._dimension = 768

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> List[float]:
        if not settings.GEMINI_API_KEY:
            raise LLMProviderError(provider="Gemini", message="GEMINI_API_KEY is not configured in .env file.")
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Gemini embedding generation failed: {str(e)}")
            raise LLMProviderError(provider="Gemini", message=str(e))

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        
        if not settings.GEMINI_API_KEY:
            raise LLMProviderError(provider="Gemini", message="GEMINI_API_KEY is not configured in .env file.")

        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)

            result = genai.embed_content(
                model=self.model_name,
                content=texts,
                task_type="retrieval_document"
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Gemini batch embedding failed: {str(e)}")
            # Fallback to item-by-item if batch API fails
            embeddings = []
            for t in texts:
                embeddings.append(self.embed_text(t))
            return embeddings
