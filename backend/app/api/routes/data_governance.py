"""
FastAPI routes for Step 33: Data Governance, Privacy & Compliance Evidence Layer.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.data_governance.exceptions import (
    DataAssetNotFoundError,
    DataGovernanceError,
    DeletionBlockedError,
    ExportSanitizationError,
    LegalHoldActiveError,
    PrivacyRequestError,
    UnauthorizedClassificationDowngradeError,
)
from backend.app.services.data_governance.schemas import (
    AccessReportResponse,
    ClassificationRecordResponse,
    ClassificationReportResponse,
    ClassificationReviewRequest,
    ComplianceEvidenceResponse,
    DataAccessRecordResponse,
    DataAssetCreate,
    DataAssetResponse,
    DataAssetUpdate,
    DataGovernanceOverviewResponse,
    DeletionReportResponse,
    DeletionRequestCreate,
    DeletionRequestResponse,
    EvidenceReportResponse,
    ExportRequestCreate,
    ExportRequestResponse,
    LegalHoldCreate,
    LegalHoldReleaseRequest,
    LegalHoldResponse,
    LineageEdgeCreate,
    LineageEdgeResponse,
    LineageGraphResponse,
    PrivacyRequestCreate,
    PrivacyRequestResponse,
    PrivacyRequestUpdate,
    RetentionPolicyCreate,
    RetentionPolicyResponse,
    RetentionPolicyUpdate,
    RetentionReportResponse,
)
from backend.app.services.data_governance.service import DataGovernanceService

router = APIRouter(prefix="/data-governance", tags=["data-governance"])


def _get_service(db: AsyncSession = Depends(get_db)) -> DataGovernanceService:
    return DataGovernanceService(db)


# ---------------------------------------------------------------------------
# Overview & Reports
# ---------------------------------------------------------------------------

@router.get("/overview", response_model=DataGovernanceOverviewResponse)
async def get_overview(
    workspace_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    """Data governance operational overview, asset counts, holds, and chain status."""
    return await service.get_overview(
        organization_id=str(current_user.organization_id),
        workspace_id=workspace_id,
    )


@router.get("/reports/retention", response_model=RetentionReportResponse)
async def get_retention_report(
    workspace_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    return await service.get_retention_report(
        organization_id=str(current_user.organization_id),
        workspace_id=workspace_id,
    )


@router.get("/reports/classification", response_model=ClassificationReportResponse)
async def get_classification_report(
    workspace_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    return await service.get_classification_report(
        organization_id=str(current_user.organization_id),
        workspace_id=workspace_id,
    )


@router.get("/reports/access", response_model=AccessReportResponse)
async def get_access_report(
    workspace_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    return await service.get_access_report(
        organization_id=str(current_user.organization_id),
        workspace_id=workspace_id,
    )


@router.get("/reports/deletion", response_model=DeletionReportResponse)
async def get_deletion_report(
    workspace_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    return await service.get_deletion_report(
        organization_id=str(current_user.organization_id),
        workspace_id=workspace_id,
    )


@router.get("/reports/evidence", response_model=EvidenceReportResponse)
async def get_evidence_report(
    workspace_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    return await service.get_evidence_report(
        organization_id=str(current_user.organization_id),
        workspace_id=workspace_id,
    )


# ---------------------------------------------------------------------------
# Data Assets
# ---------------------------------------------------------------------------

@router.get("/assets", response_model=List[DataAssetResponse])
async def list_assets(
    workspace_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    asset_type: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    classification: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    contains_secrets: Optional[bool] = Query(None),
    contains_personal_data: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    assets = await service.inventory.list_assets(
        organization_id=str(current_user.organization_id),
        workspace_id=workspace_id,
        project_id=project_id,
        asset_type=asset_type,
        resource_type=resource_type,
        classification=classification,
        status=status,
        contains_secrets=contains_secrets,
        contains_personal_data=contains_personal_data,
        limit=limit,
        offset=offset,
    )
    return [DataAssetResponse.model_validate(a) for a in assets]


@router.post("/assets", response_model=DataAssetResponse, status_code=status.HTTP_201_CREATED)
async def register_asset(
    data: DataAssetCreate,
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    asset = await service.inventory.register_asset(
        organization_id=str(current_user.organization_id),
        data=data,
        detected_by="manual",
    )
    return DataAssetResponse.model_validate(asset)


@router.get("/assets/{asset_id}", response_model=DataAssetResponse)
async def get_asset(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    try:
        asset = await service.inventory.get_asset(
            asset_id=asset_id,
            organization_id=str(current_user.organization_id),
        )
        return DataAssetResponse.model_validate(asset)
    except DataAssetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/assets/{asset_id}/lineage", response_model=LineageGraphResponse)
async def get_asset_lineage(
    asset_id: str,
    max_depth: int = Query(5, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    try:
        return await service.lineage.get_lineage_graph(
            root_asset_id=asset_id,
            organization_id=str(current_user.organization_id),
            max_depth=max_depth,
        )
    except DataAssetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/assets/{asset_id}/access-history", response_model=List[DataAccessRecordResponse])
async def get_asset_access_history(
    asset_id: str,
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    records = await service.inventory.list_access_history(
        asset_id=asset_id,
        organization_id=str(current_user.organization_id),
        limit=limit,
    )
    return [DataAccessRecordResponse.model_validate(r) for r in records]


# ---------------------------------------------------------------------------
# Classifications
# ---------------------------------------------------------------------------

@router.get("/classifications", response_model=List[ClassificationRecordResponse])
async def list_classifications(
    asset_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    records = await service.classification.list_classifications(
        asset_id=asset_id,
        organization_id=str(current_user.organization_id),
    )
    return [ClassificationRecordResponse.model_validate(r) for r in records]


@router.post("/classifications/review", response_model=ClassificationRecordResponse)
async def review_classification(
    data: ClassificationReviewRequest,
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    try:
        is_admin = getattr(current_user, "is_admin", False) or getattr(current_user, "role", "") in ("admin", "owner")
        record = await service.classification.update_classification(
            asset_id=data.asset_id,
            organization_id=str(current_user.organization_id),
            target_classification=data.target_classification,
            reason=data.reason,
            detected_by="user_confirmed",
            actor_id=str(current_user.id),
            is_admin=is_admin,
        )
        return ClassificationRecordResponse.model_validate(record)
    except UnauthorizedClassificationDowngradeError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except DataAssetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ---------------------------------------------------------------------------
# Retention Policies
# ---------------------------------------------------------------------------

@router.get("/retention-policies", response_model=List[RetentionPolicyResponse])
async def list_retention_policies(
    workspace_id: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    policies = await service.retention.list_policies(
        organization_id=str(current_user.organization_id),
        workspace_id=workspace_id,
        resource_type=resource_type,
    )
    return [RetentionPolicyResponse.model_validate(p) for p in policies]


@router.post("/retention-policies", response_model=RetentionPolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_retention_policy(
    data: RetentionPolicyCreate,
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    policy = await service.retention.create_policy(
        organization_id=str(current_user.organization_id),
        created_by=str(current_user.id),
        data=data,
    )
    return RetentionPolicyResponse.model_validate(policy)


@router.patch("/retention-policies/{policy_id}", response_model=RetentionPolicyResponse)
async def update_retention_policy(
    policy_id: str,
    data: RetentionPolicyUpdate,
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    try:
        policy = await service.retention.update_policy(
            policy_id=policy_id,
            organization_id=str(current_user.organization_id),
            data=data,
        )
        return RetentionPolicyResponse.model_validate(policy)
    except DataGovernanceError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/retention-policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_retention_policy(
    policy_id: str,
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    success = await service.retention.delete_policy(
        policy_id=policy_id,
        organization_id=str(current_user.organization_id),
    )
    if not success:
        raise HTTPException(status_code=404, detail="Retention policy not found.")


# ---------------------------------------------------------------------------
# Privacy Requests
# ---------------------------------------------------------------------------

@router.post("/privacy-requests", response_model=PrivacyRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_privacy_request(
    data: PrivacyRequestCreate,
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    req = await service.privacy.create_request(
        organization_id=str(current_user.organization_id),
        user_id=str(current_user.id),
        data=data,
    )
    return PrivacyRequestResponse.model_validate(req)


@router.get("/privacy-requests", response_model=List[PrivacyRequestResponse])
async def list_privacy_requests(
    workspace_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    requests = await service.privacy.list_requests(
        organization_id=str(current_user.organization_id),
        workspace_id=workspace_id,
        status=status,
    )
    return [PrivacyRequestResponse.model_validate(r) for r in requests]


@router.get("/privacy-requests/{request_id}", response_model=PrivacyRequestResponse)
async def get_privacy_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    requests = await service.privacy.list_requests(
        organization_id=str(current_user.organization_id),
    )
    for r in requests:
        if r.id == request_id:
            return PrivacyRequestResponse.model_validate(r)
    raise HTTPException(status_code=404, detail="Privacy request not found.")


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

@router.post("/exports", response_model=ExportRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_export(
    data: ExportRequestCreate,
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    try:
        req = await service.export.create_export_request(
            organization_id=str(current_user.organization_id),
            requested_by=str(current_user.id),
            data=data,
        )
        # Execute synchronously for small scope or queue
        req, _ = await service.export.execute_export(
            request_id=req.id,
            organization_id=str(current_user.organization_id),
        )
        return ExportRequestResponse.model_validate(req)
    except ExportSanitizationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/exports", response_model=List[ExportRequestResponse])
async def list_exports(
    workspace_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    exports = await service.export.list_exports(
        organization_id=str(current_user.organization_id),
        workspace_id=workspace_id,
    )
    return [ExportRequestResponse.model_validate(e) for e in exports]


@router.get("/exports/{export_id}", response_model=ExportRequestResponse)
async def get_export(
    export_id: str,
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    exports = await service.export.list_exports(
        organization_id=str(current_user.organization_id),
    )
    for e in exports:
        if e.id == export_id:
            return ExportRequestResponse.model_validate(e)
    raise HTTPException(status_code=404, detail="Export request not found.")


# ---------------------------------------------------------------------------
# Deletions
# ---------------------------------------------------------------------------

@router.post("/deletions", response_model=DeletionRequestResponse, status_code=status.HTTP_201_CREATED)
async def request_deletion(
    data: DeletionRequestCreate,
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    req = await service.deletion.create_deletion_request(
        organization_id=str(current_user.organization_id),
        requested_by=str(current_user.id),
        data=data,
    )
    return DeletionRequestResponse.model_validate(req)


@router.get("/deletions", response_model=List[DeletionRequestResponse])
async def list_deletions(
    workspace_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    requests = await service.deletion.list_requests(
        organization_id=str(current_user.organization_id),
        workspace_id=workspace_id,
        status=status,
    )
    return [DeletionRequestResponse.model_validate(r) for r in requests]


@router.get("/deletions/{request_id}", response_model=DeletionRequestResponse)
async def get_deletion(
    request_id: str,
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    requests = await service.deletion.list_requests(
        organization_id=str(current_user.organization_id),
    )
    for r in requests:
        if r.id == request_id:
            return DeletionRequestResponse.model_validate(r)
    raise HTTPException(status_code=404, detail="Deletion request not found.")


# ---------------------------------------------------------------------------
# Legal Holds
# ---------------------------------------------------------------------------

@router.get("/legal-holds", response_model=List[LegalHoldResponse])
async def list_legal_holds(
    workspace_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    holds = await service.legal_hold.list_holds(
        organization_id=str(current_user.organization_id),
        workspace_id=workspace_id,
        status=status,
    )
    result = []
    for h in holds:
        resp = LegalHoldResponse.model_validate(h)
        resp.asset_count = len(h.assets or [])
        result.append(resp)
    return result


@router.post("/legal-holds", response_model=LegalHoldResponse, status_code=status.HTTP_201_CREATED)
async def create_legal_hold(
    data: LegalHoldCreate,
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    hold = await service.legal_hold.create_hold(
        organization_id=str(current_user.organization_id),
        created_by=str(current_user.id),
        data=data,
    )
    resp = LegalHoldResponse.model_validate(hold)
    resp.asset_count = len(data.asset_ids or [])
    return resp


@router.patch("/legal-holds/{hold_id}/release", response_model=LegalHoldResponse)
async def release_legal_hold(
    hold_id: str,
    data: LegalHoldReleaseRequest,
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    try:
        hold = await service.legal_hold.release_hold(
            hold_id=hold_id,
            organization_id=str(current_user.organization_id),
            actor_id=str(current_user.id),
            reason=data.reason,
        )
        return LegalHoldResponse.model_validate(hold)
    except DataGovernanceError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ---------------------------------------------------------------------------
# Compliance Evidence
# ---------------------------------------------------------------------------

@router.get("/evidence", response_model=List[ComplianceEvidenceResponse])
async def list_evidence(
    workspace_id: Optional[str] = Query(None),
    evidence_type: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    records = await service.repo.list_evidence(
        organization_id=str(current_user.organization_id),
        workspace_id=workspace_id,
        evidence_type=evidence_type,
        subject_id=subject_id,
        limit=limit,
        offset=offset,
    )
    return [ComplianceEvidenceResponse.model_validate(r) for r in records]


@router.get("/evidence/{evidence_id}", response_model=ComplianceEvidenceResponse)
async def get_evidence(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    service: DataGovernanceService = Depends(_get_service),
):
    record = await service.repo.get_evidence_by_id(
        evidence_id=evidence_id,
        organization_id=str(current_user.organization_id),
    )
    if not record:
        raise HTTPException(status_code=404, detail="Compliance evidence record not found.")
    return ComplianceEvidenceResponse.model_validate(record)
