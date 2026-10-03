"""
Data Governance Repository for Step 33.
Database query operations, tenant filtering, and aggregate reporting statistics.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.data_governance.models import (
    ClassificationRecord,
    ComplianceEvidence,
    DataAccessRecord,
    DataAsset,
    DataFinding,
    DeletionRequest,
    ExportRequest,
    LegalHold,
    PrivacyRequest,
    RetentionPolicy,
)


class DataGovernanceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_overview_stats(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Computes aggregate dashboard metrics for data governance.
        """
        # Asset counts by classification
        q_class = (
            select(DataAsset.data_classification, func.count(DataAsset.id))
            .where(
                DataAsset.organization_id == organization_id,
                DataAsset.status != "deleted",
            )
        )
        if workspace_id:
            q_class = q_class.where(DataAsset.workspace_id == workspace_id)
        q_class = q_class.group_by(DataAsset.data_classification)
        res_class = await self.session.execute(q_class)
        classification_counts = {row[0]: row[1] for row in res_class.fetchall()}
        total_assets = sum(classification_counts.values())

        # Active legal holds
        q_holds = select(func.count(LegalHold.id)).where(
            LegalHold.organization_id == organization_id,
            LegalHold.status == "active",
        )
        if workspace_id:
            q_holds = q_holds.where(LegalHold.workspace_id == workspace_id)
        res_holds = await self.session.execute(q_holds)
        active_legal_holds = res_holds.scalar() or 0

        # Pending deletions
        q_del = select(func.count(DeletionRequest.id)).where(
            DeletionRequest.organization_id == organization_id,
            DeletionRequest.status.in_(["requested", "awaiting_approval", "processing"]),
        )
        if workspace_id:
            q_del = q_del.where(DeletionRequest.workspace_id == workspace_id)
        res_del = await self.session.execute(q_del)
        pending_deletions = res_del.scalar() or 0

        # Pending privacy requests
        q_priv = select(func.count(PrivacyRequest.id)).where(
            PrivacyRequest.organization_id == organization_id,
            PrivacyRequest.status.in_(["pending", "in_review", "processing"]),
        )
        if workspace_id:
            q_priv = q_priv.where(PrivacyRequest.workspace_id == workspace_id)
        res_priv = await self.session.execute(q_priv)
        pending_privacy_requests = res_priv.scalar() or 0

        # Recent evidence count
        q_ev = select(func.count(ComplianceEvidence.id)).where(
            ComplianceEvidence.organization_id == organization_id,
        )
        if workspace_id:
            q_ev = q_ev.where(ComplianceEvidence.workspace_id == workspace_id)
        res_ev = await self.session.execute(q_ev)
        recent_evidence_count = res_ev.scalar() or 0

        # Assets with findings
        q_find = select(func.count(func.distinct(DataFinding.asset_id))).join(
            DataAsset, DataFinding.asset_id == DataAsset.id
        ).where(
            DataAsset.organization_id == organization_id,
            DataAsset.status != "deleted",
        )
        if workspace_id:
            q_find = q_find.where(DataAsset.workspace_id == workspace_id)
        res_find = await self.session.execute(q_find)
        assets_with_findings = res_find.scalar() or 0

        return {
            "total_assets": total_assets,
            "classification_counts": classification_counts,
            "active_legal_holds": active_legal_holds,
            "pending_deletions": pending_deletions,
            "pending_privacy_requests": pending_privacy_requests,
            "recent_evidence_count": recent_evidence_count,
            "assets_with_findings": assets_with_findings,
        }

    async def list_evidence(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
        evidence_type: Optional[str] = None,
        subject_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ComplianceEvidence]:
        q = select(ComplianceEvidence).where(ComplianceEvidence.organization_id == organization_id)
        if workspace_id:
            q = q.where(ComplianceEvidence.workspace_id == workspace_id)
        if evidence_type:
            q = q.where(ComplianceEvidence.evidence_type == evidence_type)
        if subject_id:
            q = q.where(ComplianceEvidence.subject_id == subject_id)
        q = q.order_by(desc(ComplianceEvidence.timestamp)).limit(limit).offset(offset)
        res = await self.session.execute(q)
        return list(res.scalars().all())

    async def get_evidence_by_id(
        self,
        evidence_id: str,
        organization_id: str,
    ) -> Optional[ComplianceEvidence]:
        q = select(ComplianceEvidence).where(
            ComplianceEvidence.id == evidence_id,
            ComplianceEvidence.organization_id == organization_id,
        )
        res = await self.session.execute(q)
        return res.scalar_one_or_none()
