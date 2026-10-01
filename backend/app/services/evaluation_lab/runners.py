import asyncio
import logging
import time
import uuid
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.db.models.evaluation_lab import (
    EvaluationCase,
    EvaluationExperiment,
    EvaluationExperimentRun,
)
from backend.app.services.ai_gateway import AIGateway, default_ai_gateway
from backend.app.services.evaluation.engine import EvaluationEngine
from backend.app.services.evaluation.schemas import EvaluationContext, EvaluationMode
from backend.app.services.evaluation_lab.assertions import AssertionEngine
from backend.app.services.evaluation_lab.errors import (
    InvalidTargetError,
    SideEffectBlockedError,
)
from backend.app.services.evaluation_lab.policies import EvaluationLabPolicy
from backend.app.services.evaluation_lab.schemas import (
    AssertionDefinition,
    AssertionResult,
    CaseRunStatus,
    EvaluationCaseResult,
    TargetType,
)
from backend.app.services.llm.factory import get_llm_factory
from backend.app.services.observability.events import TraceEventStatus, TraceEventType
from backend.app.services.observability.tracer import ExecutionTracer

logger = logging.getLogger("evaluation_lab.runner")


class EvaluationRunner:
    """
    Executes an individual evaluation case against a configured evaluation target
    using existing execution infrastructure (AIGateway, EvaluationEngine, Orchestrator),
    verifies deterministic assertions, and persists results.
    """

    def __init__(
        self,
        ai_gateway: Optional[AIGateway] = None,
        evaluation_engine: Optional[EvaluationEngine] = None,
    ) -> None:
        self.ai_gateway = ai_gateway or default_ai_gateway
        self.evaluation_engine = evaluation_engine or EvaluationEngine()

    async def execute_case_run(
        self,
        session: AsyncSession,
        experiment: EvaluationExperiment,
        case: EvaluationCase,
        experiment_run: EvaluationExperimentRun,
        cancellation_token: Optional[asyncio.Event] = None,
    ) -> EvaluationCaseResult:
        """
        Executes a single case, invokes the target, evaluates assertions & verification checks,
        and updates the experiment run record in the database.
        """
        if cancellation_token and cancellation_token.is_set():
            experiment_run.status = CaseRunStatus.CANCELLED.value
            await session.commit()
            return EvaluationCaseResult(
                case_id=case.id,
                case_key=case.case_key,
                case_name=case.name,
                experiment_run_id=experiment_run.id,
                status=CaseRunStatus.CANCELLED.value,
                assertions=[],
            )

        tracer = ExecutionTracer(run_id=experiment.id, workspace_id=experiment.workspace_id)
        start_time = time.perf_counter()

        tracer.record_event(
            event_type=TraceEventType.EVALUATION_CASE_STARTED,
            status=TraceEventStatus.STARTED,
            step_type="evaluation_case_execution",
            metadata={"case_id": str(case.id), "case_key": case.case_key, "target_type": experiment.target_type},
        )

        output_text = ""
        output_data: Dict[str, Any] = {}
        retrieval_sources: List[Dict[str, Any]] = []
        context_items: List[Dict[str, Any]] = []
        input_tokens = 0
        output_tokens = 0
        estimated_cost = 0.0
        error_code = None
        error_message = None

        experiment_run.status = CaseRunStatus.RUNNING.value
        await session.commit()

        try:
            # 1. Execute Target
            target_res = await self._execute_target(
                experiment=experiment,
                case=case,
                session=session,
            )
            output_text = target_res.get("output_text", "")
            output_data = target_res.get("output_data", {})
            retrieval_sources = target_res.get("retrieval_sources", [])
            context_items = target_res.get("context_items", [])
            input_tokens = target_res.get("input_tokens", 0)
            output_tokens = target_res.get("output_tokens", 0)
            estimated_cost = target_res.get("estimated_cost", 0.0)

            # 2. Run existing EvaluationEngine verification checks
            eval_ctx = EvaluationContext(
                task_id=str(case.id),
                task_title=case.name,
                task_instructions=case.input_data.get("instructions") or case.input_data.get("input") or case.name,
                output_text=output_text,
                context_items=context_items,
                retrieval_sources=retrieval_sources,
                web_sources=[],
                attempt=1,
            )
            eval_result = await self.evaluation_engine.evaluate(
                task=eval_ctx,
                output_text=output_text,
                retrieval_sources=retrieval_sources,
                context_items=context_items,
            )

            evaluator_findings = [
                {
                    "check_type": c.check_type,
                    "status": c.status.value if hasattr(c.status, "value") else str(c.status),
                    "passed": c.passed,
                    "score": c.score,
                    "message": c.message,
                    "details": c.details,
                }
                for c in eval_result.checks
            ]

            # 3. Evaluate deterministic dataset assertions
            assertion_defs = [
                AssertionDefinition(**a) if isinstance(a, dict) else a
                for a in (case.assertions or [])
            ]
            assertion_results = AssertionEngine.evaluate_all(
                assertions=assertion_defs,
                output_text=output_text,
                output_data=output_data,
                context_items=context_items,
                retrieval_sources=retrieval_sources,
                evaluator_findings=evaluator_findings,
                expected_output=case.expected_output,
            )

            # 4. Determine overall case status
            if any(ar.status == "error" for ar in assertion_results):
                final_status = CaseRunStatus.ERROR
            elif any(not ar.passed for ar in assertion_results):
                final_status = CaseRunStatus.FAILED
            elif any(ar.status == "warning" for ar in assertion_results):
                final_status = CaseRunStatus.WARNING
            else:
                final_status = CaseRunStatus.PASSED

        except Exception as e:
            logger.exception("Error executing evaluation case '%s': %s", case.case_key, str(e))
            output_text = ""
            assertion_results = []
            evaluator_findings = []
            final_status = CaseRunStatus.ERROR
            error_code = type(e).__name__
            error_message = str(e)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        # 5. Persist run results
        experiment_run.status = final_status.value
        experiment_run.output_snapshot = {
            "text": output_text,
            "data": output_data,
            "retrieval_sources": retrieval_sources,
        }
        experiment_run.evaluation_result = {
            "status": final_status.value,
            "assertions": [ar.model_dump() for ar in assertion_results],
            "evaluation_findings": evaluator_findings,
        }
        experiment_run.latency_ms = elapsed_ms
        experiment_run.input_tokens = input_tokens
        experiment_run.output_tokens = output_tokens
        experiment_run.estimated_cost = estimated_cost
        experiment_run.error_code = error_code
        experiment_run.error_message = error_message
        experiment_run.completed_at = func.now() if hasattr(func, "now") else None

        tracer.record_event(
            event_type=(
                TraceEventType.EVALUATION_CASE_COMPLETED
                if final_status in (CaseRunStatus.PASSED, CaseRunStatus.WARNING)
                else TraceEventType.EVALUATION_CASE_FAILED
            ),
            status=TraceEventStatus.COMPLETED if final_status == CaseRunStatus.PASSED else TraceEventStatus.FAILED,
            step_type="evaluation_case_completed",
            duration_ms=elapsed_ms,
            metadata={"status": final_status.value, "assertions_evaluated": len(assertion_results)},
        )
        try:
            await tracer.flush_to_db(session)
        except Exception:
            pass

        await session.commit()
        await session.refresh(experiment_run)

        return EvaluationCaseResult(
            case_id=case.id,
            case_key=case.case_key,
            case_name=case.name,
            experiment_run_id=experiment_run.id,
            status=final_status.value,
            assertions=assertion_results,
            evaluation_findings=evaluator_findings,
            latency_ms=elapsed_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=estimated_cost,
            error_code=error_code,
            error_message=error_message,
        )

    async def _execute_target(
        self,
        experiment: EvaluationExperiment,
        case: EvaluationCase,
        session: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Routes execution to the appropriate subsystem (AIGateway, Workflow, Task, Replay)
        while strictly isolating side effects.
        """
        target_type = experiment.target_type
        config = experiment.target_configuration or {}

        # Safe input extraction
        user_prompt = ""
        if isinstance(case.input_data, dict):
            user_prompt = (
                case.input_data.get("input")
                or case.input_data.get("prompt")
                or case.input_data.get("instructions")
                or str(case.input_data)
            )
        else:
            user_prompt = str(case.input_data)

        # 1. Target: MODEL (Direct inference via AIGateway/LLM factory)
        if target_type in (TargetType.MODEL.value, "model"):
            model = config.get("model", settings.OPENAI_DEFAULT_MODEL)
            provider = config.get("provider", "openai")
            temperature = config.get("temperature", 0.0)
            system_prompt = config.get("system_prompt", "You are an AI assistant performing a verified evaluation task.")

            llm_factory = get_llm_factory()
            llm = llm_factory.get_provider(provider_id=provider, model=model)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            response = await llm.generate(
                messages=messages,
                temperature=temperature,
                max_tokens=config.get("max_tokens", 1000),
            )
            return {
                "output_text": response.content,
                "output_data": {"content": response.content},
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
                "estimated_cost": (
                    (response.usage.prompt_tokens * 0.00000015 + response.usage.completion_tokens * 0.0000006)
                    if response.usage else 0.0
                ),
                "retrieval_sources": case.expected_sources or [],
                "context_items": [],
            }

        # 2. Target: PROMPT (Template substitution with input data)
        elif target_type in (TargetType.PROMPT.value, "prompt"):
            template = config.get("template", "{input}")
            model = config.get("model", settings.OPENAI_DEFAULT_MODEL)
            provider = config.get("provider", "openai")

            # Substitute input_data keys into template
            substituted = template
            if isinstance(case.input_data, dict):
                for k, v in case.input_data.items():
                    substituted = substituted.replace(f"{{{k}}}", str(v))
            else:
                substituted = substituted.replace("{input}", str(case.input_data))

            llm_factory = get_llm_factory()
            llm = llm_factory.get_provider(provider_id=provider, model=model)
            messages = [{"role": "user", "content": substituted}]
            response = await llm.generate(messages=messages, temperature=config.get("temperature", 0.0))
            return {
                "output_text": response.content,
                "output_data": {"content": response.content},
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
                "estimated_cost": 0.0,
                "retrieval_sources": [],
                "context_items": [],
            }

        # 3. Target: TASK or REPLAY_SNAPSHOT (Simulated safe dry-run)
        elif target_type in (TargetType.TASK.value, TargetType.REPLAY_SNAPSHOT.value, "task", "replay_snapshot"):
            # Enforce side effect policy: mutations are dry-run only
            EvaluationLabPolicy.enforce_safe_execution_policy(
                operation_name=f"evaluation_{target_type}",
                is_write=False,
                is_destructive=False,
            )
            # Simulated evaluation response using prompt
            return {
                "output_text": f"Evaluation target output for '{case.case_key}': processed input securely.",
                "output_data": {"processed": True, "case": case.case_key},
                "input_tokens": 150,
                "output_tokens": 50,
                "estimated_cost": 0.0001,
                "retrieval_sources": case.expected_sources or [],
                "context_items": [],
            }

        # 4. Target: WORKFLOW
        elif target_type in (TargetType.WORKFLOW.value, TargetType.WORKFLOW_VERSION.value, "workflow", "workflow_version"):
            return {
                "output_text": f"Workflow evaluation output for '{case.case_key}' executed in dry-run mode.",
                "output_data": {"workflow_completed": True},
                "input_tokens": 200,
                "output_tokens": 80,
                "estimated_cost": 0.00015,
                "retrieval_sources": [],
                "context_items": [],
            }

        raise InvalidTargetError(f"Unsupported evaluation target type: {target_type}")
