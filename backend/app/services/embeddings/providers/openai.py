import asyncio
from typing import List, Optional
from openai import AsyncOpenAI

from backend.app.core.errors import ProviderAPIError, ProviderAuthenticationError, ProviderRateLimitError
from backend.app.core.logging import logger
from backend.app.services.embeddings.base import BaseEmbeddingProvider


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    OpenAI Embedding Provider using the official AsyncOpenAI client.
    Supports text-embedding-3-small, text-embedding-3-large, and text-embedding-ada-002
    with batching and exponential retry.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "text-embedding-3-small",
        dimension: int = 1536,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        self._api_key = api_key
        self._model_name = model_name
        self._dimension = dimension
        self._client: Optional[AsyncOpenAI] = None

        if api_key:
            self._client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=timeout,
            )

    @property
    def provider_id(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_text(self, text: str) -> List[float]:
        results = await self.embed_batch([text], batch_size=1)
        return results[0]

    async def embed_batch(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        if not texts:
            return []

        if not self._client:
            raise ProviderAuthenticationError("OpenAI API key not configured for embeddings.")

        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), batch_size):
            chunk = texts[i : i + batch_size]
            # Replace empty strings with a single space since OpenAI rejects empty embedding inputs
            sanitized_chunk = [t.strip() if t and t.strip() else " " for t in chunk]

            retries = 3
            backoff = 1.0

            for attempt in range(retries):
                try:
                    response = await self._client.embeddings.create(
                        model=self._model_name,
                        input=sanitized_chunk,
                    )
                    # Sort by index to ensure ordering is preserved
                    sorted_data = sorted(response.data, key=lambda x: x.index)
                    for item in sorted_data:
                        emb = item.embedding
                        all_embeddings.append(emb)
                    break
                except Exception as e:
                    err_str = str(e).lower()
                    if "rate" in err_str or "429" in err_str:
                        if attempt < retries - 1:
                            logger.warning(f"[OpenAIEmbedding] Rate limited, retrying in {backoff}s...")
                            await asyncio.sleep(backoff)
                            backoff *= 2
                            continue
                        raise ProviderRateLimitError(f"OpenAI embedding rate limit exceeded: {str(e)}")
                    elif "auth" in err_str or "api_key" in err_str or "401" in err_str:
                        raise ProviderAuthenticationError(f"OpenAI authentication failed: {str(e)}")
                    else:
                        if attempt < retries - 1:
                            await asyncio.sleep(backoff)
                            backoff *= 2
                            continue
                        raise ProviderAPIError(f"OpenAI embedding API failed: {str(e)}")

        return all_embeddings
