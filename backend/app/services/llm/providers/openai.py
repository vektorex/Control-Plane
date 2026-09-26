from typing import AsyncIterator, List, Optional
import openai
from openai import AsyncOpenAI

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


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI Provider Adapter implementing the BaseLLMProvider interface
    via the official AsyncOpenAI SDK.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        self._api_key = api_key or settings.OPENAI_API_KEY
        self._base_url = base_url or settings.OPENAI_BASE_URL
        self._timeout_seconds = timeout_seconds or settings.OPENAI_TIMEOUT_SECONDS
        self._client: Optional[AsyncOpenAI] = None

        if self._api_key:
            self._client = AsyncOpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=self._timeout_seconds,
            )

    @property
    def provider_id(self) -> str:
        return "openai"

    @property
    def provider_name(self) -> str:
        return "OpenAI"

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key and self._api_key.strip())

    def get_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                id="gpt-4o-mini",
                name="GPT-4o Mini",
                provider=self.provider_id,
                description="Fast, highly cost-effective flagship model for everyday reasoning and coding tasks.",
                context_window=128000,
                supports_streaming=True,
                is_default=(settings.OPENAI_DEFAULT_MODEL == "gpt-4o-mini"),
            ),
            ModelInfo(
                id="gpt-4o",
                name="GPT-4o",
                provider=self.provider_id,
                description="High-intelligence multimodal flagship model for complex multimodal work and reasoning.",
                context_window=128000,
                supports_streaming=True,
                is_default=(settings.OPENAI_DEFAULT_MODEL == "gpt-4o"),
            ),
            ModelInfo(
                id="o3-mini",
                name="o3-mini",
                provider=self.provider_id,
                description="High-speed reasoning model specialized in STEM, code architecture, and math.",
                context_window=200000,
                supports_streaming=True,
                is_default=(settings.OPENAI_DEFAULT_MODEL == "o3-mini"),
            ),
            ModelInfo(
                id="o1",
                name="o1",
                provider=self.provider_id,
                description="Advanced reasoning model designed for deep planning, science, and math problems.",
                context_window=200000,
                supports_streaming=True,
                is_default=(settings.OPENAI_DEFAULT_MODEL == "o1"),
            ),
            ModelInfo(
                id="gpt-4-turbo",
                name="GPT-4 Turbo",
                provider=self.provider_id,
                description="Legacy GPT-4 Turbo generation model with 128k context.",
                context_window=128000,
                supports_streaming=True,
                is_default=False,
            ),
        ]

    def supports_model(self, model_id: str) -> bool:
        known_ids = {m.id for m in self.get_models()}
        return model_id in known_ids or model_id.startswith("gpt-") or model_id.startswith("o1") or model_id.startswith("o3")

    def _ensure_client(self) -> AsyncOpenAI:
        if not self.is_configured or self._client is None:
            raise ProviderNotConfiguredError(
                "OpenAI provider is not configured. Please set the OPENAI_API_KEY environment variable."
            )
        return self._client

    def _prepare_messages(self, request: LLMGenerateRequest) -> list:
        return [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]

    def _prepare_kwargs(self, request: LLMGenerateRequest) -> dict:
        kwargs = {
            "model": request.model,
            "messages": self._prepare_messages(request),
        }
        
        # Reasoning models (o1, o3-mini) do not accept custom temperature parameter
        is_reasoning_model = request.model.startswith("o1") or request.model.startswith("o3")
        if not is_reasoning_model and request.temperature is not None:
            kwargs["temperature"] = request.temperature

        if request.max_tokens is not None:
            if is_reasoning_model:
                kwargs["max_completion_tokens"] = request.max_tokens
            else:
                kwargs["max_tokens"] = request.max_tokens

        return kwargs

    def _map_error(self, err: Exception) -> Exception:
        logger.error(f"[OpenAIProvider] Encountered error: {type(err).__name__}: {str(err)}")
        if isinstance(err, openai.AuthenticationError):
            return ProviderAuthenticationError(
                "OpenAI authentication failed. Please verify your OPENAI_API_KEY.",
                details=str(err),
            )
        if isinstance(err, openai.RateLimitError):
            return ProviderRateLimitError(
                "OpenAI rate limit exceeded or quota exhausted.",
                details=str(err),
            )
        if isinstance(err, openai.APITimeoutError):
            return ProviderTimeoutError(
                "OpenAI request timed out.",
                details=str(err),
            )
        if isinstance(err, (openai.APIConnectionError, openai.APIError)):
            return ProviderAPIError(
                f"OpenAI API communication error: {str(err)}",
                details=str(err),
            )
        if isinstance(err, (ProviderNotConfiguredError, ProviderAuthenticationError, ProviderRateLimitError, ProviderTimeoutError, ProviderAPIError)):
            return err
        return ProviderAPIError(f"Unexpected error communicating with OpenAI: {str(err)}")

    async def generate(self, request: LLMGenerateRequest) -> LLMGenerateResponse:
        client = self._ensure_client()
        kwargs = self._prepare_kwargs(request)

        try:
            logger.info(f"[OpenAIProvider] Dispatching non-streaming completion for model: {request.model}")
            response = await client.chat.completions.create(**kwargs)
            
            choice = response.choices[0] if response.choices else None
            content = choice.message.content if choice and choice.message else ""
            finish_reason = choice.finish_reason if choice else None

            usage = None
            if response.usage:
                usage = TokenUsage(
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                )

            return LLMGenerateResponse(
                content=content or "",
                model=response.model or request.model,
                provider=self.provider_id,
                usage=usage,
                finish_reason=finish_reason,
            )
        except Exception as e:
            raise self._map_error(e)

    async def generate_stream(
        self, request: LLMGenerateRequest
    ) -> AsyncIterator[LLMStreamChunk]:
        client = self._ensure_client()
        kwargs = self._prepare_kwargs(request)
        kwargs["stream"] = True
        kwargs["stream_options"] = {"include_usage": True}

        try:
            logger.info(f"[OpenAIProvider] Dispatching streaming completion for model: {request.model}")
            stream = await client.chat.completions.create(**kwargs)

            async for chunk in stream:
                choice = chunk.choices[0] if chunk.choices else None
                delta_content = choice.delta.content if choice and choice.delta else ""
                finish_reason = choice.finish_reason if choice else None
                is_finished = finish_reason is not None

                usage = None
                if chunk.usage:
                    usage = TokenUsage(
                        input_tokens=chunk.usage.prompt_tokens,
                        output_tokens=chunk.usage.completion_tokens,
                        total_tokens=chunk.usage.total_tokens,
                    )

                # Skip empty chunks unless finished or containing usage
                if not delta_content and not is_finished and not usage:
                    continue

                yield LLMStreamChunk(
                    content=delta_content or "",
                    model=chunk.model or request.model,
                    provider=self.provider_id,
                    is_finished=is_finished,
                    usage=usage,
                    finish_reason=finish_reason,
                )
        except Exception as e:
            raise self._map_error(e)
