import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.logging import logger
from backend.app.db.models.run import Run
from backend.app.db.models.task import Task
from backend.app.db.models.project import Project
from backend.app.db.models.workflow import WorkflowRun
from backend.app.db.models.replay import ReplayRun
from backend.app.db.models.observability import ExecutionTraceEvent
from backend.app.db.models.user import User
from backend.app.services.replay.schemas import (
    ReplayMode,
    ReplayStatus,
    ReplayRunCreateRequest,
    ReplayStepRequest,
    ExecutionSnapshot,
    ReplayEligibility,
    ReplayComparisonResult,
    FailureInsights,
)
from backend.app.services.replay.snapshot import ReplaySnapshotService
from backend.app.services.replay.policies import ReplayPolicy, ReplayEligibilityChecker
from backend.app.services.replay.runner import ReplayRunner
from backend.app.services.replay.comparator import ReplayComparator
from backend.app.services.replay.error_analysis import ErrorAnalysisService
from backend.app.services.replay.errors import (
    ReplayError,
    ReplayNotFoundError,
    ReplayEligibilityError,
    ReplayPermissionDeniedError,
)


class ReplayService:
    """
    Central orchestration service for the Execution Replay & Debugging Studio.
    Coordinates snapshot capture, sanitization, policy verification,
    runner execution, trace analysis, and factual diff comparisons.
    """

    def __init__(self, runner: Optional[ReplayRunner] = None) -> None:
        self.runner = runner or ReplayRunner()

    async def get_run_with_access(
        self,
        run_id: uuid.UUID,
        workspace_id: uuid.UUID,
        session: AsyncSession,
    ) -> Run:
        """Retrieves a Run enforcing strict workspace isolation."""
        stmt = (
            select(Run)
            .join(Task, Run.task_id == Task.id)
            .join(Project, Task.project_id == Project.id)
            .options(selectinload(Run.task))
            .where(Run.id == run_id, Project.workspace_id == workspace_id)
        )
        result = await session.execute(stmt)
        run = result.scalar_one_or_none()
        if not run:
            raise ReplayNotFoundError(f"Run {run_id} not found in workspace {workspace_id}")
        return run

    async def get_workflow_run_with_access(
        self,
        workflow_run_id: uuid.UUID,
        workspace_id: uuid.UUID,
        session: AsyncSession,
    ) -> WorkflowRun:
        """Retrieves a WorkflowRun enforcing strict workspace isolation."""
        stmt = (
            select(WorkflowRun)
            .options(selectinload(WorkflowRun.workflow))
            .where(WorkflowRun.id == workflow_run_id, WorkflowRun.workspace_id == workspace_id)
        )
        result = await session.execute(stmt)
        wf_run = result.scalar_one_or_none()
        if not wf_run:
            raise ReplayNotFoundError(f"WorkflowRun {workflow_run_id} not found in workspace {workspace_id}")
        return wf_run

    async def check_run_eligibility(
        self,
        run_id: uuid.UUID,
        workspace_id: uuid.UUID,
        session: AsyncSession,
    ) -> ReplayEligibility:
        """Evaluates whether an execution run can be safely replayed."""
        run = await self.get_run_with_access(run_id, workspace_id, session)
        return await ReplayEligibilityChecker.check_run_eligibility(run, session)

    async def create_replay(
        self,
        run_id: uuid.UUID,
        request: ReplayRunCreateRequest,
        workspace_id: uuid.UUID,
        user: Optional[User],
        session: AsyncSession,
    ) -> ReplayRun:
        """
        Initiates a replay execution for an existing Run.
        Supports inspect, dry_run, replay, and compare modes.
        Enforces immutable original runs and fresh HITL approval gating.
        """
        run = await self.get_run_with_access(run_id, workspace_id, session)

        # 1. Verify eligibility
        eligibility = await ReplayEligibilityChecker.check_run_eligibility(run, session)
        if not eligibility.eligible:
            raise ReplayEligibilityError(
                f"Run is not eligible for replay: {'; '.join(eligibility.warnings)}"
            )

        # 2. Capture deterministic, sanitized snapshot
        snapshot = await ReplaySnapshotService.create_snapshot_from_run(run, session)

        # 3. Determine dry_run flag based on mode
        is_dry_run = True
        if request.mode == ReplayMode.REPLAY:
            is_dry_run = request.dry_run
        elif request.mode in (ReplayMode.INSPECT, ReplayMode.DRY_RUN, ReplayMode.COMPARE):
            is_dry_run = True

        # Check if modified configuration
        has_overrides = bool(request.overrides)

        wf_run_id = None
        if isinstance(run.input_snapshot, dict) and run.input_snapshot.get("workflow_run_id"):
            try:
                wf_run_id = uuid.UUID(str(run.input_snapshot.get("workflow_run_id")))
            except Exception:
                pass

        # 4. Create ReplayRun record
        replay_run = ReplayRun(
            workspace_id=workspace_id,
            original_run_id=run.id,
            original_workflow_run_id=wf_run_id,
            replay_mode=request.mode.value,
            status=ReplayStatus.QUEUED.value,
            snapshot_version=snapshot.snapshot_version,
            dry_run=is_dry_run,
            snapshot=snapshot.model_dump(),
            created_by=user.id if user else None,
            replay_metadata={
                "eligibility_warnings": eligibility.warnings,
                "overrides": request.overrides or {},
                "retrieval_replay_mode": request.retrieval_replay_mode.value,
                "modified_replay": has_overrides,
                "created_by_user": str(user.id) if user else None,
            },
        )
        session.add(replay_run)
        await session.commit()
        await session.refresh(replay_run)

        # 5. Execute replay via ReplayRunner
        executed_run = await self.runner.execute_replay(
            replay_run=replay_run,
            overrides=request.overrides,
            session=session,
        )
        return executed_run

    async def create_workflow_replay(
        self,
        workflow_run_id: uuid.UUID,
        request: ReplayRunCreateRequest,
        workspace_id: uuid.UUID,
        user: Optional[User],
        session: AsyncSession,
    ) -> ReplayRun:
        """
        Initiates a workflow replay using the exact recorded workflow version.
        """
        wf_run = await self.get_workflow_run_with_access(workflow_run_id, workspace_id, session)

        # Check eligibility
        eligibility = await ReplayEligibilityChecker.check_workflow_run_eligibility(wf_run, session)
        if not eligibility.eligible:
            raise ReplayEligibilityError(
                f"WorkflowRun is not eligible for replay: {'; '.join(eligibility.warnings)}"
            )

        # Find associated Runs
        stmt = (
            select(Run)
            .options(selectinload(Run.task))
            .where(Run.workflow_run_id == wf_run.id, Run.workspace_id == workspace_id)
            .order_by(Run.created_at.desc())
        )
        run_res = await session.execute(stmt)
        associated_runs = list(run_res.scalars().all())

        if not associated_runs:
            raise ReplayEligibilityError(
                f"WorkflowRun {workflow_run_id} has no executable task runs to replay."
            )

        target_run = associated_runs[0]
        snapshot = await ReplaySnapshotService.create_snapshot_from_workflow_run(wf_run, session)

        is_dry_run = True if request.mode != ReplayMode.REPLAY else request.dry_run

        replay_run = ReplayRun(
            workspace_id=workspace_id,
            original_run_id=target_run.id,
            original_workflow_run_id=wf_run.id,
            replay_mode=request.mode.value,
            status=ReplayStatus.QUEUED.value,
            snapshot_version=snapshot.snapshot_version,
            dry_run=is_dry_run,
            snapshot=snapshot.model_dump(),
            created_by=user.id if user else None,
            replay_metadata={
                "workflow_version": wf_run.workflow_version or (wf_run.workflow.version if wf_run.workflow else 1),
                "eligibility_warnings": eligibility.warnings,
                "overrides": request.overrides or {},
                "retrieval_replay_mode": request.retrieval_replay_mode.value,
                "modified_replay": bool(request.overrides),
            },
        )
        session.add(replay_run)
        await session.commit()
        await session.refresh(replay_run)

        return await self.runner.execute_replay(
            replay_run=replay_run,
            overrides=request.overrides,
            session=session,
        )

    async def replay_step(
        self,
        run_id: uuid.UUID,
        step_id: str,
        request: ReplayStepRequest,
        workspace_id: uuid.UUID,
        user: Optional[User],
        session: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Safely re-executes an isolated individual step from an execution run.
        """
        run = await self.get_run_with_access(run_id, workspace_id, session)
        return await self.runner.replay_single_step(
            original_run=run,
            step_id=step_id,
            dry_run=request.dry_run,
            overrides=request.overrides,
            session=session,
        )

    async def get_replay(
        self,
        replay_id: uuid.UUID,
        workspace_id: uuid.UUID,
        session: AsyncSession,
    ) -> ReplayRun:
        """Retrieves a single ReplayRun ensuring workspace isolation."""
        stmt = (
            select(ReplayRun)
            .options(
                selectinload(ReplayRun.original_run).selectinload(Run.task),
                selectinload(ReplayRun.original_workflow_run),
            )
            .where(ReplayRun.id == replay_id, ReplayRun.workspace_id == workspace_id)
        )
        result = await session.execute(stmt)
        replay = result.scalar_one_or_none()
        if not replay:
            raise ReplayNotFoundError(f"Replay run {replay_id} not found in workspace {workspace_id}")
        return replay

    async def list_replays(
        self,
        workspace_id: uuid.UUID,
        session: AsyncSession,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        mode: Optional[str] = None,
        original_run_id: Optional[uuid.UUID] = None,
        workflow_run_id: Optional[uuid.UUID] = None,
    ) -> Tuple[List[ReplayRun], int]:
        """Lists replay runs with pagination and optional filtering."""
        query = select(ReplayRun).where(ReplayRun.workspace_id == workspace_id)
        count_query = select(func.count(ReplayRun.id)).where(ReplayRun.workspace_id == workspace_id)

        if status:
            query = query.where(ReplayRun.status == status)
            count_query = count_query.where(ReplayRun.status == status)
        if mode:
            query = query.where(ReplayRun.replay_mode == mode)
            count_query = count_query.where(ReplayRun.replay_mode == mode)
        if original_run_id:
            query = query.where(ReplayRun.original_run_id == original_run_id)
            count_query = count_query.where(ReplayRun.original_run_id == original_run_id)
        if workflow_run_id:
            query = query.where(ReplayRun.original_workflow_run_id == workflow_run_id)
            count_query = count_query.where(ReplayRun.original_workflow_run_id == workflow_run_id)

        # Count total
        total_res = await session.execute(count_query)
        total = total_res.scalar_one()

        # Fetch page
        offset = max(0, (page - 1) * limit)
        query = (
            query.options(selectinload(ReplayRun.original_run))
            .order_by(ReplayRun.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        results = await session.execute(query)
        return list(results.scalars().all()), total

    async def cancel_replay(
        self,
        replay_id: uuid.UUID,
        workspace_id: uuid.UUID,
        user: Optional[User],
        session: AsyncSession,
    ) -> ReplayRun:
        """Cooperatively cancels an in-flight replay."""
        replay = await self.get_replay(replay_id, workspace_id, session)
        return await self.runner.cancel_replay(replay, session)

    async def compare_replay(
        self,
        replay_id: uuid.UUID,
        workspace_id: uuid.UUID,
        session: AsyncSession,
    ) -> ReplayComparisonResult:
        """Produces a factual comparison between original and replay executions."""
        replay = await self.get_replay(replay_id, workspace_id, session)
        return ReplayComparator.compare_runs(replay.original_run, replay)

    async def get_replay_trace(
        self,
        replay_id: uuid.UUID,
        workspace_id: uuid.UUID,
        session: AsyncSession,
    ) -> List[Dict[str, Any]]:
        """Retrieves execution trace timeline events for replay debugging."""
        replay = await self.get_replay(replay_id, workspace_id, session)
        
        stmt = (
            select(ExecutionTraceEvent)
            .where(
                ExecutionTraceEvent.run_id == replay.original_run_id,
                ExecutionTraceEvent.workspace_id == workspace_id,
            )
            .order_by(ExecutionTraceEvent.sequence_number.asc())
        )
        res = await session.execute(stmt)
        events = res.scalars().all()

        return [
            {
                "id": str(e.id),
                "sequence_number": e.sequence_number,
                "event_type": e.event_type,
                "step_type": e.step_type,
                "status": e.status,
                "duration_ms": e.duration_ms,
                "model": e.model,
                "provider": e.provider,
                "error_code": e.error_code,
                "metadata": e.metadata_json or {},
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ]

    async def get_failure_diagnostics(
        self,
        run_id: uuid.UUID,
        workspace_id: uuid.UUID,
        session: AsyncSession,
    ) -> FailureInsights:
        """Generates factual failure insights for a failed run."""
        run = await self.get_run_with_access(run_id, workspace_id, session)
        return ErrorAnalysisService.analyze_failure(run)
