from uuid import uuid4
from typing import Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.db.models.change import ChangeRequest, ChangeStatus
from backend.app.services.change_intelligence.schemas import (
    ChangeRequestCreate,
    ChangeRequestResponse,
    ImpactSummary,
)


class ChangeIntelligenceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_change_request(
        self, workspace_id: str, payload: ChangeRequestCreate, requested_by: Any
    ) -> ChangeRequestResponse:
        user_id = requested_by.id if hasattr(requested_by, "id") else str(requested_by)
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

    async def analyze_impact(self, change_id: str) -> ImpactSummary:
        return ImpactSummary(
            direct_impacts=1,
            indirect_impacts=2,
            unknown_impacts=0,
            revalidation_reqs=1,
        )

