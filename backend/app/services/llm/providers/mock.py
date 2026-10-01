import asyncio
from typing import AsyncIterator, List, Optional
from backend.app.schemas.llm import (
    ChatMessage,
    LLMGenerateRequest,
    LLMGenerateResponse,
    LLMStreamChunk,
    TokenUsage,
)
from backend.app.schemas.models import ModelInfo
from backend.app.services.llm.base import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """
    Mock LLM Provider for testing, fallback simulation, and offline orchestration.
    """

    def __init__(self, should_fail: bool = False, fail_count: int = 0):
        self.should_fail = should_fail
        self.fail_count = fail_count
        self._current_failures = 0

    @property
    def provider_id(self) -> str:
        return "mock"

    @property
    def provider_name(self) -> str:
        return "Mock Provider"

    @property
    def is_configured(self) -> bool:
        return True

    def get_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                id="mock-model-v1",
                name="Mock Standard Model",
                provider=self.provider_id,
                description="Mock general-purpose model for testing and fallback validation.",
                context_window=64000,
                supports_streaming=True,
                is_default=True,
            ),
            ModelInfo(
                id="mock-planner-v1",
                name="Mock Fast Planner",
                provider=self.provider_id,
                description="Mock lightweight model specialized in planning.",
                context_window=32000,
                supports_streaming=True,
                is_default=False,
            ),
            ModelInfo(
                id="mock-fallback-v1",
                name="Mock Fallback Model",
                provider=self.provider_id,
                description="Mock secondary model for resilience failover tests.",
                context_window=128000,
                supports_streaming=True,
                is_default=False,
            ),
        ]

    def supports_model(self, model_id: str) -> bool:
        if model_id.startswith("mock-") or model_id in ["mock-model-v1", "mock-planner-v1", "mock-fallback-v1"]:
            return True
        return False

    async def generate(self, request: LLMGenerateRequest) -> LLMGenerateResponse:
        if self.should_fail or (self._current_failures < self.fail_count):
            self._current_failures += 1
            raise RuntimeError(f"Simulated Mock Provider failure for model '{request.model}'")

        # Check if this is a planning prompt (asking for JSON plan)
        last_msg = request.messages[-1].content if request.messages else ""
        if "Plan this task using only available capabilities" in last_msg or "Execution Planner" in (request.messages[0].content if request.messages else ""):
            content = """{
  "goal": "Execute synthesized workflow with validated context and generation",
  "steps": [
    {
      "id": "step_1",
      "type": "context",
      "description": "Load primary task context"
    },
    {
      "id": "step_2",
      "type": "generate",
      "description": "Synthesize response with grounded context",
      "model": "mock-model-v1",
      "temperature": 0.2
    }
  ]
}"""
        else:
            content = f"Mock LLM generated output for model '{request.model}'. Task processed successfully."

        prompt_tokens = sum(len(m.content.split()) for m in request.messages) * 2
        completion_tokens = len(content.split()) * 2
        total_tokens = prompt_tokens + completion_tokens

        return LLMGenerateResponse(
            content=content,
            model=request.model,
            provider=self.provider_id,
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                input_tokens=prompt_tokens,
                output_tokens=completion_tokens,
            ),
            latency_ms=15,
            finish_reason="stop",
        )

    async def generate_stream(
        self, request: LLMGenerateRequest
    ) -> AsyncIterator[LLMStreamChunk]:
        if self.should_fail or (self._current_failures < self.fail_count):
            self._current_failures += 1
            raise RuntimeError(f"Simulated Mock Provider streaming failure for model '{request.model}'")

        tokens = ["Mock ", "LLM ", "streamed ", "response ", "for ", f"{request.model}.", " Done."]
        for idx, tok in enumerate(tokens):
            await asyncio.sleep(0.005)
            is_last = idx == len(tokens) - 1
            yield LLMStreamChunk(
                content=tok,
                delta=tok,
                model=request.model,
                index=idx,
                finish_reason="stop" if is_last else None,
                usage=TokenUsage(input_tokens=20, output_tokens=len(tokens), total_tokens=20 + len(tokens)) if is_last else None,
            )
