import asyncio
import json
import time
from datetime import datetime, timezone
from typing import AsyncIterator, Dict, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.errors import AppError, InvalidStateError
from backend.app.core.logging import logger
from backend.app.db.models.enums import RunStatus, TaskStatus
from backend.app.db.models.run import Run
from backend.app.db.models.task import Task
from backend.app.db.models.user import User
from backend.app.repositories.run import RunRepository
from backend.app.repositories.task import TaskRepository
from backend.app.repositories.evaluation import EvaluationRepository
from backend.app.services.evaluation.schemas import EvaluationResult
from backend.app.schemas.llm import ChatMessage, LLMGenerateRequest
from backend.app.schemas.run import RunResponse
from backend.app.schemas.task import TaskRunRequest
from backend.app.services.context.engine import ContextEngine, get_context_engine
from backend.app.services.context.models import ContextBudget
from backend.app.services.llm.factory import LLMProviderFactory, get_llm_factory
from backend.app.services.models.registry import default_model_registry
from backend.app.services.models.router import ModelRequirementAnalyzer, default_model_router
from backend.app.services.orchestration.orchestrator import Orchestrator, get_orchestrator
from backend.app.services.orchestration.plan import ExecutionPlan, StepType


def calculate_estimated_cost(
    model_id: Optional[str],
    provider_id: Optional[str],
    input_tokens: Optional[int],
    output_tokens: Optional[int],
) -> Optional[float]:
    """
    Calculates estimated run cost based on configured ModelRegistry cost metadata.
    Returns None if pricing configuration is unavailable without guessing.
    """
    if not model_id or (input_tokens is None and output_tokens is None):
        return None
    model_def = default_model_registry.get_model(model_id, provider=provider_id)
    if not model_def or not model_def.cost_metadata:
        return None
    in_rate = model_def.cost_metadata.input_cost_per_1k_tokens
    out_rate = model_def.cost_metadata.output_cost_per_1k_tokens
    if in_rate is None and out_rate is None:
        return None

    in_tok = input_tokens or 0
    out_tok = output_tokens or 0
    total = ((in_tok / 1000.0) * (in_rate or 0.0)) + ((out_tok / 1000.0) * (out_rate or 0.0))
    return round(total, 6)


class TaskExecutionService:
    """
    Service responsible for turning a Task entity into an orchestrated AI workflow
    via the Orchestration Engine, coordinating planning, retrieval, tools, context,
    intelligent model routing, verification engine, and persisting execution runs with complete observability.
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
        self.eval_repo = EvaluationRepository(session)

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

        # 2. Extract planning metadata
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

        # 3. Model Requirement Extraction and Model Routing (Step 12)
        model_mode = request.model_mode or getattr(task, "model_mode", None) or settings.DEFAULT_MODEL_MODE or "auto"
        latency_pref = request.latency_preference or getattr(task, "latency_preference", "balanced")
        cost_pref = request.cost_preference or getattr(task, "cost_preference", "balanced")

        model_reqs = ModelRequirementAnalyzer.analyze(
            task=task,
            context_token_estimate=request.max_context_tokens or 8000,
            enable_tools=bool(tools_planned or request.tool_mode == "enabled" or request.enable_web_search),
            streaming=False,
            execution_plan=plan,
            latency_preference=latency_pref,
            cost_preference=cost_pref,
            manual_model_pref=request.model or getattr(task, "preferred_model", None),
        )

        if model_mode == "manual" and (request.model or getattr(task, "preferred_model", None)):
            target_manual = request.model or getattr(task, "preferred_model", settings.GENERATION_DEFAULT_MODEL)
            model_selection = default_model_router.validate_manual_selection(
                model_id=target_manual,
                provider=request.provider,
                requirements=model_reqs,
            )
        else:
            model_selection = default_model_router.route(
                requirements=model_reqs,
                policy_name=latency_pref,
            )

        # Inject routed model and fallback candidates into generate steps
        for step in plan.steps:
            if step.type == StepType.GENERATE:
                step.model = model_selection.model_id
                if step.metadata is None:
                    step.metadata = {}
                step.metadata["model_selection"] = model_selection.model_dump(mode="json")

        plan_json = plan.model_dump(mode="json")
        planner_mode = plan.metadata.get("planner_mode") or request.planner_mode or "hybrid"
        planner_model = plan.metadata.get("planner_model")
        repair_count = plan.metadata.get("repair_count", 0)

        # 4. Create initial Run in 'running' status
        start_time = time.perf_counter()
        run = Run(
            task_id=task.id,
            status=RunStatus.RUNNING.value,
            model_provider=model_selection.provider,
            model_name=model_selection.model_id,
            final_model=model_selection.model_id,
            model_selection_reason=model_selection.reason,
            model_routing_policy=model_selection.policy,
            fallback_attempts=0,
            planner_mode=planner_mode,
            planner_model=planner_model,
            repair_count=repair_count,
            iteration_count=1,
            input_snapshot={
                "model": model_selection.model_id,
                "provider": model_selection.provider,
                "model_mode": model_mode,
                "model_selection": model_selection.model_dump(mode="json"),
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

        # 5. Execute Orchestration Plan with bounded agentic loop
        try:
            state = await self.orchestrator.execute_task(
                task=task,
                request=request,
                user=user,
                session=self.session,
            )

            # 6. Harvest execution state telemetry
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

            # Final Model, Fallback & Cost telemetry (Step 12)
            final_mod = state.metadata.get("final_model") or model_selection.model_id
            final_prov = state.metadata.get("model_provider") or model_selection.provider
            fallback_attempts = state.metadata.get("fallback_attempts", 0)

            run.final_model = final_mod
            run.model_provider = final_prov
            run.fallback_attempts = fallback_attempts
            run.model_selection_reason = model_selection.reason
            run.model_routing_policy = model_selection.policy
            run.estimated_cost = calculate_estimated_cost(
                model_id=final_mod,
                provider_id=final_prov,
                input_tokens=run.input_tokens,
                output_tokens=run.output_tokens,
            )

            # Step 11 updates
            run.planner_mode = state.planning_mode or planner_mode
            run.planner_model = state.planner_model or planner_model
            run.repair_count = state.repair_count
            run.iteration_count = state.iteration
            run.completion_evaluation = state.completion_evaluation
            if state.validated_plan:
                run.execution_plan = state.validated_plan.model_dump(mode="json")

            # Step 13: Evaluation & Verification Telemetry & Records
            final_eval = state.metadata.get("evaluation_result")
            if final_eval:
                run.evaluation_status = final_eval.get("status")
                run.evaluation_mode = final_eval.get("mode")
                run.evaluation_duration_ms = final_eval.get("duration_ms", 0)
                run.evaluation_attempts = final_eval.get("attempt", 1)
                run.revision_attempts = state.metadata.get("revision_attempts", 0)
                run.evaluation_result = final_eval

                try:
                    eval_obj = EvaluationResult.model_validate(final_eval)
                    await self.eval_repo.record_evaluation_result(
                        run_id=run.id,
                        result=eval_obj,
                        evaluator_type="engine",
                    )
                except Exception as eval_persist_err:
                    logger.warning(f"Failed to record evaluation result in DB: {eval_persist_err}")

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

        tool_steps = [s for s in plan.steps if s.type == StepType.TOOL]
        tools_planned = [s.tool for s in tool_steps if s.tool]

        # 2. Model Routing (Step 12)
        model_mode = request.model_mode or getattr(task, "model_mode", None) or settings.DEFAULT_MODEL_MODE or "auto"
        latency_pref = request.latency_preference or getattr(task, "latency_preference", "balanced")
        cost_pref = request.cost_preference or getattr(task, "cost_preference", "balanced")

        model_reqs = ModelRequirementAnalyzer.analyze(
            task=task,
            context_token_estimate=request.max_context_tokens or 8000,
            enable_tools=bool(tools_planned or request.tool_mode == "enabled" or request.enable_web_search),
            streaming=True,
            execution_plan=plan,
            latency_preference=latency_pref,
            cost_preference=cost_pref,
            manual_model_pref=request.model or getattr(task, "preferred_model", None),
        )

        if model_mode == "manual" and (request.model or getattr(task, "preferred_model", None)):
            target_manual = request.model or getattr(task, "preferred_model", settings.GENERATION_DEFAULT_MODEL)
            model_selection = default_model_router.validate_manual_selection(
                model_id=target_manual,
                provider=request.provider,
                requirements=model_reqs,
            )
        else:
            model_selection = default_model_router.route(
                requirements=model_reqs,
                policy_name=latency_pref,
            )

        # Inject routed model into generate step
        for step in plan.steps:
            if step.type == StepType.GENERATE:
                step.model = model_selection.model_id
                if step.metadata is None:
                    step.metadata = {}
                step.metadata["model_selection"] = model_selection.model_dump(mode="json")

        plan_json = plan.model_dump(mode="json")
        planner_mode = plan.metadata.get("planner_mode") or request.planner_mode or "hybrid"
        planner_model = plan.metadata.get("planner_model")
        repair_count = plan.metadata.get("repair_count", 0)

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

        # 3. Create Run entity in DB
        start_time = time.perf_counter()
        run = Run(
            task_id=task.id,
            status=RunStatus.RUNNING.value,
            model_provider=model_selection.provider,
            model_name=model_selection.model_id,
            final_model=model_selection.model_id,
            model_selection_reason=model_selection.reason,
            model_routing_policy=model_selection.policy,
            fallback_attempts=0,
            planner_mode=planner_mode,
            planner_model=planner_model,
            repair_count=repair_count,
            iteration_count=1,
            execution_plan=plan_json,
            retrieval_enabled=retrieval_required,
            retrieval_mode=request.retrieval_mode or "auto",
            retrieval_required=retrieval_required,
            retrieval_strategy=retrieval_strategy,
            retrieval_scope=retrieval_scope,
            retrieval_top_k=retrieval_meta.get("top_k"),
            retrieval_reason=retrieval_meta.get("reason"),
            retrieval_confidence=retrieval_meta.get("confidence"),
            tools_used=tools_planned if tools_planned else None,
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(run)
        await self.session.flush()
        await self.session.refresh(run)

        # Emit run_start and model_selected events
        yield f"data: {json.dumps({'type': 'run_start', 'run_id': str(run.id), 'execution_plan': plan_json, 'orchestration_plan': plan_json, 'tools_used': run.tools_used, 'retrieval_enabled': retrieval_required, 'context_item_count': init_pkg.total_items, 'estimated_context_tokens': init_pkg.estimated_tokens, 'context_truncated': init_pkg.truncated, 'context_sources': list(init_pkg.sources)})}\n\n"
        yield f"data: {json.dumps({'type': 'model_selected', 'model': model_selection.model_id, 'provider': model_selection.provider, 'display_name': model_selection.display_name, 'reason': model_selection.reason, 'policy': model_selection.policy, 'satisfied_requirements': model_selection.satisfied_requirements})}\n\n"

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
                elif event.get("type") == "content_delta":
                    accumulated_output += event.get("delta", "")
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

            # Final model and fallback metadata
            final_mod = final_orch_state.get("metadata", {}).get("final_model") if final_orch_state else model_selection.model_id
            final_prov = final_orch_state.get("metadata", {}).get("model_provider") if final_orch_state else model_selection.provider
            fallback_attempts = final_orch_state.get("metadata", {}).get("fallback_attempts", 0) if final_orch_state else 0

            run.final_model = final_mod or model_selection.model_id
            run.model_provider = final_prov or model_selection.provider
            run.fallback_attempts = fallback_attempts
            run.model_selection_reason = model_selection.reason
            run.model_routing_policy = model_selection.policy
            run.estimated_cost = calculate_estimated_cost(
                model_id=run.final_model,
                provider_id=run.model_provider,
                input_tokens=run.input_tokens,
                output_tokens=run.output_tokens,
            )

            if final_orch_state:
                run.planner_mode = final_orch_state.get("planning_mode", planner_mode)
                run.planner_model = final_orch_state.get("planner_model", planner_model)
                run.repair_count = final_orch_state.get("repair_count", repair_count)
                run.iteration_count = final_orch_state.get("iteration", 1)
                run.completion_evaluation = final_orch_state.get("completion_evaluation")

                # Step 13: Evaluation & Verification metadata from streaming state
                final_eval = final_orch_state.get("metadata", {}).get("evaluation_result")
                if final_eval:
                    run.evaluation_status = final_eval.get("status")
                    run.evaluation_mode = final_eval.get("mode")
                    run.evaluation_duration_ms = final_eval.get("duration_ms", 0)
                    run.evaluation_attempts = final_eval.get("attempt", 1)
                    run.revision_attempts = final_orch_state.get("metadata", {}).get("revision_attempts", 0)
                    run.evaluation_result = final_eval

                    try:
                        eval_obj = EvaluationResult.model_validate(final_eval)
                        await self.eval_repo.record_evaluation_result(
                            run_id=run.id,
                            result=eval_obj,
                            evaluator_type="engine",
                        )
                    except Exception as eval_persist_err:
                        logger.warning(f"Failed to record evaluation result in DB: {eval_persist_err}")

            # Harvest tool results from stream
            if final_orch_state and final_orch_state.get("tool_results"):
                t_used = []
                t_lat = 0
                for tr in final_orch_state["tool_results"]:
                    tn = tr.get("tool_name", "unknown")
                    if tn not in t_used:
                        t_used.append(tn)
                    t_lat += tr.get("latency_ms", 0)
                run.tools_used = t_used
                run.tool_call_count = len(final_orch_state["tool_results"])
                run.tool_latency_ms = t_lat

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
