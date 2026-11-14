import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional

from backend.app.core.logging import logger
from backend.app.schemas.llm import ChatMessage, LLMGenerateRequest
from backend.app.services.ai_gateway.errors import (
    ModelNotFoundError,
    ProviderUnavailableError,
    ProviderTimeoutError,
    RateLimitedError,
    CapabilityUnsupportedError,
    GatewayError,
)
from backend.app.services.ai_gateway.requests import GatewayRequest
from backend.app.services.ai_gateway.responses import GatewayResponse, GatewayUsage
from backend.app.services.ai_gateway.streaming import NormalizedStreamEvent
from backend.app.services.llm.base import BaseLLMProvider
from backend.app.services.models.registry import default_model_registry


class ModelProviderAdapter(ABC):
    """
    Abstract interface for AI Gateway provider adapters.
    Isolates all provider-specific SDK logic, error formats, and protocols.
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Normalized unique identifier for the provider (e.g. 'openai', 'mock')."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Display name of the provider."""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Whether the provider has active credentials and can execute requests."""
        pass

    @abstractmethod
    async def generate(self, request: GatewayRequest) -> GatewayResponse:
        """Execute model generation and return a normalized GatewayResponse."""
        pass

    @abstractmethod
    async def generate_stream(self, request: GatewayRequest) -> AsyncIterator[Dict[str, Any]]:
        """Execute streaming generation yielding normalized stream event dicts."""
        pass

    @abstractmethod
    def validate_model(self, model: str) -> bool:
        """Validate whether this provider supports the given model identifier."""
        pass

    @abstractmethod
    def get_capabilities(self, model: str) -> List[str]:
        """Return list of supported capabilities for the model."""
        pass

    @abstractmethod
    def normalize_usage(self, raw_usage: Any) -> GatewayUsage:
        """Convert provider-specific usage dict or object into normalized GatewayUsage."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform operational health probe without generating full completions."""
        pass


class BaseProviderAdapter(ModelProviderAdapter):
    """
    Universal adapter that wraps any BaseLLMProvider implementation,
    seamlessly unifying legacy and mock providers under the AI Gateway contract.
    """

    def __init__(self, provider: BaseLLMProvider):
        self._provider = provider

    @property
    def provider(self) -> BaseLLMProvider:
        return self._provider

    @property
    def provider_id(self) -> str:
        return self._provider.provider_id

    @property
    def provider_name(self) -> str:
        return self._provider.provider_name

    @property
    def is_configured(self) -> bool:
        return self._provider.is_configured

    def validate_model(self, model: str) -> bool:
        # Check against registry first, then provider
        model_def = default_model_registry.get_model(model, provider=self.provider_id)
        if model_def and model_def.enabled:
            return True
        return self._provider.supports_model(model)

    def get_capabilities(self, model: str) -> List[str]:
        model_def = default_model_registry.get_model(model, provider=self.provider_id)
        if model_def:
            return list(model_def.capabilities)
        return ["streaming", "chat"]

    def normalize_usage(self, raw_usage: Any) -> GatewayUsage:
        if raw_usage is None:
            return GatewayUsage(input_tokens=0, output_tokens=0, total_tokens=0, usage_source="estimated")
        
        in_tok = getattr(raw_usage, "input_tokens", None) or getattr(raw_usage, "prompt_tokens", None)
        out_tok = getattr(raw_usage, "output_tokens", None) or getattr(raw_usage, "completion_tokens", None)
        tot_tok = getattr(raw_usage, "total_tokens", None)

        if isinstance(raw_usage, dict):
            in_tok = raw_usage.get("input_tokens", raw_usage.get("prompt_tokens", in_tok))
            out_tok = raw_usage.get("output_tokens", raw_usage.get("completion_tokens", out_tok))
            tot_tok = raw_usage.get("total_tokens", tot_tok)

        in_tok = int(in_tok or 0)
        out_tok = int(out_tok or 0)
        tot_tok = int(tot_tok or (in_tok + out_tok))

        return GatewayUsage(
            input_tokens=in_tok,
            output_tokens=out_tok,
            total_tokens=tot_tok,
            usage_source="provider",
        )

    def _validate_request_capabilities(self, request: GatewayRequest) -> None:
        """
        Validates that the target model satisfies any multimodal capabilities present in request.
        """
        has_images = any(
            isinstance(m.get("content"), list)
            and any(isinstance(p, dict) and p.get("type") in ("image", "input_image") for p in m["content"])
            for m in request.messages
        )
        has_audio = any(
            isinstance(m.get("content"), list)
            and any(isinstance(p, dict) and p.get("type") in ("audio", "audio_input") for p in m["content"])
            for m in request.messages
        )
        has_video = any(
            isinstance(m.get("content"), list)
            and any(isinstance(p, dict) and p.get("type") in ("video", "video_frame") for p in m["content"])
            for m in request.messages
        )

        if not (has_images or has_audio or has_video):
            return

        model_def = default_model_registry.get_model(request.model, provider=self.provider_id)

        if has_images:
            supports_vision = bool(
                model_def
                and (
                    model_def.supports_vision
                    or "vision" in model_def.capabilities
                    or "image_input" in model_def.capabilities
                    or "multimodal_input" in model_def.capabilities
                )
            )
            if not supports_vision:
                raise CapabilityUnsupportedError(
                    f"Model '{request.model}' on provider '{self.provider_id}' does not support vision or image inputs.",
                    details={"model": request.model, "required_capability": "vision"},
                )

        if has_audio:
            supports_audio = bool(
                model_def
                and (
                    getattr(model_def, "supports_audio", False)
                    or "audio_input" in model_def.capabilities
                    or "audio_transcription" in model_def.capabilities
                )
            )
            if not supports_audio:
                raise CapabilityUnsupportedError(
                    f"Model '{request.model}' on provider '{self.provider_id}' does not support direct audio inputs.",
                    details={"model": request.model, "required_capability": "audio_input"},
                )

        if has_video:
            supports_video = bool(
                model_def
                and (
                    getattr(model_def, "supports_video", False)
                    or "video" in model_def.capabilities
                    or (model_def and model_def.supports_vision)
                )
            )
            if not supports_video:
                raise CapabilityUnsupportedError(
                    f"Model '{request.model}' on provider '{self.provider_id}' does not support video capabilities.",
                    details={"model": request.model, "required_capability": "video"},
                )

    def _convert_messages(self, request: GatewayRequest) -> List[ChatMessage]:
        converted: List[ChatMessage] = []
        if request.system_instruction:
            converted.append(ChatMessage(role="system", content=request.system_instruction))

        for msg in request.messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if isinstance(content, list):
                converted.append(ChatMessage(role=role, content=content))
            else:
                converted.append(ChatMessage(role=role, content=str(content)))
        return converted

    async def generate(self, request: GatewayRequest) -> GatewayResponse:
        self._validate_request_capabilities(request)
        start_time = time.perf_counter()
        req_id = request.metadata.get("request_id") or str(uuid.uuid4())

        try:
            llm_req = LLMGenerateRequest(
                model=request.model,
                messages=self._convert_messages(request),
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=False,
            )
            raw_res = await self._provider.generate(llm_req)
            latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            usage = self.normalize_usage(raw_res.usage)

            return GatewayResponse(
                request_id=req_id,
                provider=self.provider_id,
                model=raw_res.model or request.model,
                content=raw_res.content,
                finish_reason=raw_res.finish_reason or "stop",
                usage=usage,
                latency_ms=latency_ms,
                metadata={
                    "adapter": self.__class__.__name__,
                    "provider_configured": self.is_configured,
                },
            )
        except Exception as exc:
            self._handle_provider_error(exc)

    async def generate_stream(self, request: GatewayRequest) -> AsyncIterator[Dict[str, Any]]:
        self._validate_request_capabilities(request)
        try:
            llm_req = LLMGenerateRequest(
                model=request.model,
                messages=self._convert_messages(request),
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True,
            )
            full_content = ""
            latest_usage = None
            finish_reason = "stop"

            async for chunk in self._provider.generate_stream(llm_req):
                delta = getattr(chunk, "delta", None) or getattr(chunk, "content", "")
                if delta:
                    full_content += delta
                    yield NormalizedStreamEvent.delta(delta, full_content=full_content)
                if chunk.usage:
                    latest_usage = self.normalize_usage(chunk.usage)
                if getattr(chunk, "finish_reason", None):
                    finish_reason = chunk.finish_reason

            if latest_usage:
                yield NormalizedStreamEvent.usage(latest_usage.model_dump())
            yield NormalizedStreamEvent.completed(finish_reason=finish_reason)

        except Exception as exc:
            self._handle_provider_error(exc)

    async def health_check(self) -> Dict[str, Any]:
        """Default health probe checking provider configuration and status."""
        configured = self.is_configured
        return {
            "provider": self.provider_id,
            "configured": configured,
            "status": "healthy" if configured else "unavailable",
            "models_count": len(self._provider.get_models()),
        }

    def _handle_provider_error(self, exc: Exception) -> None:
        """Translate raw provider exceptions into normalized Gateway errors."""
        from backend.app.core.errors import ProviderAuthenticationError, ProviderRateLimitError
        if isinstance(exc, (ProviderAuthenticationError, ProviderRateLimitError, GatewayError)):
            raise exc

        err_msg = str(exc)
        err_type = type(exc).__name__.lower()

        if "not found" in err_msg.lower() or "notfound" in err_type:
            raise ModelNotFoundError(f"Model error on provider '{self.provider_id}': {err_msg}")
        if "rate" in err_msg.lower() or "429" in err_msg:
            raise RateLimitedError(f"Provider '{self.provider_id}' rate limit exceeded: {err_msg}")
        if "timeout" in err_msg.lower() or "timed out" in err_msg.lower():
            raise ProviderTimeoutError(f"Provider '{self.provider_id}' timed out: {err_msg}")
        if "unauthorized" in err_msg.lower() or "auth" in err_msg.lower():
            raise ProviderAuthenticationError(f"Provider '{self.provider_id}' authentication failure: {err_msg}")
        if "notconfigured" in err_type:
            raise ProviderUnavailableError(f"Provider '{self.provider_id}' is unavailable or not configured.")
        
        # Generic provider error
        raise ProviderUnavailableError(f"Provider '{self.provider_id}' encountered error: {err_msg}")


class OpenAIAdapter(BaseProviderAdapter):
    """OpenAI Adapter wrapping official AsyncOpenAI SDK."""
    def __init__(self, provider: Optional[BaseLLMProvider] = None):
        if provider is None:
            from backend.app.services.llm.providers.openai import OpenAIProvider
            provider = OpenAIProvider()
        super().__init__(provider)


class MockAdapter(BaseProviderAdapter):
    """Mock Provider Adapter for offline development and deterministic unit testing."""
    def __init__(self, provider: Optional[BaseLLMProvider] = None):
        if provider is None:
            from backend.app.services.llm.providers.mock import MockLLMProvider
            provider = MockLLMProvider()
        super().__init__(provider)

    @property
    def is_configured(self) -> bool:
        return True


class AnthropicAdapter(BaseProviderAdapter):
    """Anthropic Claude Provider Adapter for AI Gateway runtime."""
    def __init__(self, provider: Optional[BaseLLMProvider] = None):
        if provider is None:
            from backend.app.services.llm.providers.anthropic import AnthropicProvider
            provider = AnthropicProvider()
        super().__init__(provider)


class GeminiAdapter(BaseProviderAdapter):
    """Google Gemini Provider Adapter for AI Gateway runtime."""
    def __init__(self, provider: Optional[BaseLLMProvider] = None):
        if provider is None:
            from backend.app.services.llm.providers.gemini import GeminiProvider
            provider = GeminiProvider()
        super().__init__(provider)

