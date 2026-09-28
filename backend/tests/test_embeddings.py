import pytest
from backend.app.services.embeddings.factory import get_embedding_provider, set_embedding_provider
from backend.app.services.embeddings.providers.mock import MockEmbeddingProvider


@pytest.mark.asyncio
async def test_mock_embedding_provider():
    provider = MockEmbeddingProvider(dimension=128)
    assert provider.provider_id == "mock"
    assert provider.dimension == 128

    vec1 = await provider.embed_text("hybrid search query")
    assert len(vec1) == 128
    assert isinstance(vec1[0], float)

    # Determinism
    vec2 = await provider.embed_text("hybrid search query")
    assert vec1 == vec2

    # Different text yields different embedding
    vec3 = await provider.embed_text("completely different prompt")
    assert vec1 != vec3

    # Batch embedding
    batch = await provider.embed_batch(["text one", "text two", "text three"])
    assert len(batch) == 3
    assert len(batch[0]) == 128
    assert len(batch[1]) == 128


def test_embedding_factory():
    provider = get_embedding_provider()
    assert provider is not None
    assert provider.dimension > 0
