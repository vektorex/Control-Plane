import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import openai

from backend.app.core.errors import (
    ProviderNotConfiguredError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from backend.app.schemas.llm import ChatMessage, LLMGenerateRequest
from backend.app.services.llm.providers.openai import OpenAIProvider


def test_openai_provider_unconfigured():
    provider = OpenAIProvider(api_key=None)
    assert not provider.is_configured
    assert provider.provider_id == "openai"

    request = LLMGenerateRequest(
        model="gpt-4o-mini",
        messages=[ChatMessage(role="user", content="hello")]
    )

    with pytest.raises(ProviderNotConfiguredError):
        pytest.main # Just checking type
        import asyncio
        asyncio.run(provider.generate(request))


def test_openai_provider_models_list():
    provider = OpenAIProvider(api_key="test-key")
    assert provider.is_configured
    models = provider.get_models()
    model_ids = [m.id for m in models]
    assert "gpt-4o-mini" in model_ids
    assert "gpt-4o" in model_ids
    assert "o1" in model_ids
    assert "o3-mini" in model_ids

    assert provider.supports_model("gpt-4o-mini")
    assert provider.supports_model("gpt-custom-model")
    assert not provider.supports_model("claude-3-5-sonnet")


@pytest.mark.asyncio
async def test_openai_provider_generate_success():
    provider = OpenAIProvider(api_key="test-mock-key")

    mock_choice = MagicMock()
    mock_choice.message.content = "Response from GPT-4o"
    mock_choice.finish_reason = "stop"

    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 10
    mock_usage.completion_tokens = 20
    mock_usage.total_tokens = 30

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.model = "gpt-4o-mini"
    mock_response.usage = mock_usage

    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_response
    provider._client = mock_client

    request = LLMGenerateRequest(
        model="gpt-4o-mini",
        messages=[ChatMessage(role="user", content="Hello OpenAI")],
        temperature=0.7,
    )

    result = await provider.generate(request)
    assert result.content == "Response from GPT-4o"
    assert result.model == "gpt-4o-mini"
    assert result.provider == "openai"
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 20
    assert result.usage.total_tokens == 30


@pytest.mark.asyncio
async def test_openai_provider_auth_error():
    provider = OpenAIProvider(api_key="invalid-key")

    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = openai.AuthenticationError(
        message="Incorrect API key provided",
        response=MagicMock(status_code=401),
        body={"error": {"message": "Invalid key"}}
    )
    provider._client = mock_client

    request = LLMGenerateRequest(
        model="gpt-4o-mini",
        messages=[ChatMessage(role="user", content="Hello")],
    )

    with pytest.raises(ProviderAuthenticationError):
        await provider.generate(request)


@pytest.mark.asyncio
async def test_openai_provider_rate_limit_error():
    provider = OpenAIProvider(api_key="test-key")

    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = openai.RateLimitError(
        message="Rate limit exceeded",
        response=MagicMock(status_code=429),
        body={"error": {"message": "Quota exceeded"}}
    )
    provider._client = mock_client

    request = LLMGenerateRequest(
        model="gpt-4o-mini",
        messages=[ChatMessage(role="user", content="Hello")],
    )

    with pytest.raises(ProviderRateLimitError):
        await provider.generate(request)
