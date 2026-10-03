"""
Legal Hold Service for Step 33.
Maintains protective holds that strictly prevent deletion or destructive operations.
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.services.data_governance.evidence import ComplianceEvidenceService
from backend.app.services.data_governance.exceptions import DataGovernanceError
from backend.app.services.data_governance.models import DataAsset, LegalHold, LegalHoldAsset
from backend.app.services.data_governance.schemas import LegalHoldCreate


class LegalHoldService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.evidence_service = ComplianceEvidenceService(session)

    async def create_hold(
        self,
        organization_id: str,
        created_by: str,
        data: LegalHoldCreate,
    ) -> LegalHold:
        """
        Creates a new legal hold and associates specified assets.
        """
        now = datetime.now(timezone.utc)
        hold = LegalHold(
            organization_id=organization_id,
            workspace_id=data.workspace_id,
            name=data.name,
            reason=data.reason,
            status="active",
            created_by=created_by,
            created_at=now,
        )
        self.session.add(hold)
        await self.session.flush()

        # Attach assets
        if data.asset_ids:
            for aid in set(data.asset_ids):
                # Verify asset belongs to organization
                q_ast = select(DataAsset.id).where(
                    DataAsset.id == aid,
                    DataAsset.organization_id == organization_id,
                )
                res_ast = await self.session.execute(q_ast)
                if res_ast.scalar_one_or_none():
                    lha = LegalHoldAsset(legal_hold_id=hold.id, asset_id=aid, created_at=now)
                    self.session.add(lha)

        await self.session.flush()
        await self.session.refresh(hold)

        # Record compliance evidence
        await self.evidence_service.record_evidence(
            organization_id=organization_id,
            workspace_id=data.workspace_id,
            evidence_type="legal_hold",
            subject_type="legal_hold",
            subject_id=hold.id,
            action="create_legal_hold",
            result="active",
            actor_type="user",
            actor_id=created_by,
            metadata={
                "name": hold.name,
                "reason": hold.reason,
                "asset_count": len(data.asset_ids or []),
            },
        )

        return hold

    async def get_active_holds_for_asset(self, asset_id: str) -> List[str]:
        """
        Returns list of active legal hold names covering this asset.
        """
        q = (
            select(LegalHold.name)
            .join(LegalHoldAsset, LegalHold.id == LegalHoldAsset.legal_hold_id)
            .where(
                LegalHoldAsset.asset_id == asset_id,
                LegalHold.status == "active",
            )
        )
        res = await self.session.execute(q)
        return list(res.scalars().all())

    async def is_asset_under_hold(self, asset_id: str) -> bool:
        holds = await self.get_active_holds_for_asset(asset_id)
        return len(holds) > 0

    async def release_hold(
        self,
        hold_id: str,
        organization_id: str,
        actor_id: str,
        reason: Optional[str] = None,
    ) -> LegalHold:
        """
        Releases an active legal hold.
        """
        q = select(LegalHold).where(
            LegalHold.id == hold_id,
            LegalHold.organization_id == organization_id,
        )
        res = await self.session.execute(q)
        hold = res.scalar_one_or_none()
        if not hold:
            raise DataGovernanceError(f"Legal hold '{hold_id}' not found.")

        now = datetime.now(timezone.utc)
        hold.status = "released"
        hold.released_at = now
        await self.session.flush()
        await self.session.refresh(hold)

        # Record compliance evidence
        await self.evidence_service.record_evidence(
            organization_id=organization_id,
            workspace_id=hold.workspace_id,
            evidence_type="legal_hold",
            subject_type="legal_hold",
            subject_id=hold.id,
            action="release_legal_hold",
            result="released",
            actor_type="user",
            actor_id=actor_id,
            metadata={"release_reason": reason or "Released by authorized administrator"},
        )

        return hold

    async def list_holds(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[LegalHold]:
        q = (
            select(LegalHold)
            .where(LegalHold.organization_id == organization_id)
            .options(selectinload(LegalHold.assets))
        )
        if workspace_id:
            q = q.where(LegalHold.workspace_id == workspace_id)
        if status:
            q = q.where(LegalHold.status == status)
        q = q.order_by(desc(LegalHold.created_at))
        res = await self.session.execute(q)
        return list(res.scalars().all())
