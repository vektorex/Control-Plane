"""
Embedding integration for Step 31: Semantic Cache.
Reuses the authoritative BaseEmbeddingProvider without creating a secondary embedding or vector store.
"""
from typing import List, Optional
from backend.app.core.logging import logger
from backend.app.services.embeddings.base import BaseEmbeddingProvider
from backend.app.services.embeddings.factory import get_embedding_provider


class CacheEmbeddingService:
    """
    Computes embedding vectors for normalized requests using the existing EmbeddingProvider.
    """

    def __init__(self, provider: Optional[BaseEmbeddingProvider] = None):
        self._provider = provider

    @property
    def provider(self) -> BaseEmbeddingProvider:
        if self._provider is None:
            self._provider = get_embedding_provider()
        return self._provider

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Embeds the request text into a 1536-dimensional float vector.
        Returns None gracefully if text is empty or provider fails.
        """
        clean_text = (text or "").strip()
        if not clean_text:
            return None

        try:
            # Truncate to safe length for embedding models (approx 8000 chars)
            truncated = clean_text[:8000]
            vector = await self.provider.embed_text(truncated)
            return vector
        except Exception as e:
            logger.warning(f"[CacheEmbeddingService] Failed to compute semantic embedding: {e}")
            return None
