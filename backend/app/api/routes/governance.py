"""
FastAPI routes for Step 32: AI Governance, Policy Control Plane, and Safety Guardrails.
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.governance.errors import (
    GovernanceConflictError,
    GovernanceDeniedError,
    GovernancePolicyMalformedError,
    GovernancePolicyNotFoundError,
)
from backend.app.services.governance.schemas import (
    BudgetPolicyCreate,
    BudgetPolicyResponse,
    DataClassificationRequest,
    DataClassificationResponse,
    GovernanceDecisionLogResponse,
    GovernanceDecision,
    GovernanceEvaluationRequest,
    GovernancePolicyCreate,
    GovernancePolicyResponse,
    GovernancePolicyUpdate,
    GovernancePreviewRequest,
    GovernancePreviewResponse,
    GovernanceSimulateRequest,
    GovernanceSimulateResponse,
    GovernanceStatsResponse,
    PolicyVersionCreate,
    PolicyVersionResponse,
)
from backend.app.services.governance.service import GovernanceService

router = APIRouter(prefix="/governance", tags=["governance"])


def _get_service(db: AsyncSession = Depends(get_db)) -> GovernanceService:
    return GovernanceService(db)


# ---------------------------------------------------------------------------
# Stats / Dashboard
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=GovernanceStatsResponse)
async def get_governance_stats(
    workspace_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    service: GovernanceService = Depends(_get_service),
):
    """Governance dashboard metrics: active policies, blocks, approvals, budget."""
    try:
        return await service.get_stats(
            organization_id=current_user.organization_id,
            workspace_id=workspace_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Policy CRUD
# ---------------------------------------------------------------------------

@router.post("/policies", response_model=GovernancePolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    data: GovernancePolicyCreate,
    current_user: User = Depends(get_current_user),
    service: GovernanceService = Depends(_get_service),
):
    """Create a new governance policy (Admin only)."""
    try:
        return await service.create_policy(
            organization_id=current_user.organization_id,
            created_by=current_user.id,
            data=data,
        )
    except GovernancePolicyMalformedError as exc:
        raise HTTPException(status_code=422, detail=exc.detail)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/policies", response_model=List[GovernancePolicyResponse])
async def list_policies(
    workspace_id: Optional[uuid.UUID] = Query(None),
    project_id: Optional[uuid.UUID] = Query(None),
    scope: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    service: GovernanceService = Depends(_get_service),
):
    """List governance policies scoped to the caller's organization/workspace."""
    return await service.list_policies(
        organization_id=current_user.organization_id,
        workspace_id=workspace_id,
        project_id=project_id,
        scope=scope,
        status=status_filter,
    )


@router.get("/policies/{policy_id}", response_model=GovernancePolicyResponse)
async def get_policy(
    policy_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: GovernanceService = Depends(_get_service),
):
    try:
        return await service.get_policy(policy_id)
    except GovernancePolicyNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.detail)


@router.patch("/policies/{policy_id}", response_model=GovernancePolicyResponse)
async def update_policy(
    policy_id: uuid.UUID,
    data: GovernancePolicyUpdate,
    current_user: User = Depends(get_current_user),
    service: GovernanceService = Depends(_get_service),
):
    """Update a governance policy (Admin only)."""
    try:
        return await service.update_policy(
            policy_id=policy_id,
            actor_id=current_user.id,
            data=data,
        )
    except GovernancePolicyNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.detail)


@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: GovernanceService = Depends(_get_service),
):
    """Archive a governance policy (Admin only)."""
    try:
        await service.delete_policy(
            policy_id=policy_id,
            actor_id=current_user.id,
            organization_id=current_user.organization_id,
        )
    except GovernancePolicyNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.detail)


# ---------------------------------------------------------------------------
# Policy Versions
# ---------------------------------------------------------------------------

@router.post(
    "/policies/{policy_id}/versions",
    response_model=PolicyVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_version(
    policy_id: uuid.UUID,
    data: PolicyVersionCreate,
    current_user: User = Depends(get_current_user),
    service: GovernanceService = Depends(_get_service),
):
    """Create a new draft version for an existing policy."""
    try:
        return await service.create_version(
            policy_id=policy_id,
            created_by=current_user.id,
            organization_id=current_user.organization_id,
            data=data,
        )
    except GovernancePolicyNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.detail)
    except GovernancePolicyMalformedError as exc:
        raise HTTPException(status_code=422, detail=exc.detail)


@router.get("/policies/{policy_id}/versions", response_model=List[PolicyVersionResponse])
async def list_versions(
    policy_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: GovernanceService = Depends(_get_service),
):
    return await service.list_versions(policy_id)


@router.post(
    "/policies/{policy_id}/versions/{version_id}/activate",
    response_model=PolicyVersionResponse,
)
async def activate_version(
    policy_id: uuid.UUID,
    version_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: GovernanceService = Depends(_get_service),
):
    """Activate a draft policy version (Admin only). Active versions are immutable."""
    try:
        return await service.activate_version(
            policy_id=policy_id,
            version_id=version_id,
            actor_id=current_user.id,
            organization_id=current_user.organization_id,
        )
    except GovernancePolicyNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.detail)
    except (GovernanceConflictError, GovernancePolicyMalformedError) as exc:
        raise HTTPException(status_code=409, detail=exc.detail)


# ---------------------------------------------------------------------------
# Evaluation / Simulation / Preview
# ---------------------------------------------------------------------------

@router.post("/evaluate", response_model=GovernanceDecision)
async def evaluate(
    data: GovernanceEvaluationRequest,
    current_user: User = Depends(get_current_user),
    service: GovernanceService = Depends(_get_service),
):
    """Evaluate a governance decision for a given trusted execution context."""
    data.organization_id = current_user.organization_id
    data.user_id = data.user_id or current_user.id
    return await service.evaluate(data)


@router.post("/simulate", response_model=GovernanceSimulateResponse)
async def simulate(
    data: GovernanceSimulateRequest,
    current_user: User = Depends(get_current_user),
    service: GovernanceService = Depends(_get_service),
):
    """
    Dry-run governance simulation. Returns decision without executing the operation.
    """
    data.evaluation.organization_id = current_user.organization_id
    return await service.simulate(data)


@router.post("/preview", response_model=GovernancePreviewResponse)
async def preview(
    data: GovernancePreviewRequest,
    current_user: User = Depends(get_current_user),
    service: GovernanceService = Depends(_get_service),
):
    """
    Test a hypothetical policy configuration. Never mutates production state.
    Admin only.
    """
    try:
        data.evaluation.organization_id = current_user.organization_id
        return await service.preview(data)
    except GovernancePolicyMalformedError as exc:
        raise HTTPException(status_code=422, detail=exc.detail)


# ---------------------------------------------------------------------------
# Budget Policies
# ---------------------------------------------------------------------------

@router.post("/budgets", response_model=BudgetPolicyResponse, status_code=status.HTTP_201_CREATED)
async def upsert_budget(
    data: BudgetPolicyCreate,
    current_user: User = Depends(get_current_user),
    service: GovernanceService = Depends(_get_service),
):
    """Create or update a budget policy for a workspace/project (Admin only)."""
    return await service.upsert_budget_policy(
        organization_id=current_user.organization_id,
        created_by=current_user.id,
        data=data,
    )


@router.get("/budgets", response_model=Optional[BudgetPolicyResponse])
async def get_budget(
    workspace_id: Optional[uuid.UUID] = Query(None),
    project_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    service: GovernanceService = Depends(_get_service),
):
    """Get the active budget policy for a workspace/project."""
    return await service.get_budget_policy(
        organization_id=current_user.organization_id,
        workspace_id=workspace_id,
        project_id=project_id,
    )


# ---------------------------------------------------------------------------
# Data Classification
# ---------------------------------------------------------------------------

@router.post("/classify", response_model=DataClassificationResponse)
async def classify_data(
    data: DataClassificationRequest,
    current_user: User = Depends(get_current_user),
    service: GovernanceService = Depends(_get_service),
):
    """Assign a data classification to an artifact, document, connector, or entity."""
    return service.classify(data)


# ---------------------------------------------------------------------------
# Decision Log
# ---------------------------------------------------------------------------

@router.get("/decisions", response_model=List[GovernanceDecisionLogResponse])
async def list_decisions(
    workspace_id: uuid.UUID = Query(...),
    enforcement_point: Optional[str] = Query(None),
    decision: Optional[str] = Query(None),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    service: GovernanceService = Depends(_get_service),
):
    """List governance decision audit log entries (Admin/Audit only)."""
    logs = await service.repo.list_decision_logs(
        workspace_id=workspace_id,
        enforcement_point=enforcement_point,
        decision=decision,
        limit=limit,
    )
    return [GovernanceDecisionLogResponse.model_validate(l) for l in logs]
