import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.core.errors import (
    ProviderNotConfiguredError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from backend.app.schemas.llm import ChatMessage, LLMGenerateRequest
from backend.app.services.llm.providers.gemini import GeminiProvider
from backend.app.services.ai_gateway.adapters import GeminiAdapter
from backend.app.services.ai_gateway.requests import GatewayRequest


def test_gemini_provider_unconfigured():
    provider = GeminiProvider(api_key=None)
    provider._api_key = None
    assert not provider.is_configured
    assert provider.provider_id == "gemini"

    request = LLMGenerateRequest(
        model="gemini-1.5-flash",
        messages=[ChatMessage(role="user", content="hello")]
    )

    with pytest.raises(ProviderNotConfiguredError):
        import asyncio
        asyncio.run(provider.generate(request))


def test_gemini_provider_models_list():
    provider = GeminiProvider(api_key="test-key")
    assert provider.is_configured
    models = provider.get_models()
    model_ids = [m.id for m in models]
    assert "gemini-1.5-flash" in model_ids
    assert "gemini-1.5-pro" in model_ids
    assert "gemini-2.0-flash" in model_ids
    assert "gemini-2.0-flash-lite" in model_ids

    assert provider.supports_model("gemini-1.5-flash")
    assert provider.supports_model("gemini-custom-model")
    assert not provider.supports_model("claude-3-5-sonnet")


@pytest.mark.asyncio
async def test_gemini_provider_generate_success():
    provider = GeminiProvider(api_key="test-mock-key")

    mock_usage = MagicMock()
    mock_usage.prompt_token_count = 12
    mock_usage.candidates_token_count = 38

    mock_candidate = MagicMock()
    mock_candidate.finish_reason = "STOP"

    mock_response = MagicMock()
    mock_response.text = "Response from Gemini 1.5 Flash"
    mock_response.usage_metadata = mock_usage
    mock_response.candidates = [mock_candidate]

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
    provider._client = mock_client

    request = LLMGenerateRequest(
        model="gemini-1.5-flash",
        messages=[
            ChatMessage(role="system", content="System instruction"),
            ChatMessage(role="user", content="Hello Gemini"),
        ],
        temperature=0.2,
        max_tokens=1024,
    )

    result = await provider.generate(request)

    assert result.content == "Response from Gemini 1.5 Flash"
    assert result.provider == "gemini"
    assert result.usage.input_tokens == 12
    assert result.usage.output_tokens == 38
    assert result.usage.total_tokens == 50


@pytest.mark.asyncio
async def test_gemini_adapter_in_gateway():
    provider = GeminiProvider(api_key="test-mock-key")

    mock_usage = MagicMock()
    mock_usage.prompt_token_count = 20
    mock_usage.candidates_token_count = 40

    mock_candidate = MagicMock()
    mock_candidate.finish_reason = "STOP"

    mock_response = MagicMock()
    mock_response.text = "Gateway text from Gemini"
    mock_response.usage_metadata = mock_usage
    mock_response.candidates = [mock_candidate]

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
    provider._client = mock_client

    adapter = GeminiAdapter(provider=provider)
    assert adapter.provider_id == "gemini"
    assert adapter.is_configured

    gw_req = GatewayRequest(
        model="gemini-1.5-flash",
        messages=[{"role": "user", "content": "Test prompt"}],
    )
    gw_resp = await adapter.generate(gw_req)
    assert gw_resp.content == "Gateway text from Gemini"
    assert gw_resp.provider == "gemini"
    assert gw_resp.usage.input_tokens == 20
    assert gw_resp.usage.output_tokens == 40

