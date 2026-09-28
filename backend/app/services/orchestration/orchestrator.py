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
from backend.app.services.orchestration.executor import OrchestrationExecutor
from backend.app.services.orchestration.plan import ExecutionPlan, ExecutionStepPlan, StepStatus, StepType
from backend.app.services.orchestration.planner import ExecutionPlanner
from backend.app.services.orchestration.policies import FailurePolicy
from backend.app.services.orchestration.state import ExecutionState, ExecutionStepRecord
from backend.app.services.orchestration.validator import PlanValidator
from backend.app.services.retrieval.router import RetrievalRouter, get_retrieval_router
from backend.app.services.tools.executor import ToolExecutor, get_tool_executor
from backend.app.services.tools.registry import ToolRegistry, get_tool_registry


class Orchestrator:
    """
    Main Orchestration Engine coordinating deterministic planning, plan validation,
    sequential step execution, context assembly, tools, and LLM generation.
    """

    def __init__(
        self,
        planner: Optional[ExecutionPlanner] = None,
        validator: Optional[PlanValidator] = None,
        executor: Optional[OrchestrationExecutor] = None,
        context_engine: Optional[ContextEngine] = None,
        llm_factory: Optional[LLMProviderFactory] = None,
    ) -> None:
        self.context_engine = context_engine or get_context_engine()
        self.llm_factory = llm_factory or get_llm_factory()
        self.planner = planner or ExecutionPlanner()
        self.validator = validator or PlanValidator(llm_factory=self.llm_factory)
        self.executor = executor or OrchestrationExecutor(
            context_engine=self.context_engine,
            llm_factory=self.llm_factory,
        )

    async def plan_task(
        self,
        task: Task,
        request: Optional[TaskRunRequest] = None,
        user: Optional[User] = None,
        session: Optional[AsyncSession] = None,
    ) -> ExecutionPlan:
        """
        Synthesizes and validates a deterministic ExecutionPlan for a task.
        """
        plan = await self.planner.plan(
            task=task,
            request=request,
            user=user,
            session=session,
        )
        self.validator.validate(plan, user=user)
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
        Plans, validates, and executes a task through the orchestration pipeline.
        """
        plan = await self.plan_task(
            task=task,
            request=request,
            user=user,
            session=session,
        )

        state = await self.executor.execute(
            task=task,
            plan=plan,
            user=user,
            session=session,
            policy=policy,
            on_step_start=on_step_start,
            on_step_complete=on_step_complete,
            on_step_failed=on_step_failed,
        )
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
        Executes an orchestration plan with real-time SSE event emission for intermediate steps
        and LLM token chunks.
        """
        active_policy = policy or FailurePolicy()
        req = request or TaskRunRequest()

        # 1. Generate & validate plan
        plan = await self.plan_task(
            task=task,
            request=req,
            user=user,
            session=session,
        )

        state = ExecutionState(task_id=str(task.id), plan=plan)
        accumulated_context_items: List[ContextItem] = []
        retrieval_sources_meta: List[Dict[str, Any]] = []

        yield {
            "type": "orchestration_plan",
            "plan": plan.model_dump(mode="json"),
            "step_count": len(plan.steps),
        }

        # 2. Execute intermediate non-generate steps
        for idx, step in enumerate(plan.steps):
            state.current_step_index = idx
            step_type_str = step.type.value if hasattr(step.type, "value") else str(step.type)

            record = state.get_or_create_step_record(
                step_id=step.id,
                step_index=idx,
                step_type=step_type_str,
                tool_name=step.tool if step.type == StepType.TOOL else None,
                retrieval_strategy=step.strategy if step.type == StepType.RETRIEVE else None,
            )
            record.mark_started()

            yield {
                "type": "step_start",
                "step": record.model_dump(mode="json"),
            }

            if step_type_str != StepType.GENERATE.value:
                try:
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

                except Exception as step_err:
                    err_msg = str(step_err)
                    err_code = getattr(step_err, "code", "STEP_EXECUTION_ERROR")
                    record.mark_failed(error_code=err_code, error_message=err_msg)
                    state.record_error(step.id, error_code=err_code, error_message=err_msg)

                    yield {
                        "type": "step_failed",
                        "step": record.model_dump(mode="json"),
                    }

                    is_required = step.required or active_policy.strict_mode
                    if is_required:
                        state.complete()
                        yield {
                            "type": "error",
                            "error": {"code": err_code, "message": f"Required step '{step.id}' failed: {err_msg}"},
                        }
                        return

            else:
                # 3. Final generation step with live streaming
                try:
                    # Merge task & manual context
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

                    max_context_tokens = step.metadata.get("max_context_tokens", 8000) if step.metadata else 8000
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

                    target_model = step.model or settings.OPENAI_DEFAULT_MODEL
                    target_temp = step.temperature if step.temperature is not None else 0.2
                    provider = self.llm_factory.get_provider_for_model(target_model)

                    llm_request = LLMGenerateRequest(
                        model=target_model,
                        messages=messages,
                        temperature=target_temp,
                    )

                    accumulated_content = ""
                    async for stream_chunk in provider.generate_stream(llm_request):
                        chunk_text = getattr(stream_chunk, "content", None) or getattr(stream_chunk, "delta", "")
                        if chunk_text:
                            accumulated_content += chunk_text
                            yield {
                                "type": "chunk",
                                "content": chunk_text,
                                "delta": chunk_text,
                            }
                        if getattr(stream_chunk, "usage", None):
                            u = stream_chunk.usage
                            state.token_usage = {
                                "input_tokens": getattr(u, "input_tokens", None) or getattr(u, "prompt_tokens", 0) or 0,
                                "output_tokens": getattr(u, "output_tokens", None) or getattr(u, "completion_tokens", 0) or 0,
                                "total_tokens": getattr(u, "total_tokens", 0) or 0,
                            }

                    state.generated_output = accumulated_content
                    record.mark_completed({"output_length": len(accumulated_content)})

                    yield {
                        "type": "step_completed",
                        "step": record.model_dump(mode="json"),
                    }

                except Exception as gen_err:
                    err_msg = str(gen_err)
                    err_code = getattr(gen_err, "code", "GENERATION_ERROR")
                    record.mark_failed(error_code=err_code, error_message=err_msg)
                    state.record_error(step.id, error_code=err_code, error_message=err_msg)
                    yield {
                        "type": "step_failed",
                        "step": record.model_dump(mode="json"),
                    }
                    yield {
                        "type": "error",
                        "error": {"code": err_code, "message": err_msg},
                    }
                    return

        state.complete()
        yield {
            "type": "orchestration_completed",
            "state": {
                "elapsed_time_ms": state.elapsed_time_ms,
                "step_records": [r.model_dump(mode="json") for r in state.step_records],
                "generated_output": state.generated_output,
                "context_items": state.context_items,
                "retrieval_results": state.retrieval_results,
                "token_usage": state.token_usage,
                "metadata": state.metadata,
            },
        }


# Singleton accessor
_global_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    global _global_orchestrator
    if _global_orchestrator is None:
        _global_orchestrator = Orchestrator()
    return _global_orchestrator
