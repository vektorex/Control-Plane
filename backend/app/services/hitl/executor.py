"""
Execution pause and resume coordinator for Human-in-the-Loop workflows (Step 18).
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.hitl import HumanInterventionRequest
from backend.app.db.models.user import User
from backend.app.db.models.workflow import WorkflowRun
from backend.app.services.hitl.errors import HITLNotFoundError, HITLStatusError
from backend.app.services.observability.events import TraceEventStatus, TraceEventType
from backend.app.services.observability.tracer import ExecutionTracer
from backend.app.services.workflows.schemas import WorkflowRunStatus

logger = logging.getLogger(__name__)


class HITLExecutionCoordinator:
    """
    Coordinates pausing and resuming workflow executions when human intervention is triggered.
    """

    @classmethod
    async def pause_workflow(
        cls,
        session: AsyncSession,
        run: WorkflowRun,
        step_id: str,
        current_step_idx: int,
        intervention: HumanInterventionRequest,
        execution_state: Dict[str, Any],
        tracer: Optional[ExecutionTracer] = None,
    ) -> WorkflowRun:
        """
        Safely pauses a WorkflowRun, persisting current state, pending step ID, and intervention linkage.
        """
        now = datetime.now(timezone.utc)
        run.status = WorkflowRunStatus.WAITING_FOR_APPROVAL.value

        # Persist checkpoint state
        saved_state = dict(execution_state or {})
        saved_state["pending_step_id"] = step_id
        saved_state["current_step_idx"] = current_step_idx
        saved_state["intervention_id"] = str(intervention.id)
        saved_state["paused_at"] = now.isoformat()
        run.execution_state = saved_state

        if tracer:
            tracer.record_event(
                TraceEventType.WORKFLOW_PAUSED if hasattr(TraceEventType, "WORKFLOW_PAUSED") else TraceEventType.STEP_STARTED,
                status=TraceEventStatus.COMPLETED,
                metadata={
                    "intervention_id": str(intervention.id),
                    "step_id": step_id,
                    "reason": "waiting_for_human_approval",
                },
            )
            await tracer.flush_to_db(session)

        await session.commit()
        await session.refresh(run)

        try:
            from backend.app.services.notifications.dispatcher import NotificationEventBus
            from backend.app.services.notifications.constants import NotificationEventType
            await NotificationEventBus.publish({
                "workspace_id": run.workspace_id,
                "event_type": NotificationEventType.WORKFLOW_WAITING_APPROVAL.value,
                "source_type": "workflow_run",
                "source_id": str(run.id),
                "metadata": {
                    "workflow_id": str(run.workflow_id),
                    "step_id": step_id,
                    "intervention_id": str(intervention.id),
                },
            }, session=session)
        except Exception as notif_err:
            logger.warning(f"[HITLExecutor] Failed to publish approval notification: {notif_err}")

        logger.info(f"[HITLExecutor] WorkflowRun '{run.id}' paused at step '{step_id}' awaiting intervention '{intervention.id}'")
        return run

    @classmethod
    async def resume_workflow(
        cls,
        session: AsyncSession,
        workflow_run_id: UUID,
        workspace_id: UUID,
        user: User,
        intervention: HumanInterventionRequest,
    ) -> WorkflowRun:
        """
        Resumes a paused WorkflowRun after an intervention decision has been committed.
        """
        now = datetime.now(timezone.utc)

        # 1. Fetch WorkflowRun
        run = await session.get(WorkflowRun, workflow_run_id)
        if not run or run.workspace_id != workspace_id:
            raise HITLNotFoundError(f"WorkflowRun '{workflow_run_id}' not found.")

        if run.status != WorkflowRunStatus.WAITING_FOR_APPROVAL.value:
            raise HITLStatusError(
                f"WorkflowRun '{run.id}' cannot be resumed from current status '{run.status}' (expected 'waiting_for_approval')."
            )

        # 2. Check Decision Status
        if intervention.status in ["rejected", "cancelled"]:
            run.status = WorkflowRunStatus.FAILED.value
            run.completed_at = now
            run.error_code = f"human_intervention_{intervention.status}"
            run.error_message = (
                f"Workflow halted because human intervention '{intervention.id}' "
                f"was {intervention.status} by reviewer."
            )
            await session.commit()
            await session.refresh(run)
            logger.info(f"[HITLExecutor] WorkflowRun '{run.id}' marked failed following human rejection.")
            return run

        # 3. Resume Execution via WorkflowExecutor
        from backend.app.services.workflows.executor import WorkflowExecutor
        executor = WorkflowExecutor(session=session)
        resumed_run = await executor.resume_execution(
            run=run,
            intervention=intervention,
            user=user,
        )
        return resumed_run
