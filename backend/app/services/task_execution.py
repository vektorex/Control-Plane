import asyncio
import json
import time
from datetime import datetime, timezone
from typing import AsyncIterator, Dict, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.errors import AppError, InvalidStateError
from backend.app.core.logging import logger
from backend.app.db.models.enums import RunStatus, TaskStatus
from backend.app.db.models.run import Run
from backend.app.db.models.task import Task
from backend.app.db.models.user import User
from backend.app.repositories.run import RunRepository
from backend.app.repositories.task import TaskRepository
from backend.app.schemas.llm import ChatMessage, LLMGenerateRequest
from backend.app.schemas.run import RunResponse
from backend.app.schemas.task import TaskRunRequest
from backend.app.services.context.engine import ContextEngine, get_context_engine
from backend.app.services.context.models import ContextBudget
from backend.app.services.llm.factory import LLMProviderFactory, get_llm_factory
from backend.app.services.orchestration.orchestrator import Orchestrator, get_orchestrator
from backend.app.services.orchestration.plan import ExecutionPlan, StepType


class TaskExecutionService:
    """
    Service responsible for turning a Task entity into an orchestrated AI workflow
    via the Orchestration Engine, coordinating planning, retrieval, tools, context,
    and persisting execution runs with complete observability.
    """

    def __init__(
        self,
        session: AsyncSession,
        factory: LLMProviderFactory,
        context_engine: Optional[ContextEngine] = None,
        orchestrator: Optional[Orchestrator] = None,
    ):
        self.session = session
        self.factory = factory
        self.context_engine = context_engine or get_context_engine()
        self.orchestrator = orchestrator or Orchestrator(
            context_engine=self.context_engine,
            llm_factory=self.factory,
        )
        self.task_repo = TaskRepository(session)
        self.run_repo = RunRepository(session)

    async def plan_task(
        self,
        task_id: UUID,
        user: User,
        request: TaskRunRequest,
    ) -> ExecutionPlan:
        """
        Synthesizes, validates, and returns an ExecutionPlan for a task without executing it.
        """
        task = await self.task_repo.get_by_id_and_owner_or_raise(task_id, user.id)
        prompt_check = (task.instructions or "").strip() or (task.description or "").strip() or (task.title or "").strip()
        if not prompt_check:
            raise InvalidStateError("Task has no instructions, description, or title to plan.")

        return await self.orchestrator.plan_task(
            task=task,
            request=request,
            user=user,
            session=self.session,
        )

    async def execute_task(
        self,
        task_id: UUID,
        user: User,
        request: TaskRunRequest,
    ) -> Run:
        """
        Executes a task through the Orchestration Engine and persists the resulting Run entity.
        """
        task = await self.task_repo.get_by_id_and_owner_or_raise(task_id, user.id)
        prompt_check = (task.instructions or "").strip() or (task.description or "").strip() or (task.title or "").strip()
        if not prompt_check:
            raise InvalidStateError("Task has no instructions, description, or title to execute.")

        # 1. Generate & Validate Plan
        plan = await self.orchestrator.plan_task(
            task=task,
            request=request,
            user=user,
            session=self.session,
        )

        model_name = request.model or "gpt-4o-mini"
        provider = self.factory.get_provider_for_model(model_name)

        # 2. Extract planning metadata for initial run snapshot
        retrieval_meta = plan.metadata.get("retrieval_decision", {})
        retrieval_required = retrieval_meta.get("retrieval_required", False)
        raw_strat = retrieval_meta.get("strategy")
        retrieval_strategy = raw_strat.value if hasattr(raw_strat, "value") else (str(raw_strat) if raw_strat else None)
        raw_scope = retrieval_meta.get("scope")
        retrieval_scope = raw_scope.value if hasattr(raw_scope, "value") else (str(raw_scope) if raw_scope else None)
        retrieval_top_k = retrieval_meta.get("top_k")
        retrieval_reason = retrieval_meta.get("reason")
        retrieval_confidence = retrieval_meta.get("confidence")

        retrieval_steps = [s for s in plan.steps if s.type == StepType.RETRIEVE]
        retrieval_strategies = [s.strategy for s in retrieval_steps if s.strategy]

        tool_steps = [s for s in plan.steps if s.type == StepType.TOOL]
        tools_planned = [s.tool for s in tool_steps if s.tool]

        plan_json = plan.model_dump(mode="json")

        # 3. Create initial Run in 'running' status
        start_time = time.perf_counter()
        run = Run(
            task_id=task.id,
            status=RunStatus.RUNNING.value,
            model_provider=provider.provider_id,
            model_name=model_name,
            final_model=model_name,
            input_snapshot={
                "model": model_name,
                "temperature": request.temperature,
                "max_context_tokens": request.max_context_tokens or 8000,
                "execution_plan": plan_json,
                "plan_reason": plan.plan_reason,
            },
            execution_plan=plan_json,
            retrieval_enabled=retrieval_required,
            retrieval_mode=request.retrieval_mode or "auto",
            retrieval_required=retrieval_required,
            retrieval_strategy=retrieval_strategy,
            retrieval_scope=retrieval_scope,
            retrieval_top_k=retrieval_top_k,
            retrieval_reason=retrieval_reason,
            retrieval_confidence=retrieval_confidence,
            retrieval_strategies=retrieval_strategies if retrieval_strategies else None,
            tools_used=tools_planned if tools_planned else None,
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(run)
        await self.session.flush()
        await self.session.refresh(run)

        # 4. Execute Orchestration Plan
        try:
            state = await self.orchestrator.executor.execute(
                task=task,
                plan=plan,
                user=user,
                session=self.session,
            )

            # 5. Harvest execution state telemetry
            tools_used = []
            tool_call_count = len(state.tool_results)
            tool_latency_total = 0
            tool_errors = []
            tool_executions = []

            for tr in state.tool_results:
                t_name = tr.get("tool_name", "unknown")
                if t_name not in tools_used:
                    tools_used.append(t_name)
                t_lat = tr.get("latency_ms", 0)
                tool_latency_total += t_lat
                t_succ = tr.get("success", True)
                t_err = tr.get("error")
                if not t_succ and t_err:
                    tool_errors.append({"tool": t_name, "error": t_err})
                tool_executions.append({
                    "tool_name": t_name,
                    "success": t_succ,
                    "latency_ms": t_lat,
                    "error": t_err,
                })

            # Harvest web sources for UI transparency
            web_sources = []
            for it in state.context_items:
                if it.get("source_type") == "web":
                    meta = it.get("metadata", {})
                    web_sources.append({
                        "title": it.get("title"),
                        "url": meta.get("url"),
                        "source": meta.get("source"),
                        "published_at": meta.get("published_at"),
                        "snippet": it.get("content"),
                    })

            # Context & Retrieval telemetry
            ctx_meta = state.metadata.get("context_package", {})
            run.status = RunStatus.COMPLETED.value
            run.output_content = state.generated_output
            run.latency_ms = state.elapsed_time_ms
            run.orchestration_duration_ms = state.elapsed_time_ms
            run.step_count = len(state.step_records)
            run.execution_steps = [r.model_dump(mode="json") for r in state.step_records]
            run.context_item_count = len(state.context_items)
            run.context_sources = list(set(it.get("source_type", "task") for it in state.context_items))
            run.estimated_context_tokens = ctx_meta.get("estimated_tokens", 0)
            run.context_truncated = ctx_meta.get("truncated", False)
            run.retrieved_chunk_count = len(state.retrieval_results)
            run.retrieval_sources = state.metadata.get("retrieval_sources")
            run.retrieval_latency_ms = sum(r.duration_ms for r in state.step_records if r.step_type == "retrieve") if state.retrieval_results else None
            run.input_tokens = state.token_usage.get("input_tokens", 0)
            run.output_tokens = state.token_usage.get("output_tokens", 0)
            run.total_tokens = state.token_usage.get("total_tokens", 0)
            run.tools_used = tools_used if tools_used else None
            run.tool_call_count = tool_call_count
            run.tool_latency_ms = tool_latency_total
            run.tool_errors = tool_errors if tool_errors else None
            run.tool_executions = tool_executions if tool_executions else None

            # Input snapshot update with web sources and context summary
            snap = dict(run.input_snapshot) if run.input_snapshot else {}
            snap["web_sources"] = web_sources
            snap["context_summary"] = {
                "item_count": run.context_item_count,
                "estimated_tokens": run.estimated_context_tokens,
                "truncated": run.context_truncated,
                "sources": run.context_sources,
            }
            run.input_snapshot = snap

            # Auto-mark task completed if not draft
            if task.status != TaskStatus.DRAFT.value:
                task.status = TaskStatus.COMPLETED.value
                self.session.add(task)

            run.completed_at = datetime.now(timezone.utc)
            await self.session.flush()
            await self.session.refresh(run)

            return run

        except Exception as exc:
            run.status = RunStatus.FAILED.value
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            run.latency_ms = elapsed_ms
            run.orchestration_duration_ms = elapsed_ms
            await self.session.commit()
            raise exc

    async def execute_task_stream(
        self,
        task_id: UUID,
        user: User,
        request: TaskRunRequest,
    ) -> AsyncIterator[str]:
        """
        Executes a task with Server-Sent Events (SSE) streaming while persisting the Run.
        """
        task = await self.task_repo.get_by_id_and_owner_or_raise(task_id, user.id)
        prompt_check = (task.instructions or "").strip() or (task.description or "").strip() or (task.title or "").strip()
        if not prompt_check:
            yield f"data: {json.dumps({'type': 'error', 'error': 'Task has no instructions, description, or title.'})}\n\n"
            return

        model_name = request.model or "gpt-4o-mini"
        provider = self.factory.get_provider_for_model(model_name)

        # 1. Generate & Validate Plan
        try:
            plan = await self.orchestrator.plan_task(
                task=task,
                request=request,
                user=user,
                session=self.session,
            )
        except Exception as plan_err:
            yield f"data: {json.dumps({'type': 'error', 'error': {'code': 'PLAN_ERROR', 'message': str(plan_err)}})}\n\n"
            return

        retrieval_meta = plan.metadata.get("retrieval_decision", {})
        retrieval_required = retrieval_meta.get("retrieval_required", False)
        raw_strat = retrieval_meta.get("strategy")
        retrieval_strategy = raw_strat.value if hasattr(raw_strat, "value") else (str(raw_strat) if raw_strat else None)
        raw_scope = retrieval_meta.get("scope")
        retrieval_scope = raw_scope.value if hasattr(raw_scope, "value") else (str(raw_scope) if raw_scope else None)
        plan_json = plan.model_dump(mode="json")

        # Pre-calculate initial context metadata for run_start event
        init_items = []
        task_prov = self.context_engine.get_provider("task_context")
        if task_prov:
            t_raw = await task_prov.collect(task, session=self.session)
            init_items.extend(task_prov.normalize(t_raw))
        man_prov = self.context_engine.get_provider("manual_context")
        if man_prov:
            m_raw = await man_prov.collect(task, session=self.session)
            init_items.extend(man_prov.normalize(m_raw))

        init_pkg = self.context_engine.builder.build(
            raw_items=init_items,
            budget=ContextBudget(max_context_tokens=request.max_context_tokens or 8000),
        )

        # 2. Create Run entity in DB
        start_time = time.perf_counter()
        run = Run(
            task_id=task.id,
            status=RunStatus.RUNNING.value,
            model_provider=provider.provider_id,
            model_name=model_name,
            final_model=model_name,
            execution_plan=plan_json,
            retrieval_enabled=retrieval_required,
            retrieval_mode=request.retrieval_mode or "auto",
            retrieval_required=retrieval_required,
            retrieval_strategy=retrieval_strategy,
            retrieval_scope=retrieval_scope,
            retrieval_top_k=retrieval_meta.get("top_k"),
            retrieval_reason=retrieval_meta.get("reason"),
            retrieval_confidence=retrieval_meta.get("confidence"),
            tools_used=[s.tool for s in plan.steps if s.type == StepType.TOOL and s.tool],
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(run)
        await self.session.flush()
        await self.session.refresh(run)

        # Emit run_start
        yield f"data: {json.dumps({'type': 'run_start', 'run_id': str(run.id), 'execution_plan': plan_json, 'tools_used': run.tools_used, 'retrieval_enabled': retrieval_required, 'context_item_count': init_pkg.total_items, 'estimated_context_tokens': init_pkg.estimated_tokens, 'context_truncated': init_pkg.truncated, 'context_sources': list(init_pkg.sources)})}\n\n"

        accumulated_output = ""
        step_records_final = []
        final_orch_state = None

        try:
            async for event in self.orchestrator.execute_task_stream(
                task=task,
                request=request,
                user=user,
                session=self.session,
            ):
                if event.get("type") == "chunk":
                    accumulated_output += event.get("content", "")
                elif event.get("type") == "step_completed" and event.get("step"):
                    step_records_final.append(event.get("step"))
                elif event.get("type") == "orchestration_completed" and event.get("state"):
                    final_orch_state = event["state"]
                    step_records_final = final_orch_state.get("step_records", step_records_final)

                yield f"data: {json.dumps(event)}\n\n"

            # Finalize run
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            run.status = RunStatus.COMPLETED.value
            run.output_content = accumulated_output
            run.latency_ms = elapsed_ms
            run.orchestration_duration_ms = elapsed_ms
            run.step_count = len(step_records_final)
            run.execution_steps = step_records_final

            ctx_meta = final_orch_state.get("metadata", {}).get("context_package", {}) if final_orch_state else {}
            tok_meta = final_orch_state.get("token_usage", {}) if final_orch_state else {}
            run.estimated_context_tokens = ctx_meta.get("estimated_tokens", init_pkg.estimated_tokens)
            run.context_truncated = ctx_meta.get("truncated", init_pkg.truncated)
            run.context_item_count = len(final_orch_state.get("context_items", [])) if final_orch_state else init_pkg.total_items
            run.context_sources = list(set(it.get("source_type", "task") for it in final_orch_state.get("context_items", []))) if final_orch_state else list(init_pkg.sources)
            run.retrieved_chunk_count = len(final_orch_state.get("retrieval_results", [])) if final_orch_state else 0
            run.retrieval_latency_ms = sum(r.get("duration_ms", 0) for r in step_records_final if r.get("step_type") == "retrieve") if run.retrieved_chunk_count else None
            run.input_tokens = tok_meta.get("input_tokens")
            run.output_tokens = tok_meta.get("output_tokens")
            run.total_tokens = tok_meta.get("total_tokens")

            run.completed_at = datetime.now(timezone.utc)
            await self.session.flush()
            await self.session.refresh(run)

            yield f"data: {json.dumps({'type': 'run_completed', 'run': RunResponse.model_validate(run).model_dump(mode='json')})}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as stream_err:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            run.status = RunStatus.FAILED.value
            run.error_message = str(stream_err)
            run.latency_ms = elapsed_ms
            run.orchestration_duration_ms = elapsed_ms
            run.completed_at = datetime.now(timezone.utc)
            await self.session.flush()
            yield f"data: {json.dumps({'type': 'error', 'error': {'message': str(stream_err)}})}\n\n"
            yield "data: [DONE]\n\n"
