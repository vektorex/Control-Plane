from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional
from backend.app.schemas.llm import (
    LLMGenerateRequest,
    LLMGenerateResponse,
    LLMStreamChunk,
)
from backend.app.schemas.models import ModelInfo


class BaseLLMProvider(ABC):
    """
    Abstract Base Class for LLM Provider Adapters.
    Encapsulates all vendor-specific SDK calls, error translations,
    and streaming protocols behind a unified interface.
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique identifier for the provider (e.g. 'openai', 'anthropic', 'gemini')."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Display name of the provider."""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Whether the provider has active API credentials and is ready for traffic."""
        pass

    @abstractmethod
    def get_models(self) -> List[ModelInfo]:
        """Return list of models supported and recognized by this provider."""
        pass

    @abstractmethod
    def supports_model(self, model_id: str) -> bool:
        """Check if this provider handles the specified model identifier."""
        pass

    @abstractmethod
    async def generate(self, request: LLMGenerateRequest) -> LLMGenerateResponse:
        """
        Execute standard completion request.
        Translates vendor response into unified LLMGenerateResponse.
        """
        pass

    @abstractmethod
    async def generate_stream(
        self, request: LLMGenerateRequest
    ) -> AsyncIterator[LLMStreamChunk]:
        """
        Execute streaming completion request.
        Yields normalized LLMStreamChunk tokens as they arrive.
        """
        pass
