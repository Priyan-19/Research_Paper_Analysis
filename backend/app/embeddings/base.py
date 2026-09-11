from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingModel(ABC):
    """
    Abstract Base Class for Embedding Provider Models.
    """
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Returns vector dimensionality (e.g. 384 or 768)."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generates a dense vector embedding for a single text string."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates dense vector embeddings for a list of text strings."""
        pass
