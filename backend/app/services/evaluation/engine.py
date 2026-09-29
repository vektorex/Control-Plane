import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from backend.app.config import settings
from backend.app.db.models.task import Task
from backend.app.services.evaluation.aggregation import EvaluationAggregator
from backend.app.services.evaluation.base import BaseEvaluator
from backend.app.services.evaluation.evaluators.citation import CitationEvaluator
from backend.app.services.evaluation.evaluators.completeness import CompletenessEvaluator
from backend.app.services.evaluation.evaluators.format import FormatEvaluator
from backend.app.services.evaluation.evaluators.grounding import GroundingEvaluator
from backend.app.services.evaluation.evaluators.safety import SafetyEvaluator
from backend.app.services.evaluation.policies import EvaluationPolicy
from backend.app.services.evaluation.reviser import ControlledReviser
from backend.app.services.evaluation.schemas import (
    CheckResult,
    EvaluationContext,
    EvaluationMode,
    EvaluationRecommendation,
    EvaluationResult,
    EvaluationStatus,
)
from backend.app.services.llm.factory import LLMProviderFactory, get_llm_factory

logger = logging.getLogger("evaluation.engine")


class EvaluationEngine:
    """
    Main Evaluation & Verification Engine that coordinates grounding, completeness,
    citation, format, and safety checks on draft task outputs.
    
    The evaluator does NOT modify outputs directly.
    """

    def __init__(
        self,
        llm_factory: Optional[LLMProviderFactory] = None,
        evaluator_model: Optional[str] = None,
        evaluator_provider: Optional[str] = None,
        reviser: Optional[ControlledReviser] = None,
    ) -> None:
        self.llm_factory = llm_factory or get_llm_factory()
        self.evaluator_model = evaluator_model or settings.EVALUATOR_MODEL
        self.evaluator_provider = evaluator_provider or settings.EVALUATOR_MODEL_PROVIDER

        # Instantiate evaluators
        self.grounding_evaluator = GroundingEvaluator(
            llm_factory=self.llm_factory,
            evaluator_model=self.evaluator_model,
            evaluator_provider=self.evaluator_provider,
        )
        self.completeness_evaluator = CompletenessEvaluator(
            llm_factory=self.llm_factory,
            evaluator_model=self.evaluator_model,
            evaluator_provider=self.evaluator_provider,
        )
        self.citation_evaluator = CitationEvaluator()
        self.format_evaluator = FormatEvaluator()
        self.safety_evaluator = SafetyEvaluator()

        self.reviser = reviser or ControlledReviser(
            llm_factory=self.llm_factory,
            model_name=settings.GENERATION_DEFAULT_MODEL,
            provider_id=settings.GENERATION_MODEL_PROVIDER,
        )

    async def evaluate(
        self,
        task: Any,
        output_text: Optional[str] = None,
        context_items: Optional[List[Dict[str, Any]]] = None,
        retrieval_sources: Optional[List[Dict[str, Any]]] = None,
        web_sources: Optional[List[Dict[str, Any]]] = None,
        expected_format: Optional[str] = None,
        required_sections: Optional[List[str]] = None,
        policy: Optional[EvaluationPolicy] = None,
        attempt: int = 1,
    ) -> EvaluationResult:
        """
        Runs configured verification checks and produces a structured EvaluationResult.
        """
        start_time = time.perf_counter()

        if isinstance(task, EvaluationContext):
            if output_text is not None:
                ctx = task.model_copy(update={"output_text": output_text, "attempt": attempt})
            else:
                ctx = task
            active_policy = policy or EvaluationPolicy.from_mode(mode=settings.EVALUATION_DEFAULT_MODE)
        else:
            active_policy = policy or EvaluationPolicy.from_mode(
                mode=getattr(task, "evaluation_mode", None) or settings.EVALUATION_DEFAULT_MODE,
                strict=getattr(task, "strict_evaluation", False) or False,
            )
            # Build sanitized EvaluationContext
            ctx = EvaluationContext(
                task_id=str(getattr(task, "id", getattr(task, "task_id", "task_eval"))),
                task_title=getattr(task, "title", getattr(task, "task_title", "")) or "",
                task_instructions=getattr(task, "instructions", None) or getattr(task, "description", None) or getattr(task, "task_instructions", "") or "",
                output_text=output_text or getattr(task, "output_text", "") or "",
                context_items=context_items or getattr(task, "context_items", []) or [],
                retrieval_sources=retrieval_sources or getattr(task, "retrieval_sources", []) or [],
                web_sources=web_sources or getattr(task, "web_sources", []) or [],
                expected_format=expected_format or getattr(task, "expected_format", None),
                required_sections=required_sections or getattr(task, "required_sections", []) or [],
                attempt=attempt or getattr(task, "attempt", 1),
            )

        # Mode OFF: Skip evaluation immediately
        if active_policy.mode == EvaluationMode.OFF:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            return EvaluationResult(
                status=EvaluationStatus.SKIPPED,
                recommendation=EvaluationRecommendation.ACCEPT,
                mode=EvaluationMode.OFF,
                attempt=attempt,
                checks=[],
                findings=[],
                summary="Evaluation policy is turned off. Verification skipped.",
                duration_ms=elapsed_ms,
                revision_suggested=False,
            )

        # Select which evaluators to run based on policy
        checks_to_run: List[Tuple[str, BaseEvaluator]] = []

        if active_policy.enable_safety:
            checks_to_run.append(("safety", self.safety_evaluator))

        if active_policy.enable_format:
            checks_to_run.append(("format", self.format_evaluator))

        if active_policy.enable_citation:
            checks_to_run.append(("citation", self.citation_evaluator))

        if active_policy.enable_completeness:
            checks_to_run.append(("completeness", self.completeness_evaluator))

        if active_policy.enable_grounding:
            checks_to_run.append(("grounding", self.grounding_evaluator))

        check_results: List[CheckResult] = []

        # Run checks (deterministic checks first, then LLM checks)
        for name, evaluator in checks_to_run:
            try:
                res = await evaluator.evaluate(ctx, active_policy)
                check_results.append(res)
            except Exception as exc:
                logger.error(f"[EvaluationEngine] Check '{name}' raised unhandled exception: {exc}")
                # Record error safely without crashing the evaluation pipeline
                from backend.app.services.evaluation.schemas import FindingStatus
                check_results.append(
                    CheckResult(
                        type=evaluator.check_type,
                        status=FindingStatus.WARNING,
                        confidence=0.5,
                        description=f"Evaluator error: {exc}",
                        issues=[f"Evaluator failed: {exc}"],
                        findings=[],
                        metadata={"error": str(exc)},
                        duration_ms=0,
                    )
                )

        total_duration_ms = int((time.perf_counter() - start_time) * 1000)
        return EvaluationAggregator.aggregate(
            checks=check_results,
            policy=active_policy,
            attempt=attempt,
            duration_ms=total_duration_ms,
        )

    async def revise_and_re_evaluate(
        self,
        task: Any = None,
        draft_output: Optional[str] = None,
        initial_evaluation: Optional[EvaluationResult] = None,
        context_items: Optional[List[Dict[str, Any]]] = None,
        retrieval_sources: Optional[List[Dict[str, Any]]] = None,
        web_sources: Optional[List[Dict[str, Any]]] = None,
        policy: Optional[EvaluationPolicy] = None,
        model_override: Optional[str] = None,
        max_attempts: Optional[int] = None,
        ctx: Optional[EvaluationContext] = None,
        initial_result: Optional[EvaluationResult] = None,
    ) -> Tuple[str, EvaluationResult, int]:
        """
        Executes bounded revision loop up to MAX_REVISION_ATTEMPTS.
        Returns: (final_output, final_evaluation_result, revision_attempts_made)
        """
        target_task = task or ctx
        current_eval = initial_evaluation or initial_result

        if isinstance(target_task, EvaluationContext):
            task_title = target_task.task_title
            task_instructions = target_task.task_instructions
            task_id = target_task.task_id
            current_output = draft_output or target_task.output_text
            expected_format = target_task.expected_format
            ctx_items = context_items or target_task.context_items
        else:
            task_title = getattr(target_task, "title", "") or ""
            task_instructions = getattr(target_task, "instructions", None) or getattr(target_task, "description", "") or ""
            task_id = str(getattr(target_task, "id", "task"))
            current_output = draft_output or ""
            expected_format = getattr(target_task, "expected_format", None)
            ctx_items = context_items or []

        active_policy = policy or EvaluationPolicy.from_mode(
            mode=getattr(target_task, "evaluation_mode", None) or settings.EVALUATION_DEFAULT_MODE,
            strict=getattr(target_task, "strict_evaluation", False) or False,
        )
        allowed_revisions = max_attempts if max_attempts is not None else active_policy.max_revision_attempts

        revision_count = 0

        while revision_count < allowed_revisions and current_eval.recommendation == EvaluationRecommendation.REVISE:
            revision_count += 1
            logger.info(
                f"[EvaluationEngine] Executing revision attempt {revision_count}/{allowed_revisions} for task '{task_id}'."
            )

            revised_text = await self.reviser.revise(
                task_title=task_title,
                task_instructions=task_instructions,
                draft_output=current_output,
                evaluation_result=current_eval,
                context_items=ctx_items,
                expected_format=expected_format,
                model_override=model_override,
            )

            current_output = revised_text

            # Re-evaluate the revised output
            current_eval = await self.evaluate(
                task=target_task,
                output_text=current_output,
                context_items=ctx_items,
                retrieval_sources=retrieval_sources,
                web_sources=web_sources,
                policy=active_policy,
                attempt=revision_count + 1,
            )

            if current_eval.status == EvaluationStatus.PASSED:
                logger.info(
                    f"[EvaluationEngine] Revision attempt {revision_count} PASSED for task '{task_id}'."
                )
                break

        return current_output, current_eval, revision_count


_evaluation_engine_instance: Optional[EvaluationEngine] = None


def get_evaluation_engine() -> EvaluationEngine:
    global _evaluation_engine_instance
    if _evaluation_engine_instance is None:
        _evaluation_engine_instance = EvaluationEngine()
    return _evaluation_engine_instance
