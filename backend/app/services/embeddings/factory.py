from typing import Optional
from backend.app.config import settings
from backend.app.services.embeddings.base import BaseEmbeddingProvider
from backend.app.services.embeddings.providers.mock import MockEmbeddingProvider
from backend.app.services.embeddings.providers.openai import OpenAIEmbeddingProvider

_global_embedding_provider: Optional[BaseEmbeddingProvider] = None


class EmbeddingProviderFactory:
    """
    Factory for resolving and instantiating the active EmbeddingProvider.
    """

    @staticmethod
    def create_provider() -> BaseEmbeddingProvider:
        if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("mock-"):
            return OpenAIEmbeddingProvider(
                api_key=settings.OPENAI_API_KEY,
                model_name=settings.EMBEDDING_MODEL,
                dimension=settings.EMBEDDING_DIMENSION,
                base_url=settings.OPENAI_BASE_URL,
                timeout=settings.OPENAI_TIMEOUT_SECONDS,
            )
        # Fallback to deterministic mock provider for testing and development without live API keys
        return MockEmbeddingProvider(dimension=settings.EMBEDDING_DIMENSION)


def get_embedding_provider() -> BaseEmbeddingProvider:
    """Dependency injector / factory function for EmbeddingProvider."""
    global _global_embedding_provider
    if _global_embedding_provider is None:
        _global_embedding_provider = EmbeddingProviderFactory.create_provider()
    return _global_embedding_provider


def set_embedding_provider(provider: BaseEmbeddingProvider) -> None:
    """Override embedding provider for testing."""
    global _global_embedding_provider
    _global_embedding_provider = provider
