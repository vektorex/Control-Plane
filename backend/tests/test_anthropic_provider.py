import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import anthropic

from backend.app.core.errors import (
    ProviderNotConfiguredError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from backend.app.schemas.llm import ChatMessage, LLMGenerateRequest
from backend.app.services.llm.providers.anthropic import AnthropicProvider
from backend.app.services.ai_gateway.adapters import AnthropicAdapter
from backend.app.services.ai_gateway.requests import GatewayRequest


def test_anthropic_provider_unconfigured():
    provider = AnthropicProvider(api_key=None)
    assert not provider.is_configured
    assert provider.provider_id == "anthropic"

    request = LLMGenerateRequest(
        model="claude-3-5-sonnet",
        messages=[ChatMessage(role="user", content="hello")]
    )

    with pytest.raises(ProviderNotConfiguredError):
        import asyncio
        asyncio.run(provider.generate(request))


def test_anthropic_provider_models_list():
    provider = AnthropicProvider(api_key="test-key")
    assert provider.is_configured
    models = provider.get_models()
    model_ids = [m.id for m in models]
    assert "claude-3-5-sonnet" in model_ids
    assert "claude-3-5-haiku" in model_ids
    assert "claude-3-haiku" in model_ids
    assert "claude-3-opus" in model_ids

    assert provider.supports_model("claude-3-5-sonnet")
    assert provider.supports_model("claude-anything-custom")
    assert not provider.supports_model("gpt-4o")


@pytest.mark.asyncio
async def test_anthropic_provider_generate_success():
    provider = AnthropicProvider(api_key="test-mock-key")

    mock_block = MagicMock()
    mock_block.text = "Response from Claude 3.5 Sonnet"

    mock_usage = MagicMock()
    mock_usage.input_tokens = 15
    mock_usage.output_tokens = 45

    mock_response = MagicMock()
    mock_response.content = [mock_block]
    mock_response.model = "claude-3-5-sonnet-20241022"
    mock_response.stop_reason = "end_turn"
    mock_response.usage = mock_usage

    mock_client = AsyncMock()
    mock_client.messages.create.return_value = mock_response
    provider._client = mock_client

    request = LLMGenerateRequest(
        model="claude-3-5-sonnet",
        messages=[
            ChatMessage(role="system", content="You are a helpful assistant."),
            ChatMessage(role="user", content="Hello Claude"),
        ],
        temperature=0.3,
        max_tokens=2048,
    )

    result = await provider.generate(request)

    assert result.content == "Response from Claude 3.5 Sonnet"
    assert result.provider == "anthropic"
    assert result.usage.input_tokens == 15
    assert result.usage.output_tokens == 45
    assert result.usage.total_tokens == 60


@pytest.mark.asyncio
async def test_anthropic_adapter_in_gateway():
    provider = AnthropicProvider(api_key="test-mock-key")

    mock_block = MagicMock()
    mock_block.text = "Gateway text from Claude"
    mock_usage = MagicMock()
    mock_usage.input_tokens = 10
    mock_usage.output_tokens = 20

    mock_response = MagicMock()
    mock_response.content = [mock_block]
    mock_response.model = "claude-3-5-sonnet-20241022"
    mock_response.stop_reason = "end_turn"
    mock_response.usage = mock_usage

    mock_client = AsyncMock()
    mock_client.messages.create.return_value = mock_response
    provider._client = mock_client

    adapter = AnthropicAdapter(provider=provider)
    assert adapter.provider_id == "anthropic"
    assert adapter.is_configured

    gw_req = GatewayRequest(
        model="claude-3-5-sonnet",
        messages=[{"role": "user", "content": "Test prompt"}],
    )
    gw_resp = await adapter.generate(gw_req)
    assert gw_resp.content == "Gateway text from Claude"
    assert gw_resp.provider == "anthropic"
    assert gw_resp.usage.input_tokens == 10
    assert gw_resp.usage.output_tokens == 20

