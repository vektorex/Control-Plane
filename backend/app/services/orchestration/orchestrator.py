import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Callable, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.db.models.task import Task
from backend.app.db.models.user import User
from backend.app.schemas.llm import ChatMessage, LLMGenerateRequest
from backend.app.schemas.task import TaskRunRequest
from backend.app.services.context.engine import ContextEngine, get_context_engine
from backend.app.services.context.models import ContextBudget, ContextItem
from backend.app.services.llm.factory import LLMProviderFactory, get_llm_factory
from backend.app.services.orchestration.errors import (
    OrchestrationError,
    PlanValidationError,
    StepExecutionError,
)
from backend.app.services.orchestration.evaluator import (
    AntiLoopDetector,
    CompletionEvaluation,
    CompletionEvaluator,
)
from backend.app.services.orchestration.executor import OrchestrationExecutor
from backend.app.services.orchestration.plan import ExecutionPlan, ExecutionStepPlan, StepStatus, StepType
from backend.app.services.orchestration.planner import ExecutionPlanner
from backend.app.services.orchestration.planners.base import PlannerContext
from backend.app.services.orchestration.policies import FailurePolicy
from backend.app.services.orchestration.state import ExecutionState, ExecutionStepRecord
from backend.app.services.orchestration.validator import PlanValidator
from backend.app.services.retrieval.router import RetrievalRouter, get_retrieval_router
from backend.app.services.tools.executor import ToolExecutor, get_tool_executor
from backend.app.services.tools.registry import ToolRegistry, get_tool_registry


class Orchestrator:
    """
    Main Orchestration Engine coordinating LLM-assisted / deterministic planning,
    plan validation, sequential execution, bounded agentic loop, completion evaluation,
    and observable SSE streaming.
    """

    def __init__(
        self,
        planner: Optional[ExecutionPlanner] = None,
        validator: Optional[PlanValidator] = None,
        executor: Optional[OrchestrationExecutor] = None,
        evaluator: Optional[CompletionEvaluator] = None,
        context_engine: Optional[ContextEngine] = None,
        llm_factory: Optional[LLMProviderFactory] = None,
    ) -> None:
        self.context_engine = context_engine or get_context_engine()
        self.llm_factory = llm_factory or get_llm_factory()
        self.planner = planner or ExecutionPlanner(llm_factory=self.llm_factory)
        self.validator = validator or PlanValidator(llm_factory=self.llm_factory)
        self.executor = executor or OrchestrationExecutor(
            context_engine=self.context_engine,
            llm_factory=self.llm_factory,
        )
        self.evaluator = evaluator or CompletionEvaluator(llm_factory=self.llm_factory)

    async def plan_task(
        self,
        task: Task,
        request: Optional[TaskRunRequest] = None,
        user: Optional[User] = None,
        session: Optional[AsyncSession] = None,
        context: Optional[PlannerContext] = None,
    ) -> ExecutionPlan:
        """
        Synthesizes and validates an ExecutionPlan for a task.
        """
        plan = await self.planner.plan(
            task=task,
            request=request,
            user=user,
            session=session,
            context=context,
        )
        self.validator.validate(plan, user=user, request=request)
        return plan

    async def execute_task(
        self,
        task: Task,
        request: Optional[TaskRunRequest] = None,
        user: Optional[User] = None,
        session: Optional[AsyncSession] = None,
        policy: Optional[FailurePolicy] = None,
        on_step_start: Optional[Callable[[ExecutionStepRecord], Any]] = None,
        on_step_complete: Optional[Callable[[ExecutionStepRecord], Any]] = None,
        on_step_failed: Optional[Callable[[ExecutionStepRecord], Any]] = None,
    ) -> ExecutionState:
        """
        Plans, validates, and executes a task through the orchestration pipeline
        with bounded agentic loop iterations and completion evaluation.
        """
        req = request or TaskRunRequest()
        active_policy = policy or FailurePolicy()
        max_iterations = min(req.max_agent_iterations or settings.MAX_AGENT_ITERATIONS, 5)

        # 1. Generate initial plan
        initial_plan = await self.plan_task(
            task=task,
            request=req,
            user=user,
            session=session,
        )

        state = ExecutionState(
            task_id=str(task.id),
            plan=initial_plan,
            planning_mode=req.planner_mode or "hybrid",
            planner_model=initial_plan.metadata.get("planner_model", settings.PLANNER_MODEL),
            repair_count=initial_plan.metadata.get("repair_count", 0),
        )

        accumulated_context_items: List[ContextItem] = []
        retrieval_sources_meta: List[Dict[str, Any]] = []
        anti_loop = AntiLoopDetector()

        current_iteration = 1
        current_plan = initial_plan
        step_global_index = 0

        while current_iteration <= max_iterations:
            state.iteration = current_iteration

            # Separate non-generate steps from generate step
            non_generate_steps = [s for s in current_plan.steps if s.type != StepType.GENERATE]
            generate_steps = [s for s in current_plan.steps if s.type == StepType.GENERATE]

            # Execute non-generate steps for this iteration
            for step in non_generate_steps:
                # Anti-loop check
                if anti_loop.check_and_record(step):
                    logger.warning(f"[Orchestrator] Anti-loop detected repeated step '{step.id}' ({step.type}). Skipping.")
                    continue

                await self.executor.execute_single_step(
                    step=step,
                    step_index=step_global_index,
                    task=task,
                    state=state,
                    accumulated_context_items=accumulated_context_items,
                    retrieval_sources_meta=retrieval_sources_meta,
                    user=user,
                    session=session,
                    policy=active_policy,
                    on_step_start=on_step_start,
                    on_step_complete=on_step_complete,
                    on_step_failed=on_step_failed,
                )
                step_global_index += 1

            # Step 15: Evaluate completion sufficiency
            evaluation: CompletionEvaluation = await self.evaluator.evaluate(
                task=task,
                accumulated_items=accumulated_context_items,
                iteration=current_iteration,
                max_iterations=max_iterations,
            )
            state.completion_evaluation = evaluation.model_dump()

            if evaluation.complete or current_iteration >= max_iterations:
                # Evidence sufficient or max iterations reached -> execute final generate step
                final_gen_step = generate_steps[0] if generate_steps else ExecutionStepPlan(
                    id=f"step_{step_global_index + 1}",
                    type=StepType.GENERATE,
                    model=req.model or settings.OPENAI_DEFAULT_MODEL,
                    temperature=req.temperature or 0.2,
                )

                await self.executor.execute_single_step(
                    step=final_gen_step,
                    step_index=step_global_index,
                    task=task,
                    state=state,
                    accumulated_context_items=accumulated_context_items,
                    retrieval_sources_meta=retrieval_sources_meta,
                    user=user,
                    session=session,
                    policy=active_policy,
                    on_step_start=on_step_start,
                    on_step_complete=on_step_complete,
                    on_step_failed=on_step_failed,
                )
                break

            else:
                # Evidence incomplete and iterations remain -> Replan for missing information
                logger.info(
                    f"[Orchestrator] Iteration {current_iteration} incomplete. Missing: {evaluation.missing_information}. Replanning."
                )
                current_iteration += 1

                replan_context = PlannerContext(
                    task_id=str(task.id),
                    task_title=task.title or "",
                    task_instructions=task.instructions or task.description or "",
                    context_text=task.context_text,
                    has_manual_context=bool(accumulated_context_items),
                    manual_context_count=len(accumulated_context_items),
                    retrieval_mode=req.retrieval_mode or "auto",
                    tool_mode=req.tool_mode or "disabled",
                    tools_enabled=req.tools_enabled or [],
                    target_model=req.model or settings.OPENAI_DEFAULT_MODEL,
                    temperature=req.temperature or 0.2,
                    max_context_tokens=req.max_context_tokens or 8000,
                    missing_information=evaluation.missing_information,
                    iteration=current_iteration,
                )

                current_plan = await self.plan_task(
                    task=task,
                    request=req,
                    user=user,
                    session=session,
                    context=replan_context,
                )

        state.complete()
        return state

    async def execute_task_stream(
        self,
        task: Task,
        request: Optional[TaskRunRequest] = None,
        user: Optional[User] = None,
        session: Optional[AsyncSession] = None,
        policy: Optional[FailurePolicy] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Executes an orchestration plan with real-time SSE event emission for intermediate steps,
        agent loop iterations, completion evaluations, and LLM token chunks.
        """
        active_policy = policy or FailurePolicy()
        req = request or TaskRunRequest()
        max_iterations = min(req.max_agent_iterations or settings.MAX_AGENT_ITERATIONS, 5)

        yield {
            "type": "planning_start",
            "planner_mode": req.planner_mode or "hybrid",
            "task_id": str(task.id),
        }

        # 1. Generate initial plan
        initial_plan = await self.plan_task(
            task=task,
            request=req,
            user=user,
            session=session,
        )

        state = ExecutionState(
            task_id=str(task.id),
            plan=initial_plan,
            planning_mode=req.planner_mode or "hybrid",
            planner_model=initial_plan.metadata.get("planner_model", settings.PLANNER_MODEL),
            repair_count=initial_plan.metadata.get("repair_count", 0),
        )

        accumulated_context_items: List[ContextItem] = []
        retrieval_sources_meta: List[Dict[str, Any]] = []
        anti_loop = AntiLoopDetector()

        yield {
            "type": "plan_generated",
            "plan": initial_plan.model_dump(mode="json"),
            "step_count": len(initial_plan.steps),
            "planner_mode": state.planning_mode,
            "planner_model": state.planner_model,
        }

        current_iteration = 1
        current_plan = initial_plan
        step_global_index = 0

        while current_iteration <= max_iterations:
            state.iteration = current_iteration
            non_generate_steps = [s for s in current_plan.steps if s.type != StepType.GENERATE]
            generate_steps = [s for s in current_plan.steps if s.type == StepType.GENERATE]

            # Execute non-generate steps for this iteration
            for step in non_generate_steps:
                if anti_loop.check_and_record(step):
                    logger.warning(f"[Orchestrator SSE] Anti-loop detected repeated step '{step.id}'. Skipping.")
                    continue

                tool_name = step.tool if step.type == StepType.TOOL else None
                strategy = step.strategy if step.type == StepType.RETRIEVE else None

                record = state.get_or_create_step_record(
                    step_id=step.id,
                    step_index=step_global_index,
                    step_type=step.type.value if hasattr(step.type, "value") else str(step.type),
                    tool_name=tool_name,
                    retrieval_strategy=strategy,
                )
                record.mark_started()

                yield {
                    "type": "step_start",
                    "step": record.model_dump(mode="json"),
                }

                try:
                    step_type_str = step.type.value if hasattr(step.type, "value") else str(step.type)
                    if step_type_str == StepType.RETRIEVE.value:
                        summary = await self.executor._execute_retrieve_step(
                            step=step,
                            task=task,
                            session=session,
                            user=user,
                            accumulated_items=accumulated_context_items,
                            retrieval_sources=retrieval_sources_meta,
                            state=state,
                        )
                        record.mark_completed(summary)

                    elif step_type_str == StepType.TOOL.value:
                        summary = await self.executor._execute_tool_step(
                            step=step,
                            user=user,
                            accumulated_items=accumulated_context_items,
                            state=state,
                        )
                        record.mark_completed(summary)

                    elif step_type_str == StepType.CONTEXT.value:
                        summary = await self.executor._execute_context_step(
                            step=step,
                            task=task,
                            session=session,
                            accumulated_items=accumulated_context_items,
                            state=state,
                        )
                        record.mark_completed(summary)

                    yield {
                        "type": "step_completed",
                        "step": record.model_dump(mode="json"),
                    }
                    step_global_index += 1

                except Exception as step_err:
                    err_msg = str(step_err)
                    err_code = getattr(step_err, "code", "STEP_EXECUTION_ERROR")
                    record.mark_failed(error_code=err_code, error_message=err_msg)
                    state.record_error(step.id, error_code=err_code, error_message=err_msg)

                    yield {
                        "type": "step_failed",
                        "step": record.model_dump(mode="json"),
                    }
                    step_global_index += 1

                    is_required = step.required or active_policy.strict_mode
                    if is_required:
                        state.complete()
                        yield {
                            "type": "error",
                            "error": {"code": err_code, "message": f"Required step '{step.id}' failed: {err_msg}"},
                        }
                        return

            # Evaluate completion
            yield {
                "type": "evaluating",
                "iteration": current_iteration,
                "max_iterations": max_iterations,
            }

            evaluation: CompletionEvaluation = await self.evaluator.evaluate(
                task=task,
                accumulated_items=accumulated_context_items,
                iteration=current_iteration,
                max_iterations=max_iterations,
            )
            state.completion_evaluation = evaluation.model_dump()

            yield {
                "type": "evaluation_completed",
                "evaluation": evaluation.model_dump(mode="json"),
                "iteration": current_iteration,
            }

            if evaluation.complete or current_iteration >= max_iterations:
                break
            else:
                current_iteration += 1
                replan_context = PlannerContext(
                    task_id=str(task.id),
                    task_title=task.title or "",
                    task_instructions=task.instructions or task.description or "",
                    context_text=task.context_text,
                    has_manual_context=bool(accumulated_context_items),
                    manual_context_count=len(accumulated_context_items),
                    retrieval_mode=req.retrieval_mode or "auto",
                    tool_mode=req.tool_mode or "disabled",
                    tools_enabled=req.tools_enabled or [],
                    target_model=req.model or settings.OPENAI_DEFAULT_MODEL,
                    temperature=req.temperature or 0.2,
                    max_context_tokens=req.max_context_tokens or 8000,
                    missing_information=evaluation.missing_information,
                    iteration=current_iteration,
                )
                current_plan = await self.plan_task(
                    task=task,
                    request=req,
                    user=user,
                    session=session,
                    context=replan_context,
                )

                yield {
                    "type": "replan_generated",
                    "plan": current_plan.model_dump(mode="json"),
                    "iteration": current_iteration,
                }

        # Final Generation Step with streaming deltas
        final_gen_step = generate_steps[0] if generate_steps else ExecutionStepPlan(
            id=f"step_{step_global_index + 1}",
            type=StepType.GENERATE,
            model=req.model or settings.OPENAI_DEFAULT_MODEL,
            temperature=req.temperature or 0.2,
        )

        gen_record = state.get_or_create_step_record(
            step_id=final_gen_step.id,
            step_index=step_global_index,
            step_type=StepType.GENERATE.value,
        )
        gen_record.mark_started()

        yield {
            "type": "step_start",
            "step": gen_record.model_dump(mode="json"),
        }

        try:
            # Build context package
            has_task_ctx = any(it.source_type == "task" for it in accumulated_context_items)
            if not has_task_ctx:
                task_provider = self.context_engine.get_provider("task_context")
                if task_provider:
                    t_items = await task_provider.collect(task, session=session)
                    accumulated_context_items.extend(task_provider.normalize(t_items))

            has_manual_ctx = any(it.source_type == "manual" for it in accumulated_context_items)
            if not has_manual_ctx:
                manual_provider = self.context_engine.get_provider("manual_context")
                if manual_provider:
                    m_items = await manual_provider.collect(task, session=session)
                    accumulated_context_items.extend(manual_provider.normalize(m_items))

            max_context_tokens = final_gen_step.metadata.get("max_context_tokens", 8000) if final_gen_step.metadata else 8000
            budget = ContextBudget(max_context_tokens=max_context_tokens)
            context_package = self.context_engine.builder.build(
                raw_items=accumulated_context_items,
                budget=budget,
            )
            state.context_items = [it.model_dump(mode="json") for it in context_package.items]
            state.metadata["context_package"] = {
                "estimated_tokens": context_package.estimated_tokens,
                "truncated": context_package.truncated,
                "total_items": context_package.total_items,
                "dropped_items_count": context_package.dropped_items_count,
                "sources": list(context_package.sources),
            }

            messages = self.context_engine.builder.format_as_messages(context_package, task)

            target_model = final_gen_step.model or settings.OPENAI_DEFAULT_MODEL
            target_temp = final_gen_step.temperature if final_gen_step.temperature is not None else 0.2
            provider = self.llm_factory.get_provider_for_model(target_model)

            llm_request = LLMGenerateRequest(
                model=target_model,
                messages=messages,
                temperature=target_temp,
            )

            full_content = ""
            async for chunk in provider.generate_stream(llm_request):
                delta_text = getattr(chunk, "delta", None) or getattr(chunk, "content", "")
                full_content += delta_text
                if chunk.usage:
                    state.token_usage = {
                        "input_tokens": getattr(chunk.usage, "input_tokens", None) or getattr(chunk.usage, "prompt_tokens", 0) or 0,
                        "output_tokens": getattr(chunk.usage, "output_tokens", None) or getattr(chunk.usage, "completion_tokens", 0) or 0,
                        "total_tokens": getattr(chunk.usage, "total_tokens", 0) or 0,
                    }
                yield {
                    "type": "content_delta",
                    "delta": delta_text,
                    "content": full_content,
                }

            state.generated_output = full_content
            gen_record.mark_completed({"output_length": len(full_content)})
            state.complete()

            yield {
                "type": "step_completed",
                "step": gen_record.model_dump(mode="json"),
            }

            yield {
                "type": "generation_completed",
                "content": full_content,
                "total_steps": len(state.step_records),
                "iterations": state.iteration,
            }

            yield {
                "type": "orchestration_completed",
                "state": state.model_dump(mode="json"),
            }

        except Exception as gen_err:
            err_msg = str(gen_err)
            gen_record.mark_failed(error_code="GENERATION_ERROR", error_message=err_msg)
            state.record_error(final_gen_step.id, error_code="GENERATION_ERROR", error_message=err_msg)
            state.complete()

            yield {
                "type": "step_failed",
                "step": gen_record.model_dump(mode="json"),
            }
            yield {
                "type": "error",
                "error": {"code": "GENERATION_ERROR", "message": f"Final generation failed: {err_msg}"},
            }
            return


_orchestrator_instance: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = Orchestrator()
    return _orchestrator_instance
