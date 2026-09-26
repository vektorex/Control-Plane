import pytest
from typing import AsyncIterator, List
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.llm import (
    LLMGenerateRequest,
    LLMGenerateResponse,
    LLMStreamChunk,
    TokenUsage,
)
from backend.app.schemas.models import ModelInfo
from backend.app.services.llm.base import BaseLLMProvider
from backend.app.services.llm.factory import LLMProviderFactory, get_llm_factory


class MockTestProvider(BaseLLMProvider):
    """
    Mock LLM Provider for deterministic unit testing at the service boundary.
    """

    def __init__(self, configured: bool = True, should_fail: bool = False, fail_type: str = "general"):
        self._configured = configured
        self._should_fail = should_fail
        self._fail_type = fail_type

    @property
    def provider_id(self) -> str:
        return "mock_provider"

    @property
    def provider_name(self) -> str:
        return "Mock Test Provider"

    @property
    def is_configured(self) -> bool:
        return self._configured

    def get_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                id="mock-model-v1",
                name="Mock Model v1",
                provider=self.provider_id,
                description="Mock testing model",
                context_window=32000,
                supports_streaming=True,
                is_default=True,
            )
        ]

    def supports_model(self, model_id: str) -> bool:
        return model_id in ["mock-model-v1", "mock-custom"]

    async def generate(self, request: LLMGenerateRequest) -> LLMGenerateResponse:
        if not self._configured:
            from backend.app.core.errors import ProviderNotConfiguredError
            raise ProviderNotConfiguredError("Mock provider is not configured.")

        if self._should_fail:
            from backend.app.core.errors import (
                ProviderAuthenticationError,
                ProviderRateLimitError,
                ProviderAPIError,
            )
            if self._fail_type == "auth":
                raise ProviderAuthenticationError("Mock authentication failure.")
            elif self._fail_type == "rate_limit":
                raise ProviderRateLimitError("Mock rate limit exceeded.")
            else:
                raise ProviderAPIError("Mock upstream API failure.")

        return LLMGenerateResponse(
            content=f"Mock response for: {request.messages[-1].content}",
            model=request.model,
            provider=self.provider_id,
            usage=TokenUsage(input_tokens=15, output_tokens=25, total_tokens=40),
            finish_reason="stop",
        )

    async def generate_stream(
        self, request: LLMGenerateRequest
    ) -> AsyncIterator[LLMStreamChunk]:
        if not self._configured:
            from backend.app.core.errors import ProviderNotConfiguredError
            raise ProviderNotConfiguredError("Mock provider is not configured.")

        if self._should_fail:
            from backend.app.core.errors import ProviderAPIError
            raise ProviderAPIError("Mock streaming failure.")

        tokens = ["Mock", " ", "streamed", " ", "response", "!"]
        for idx, token in enumerate(tokens):
            is_last = idx == len(tokens) - 1
            yield LLMStreamChunk(
                content=token,
                model=request.model,
                provider=self.provider_id,
                is_finished=is_last,
                usage=TokenUsage(input_tokens=12, output_tokens=6, total_tokens=18) if is_last else None,
                finish_reason="stop" if is_last else None,
            )


@pytest.fixture
def mock_factory():
    factory = LLMProviderFactory()
    mock_provider = MockTestProvider(configured=True)
    factory.register_provider(mock_provider)
    return factory


@pytest.fixture
def client(mock_factory):
    app.dependency_overrides[get_llm_factory] = lambda: mock_factory
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
