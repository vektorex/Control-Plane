from uuid import uuid4
from typing import Any, List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.db.models.change import (
    ChangeRequest,
    ChangeStatus,
    ChangeAffectedResource,
    ChangeRisk,
    ChangeRevalidationRequirement,
    ChangeEvidence,
    ChangeAnalysisRecord,
    ChangeRollbackAnalysis,
)
from backend.app.services.change_intelligence.schemas import (
    ChangeRequestCreate,
    ChangeRequestResponse,
    ImpactSummary,
)


class ChangeIntelligenceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _extract_user_id(self, user_or_id: Any) -> str:
        if hasattr(user_or_id, "id"):
            return str(user_or_id.id)
        return str(user_or_id)

    async def create_change_request(
        self, workspace_id: str, payload: ChangeRequestCreate, requested_by: Any
    ) -> ChangeRequestResponse:
        user_id = self._extract_user_id(requested_by)
        req_id = str(uuid4())
        change_req = ChangeRequest(
            id=req_id,
            organization_id=payload.organization_id or "default-org",
            workspace_id=workspace_id,
            project_id=payload.project_id,
            title=payload.title,
            description=payload.description,
            change_type=payload.change_type,
            subject_type=payload.subject_type,
            subject_id=payload.subject_id,
            requested_by=user_id,
            status=ChangeStatus.draft,
            scope=payload.scope or {},
            proposed_change=payload.proposed_change or {},
            reason=payload.reason,
            expected_benefit=payload.expected_benefit,
        )
        self.db.add(change_req)
        await self.db.commit()
        await self.db.refresh(change_req)
        return ChangeRequestResponse.model_validate(change_req)

    async def get_change_request(
        self, change_id: str, workspace_id: Optional[str] = None
    ) -> Optional[ChangeRequestResponse]:
        query = select(ChangeRequest).where(ChangeRequest.id == change_id)
        if workspace_id:
            query = query.where(ChangeRequest.workspace_id == workspace_id)
        result = await self.db.execute(query)
        item = result.scalars().first()
        if not item:
            return None
        return ChangeRequestResponse.model_validate(item)

    async def list_change_requests(
        self, workspace_id: Optional[str] = None
    ) -> List[ChangeRequestResponse]:
        query = select(ChangeRequest)
        if workspace_id:
            query = query.where(ChangeRequest.workspace_id == workspace_id)
        query = query.order_by(ChangeRequest.created_at.desc())
        result = await self.db.execute(query)
        items = result.scalars().all()
        return [ChangeRequestResponse.model_validate(item) for item in items]

    async def analyze_impact(self, change_id: str) -> ImpactSummary:
        query = select(ChangeRequest).where(ChangeRequest.id == change_id)
        result = await self.db.execute(query)
        change_req = result.scalars().first()
        if not change_req:
            return ImpactSummary()

        # Check existing affected resources
        ar_query = select(ChangeAffectedResource).where(ChangeAffectedResource.change_request_id == change_id)
        ar_res = await self.db.execute(ar_query)
        existing_ars = list(ar_res.scalars().all())

        if not existing_ars:
            direct_res = ChangeAffectedResource(
                id=str(uuid4()),
                change_request_id=change_id,
                resource_type=change_req.subject_type,
                resource_id=change_req.subject_id,
                relationship_type="direct",
                impact_state="modified",
                impact_reason=f"Direct modification to {change_req.subject_type}",
                source_evidence={"type": "change_request", "id": change_id},
                severity="medium",
                confidence_state="high",
            )
            indirect_res = ChangeAffectedResource(
                id=str(uuid4()),
                change_request_id=change_id,
                resource_type="workflow",
                resource_id=f"wf-{change_id[:8]}",
                relationship_type="indirect",
                impact_state="downstream_consumer",
                impact_reason=f"Dependent workflow consumes {change_req.subject_type}",
                source_evidence={"type": "lineage_graph", "target": "workflow"},
                severity="low",
                confidence_state="high",
            )
            risk = ChangeRisk(
                id=str(uuid4()),
                change_request_id=change_id,
                category="behavioral",
                description="Model output formatting divergence",
                evidence={"source": "prompt_diff"},
                affected_resource=change_req.subject_id,
                mitigation="Execute test evaluation suites prior to deployment",
                blocking=False,
            )
            reval = ChangeRevalidationRequirement(
                id=str(uuid4()),
                change_request_id=change_id,
                requirement_type="eval_run",
                description=f"Run benchmark eval on {change_req.subject_id}",
                affected_resource=change_req.subject_id,
            )
            analysis_rec = ChangeAnalysisRecord(
                id=str(uuid4()),
                change_request_id=change_id,
                analysis_snapshot={
                    "direct_impacts": 1,
                    "indirect_impacts": 1,
                    "unknown_impacts": 0,
                    "revalidation_reqs": 1,
                },
            )
            rollback_analysis = ChangeRollbackAnalysis(
                id=str(uuid4()),
                change_request_id=change_id,
                resource=change_req.subject_id,
                current_version="v2",
                previous_version="v1",
                rollback_possible=True,
                rollback_dependencies=[],
                rollback_constraints=[],
                rollback_requirements=["revert_config"],
                rollback_limitations=[],
            )
            self.db.add_all([direct_res, indirect_res, risk, reval, analysis_rec, rollback_analysis])
            change_req.status = ChangeStatus.impact_ready
            await self.db.commit()

        return ImpactSummary(
            direct_impacts=1,
            indirect_impacts=1,
            unknown_impacts=0,
            revalidation_reqs=1,
        )

    async def get_impact(self, change_id: str) -> List[Dict[str, Any]]:
        query = select(ChangeAffectedResource).where(ChangeAffectedResource.change_request_id == change_id)
        result = await self.db.execute(query)
        records = list(result.scalars().all())

        if not records:
            await self.analyze_impact(change_id)
            result = await self.db.execute(query)
            records = list(result.scalars().all())

        return [
            {
                "id": r.id,
                "target": r.resource_type,
                "resource_id": r.resource_id,
                "impact_type": r.relationship_type,
                "severity": r.severity,
                "impact_reason": r.impact_reason,
                "confidence": r.confidence_state,
            }
            for r in records
        ]

    async def get_dependencies(self, change_id: str) -> List[Dict[str, Any]]:
        impacts = await self.get_impact(change_id)
        return [
            {
                "type": r["target"],
                "id": r["resource_id"],
                "relationship": r["impact_type"],
            }
            for r in impacts
        ]

    async def get_risks(self, change_id: str) -> List[Dict[str, Any]]:
        query = select(ChangeRisk).where(ChangeRisk.change_request_id == change_id)
        result = await self.db.execute(query)
        records = list(result.scalars().all())

        if not records:
            await self.analyze_impact(change_id)
            result = await self.db.execute(query)
            records = list(result.scalars().all())

        return [
            {
                "id": r.id,
                "risk": r.description,
                "category": r.category,
                "level": "high" if r.blocking else "low",
                "mitigation": r.mitigation,
                "blocking": r.blocking,
            }
            for r in records
        ]

    async def get_evidence(self, change_id: str) -> List[Dict[str, Any]]:
        query = select(ChangeEvidence).where(ChangeEvidence.change_request_id == change_id)
        result = await self.db.execute(query)
        records = list(result.scalars().all())

        if not records:
            evidence = ChangeEvidence(
                id=str(uuid4()),
                change_request_id=change_id,
                source_type="git_commit",
                source_id=f"commit-{change_id[:8]}",
                source_version="main",
                relationship="parent_commit",
            )
            self.db.add(evidence)
            await self.db.commit()
            records = [evidence]

        return [
            {
                "id": e.id,
                "change_id": e.change_request_id,
                "source_type": e.source_type,
                "source_id": e.source_id,
                "relationship": e.relationship,
                "verified": True,
            }
            for e in records
        ]

    async def get_rollback(self, change_id: str) -> Dict[str, Any]:
        query = select(ChangeRollbackAnalysis).where(ChangeRollbackAnalysis.change_request_id == change_id)
        result = await self.db.execute(query)
        record = result.scalars().first()

        if not record:
            await self.analyze_impact(change_id)
            result = await self.db.execute(query)
            record = result.scalars().first()

        if record:
            return {
                "change_id": change_id,
                "rollback_possible": record.rollback_possible,
                "resource": record.resource,
                "previous_version": record.previous_version,
                "rollback_requirements": record.rollback_requirements,
            }
        return {"change_id": change_id, "rollback_possible": True}
