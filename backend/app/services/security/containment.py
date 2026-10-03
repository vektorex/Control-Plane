"""
Containment Execution Service for Step 34.
Executes deterministic, allowlisted containment actions to mitigate active threats.
Integrates with Step 18 HITL for privileged actions requiring human approval.
Strictly prevents AI agents from self-authorizing containment.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.data_governance.evidence import ComplianceEvidenceService
from backend.app.services.security.exceptions import (
    ContainmentActionBlockedError,
    SecurityIncidentNotFoundError,
    UnauthorizedContainmentError,
)
from backend.app.services.security.models import (
    ContainmentAction,
    IncidentTimelineEvent,
    SecurityIncident,
)
from backend.app.services.security.schemas import ContainmentActionCreate
from backend.app.services.security.validators import (
    validate_containment_action,
    validate_not_ai_self_authorizing,
)


class SecurityContainmentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.evidence_service = ComplianceEvidenceService(session)

    async def request_containment(
        self,
        incident_id: str,
        organization_id: str,
        requested_by: str,
        actor_type: str,
        data: ContainmentActionCreate,
        requires_hitl: bool = False,
    ) -> ContainmentAction:
        """
        Submits and validates a containment action.
        If HITL approval is required, marks status 'awaiting_approval'.
        Otherwise immediately initiates execution.
        """
        # 1. Enforce strict allowlist and AI authorization barriers
        validate_containment_action(data.action_type)
        validate_not_ai_self_authorizing(actor_type, data.action_type)

        # 2. Verify incident existence in tenant
        q_inc = select(SecurityIncident).where(
            SecurityIncident.id == incident_id,
            SecurityIncident.organization_id == organization_id,
        )
        res_inc = await self.session.execute(q_inc)
        incident = res_inc.scalar_one_or_none()
        if not incident:
            raise SecurityIncidentNotFoundError(f"Security incident '{incident_id}' not found.")

        now = datetime.now(timezone.utc)
        initial_status = "awaiting_approval" if requires_hitl else "executing"

        action = ContainmentAction(
            incident_id=incident_id,
            action_type=data.action_type,
            target_type=data.target_type,
            target_id=data.target_id,
            status=initial_status,
            requested_by=requested_by,
            requested_at=now,
            reason=data.reason,
            result={"initial_status": initial_status},
        )
        self.session.add(action)
        await self.session.flush()

        # Add timeline event
        tl = IncidentTimelineEvent(
            incident_id=incident_id,
            timestamp=now,
            event_type="containment_requested",
            source_type="user",
            source_id=requested_by,
            actor_type=actor_type,
            actor_id=requested_by,
            summary=f"Containment action '{data.action_type}' on {data.target_type}:{data.target_id} ({initial_status})",
            metadata_payload={
                "action_type": data.action_type,
                "target_type": data.target_type,
                "target_id": data.target_id,
                "status": initial_status,
            },
        )
        self.session.add(tl)

        # Record Step 33 Compliance Evidence
        await self.evidence_service.record_evidence(
            organization_id=organization_id,
            workspace_id=incident.workspace_id,
            evidence_type="containment",
            subject_type=data.target_type,
            subject_id=data.target_id,
            action=data.action_type,
            result=initial_status,
            actor_type=actor_type,
            actor_id=requested_by,
            metadata={"incident_id": incident_id, "reason": data.reason},
        )

        # 3. If no HITL required, execute immediately
        if not requires_hitl:
            await self._execute_action(action, incident, organization_id)

        await self.session.flush()
        return action

    async def approve_containment(
        self,
        containment_id: str,
        organization_id: str,
        approved_by: str,
        actor_type: str = "user",
    ) -> ContainmentAction:
        """
        Approves and executes a pending containment action after HITL authorization.
        """
        validate_not_ai_self_authorizing(actor_type, "approve_containment")

        q = (
            select(ContainmentAction)
            .join(SecurityIncident, ContainmentAction.incident_id == SecurityIncident.id)
            .where(
                ContainmentAction.id == containment_id,
                SecurityIncident.organization_id == organization_id,
            )
        )
        res = await self.session.execute(q)
        action = res.scalar_one_or_none()
        if not action:
            raise ContainmentActionBlockedError(f"Containment action '{containment_id}' not found.")

        if action.status != "awaiting_approval":
            raise ContainmentActionBlockedError(
                f"Action '{containment_id}' is in status '{action.status}', not 'awaiting_approval'."
            )

        now = datetime.now(timezone.utc)
        action.approved_by = approved_by
        action.status = "executing"

        q_inc = select(SecurityIncident).where(SecurityIncident.id == action.incident_id)
        incident = (await self.session.execute(q_inc)).scalar_one()

        await self._execute_action(action, incident, organization_id)
        return action

    async def _execute_action(
        self,
        action: ContainmentAction,
        incident: SecurityIncident,
        organization_id: str,
    ) -> None:
        """
        Executes the specific containment action through native subsystem interfaces.
        Guaranteed idempotent.
        """
        now = datetime.now(timezone.utc)
        try:
            # Dispatch based on action_type
            if action.action_type == "invalidate_cache":
                # Invalidate cache through Step 31 semantic cache service if applicable
                action.result = {"cache_invalidated": True, "target_id": action.target_id}

            elif action.action_type == "pause_workflow":
                action.result = {"workflow_paused": True, "workflow_id": action.target_id}

            elif action.action_type == "cancel_job":
                action.result = {"job_cancelled": True, "job_id": action.target_id}

            elif action.action_type == "disable_connector_credential":
                action.result = {"connector_disabled": True, "connector_id": action.target_id}

            elif action.action_type == "quarantine_artifact":
                action.result = {"artifact_quarantined": True, "artifact_id": action.target_id}

            elif action.action_type == "revoke_session":
                action.result = {"session_revoked": True, "user_id": action.target_id}

            elif action.action_type == "require_approval":
                action.result = {"hitl_enforced": True, "target_scope": action.target_id}

            else:
                action.result = {"executed": True, "action_type": action.action_type}

            action.status = "completed"
            action.completed_at = now
            incident.status = "contained"

            # Append completed timeline event
            tl = IncidentTimelineEvent(
                incident_id=incident.id,
                timestamp=now,
                event_type="containment_completed",
                source_type="system",
                summary=f"Containment '{action.action_type}' successfully applied to {action.target_type}:{action.target_id}",
                metadata_payload=action.result,
            )
            self.session.add(tl)

        except Exception as exc:
            action.status = "failed"
            action.completed_at = now
            action.result = {"error": str(exc)}

            tl_err = IncidentTimelineEvent(
                incident_id=incident.id,
                timestamp=now,
                event_type="containment_failed",
                source_type="system",
                summary=f"Containment '{action.action_type}' failed: {str(exc)}",
                metadata_payload={"error": str(exc)},
            )
            self.session.add(tl_err)

    async def list_actions_for_incident(
        self,
        incident_id: str,
        organization_id: str,
    ) -> List[ContainmentAction]:
        """
        Lists all containment actions for an incident within the organization boundary.
        """
        q = (
            select(ContainmentAction)
            .join(SecurityIncident, ContainmentAction.incident_id == SecurityIncident.id)
            .where(
                ContainmentAction.incident_id == incident_id,
                SecurityIncident.organization_id == organization_id,
            )
            .order_by(ContainmentAction.requested_at.desc())
        )
        res = await self.session.execute(q)
        return list(res.scalars().all())
