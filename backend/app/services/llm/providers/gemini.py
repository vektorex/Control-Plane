from typing import AsyncIterator, List, Optional
import os

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


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini Provider Adapter implementing the BaseLLMProvider interface
    via the official modern Google GenAI SDK (google-genai).
    """

    SUPPORTED_MODELS = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro-latest",
    ]

    MODEL_ALIASES = {
        "gemini-1.5-flash": "gemini-1.5-flash",
        "gemini-1.5-pro": "gemini-1.5-pro",
        "gemini-2.0-flash": "gemini-2.0-flash",
        "gemini-2.0-flash-lite": "gemini-2.0-flash-lite",
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        self._api_key = api_key or getattr(settings, "GEMINI_API_KEY", None) or os.environ.get("GEMINI_API_KEY")
        self._timeout_seconds = timeout_seconds or getattr(settings, "GEMINI_TIMEOUT_SECONDS", 60.0)
        self._client = None

        if self._api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self._api_key)
            except Exception as e:
                logger.warning(f"[GeminiProvider] Failed to instantiate genai.Client: {e}")

    @property
    def provider_id(self) -> str:
        return "gemini"

    @property
    def provider_name(self) -> str:
        return "Google Gemini"

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key and self._api_key.strip())

    def get_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                id="gemini-1.5-flash",
                name="Gemini 1.5 Flash",
                provider=self.provider_id,
                description="High-speed, multimodal model with 1M token context window for fast generation and analysis.",
                context_window=1000000,
                supports_streaming=True,
                is_default=(getattr(settings, "GEMINI_DEFAULT_MODEL", "gemini-1.5-flash") == "gemini-1.5-flash"),
            ),
            ModelInfo(
                id="gemini-1.5-pro",
                name="Gemini 1.5 Pro",
                provider=self.provider_id,
                description="Advanced reasoning model with 2M token context window for massive repository synthesis.",
                context_window=2000000,
                supports_streaming=True,
                is_default=(getattr(settings, "GEMINI_DEFAULT_MODEL", "") == "gemini-1.5-pro"),
            ),
            ModelInfo(
                id="gemini-2.0-flash",
                name="Gemini 2.0 Flash",
                provider=self.provider_id,
                description="Next-generation multimodal model with enhanced real-time reasoning and agentic tools.",
                context_window=1000000,
                supports_streaming=True,
                is_default=False,
            ),
            ModelInfo(
                id="gemini-2.0-flash-lite",
                name="Gemini 2.0 Flash Lite",
                provider=self.provider_id,
                description="Ultra-cost-efficient lightweight Gemini model for high-throughput operational tasks.",
                context_window=1000000,
                supports_streaming=True,
                is_default=False,
            ),
        ]

    def supports_model(self, model_id: str) -> bool:
        norm = model_id.lower()
        return norm.startswith("gemini-") or norm in self.SUPPORTED_MODELS

    def _resolve_model(self, model_id: str) -> str:
        norm = model_id.lower()
        return self.MODEL_ALIASES.get(norm, model_id)

    def _prepare_payload(self, request: LLMGenerateRequest):
        from google.genai import types

        system_prompts: List[str] = []
        contents: List[types.Content] = []

        for msg in request.messages:
            role = msg.role.lower() if hasattr(msg, "role") else "user"
            content = msg.content if hasattr(msg, "content") else str(msg)

            if role == "system":
                if isinstance(content, list):
                    text_parts = [p.get("text", "") for p in content if isinstance(p, dict) and "text" in p]
                    system_prompts.append(" ".join(text_parts))
                else:
                    system_prompts.append(str(content))
            else:
                gemini_role = "user" if role == "user" else "model"
                parts = []
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and "text" in part:
                            parts.append(types.Part.from_text(text=part["text"]))
                        elif isinstance(part, str):
                            parts.append(types.Part.from_text(text=part))
                else:
                    parts.append(types.Part.from_text(text=str(content)))

                contents.append(types.Content(role=gemini_role, parts=parts))

        system_instruction = "\n\n".join(system_prompts) if system_prompts else None
        target_model = self._resolve_model(request.model)

        config_kwargs = {}
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
        if request.temperature is not None:
            config_kwargs["temperature"] = request.temperature
        if request.max_tokens:
            config_kwargs["max_output_tokens"] = request.max_tokens

        config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None
        return target_model, contents, config

    async def generate(self, request: LLMGenerateRequest) -> LLMGenerateResponse:
        if not self.is_configured or not self._client:
            raise ProviderNotConfiguredError(
                f"Google Gemini provider is not configured. Please set GEMINI_API_KEY environment variable."
            )

        model, contents, config = self._prepare_payload(request)

        try:
            response = await self._client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )

            text_content = response.text or ""
            prompt_tokens = 0
            candidate_tokens = 0
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
                candidate_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0

            usage = TokenUsage(
                input_tokens=prompt_tokens,
                output_tokens=candidate_tokens,
                total_tokens=prompt_tokens + candidate_tokens,
            )

            finish_reason = "stop"
            if hasattr(response, "candidates") and response.candidates:
                first_cand = response.candidates[0]
                if hasattr(first_cand, "finish_reason") and first_cand.finish_reason:
                    finish_reason = str(first_cand.finish_reason).lower()

            return LLMGenerateResponse(
                content=text_content,
                model=model,
                provider=self.provider_id,
                finish_reason=finish_reason,
                usage=usage,
            )

        except Exception as e:
            err_str = str(e)
            if "API_KEY_INVALID" in err_str or "401" in err_str or "unauthenticated" in err_str.lower():
                raise ProviderAuthenticationError(f"Google Gemini authentication failed: {err_str}")
            elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "rate limit" in err_str.lower():
                raise ProviderRateLimitError(f"Google Gemini rate limit exceeded: {err_str}")
            elif "deadline" in err_str.lower() or "timeout" in err_str.lower():
                raise ProviderTimeoutError(f"Google Gemini request timed out: {err_str}")
            else:
                raise ProviderAPIError(f"Google Gemini API error: {err_str}")

    async def generate_stream(
        self, request: LLMGenerateRequest
    ) -> AsyncIterator[LLMStreamChunk]:
        if not self.is_configured or not self._client:
            raise ProviderNotConfiguredError(
                f"Google Gemini provider is not configured. Please set GEMINI_API_KEY environment variable."
            )

        model, contents, config = self._prepare_payload(request)

        try:
            stream = await self._client.aio.models.generate_content_stream(
                model=model,
                contents=contents,
                config=config,
            )

            async for chunk in stream:
                chunk_text = chunk.text or ""
                if chunk_text:
                    yield LLMStreamChunk(
                        content=chunk_text,
                        model=request.model,
                        is_finished=False,
                    )

            yield LLMStreamChunk(
                content="",
                model=request.model,
                is_finished=True,
                finish_reason="stop",
            )

        except Exception as e:
            err_str = str(e)
            if "API_KEY_INVALID" in err_str or "401" in err_str or "unauthenticated" in err_str.lower():
                raise ProviderAuthenticationError(f"Google Gemini authentication failed: {err_str}")
            elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "rate limit" in err_str.lower():
                raise ProviderRateLimitError(f"Google Gemini rate limit exceeded: {err_str}")
            elif "deadline" in err_str.lower() or "timeout" in err_str.lower():
                raise ProviderTimeoutError(f"Google Gemini stream timed out: {err_str}")
            else:
                raise ProviderAPIError(f"Google Gemini streaming error: {err_str}")

