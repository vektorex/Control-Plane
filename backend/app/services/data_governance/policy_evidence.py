"""
Policy Evidence Snapshot Engine for Step 33.
Captures and cryptographically records Step 32 Governance consequential decisions.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.data_governance.evidence import ComplianceEvidenceService
from backend.app.services.data_governance.models import ComplianceEvidence


class PolicyEvidenceRecorder:
    """
    Connects Step 32 Governance decision outputs into immutable Step 33 Compliance Evidence.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.evidence_service = ComplianceEvidenceService(session)

    async def record_governance_decision(
        self,
        organization_id: str,
        governance_decision_id: str,
        decision: str,
        reasons: List[str],
        matched_policies: List[str],
        enforcement_point: str,
        subject_type: str,
        subject_id: str,
        actor_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        policy_version_id: Optional[str] = None,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> ComplianceEvidence:
        """
        Records an immutable snapshot of an authoritative Step 32 Governance decision.
        """
        meta = {
            "enforcement_point": enforcement_point,
            "reasons": reasons,
            "matched_policies": matched_policies,
            "constraints": constraints or {},
        }

        return await self.evidence_service.record_evidence(
            organization_id=organization_id,
            evidence_type="governance_decision",
            subject_type=subject_type,
            subject_id=subject_id,
            action=f"governance_evaluate:{enforcement_point}",
            result=decision,
            actor_type="user" if actor_id else "system",
            actor_id=actor_id,
            workspace_id=workspace_id,
            policy_version_id=policy_version_id,
            governance_decision_id=governance_decision_id,
            metadata=meta,
        )
