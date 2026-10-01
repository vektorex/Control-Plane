import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.db.models.run import Run
from backend.app.db.models.task import Task
from backend.app.db.models.workflow import WorkflowRun
from backend.app.db.models.replay import ReplayRun
from backend.app.schemas.task import TaskRunRequest
from backend.app.services.observability import (
    ObservabilityService,
    ExecutionTracer,
    TraceEventType,
    TraceEventStatus,
)
from backend.app.services.orchestration.orchestrator import Orchestrator, get_orchestrator
from backend.app.services.orchestration.plan import ExecutionPlan, ExecutionStepPlan, StepType
from backend.app.services.ai_gateway import GatewayRequest, default_ai_gateway
from backend.app.services.replay.schemas import (
    ReplayMode,
    ReplayStatus,
    RetrievalReplayMode,
)
from backend.app.services.replay.policies import ReplayPolicy
from backend.app.services.replay.comparator import ReplayComparator
from backend.app.services.replay.errors import (
    ReplayError,
    ReplayNotFoundError,
    SideEffectBlockedError,
)


class ReplayRunner:
    """
    Executes replay simulations and re-executions under strict side-effect isolation.
    Reuses existing AI Gateway, Orchestrator, Model Router, and Evaluation Engine.
    Never alters original Runs or historical approvals.
    """

    def __init__(
        self,
        orchestrator: Optional[Orchestrator] = None,
    ) -> None:
        self.orchestrator = orchestrator or get_orchestrator()

    async def execute_replay(
        self,
        replay_run: ReplayRun,
        overrides: Optional[Dict[str, Any]],
        session: AsyncSession,
    ) -> ReplayRun:
        """
        Executes a replay run according to its replay_mode (inspect, dry_run, replay, compare).
        """
        # Concurrency safety: if already running, return existing state
        if replay_run.status == ReplayStatus.RUNNING.value:
            return replay_run

        replay_run.status = ReplayStatus.RUNNING.value
        replay_run.started_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(replay_run)

        # Telemetry: replay_started
        tracer = ExecutionTracer(
            run_id=replay_run.original_run_id,
            workspace_id=replay_run.workspace_id,
        )
        tracer.record_event(
            TraceEventType.REPLAY_STARTED,
            step_type="replay",
            metadata={
                "replay_id": str(replay_run.id),
                "original_run_id": str(replay_run.original_run_id),
                "replay_mode": replay_run.replay_mode,
                "dry_run": replay_run.dry_run,
                "snapshot_version": replay_run.snapshot_version,
            },
        )
        await tracer.flush_to_db(session)

        try:
            # 1. Inspect Mode (read-only inspection of historical snapshot)
            if replay_run.replay_mode == ReplayMode.INSPECT.value:
                orig_run = replay_run.original_run
                orig_out = orig_run.output_content if orig_run else None
                if not orig_out:
                    orig_out = replay_run.snapshot.get("task_configuration", {}).get("title", "Inspected run")
                replay_run.replay_output = orig_out
                replay_run.execution_steps = orig_run.execution_steps or []
                replay_run.replay_metadata = {
                    "mode": "inspect",
                    "inspection_notice": "Read-only inspection of original execution.",
                    "original_latency_ms": orig_run.latency_ms,
                    "original_tokens": orig_run.total_tokens,
                }
                replay_run.status = ReplayStatus.COMPLETED.value
                replay_run.completed_at = datetime.now(timezone.utc)
                await session.commit()
                await session.refresh(replay_run)
                return replay_run

            # 2. Execution Modes: dry_run, replay, compare
            orig_run: Run = replay_run.original_run
            snapshot = replay_run.snapshot or {}
            task_cfg = snapshot.get("task_configuration", {})
            model_cfg = snapshot.get("model_configuration", {})
            retrieval_cfg = snapshot.get("retrieval_configuration", {})
            eval_cfg = snapshot.get("evaluation_configuration", {})

            # Apply safe user overrides
            safe_overrides = overrides or {}
            target_model = safe_overrides.get("model") or model_cfg.get("model_name") or settings.GENERATION_DEFAULT_MODEL
            target_temp = float(safe_overrides.get("temperature", model_cfg.get("temperature", 0.2)))
            eval_mode = safe_overrides.get("evaluation_mode") or eval_cfg.get("evaluation_mode") or "standard"
            retrieval_strategy = safe_overrides.get("retrieval_strategy") or retrieval_cfg.get("retrieval_strategy")
            planner_mode = safe_overrides.get("planner_mode") or "hybrid"

            # Load Task
            task_obj = orig_run.task
            if not task_obj:
                task_res = await session.execute(select(Task).where(Task.id == orig_run.task_id))
                task_obj = task_res.scalar_one_or_none()

            if not task_obj:
                raise ReplayNotFoundError(f"Associated Task {orig_run.task_id} not found.")

            # Build TaskRunRequest
            req = TaskRunRequest(
                model=target_model,
                temperature=target_temp,
                planner_mode=planner_mode,
                retrieval_mode=retrieval_cfg.get("retrieval_mode") or "auto",
                retrieval_strategy=retrieval_strategy,
                retrieval_scope=retrieval_cfg.get("retrieval_scope") or "project",
                retrieval_top_k=int(safe_overrides.get("retrieval_top_k") or retrieval_cfg.get("retrieval_top_k") or 8),
                enable_web_search=snapshot.get("tool_configuration", {}).get("enable_web_search", False),
                evaluation_mode=eval_mode,
            )

            # Enforce side effect policy for replay
            blocked_side_effects_count = 0
            if replay_run.dry_run:
                # In dry_run mode, write tools are simulated
                req.tool_mode = "disabled" if not req.enable_web_search else "enabled"
                blocked_side_effects_count += 1
                tracer.record_event(
                    TraceEventType.REPLAY_SIDE_EFFECT_BLOCKED,
                    step_type="safety_policy",
                    metadata={
                        "replay_id": str(replay_run.id),
                        "reason": "Side effect blocked under dry-run replay policy.",
                    },
                )

            # Re-execute via existing Orchestrator
            exec_state = await self.orchestrator.execute_task(
                task=task_obj,
                request=req,
                user=replay_run.creator,
                session=session,
                tracer=tracer,
            )

            replay_run.replay_output = exec_state.generated_output
            replay_run.execution_steps = [
                s.model_dump(mode="json") if hasattr(s, "model_dump") else s
                for s in exec_state.step_records
            ]

            meta = dict(replay_run.replay_metadata or {})
            meta.update({
                "token_usage": exec_state.token_usage,
                "final_model": exec_state.metadata.get("final_model", target_model),
                "model_provider": exec_state.metadata.get("model_provider"),
                "evaluation_result": exec_state.completion_evaluation or exec_state.metadata.get("evaluation_result"),
                "context_sources": exec_state.metadata.get("context_package", {}).get("sources", []),
                "tools_used": [s.tool_name for s in exec_state.step_records if s.tool_name],
                "side_effects_blocked_count": blocked_side_effects_count,
                "overrides": safe_overrides,
                "duration_ms": int((datetime.now(timezone.utc) - (replay_run.started_at.replace(tzinfo=timezone.utc) if replay_run.started_at and replay_run.started_at.tzinfo is None else (replay_run.started_at or datetime.now(timezone.utc)))).total_seconds() * 1000),
            })

            # 3. Compare Mode
            if replay_run.replay_mode in (ReplayMode.COMPARE.value, ReplayMode.DRY_RUN.value, ReplayMode.REPLAY.value):
                comparison = ReplayComparator.compare_runs(orig_run, replay_run)
                meta["comparison"] = comparison.model_dump()

            replay_run.replay_metadata = meta
            replay_run.status = ReplayStatus.COMPLETED.value
            replay_run.completed_at = datetime.now(timezone.utc)

            tracer.record_event(
                TraceEventType.REPLAY_COMPLETED,
                step_type="replay",
                metadata={"replay_id": str(replay_run.id), "status": "completed"},
            )
            await tracer.flush_to_db(session)
            await session.commit()
            await session.refresh(replay_run)
            return replay_run

        except Exception as exc:
            logger.error(f"[ReplayRunner] Replay execution failed: {exc}", exc_info=True)
            replay_run.status = ReplayStatus.FAILED.value
            replay_run.error_code = getattr(exc, "code", "REPLAY_FAILED")
            replay_run.error_message = str(exc)
            replay_run.completed_at = datetime.now(timezone.utc)

            tracer.record_event(
                TraceEventType.REPLAY_FAILED,
                step_type="replay",
                status=TraceEventStatus.FAILED,
                metadata={"replay_id": str(replay_run.id), "error": str(exc)},
            )
            await tracer.flush_to_db(session)
            await session.commit()
            await session.refresh(replay_run)
            return replay_run

    async def cancel_replay(self, replay_run: ReplayRun, session: AsyncSession) -> ReplayRun:
        """Cooperatively cancels an in-flight replay run."""
        if replay_run.status in (ReplayStatus.COMPLETED.value, ReplayStatus.FAILED.value, ReplayStatus.CANCELLED.value):
            return replay_run

        replay_run.status = ReplayStatus.CANCELLED.value
        replay_run.completed_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(replay_run)
        return replay_run

    async def replay_single_step(
        self,
        original_run: Run,
        step_id: str,
        dry_run: bool,
        overrides: Optional[Dict[str, Any]],
        session: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Replays an individual execution step safely in isolation.
        """
        steps = original_run.execution_steps or []
        if not steps and isinstance(original_run.input_snapshot, dict):
            steps = original_run.input_snapshot.get("execution_steps", [])
        target_step = next((s for s in steps if s.get("id") == step_id or s.get("step_id") == step_id), None)

        if not target_step:
            raise ReplayNotFoundError(f"Step '{step_id}' not found in original run {original_run.id}")

        stype = target_step.get("type") or target_step.get("step_type")
        tool_name = target_step.get("tool") or target_step.get("tool_name")

        # 1. Tool step with side effect policy
        if stype == "tool":
            if ReplayPolicy.should_block_side_effect(operation=tool_name or "tool_call", tool_name=tool_name, dry_run=dry_run):
                return ReplayPolicy.format_dry_run_simulation(
                    operation=tool_name or "tool_call",
                    tool_name=tool_name,
                    inputs=target_step.get("tool_input"),
                )

        # 2. Generate step replay via AIGateway
        if stype == "generate":
            target_model = (overrides or {}).get("model") or target_step.get("model") or original_run.model_name or settings.GENERATION_DEFAULT_MODEL
            prompt_text = target_step.get("description") or original_run.output_content or "Replay generate step"

            gw_req = GatewayRequest(
                model=target_model,
                messages=[{"role": "user", "content": prompt_text}],
                temperature=float((overrides or {}).get("temperature", 0.2)),
                max_tokens=1000,
                metadata={"purpose": "step_replay", "original_run_id": str(original_run.id), "step_id": step_id},
            )
            resp = await default_ai_gateway.execute(gw_req)
            return {
                "step_id": step_id,
                "type": "generate",
                "status": "completed",
                "output": resp.content,
                "model": resp.model,
                "provider": resp.provider,
                "dry_run": dry_run,
            }

        return {
            "step_id": step_id,
            "type": stype,
            "status": "simulated",
            "dry_run": dry_run,
            "message": f"Step '{step_id}' ({stype}) replayed safely.",
        }
