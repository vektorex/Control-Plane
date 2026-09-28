import hashlib
import math
from typing import List
from backend.app.services.embeddings.base import BaseEmbeddingProvider


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic Mock Embedding Provider for fast, zero-API-cost unit and integration testing.
    Generates unit-normalized float vectors derived from content hash projections.
    """

    def __init__(self, dimension: int = 1536, model_name: str = "mock-embedding-v1") -> None:
        self._dimension = dimension
        self._model_name = model_name

    @property
    def provider_id(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    def _generate_vector(self, text: str) -> List[float]:
        """Generates a deterministic unit-length float vector of self._dimension."""
        if not text:
            return [0.0] * self._dimension

        vector = [0.0] * self._dimension
        words = text.lower().split()
        for word in words:
            # Hash word to a dimension index and sign
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dimension
            sign = 1.0 if (h >> 16) % 2 == 0 else -1.0
            vector[idx] += sign

        # Compute Euclidean norm
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            return [x / norm for x in vector]

        # Fallback pseudo-random unit vector
        h_seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
        raw = [((h_seed + i * 31) % 1000) / 1000.0 - 0.5 for i in range(self._dimension)]
        raw_norm = math.sqrt(sum(x * x for x in raw))
        return [x / raw_norm for x in raw]

    async def embed_text(self, text: str) -> List[float]:
        return self._generate_vector(text)

    async def embed_batch(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]
