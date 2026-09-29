import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel

from backend.app.config import settings
from backend.app.schemas.llm import ChatMessage, LLMGenerateRequest
from backend.app.services.evaluation.policies import EvaluationPolicy
from backend.app.services.evaluation.schemas import (
    CheckResult,
    CheckType,
    EvaluationContext,
    FindingStatus,
)
from backend.app.services.llm.factory import LLMProviderFactory, get_llm_factory

logger = logging.getLogger("evaluation.base")

T = TypeVar("T", bound=BaseModel)


class BaseEvaluator(ABC):
    """
    Abstract base evaluator interface.
    All evaluators must implement evaluate() and declare their CheckType.
    Evaluators must NOT modify the task output directly or execute arbitrary tools.
    """
    check_type: CheckType

    @abstractmethod
    async def evaluate(
        self,
        ctx: EvaluationContext,
        policy: EvaluationPolicy,
    ) -> CheckResult:
        """
        Executes verification check against the evaluation context.
        """
        pass


class DeterministicEvaluator(BaseEvaluator):
    """
    Base class for fast, deterministic evaluators (e.g. format, citations, safety regex)
    that run without requiring an LLM inference call.
    """
    pass


class LLMEvaluator(BaseEvaluator):
    """
    Base class for semantic evaluators (e.g. grounding, completeness)
    that invoke a configured evaluation model and strictly validate output via Pydantic.
    """

    def __init__(
        self,
        llm_factory: Optional[LLMProviderFactory] = None,
        evaluator_model: Optional[str] = None,
        evaluator_provider: Optional[str] = None,
    ) -> None:
        self.llm_factory = llm_factory or get_llm_factory()
        self.evaluator_model = evaluator_model or settings.EVALUATOR_MODEL
        self.evaluator_provider = evaluator_provider or settings.EVALUATOR_MODEL_PROVIDER

    def _extract_json(self, raw: str) -> Dict[str, Any]:
        """
        Safely extracts and parses JSON from model output, handling code fences.
        """
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1)

        return json.loads(cleaned)

    async def _call_structured_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> T:
        """
        Executes a prompt against the evaluator model and validates the JSON response
        into a typed Pydantic model. Never parses unstructured arbitrary natural language.
        """
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt),
        ]

        req = LLMGenerateRequest(
            model=self.evaluator_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        try:
            if self.evaluator_provider:
                try:
                    provider = self.llm_factory.get_provider_for_model(
                        self.evaluator_model,
                        provider_id=self.evaluator_provider,
                    )
                except TypeError:
                    provider = self.llm_factory.get_provider_for_model(self.evaluator_model)
            else:
                provider = self.llm_factory.get_provider_for_model(self.evaluator_model)

            resp = await provider.generate(req)
            parsed_json = self._extract_json(resp.content)
            return response_model.model_validate(parsed_json)

        except Exception as exc:
            logger.warning(
                f"[LLMEvaluator] Structured generation failed ({exc}) using model '{self.evaluator_model}'."
            )
            raise exc
