from typing import AsyncIterator, List, Optional
import anthropic
from anthropic import AsyncAnthropic

from backend.app.config import settings
from backend.app.core.errors import (
    ProviderNotConfiguredError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderAPIError,
)
from backend.app.core.logging import logger
from backend.app.schemas.llm import (
    LLMGenerateRequest,
    LLMGenerateResponse,
    LLMStreamChunk,
    TokenUsage,
)
from backend.app.schemas.models import ModelInfo
from backend.app.services.llm.base import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Claude Provider Adapter implementing the BaseLLMProvider interface
    via the official AsyncAnthropic SDK.
    """

    SUPPORTED_MODELS = [
        "claude-3-5-sonnet",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku",
        "claude-3-5-haiku-20241022",
        "claude-3-haiku",
        "claude-3-haiku-20240307",
        "claude-3-opus",
        "claude-3-opus-20240229",
    ]

    MODEL_ALIASES = {
        "claude-3-5-sonnet": "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku": "claude-3-5-haiku-20241022",
        "claude-3-haiku": "claude-3-haiku-20240307",
        "claude-3-opus": "claude-3-opus-20240229",
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        self._api_key = api_key or getattr(settings, "ANTHROPIC_API_KEY", None)
        self._base_url = base_url or getattr(settings, "ANTHROPIC_BASE_URL", None)
        self._timeout_seconds = timeout_seconds or getattr(settings, "ANTHROPIC_TIMEOUT_SECONDS", 60.0)
        self._client: Optional[AsyncAnthropic] = None

        if self._api_key:
            self._client = AsyncAnthropic(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=self._timeout_seconds,
            )

    @property
    def provider_id(self) -> str:
        return "anthropic"

    @property
    def provider_name(self) -> str:
        return "Anthropic"

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key and self._api_key.strip())

    def get_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                id="claude-3-5-sonnet",
                name="Claude 3.5 Sonnet",
                provider=self.provider_id,
                description="High-capability flagship Claude model for advanced reasoning, coding, and multi-step tasks.",
                context_window=200000,
                supports_streaming=True,
                is_default=(getattr(settings, "ANTHROPIC_DEFAULT_MODEL", "claude-3-5-sonnet") == "claude-3-5-sonnet"),
            ),
            ModelInfo(
                id="claude-3-5-haiku",
                name="Claude 3.5 Haiku",
                provider=self.provider_id,
                description="Fast and compact Claude model with high intelligence and ultra-low latency.",
                context_window=200000,
                supports_streaming=True,
                is_default=(getattr(settings, "ANTHROPIC_DEFAULT_MODEL", "") == "claude-3-5-haiku"),
            ),
            ModelInfo(
                id="claude-3-haiku",
                name="Claude 3 Haiku",
                provider=self.provider_id,
                description="Compact Claude 3 model for rapid throughput and quick responses.",
                context_window=200000,
                supports_streaming=True,
                is_default=False,
            ),
            ModelInfo(
                id="claude-3-opus",
                name="Claude 3 Opus",
                provider=self.provider_id,
                description="Deep reasoning model for open-ended synthesis and complex analysis.",
                context_window=200000,
                supports_streaming=True,
                is_default=False,
            ),
        ]

    def supports_model(self, model_id: str) -> bool:
        norm = model_id.lower()
        return norm.startswith("claude-") or norm in self.SUPPORTED_MODELS

    def _resolve_model(self, model_id: str) -> str:
        norm = model_id.lower()
        return self.MODEL_ALIASES.get(norm, model_id)

    def _prepare_payload(self, request: LLMGenerateRequest):
        system_prompts: List[str] = []
        messages: List[dict] = []

        for msg in request.messages:
            role = msg.role.lower() if hasattr(msg, "role") else "user"
            content = msg.content if hasattr(msg, "content") else str(msg)

            if role == "system":
                if isinstance(content, list):
                    text_parts = [p.get("text", "") for p in content if isinstance(p, dict) and "text" in p]
                    system_prompts.append(" ".join(text_parts))
                else:
                    system_prompts.append(str(content))
            elif role in ("user", "assistant"):
                messages.append({"role": role, "content": content})
            else:
                messages.append({"role": "user", "content": content})

        system = "\n\n".join(system_prompts) if system_prompts else None
        target_model = self._resolve_model(request.model)
        max_tokens = request.max_tokens or 4096
        temp = request.temperature if request.temperature is not None else 0.7

        return target_model, system, messages, max_tokens, temp

    async def generate(self, request: LLMGenerateRequest) -> LLMGenerateResponse:
        if not self.is_configured or not self._client:
            raise ProviderNotConfiguredError(
                f"Anthropic provider is not configured. Please set ANTHROPIC_API_KEY environment variable."
            )

        model, system, messages, max_tokens, temp = self._prepare_payload(request)

        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temp,
            }
            if system:
                kwargs["system"] = system

            response = await self._client.messages.create(**kwargs)

            text_content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text_content += block.text

            usage = TokenUsage(
                input_tokens=getattr(response.usage, "input_tokens", 0),
                output_tokens=getattr(response.usage, "output_tokens", 0),
                total_tokens=getattr(response.usage, "input_tokens", 0) + getattr(response.usage, "output_tokens", 0),
            )

            finish_reason = getattr(response, "stop_reason", "end_turn") or "stop"
            return LLMGenerateResponse(
                content=text_content,
                model=response.model or request.model,
                provider=self.provider_id,
                finish_reason=finish_reason,
                usage=usage,
            )

        except anthropic.AuthenticationError as e:
            raise ProviderAuthenticationError(f"Anthropic authentication failed: {str(e)}")
        except anthropic.RateLimitError as e:
            raise ProviderRateLimitError(f"Anthropic rate limit exceeded: {str(e)}")
        except anthropic.APITimeoutError as e:
            raise ProviderTimeoutError(f"Anthropic request timed out: {str(e)}")
        except anthropic.APIError as e:
            raise ProviderAPIError(f"Anthropic API error: {str(e)}")
        except Exception as e:
            raise ProviderAPIError(f"Unexpected error communicating with Anthropic: {str(e)}")

    async def generate_stream(
        self, request: LLMGenerateRequest
    ) -> AsyncIterator[LLMStreamChunk]:
        if not self.is_configured or not self._client:
            raise ProviderNotConfiguredError(
                f"Anthropic provider is not configured. Please set ANTHROPIC_API_KEY environment variable."
            )

        model, system, messages, max_tokens, temp = self._prepare_payload(request)

        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temp,
            }
            if system:
                kwargs["system"] = system

            async with self._client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    yield LLMStreamChunk(
                        content=text,
                        model=request.model,
                        is_finished=False,
                    )

                final_msg = await stream.get_final_message()
                finish_reason = getattr(final_msg, "stop_reason", "end_turn") or "stop"
                yield LLMStreamChunk(
                    content="",
                    model=request.model,
                    is_finished=True,
                    finish_reason=finish_reason,
                )

        except anthropic.AuthenticationError as e:
            raise ProviderAuthenticationError(f"Anthropic authentication failed: {str(e)}")
        except anthropic.RateLimitError as e:
            raise ProviderRateLimitError(f"Anthropic rate limit exceeded: {str(e)}")
        except anthropic.APITimeoutError as e:
            raise ProviderTimeoutError(f"Anthropic stream timed out: {str(e)}")
        except anthropic.APIError as e:
            raise ProviderAPIError(f"Anthropic API streaming error: {str(e)}")
        except Exception as e:
            raise ProviderAPIError(f"Unexpected error streaming from Anthropic: {str(e)}")

