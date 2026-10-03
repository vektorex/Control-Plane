"""
Unified Data Governance Service Facade for Step 33.
Single entry point coordinating data inventory, classification, lineage, retention,
deletion, export, privacy requests, legal holds, and immutable compliance evidence.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.data_governance.classification import DataClassificationService
from backend.app.services.data_governance.deletion import SafeDeletionEngine
from backend.app.services.data_governance.evidence import ComplianceEvidenceService
from backend.app.services.data_governance.export import DataExportEngine
from backend.app.services.data_governance.inventory import DataInventoryService
from backend.app.services.data_governance.legal_hold import LegalHoldService
from backend.app.services.data_governance.lineage import DataLineageService
from backend.app.services.data_governance.models import (
    ComplianceEvidence,
    DataAccessRecord,
    DataAsset,
    DeletionRequest,
    ExportRequest,
    LegalHold,
    PrivacyRequest,
    RetentionPolicy,
)
from backend.app.services.data_governance.policy_evidence import PolicyEvidenceRecorder
from backend.app.services.data_governance.privacy_requests import PrivacyRequestService
from backend.app.services.data_governance.repository import DataGovernanceRepository
from backend.app.services.data_governance.retention import RetentionPolicyEngine
from backend.app.services.data_governance.schemas import (
    AccessReportResponse,
    ClassificationReportResponse,
    DataAssetCreate,
    DataAssetUpdate,
    DataGovernanceOverviewResponse,
    DeletionReportResponse,
    DeletionRequestCreate,
    EvidenceReportResponse,
    EvidenceVerificationResult,
    ExportRequestCreate,
    LegalHoldCreate,
    LineageEdgeCreate,
    PrivacyRequestCreate,
    RetentionPolicyCreate,
    RetentionPolicyUpdate,
    RetentionReportResponse,
)


class DataGovernanceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.inventory = DataInventoryService(session)
        self.classification = DataClassificationService(session)
        self.lineage = DataLineageService(session)
        self.retention = RetentionPolicyEngine(session)
        self.legal_hold = LegalHoldService(session)
        self.deletion = SafeDeletionEngine(session)
        self.export = DataExportEngine(session)
        self.privacy = PrivacyRequestService(session)
        self.evidence = ComplianceEvidenceService(session)
        self.policy_evidence = PolicyEvidenceRecorder(session)
        self.repo = DataGovernanceRepository(session)

    # -----------------------------------------------------------------------
    # Overview & Reports
    # -----------------------------------------------------------------------

    async def get_overview(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
    ) -> DataGovernanceOverviewResponse:
        stats = await self.repo.get_overview_stats(organization_id, workspace_id)
        is_valid, _, _ = await self.evidence.verify_chain(organization_id, workspace_id)
        return DataGovernanceOverviewResponse(
            total_assets=stats["total_assets"],
            classification_counts=stats["classification_counts"],
            active_legal_holds=stats["active_legal_holds"],
            pending_deletions=stats["pending_deletions"],
            pending_privacy_requests=stats["pending_privacy_requests"],
            recent_evidence_count=stats["recent_evidence_count"],
            assets_with_findings=stats["assets_with_findings"],
            evidence_chain_valid=is_valid,
        )

    async def get_retention_report(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
    ) -> RetentionReportResponse:
        policies = await self.retention.list_policies(organization_id, workspace_id)
        actions: Dict[str, int] = {}
        for p in policies:
            actions[p.action] = actions.get(p.action, 0) + 1

        expired_items = await self.retention.find_expired_assets(organization_id, workspace_id, limit=200)

        return RetentionReportResponse(
            total_policies=len(policies),
            policies_by_action=actions,
            assets_expiring_soon=len(expired_items),
            assets_expired=len(expired_items),
        )

    async def get_classification_report(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
    ) -> ClassificationReportResponse:
        stats = await self.repo.get_overview_stats(organization_id, workspace_id)
        return ClassificationReportResponse(
            total_classified=stats["total_assets"],
            distribution=stats["classification_counts"],
            recent_reviews=0,
            unreviewed_sensitive_assets=stats["assets_with_findings"],
        )

    async def get_access_report(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
    ) -> AccessReportResponse:
        q = select(DataAccessRecord.action, func.count(DataAccessRecord.id)).where(
            DataAccessRecord.organization_id == organization_id
        )
        if workspace_id:
            q = q.where(DataAccessRecord.workspace_id == workspace_id)
        q = q.group_by(DataAccessRecord.action)
        res = await self.session.execute(q)
        actions = {r[0]: r[1] for r in res.fetchall()}

        q_denied = select(func.count(DataAccessRecord.id)).where(
            DataAccessRecord.organization_id == organization_id,
            DataAccessRecord.result == "denied",
        )
        if workspace_id:
            q_denied = q_denied.where(DataAccessRecord.workspace_id == workspace_id)
        res_denied = await self.session.execute(q_denied)
        denied_count = res_denied.scalar() or 0

        return AccessReportResponse(
            total_access_events=sum(actions.values()),
            actions_distribution=actions,
            denied_access_count=denied_count,
        )

    async def get_deletion_report(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
    ) -> DeletionReportResponse:
        requests = await self.deletion.list_requests(organization_id, workspace_id)
        completed = sum(1 for r in requests if r.status == "completed")
        blocked = sum(1 for r in requests if r.status == "blocked")
        failed = sum(1 for r in requests if r.status == "failed")

        return DeletionReportResponse(
            total_requests=len(requests),
            completed=completed,
            blocked=blocked,
            failed=failed,
        )

    async def get_evidence_report(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
    ) -> EvidenceReportResponse:
        is_valid, count, broken = await self.evidence.verify_chain(organization_id, workspace_id)
        q = select(ComplianceEvidence.evidence_type, func.count(ComplianceEvidence.id)).where(
            ComplianceEvidence.organization_id == organization_id
        )
        if workspace_id:
            q = q.where(ComplianceEvidence.workspace_id == workspace_id)
        q = q.group_by(ComplianceEvidence.evidence_type)
        res = await self.session.execute(q)
        types_dist = {r[0]: r[1] for r in res.fetchall()}

        return EvidenceReportResponse(
            total_records=count,
            chain_valid=is_valid,
            evidence_types_distribution=types_dist,
        )
