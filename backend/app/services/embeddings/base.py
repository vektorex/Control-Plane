from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingProvider(ABC):
    """
    Abstract Base Class for text embedding generation providers.
    Decoupled from specific generation models and API architectures.
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique provider identifier (e.g. 'openai', 'mock')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier (e.g. 'text-embedding-3-small')."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimensionality of produced embedding vectors (e.g. 1536)."""
        pass

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """
        Generates an embedding vector for a single string.
        """
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        """
        Generates embedding vectors for a list of strings with chunked batching.
        """
        pass
