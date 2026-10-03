"""
Security Evidence Integration Service for Step 34.
Records tamper-evident security audit snapshots into Step 33 ComplianceEvidence hash chain.
Never duplicates the evidence store.
"""
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.data_governance.evidence import ComplianceEvidenceService
from backend.app.services.security.models import ContainmentAction, SecurityIncident, SecuritySignal


class SecurityEvidenceRecorder:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.evidence_service = ComplianceEvidenceService(session)

    async def record_incident_evidence(
        self,
        incident: SecurityIncident,
        action: str,
        actor_id: Optional[str] = None,
        actor_type: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Appends an incident lifecycle event (opened, escalated, contained, resolved) to the evidence chain.
        """
        meta = dict(metadata or {})
        meta["severity"] = incident.severity
        meta["category"] = incident.category
        meta["title"] = incident.title

        return await self.evidence_service.record_evidence(
            organization_id=incident.organization_id,
            workspace_id=incident.workspace_id,
            evidence_type="security_event",
            subject_type="security_incident",
            subject_id=incident.id,
            action=action,
            result=incident.status,
            actor_type=actor_type,
            actor_id=actor_id,
            metadata=meta,
        )

    async def record_containment_evidence(
        self,
        action: ContainmentAction,
        organization_id: str,
        workspace_id: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> Any:
        """
        Appends containment action execution to the evidence chain.
        """
        return await self.evidence_service.record_evidence(
            organization_id=organization_id,
            workspace_id=workspace_id,
            evidence_type="containment",
            subject_type=action.target_type,
            subject_id=action.target_id,
            action=action.action_type,
            result=action.status,
            actor_type="user" if actor_id else "system",
            actor_id=actor_id,
            metadata={
                "incident_id": action.incident_id,
                "containment_id": action.id,
                "reason": action.reason,
            },
        )
