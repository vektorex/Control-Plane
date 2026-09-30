"""
Transactional approval decision processing and audit recording (Step 18).
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.hitl import (
    ApprovalDecision,
    HumanAction,
    HumanInterventionRequest,
)
from backend.app.db.models.user import User
from backend.app.db.models.workspace import Workspace
from backend.app.services.hitl.errors import (
    HITLExpiredError,
    HITLNotFoundError,
    HITLPermissionError,
    HITLStatusError,
    HITLValidationError,
)
from backend.app.services.hitl.notifications import NotificationService
from backend.app.services.hitl.requests import InterventionRequestManager
from backend.app.services.hitl.schemas import (
    ApprovalDecisionType,
    InterventionStatus,
)

logger = logging.getLogger(__name__)


class ApprovalDecisionProcessor:
    """
    Atomically processes human approval, rejection, editing, and cancellation decisions.
    """

    @classmethod
    async def process_decision(
        cls,
        session: AsyncSession,
        intervention_id: UUID,
        workspace_id: UUID,
        user: User,
        decision: ApprovalDecisionType,
        comment: Optional[str] = None,
        edited_data: Optional[Dict[str, Any]] = None,
    ) -> HumanInterventionRequest:
        """
        Processes an intervention decision with strict locking, expiration, and permission checks.
        """
        now = datetime.now(timezone.utc)

        # 1. Fetch intervention request
        stmt = (
            select(HumanInterventionRequest)
            .where(
                and_(
                    HumanInterventionRequest.id == intervention_id,
                    HumanInterventionRequest.workspace_id == workspace_id,
                )
            )
            .with_for_update()
        )
        res = await session.execute(stmt)
        intervention = res.scalars().first()
        if not intervention:
            raise HITLNotFoundError(str(intervention_id))

        # 2. Check Expiration
        exp = intervention.expires_at
        if exp and exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp and now > exp:
            intervention.status = InterventionStatus.EXPIRED.value
            intervention.resolved_at = now
            await session.commit()
            raise HITLExpiredError(f"Intervention request '{intervention_id}' expired at {intervention.expires_at}.")

        # 3. Check Status
        if intervention.status != InterventionStatus.PENDING.value:
            raise HITLStatusError(
                f"Intervention request '{intervention_id}' is already in '{intervention.status}' state."
            )

        # 4. Check Authorization
        # If assigned to a specific user, only that user or the workspace owner can resolve it
        if intervention.assigned_to and intervention.assigned_to != user.id:
            ws = await session.get(Workspace, workspace_id)
            if not ws or ws.owner_user_id != user.id:
                raise HITLPermissionError(
                    f"User '{user.id}' is not authorized to resolve request assigned to '{intervention.assigned_to}'."
                )

        # 5. Handle Decision Specifics
        clean_edited_data = None
        if decision == ApprovalDecisionType.EDIT:
            if not edited_data:
                raise HITLValidationError("Edited data payload is required for 'edit' decision.")
            clean_edited_data = InterventionRequestManager.sanitize_payload(edited_data)
            intervention.status = InterventionStatus.EDITED.value
            intervention.selected_action = "edit"
            intervention.response_data = clean_edited_data
        elif decision == ApprovalDecisionType.APPROVE:
            intervention.status = InterventionStatus.APPROVED.value
            intervention.selected_action = "approve"
            intervention.response_data = intervention.input_snapshot
        elif decision == ApprovalDecisionType.REJECT:
            intervention.status = InterventionStatus.REJECTED.value
            intervention.selected_action = "reject"
        elif decision == ApprovalDecisionType.CANCEL:
            intervention.status = InterventionStatus.CANCELLED.value
            intervention.selected_action = "cancel"

        intervention.resolved_at = now

        # 6. Record ApprovalDecision
        decision_record = ApprovalDecision(
            intervention_id=intervention.id,
            workspace_id=workspace_id,
            user_id=user.id,
            decision=decision.value,
            comment=comment,
            edited_data=clean_edited_data,
            created_at=now,
        )
        session.add(decision_record)

        # 7. Record HumanAction Audit Log
        audit = HumanAction(
            workspace_id=workspace_id,
            intervention_id=intervention.id,
            user_id=user.id,
            action_type=decision.value,
            target_type="intervention",
            target_id=str(intervention.id),
            metadata_json={
                "decision": decision.value,
                "comment": comment,
                "workflow_run_id": str(intervention.workflow_run_id) if intervention.workflow_run_id else None,
                "has_edited_data": bool(clean_edited_data),
            },
            created_at=now,
        )
        session.add(audit)

        # 8. Dispatch notification
        await NotificationService.notify_approval_resolved(
            session=session,
            intervention=intervention,
            decision=decision.value,
            resolved_by_user_id=user.id,
        )

        await session.commit()
        await session.refresh(intervention)

        logger.info(
            f"[ApprovalProcessor] Decision '{decision.value}' recorded for intervention '{intervention.id}' by user '{user.id}'"
        )
        return intervention

    @classmethod
    async def assign_request(
        cls,
        session: AsyncSession,
        intervention_id: UUID,
        workspace_id: UUID,
        user: User,
        assigned_to: UUID,
    ) -> HumanInterventionRequest:
        """
        Reassigns an intervention to a specific authorized user.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(HumanInterventionRequest)
            .where(
                and_(
                    HumanInterventionRequest.id == intervention_id,
                    HumanInterventionRequest.workspace_id == workspace_id,
                )
            )
            .with_for_update()
        )
        res = await session.execute(stmt)
        intervention = res.scalars().first()
        if not intervention:
            raise HITLNotFoundError(str(intervention_id))

        if intervention.status != InterventionStatus.PENDING.value:
            raise HITLStatusError(f"Cannot reassign request in '{intervention.status}' state.")

        old_assigned = intervention.assigned_to
        intervention.assigned_to = assigned_to

        audit = HumanAction(
            workspace_id=workspace_id,
            intervention_id=intervention.id,
            user_id=user.id,
            action_type="assigned",
            target_type="intervention",
            target_id=str(intervention.id),
            metadata_json={"previous_assigned_to": str(old_assigned), "new_assigned_to": str(assigned_to)},
            created_at=now,
        )
        session.add(audit)

        # Dispatch notification to newly assigned user
        await NotificationService.notify_approval_required(session, intervention)

        await session.commit()
        await session.refresh(intervention)
        return intervention
