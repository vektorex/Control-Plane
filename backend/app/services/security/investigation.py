"""
Incident Investigation Service for Step 34.
Assembles a bounded, tenant-isolated investigation context aggregating related
signals, assets, governance decisions, compliance evidence, jobs, and containment actions.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.services.data_governance.models import (
    ComplianceEvidence,
    DataAccessRecord,
    DataAsset,
)
from backend.app.services.security.exceptions import SecurityIncidentNotFoundError
from backend.app.services.security.models import (
    ContainmentAction,
    IncidentSignal,
    IncidentTimelineEvent,
    SecurityIncident,
    SecuritySignal,
)
from backend.app.services.security.schemas import (
    IncidentInvestigationResponse,
    IncidentTimelineEventResponse,
    SecurityIncidentResponse,
    SecuritySignalResponse,
)


class IncidentInvestigationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_investigation_context(
        self,
        incident_id: str,
        organization_id: str,
    ) -> IncidentInvestigationResponse:
        """
        Builds a comprehensive, bounded investigation graph for a security incident.
        Strictly tenant-isolated.
        """
        # 1. Fetch incident with eager-loaded signals and timeline
        q_inc = (
            select(SecurityIncident)
            .where(
                SecurityIncident.id == incident_id,
                SecurityIncident.organization_id == organization_id,
            )
            .options(
                selectinload(SecurityIncident.signals).selectinload(IncidentSignal.signal),
                selectinload(SecurityIncident.timeline_events),
                selectinload(SecurityIncident.containment_actions),
            )
        )
        res_inc = await self.session.execute(q_inc)
        inc = res_inc.scalar_one_or_none()
        if not inc:
            raise SecurityIncidentNotFoundError(f"Incident '{incident_id}' not found.")

        # 2. Extract signals and associated actors / resources
        signals_list = [assoc.signal for assoc in inc.signals if assoc.signal is not None]
        affected_actors = set()
        affected_resource_ids = set()

        for s in signals_list:
            if s.actor_id:
                affected_actors.add(s.actor_id)
            if s.resource_id:
                affected_resource_ids.add(s.resource_id)

        meta = inc.metadata_payload or {}
        if meta.get("primary_actor_id"):
            affected_actors.add(meta["primary_actor_id"])
        if meta.get("primary_resource_id"):
            affected_resource_ids.add(meta["primary_resource_id"])

        # 3. Retrieve related Step 33 Data Assets
        related_assets = []
        affected_classifications = set()
        if affected_resource_ids:
            q_assets = select(DataAsset).where(
                DataAsset.organization_id == organization_id,
                DataAsset.resource_id.in_(list(affected_resource_ids)[:20]),
            )
            res_assets = await self.session.execute(q_assets)
            for a in res_assets.scalars().all():
                related_assets.append({
                    "id": a.id,
                    "name": a.name,
                    "resource_type": a.resource_type,
                    "resource_id": a.resource_id,
                    "classification": a.data_classification,
                    "contains_secrets": a.contains_secrets,
                    "contains_personal_data": a.contains_personal_data,
                    "status": a.status,
                })
                affected_classifications.add(a.data_classification)

        # 4. Retrieve related Step 33 Compliance Evidence
        q_evidence = (
            select(ComplianceEvidence)
            .where(ComplianceEvidence.organization_id == organization_id)
            .order_by(desc(ComplianceEvidence.timestamp))
            .limit(20)
        )
        res_evidence = await self.session.execute(q_evidence)
        compliance_evidence_items = []
        for ev in res_evidence.scalars().all():
            compliance_evidence_items.append({
                "id": ev.id,
                "evidence_type": ev.evidence_type,
                "action": ev.action,
                "result": ev.result,
                "subject_type": ev.subject_type,
                "subject_id": ev.subject_id,
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                "evidence_hash": ev.evidence_hash,
            })

        # 5. Build containment actions summary
        containment_items = []
        for c in inc.containment_actions or []:
            containment_items.append({
                "id": c.id,
                "action_type": c.action_type,
                "target_type": c.target_type,
                "target_id": c.target_id,
                "status": c.status,
                "requested_by": c.requested_by,
                "approved_by": c.approved_by,
                "requested_at": c.requested_at.isoformat() if c.requested_at else None,
                "completed_at": c.completed_at.isoformat() if c.completed_at else None,
                "reason": c.reason,
            })

        # Assemble Investigation Response
        inc_resp = SecurityIncidentResponse.model_validate(inc)
        inc_resp.signal_count = len(signals_list)

        signals_resp = [SecuritySignalResponse.model_validate(s) for s in signals_list]
        timeline_resp = [IncidentTimelineEventResponse.model_validate(t) for t in inc.timeline_events]

        return IncidentInvestigationResponse(
            incident=inc_resp,
            signals=signals_resp,
            timeline=timeline_resp,
            related_assets=related_assets,
            governance_decisions=[],
            compliance_evidence=compliance_evidence_items,
            containment_actions=containment_items,
            affected_actors=sorted(list(affected_actors)),
            affected_classifications=sorted(list(affected_classifications)),
        )
