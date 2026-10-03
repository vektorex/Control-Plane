"""
Privacy Request Workflow Service for Step 33.
Manages user/tenant data rights workflows (access, export, deletion, correction, restriction).
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.data_governance.evidence import ComplianceEvidenceService
from backend.app.services.data_governance.exceptions import PrivacyRequestError
from backend.app.services.data_governance.models import PrivacyRequest
from backend.app.services.data_governance.schemas import PrivacyRequestCreate


class PrivacyRequestService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.evidence_service = ComplianceEvidenceService(session)

    async def create_request(
        self,
        organization_id: str,
        user_id: str,
        data: PrivacyRequestCreate,
    ) -> PrivacyRequest:
        """
        Submits a new privacy workflow request.
        """
        now = datetime.now(timezone.utc)
        req = PrivacyRequest(
            organization_id=organization_id,
            workspace_id=data.workspace_id,
            requester_user_id=user_id,
            request_type=data.request_type.lower(),
            scope=data.scope,
            status="pending",
            verification_status="unverified",
            created_at=now,
            updated_at=now,
        )
        self.session.add(req)
        await self.session.flush()
        await self.session.refresh(req)

        # Record compliance evidence
        await self.evidence_service.record_evidence(
            organization_id=organization_id,
            workspace_id=data.workspace_id,
            evidence_type="privacy_request",
            subject_type="privacy_request",
            subject_id=req.id,
            action="submit_privacy_request",
            result="pending",
            actor_type="user",
            actor_id=user_id,
            metadata={
                "request_type": req.request_type,
                "scope": req.scope,
            },
        )

        return req

    async def verify_request(
        self,
        request_id: str,
        organization_id: str,
        reviewer_id: str,
        verification_status: str,  # verified, rejected
    ) -> PrivacyRequest:
        """
        Verifies identity/authorization for a privacy request.
        """
        q = select(PrivacyRequest).where(
            PrivacyRequest.id == request_id,
            PrivacyRequest.organization_id == organization_id,
        )
        res = await self.session.execute(q)
        req = res.scalar_one_or_none()
        if not req:
            raise PrivacyRequestError(f"Privacy request '{request_id}' not found.")

        now = datetime.now(timezone.utc)
        req.verification_status = verification_status
        req.status = "in_review" if verification_status == "verified" else "rejected"
        req.updated_at = now
        await self.session.flush()
        await self.session.refresh(req)

        await self.evidence_service.record_evidence(
            organization_id=organization_id,
            workspace_id=req.workspace_id,
            evidence_type="privacy_request",
            subject_type="privacy_request",
            subject_id=req.id,
            action="verify_privacy_request",
            result=verification_status,
            actor_type="user",
            actor_id=reviewer_id,
            metadata={"status": req.status},
        )

        return req

    async def complete_request(
        self,
        request_id: str,
        organization_id: str,
        actor_id: str,
    ) -> PrivacyRequest:
        q = select(PrivacyRequest).where(
            PrivacyRequest.id == request_id,
            PrivacyRequest.organization_id == organization_id,
        )
        res = await self.session.execute(q)
        req = res.scalar_one_or_none()
        if not req:
            raise PrivacyRequestError(f"Privacy request '{request_id}' not found.")

        now = datetime.now(timezone.utc)
        req.status = "completed"
        req.completed_at = now
        req.updated_at = now
        await self.session.flush()
        await self.session.refresh(req)

        await self.evidence_service.record_evidence(
            organization_id=organization_id,
            workspace_id=req.workspace_id,
            evidence_type="privacy_request",
            subject_type="privacy_request",
            subject_id=req.id,
            action="complete_privacy_request",
            result="completed",
            actor_type="user",
            actor_id=actor_id,
        )

        return req

    async def list_requests(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[PrivacyRequest]:
        q = select(PrivacyRequest).where(PrivacyRequest.organization_id == organization_id)
        if workspace_id:
            q = q.where(PrivacyRequest.workspace_id == workspace_id)
        if status:
            q = q.where(PrivacyRequest.status == status)
        q = q.order_by(desc(PrivacyRequest.created_at))
        res = await self.session.execute(q)
        return list(res.scalars().all())
