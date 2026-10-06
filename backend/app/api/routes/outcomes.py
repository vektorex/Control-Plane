"""
Internal API Routes for Step 43:
AI Outcome Intelligence & Work Impact Layer.
Mounted under:
  /api/objectives
  /api/outcomes
  /api/outcome-targets
  /api/outcome-evidence
  /api/outcome-measurements
  /api/outcome-decisions
  /api/outcome-impact
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.outcomes.errors import (
    ObjectiveNotFoundError,
    OutcomeNotFoundError,
    OutcomeTargetNotFoundError,
    MilestoneNotFoundError,
    WorkDecisionNotFoundError,
    EvidenceNotFoundError,
    RequirementNotMetError,
    OutcomeTenantViolationError,
)
from backend.app.services.outcomes.schemas import (
    ObjectiveCreate,
    ObjectiveUpdate,
    ObjectiveResponse,
    ObjectiveDetailResponse,
    OutcomeTargetCreate,
    OutcomeTargetUpdate,
    OutcomeTargetResponse,
    OutcomeMilestoneCreate,
    OutcomeMilestoneUpdate,
    OutcomeMilestoneResponse,
    OutcomeCreate,
    OutcomeUpdate,
    OutcomeResponse,
    OutcomeDetailResponse,
    OutcomeEvidenceCreate,
    OutcomeEvidenceResponse,
    OutcomeMeasurementCreate,
    OutcomeMeasurementResponse,
    OutcomeWorkLinkCreate,
    OutcomeWorkLinkResponse,
    WorkDecisionCreate,
    WorkDecisionUpdate,
    WorkDecisionResponse,
    OutcomeAttributionCreate,
    OutcomeAttributionResponse,
    ImpactAnalysisCreate,
    ImpactAnalysisResponse,
    OutcomeVerifyRequest,
    OutcomeDisputeRequest,
    OutcomeHealthResponse,
    OutcomeWorkMapResponse,
    OutcomeRecommendationResponse,
)
from backend.app.services.outcomes.service import OutcomeService


objectives_router = APIRouter(prefix="/objectives", tags=["Objectives"])
outcomes_router = APIRouter(prefix="/outcomes", tags=["Outcomes"])
targets_router = APIRouter(prefix="/outcome-targets", tags=["Outcome Targets"])
evidence_router = APIRouter(prefix="/outcome-evidence", tags=["Outcome Evidence"])
measurements_router = APIRouter(prefix="/outcome-measurements", tags=["Outcome Measurements"])
decisions_router = APIRouter(prefix="/outcome-decisions", tags=["Outcome Decisions"])
impact_router = APIRouter(prefix="/outcome-impact", tags=["Outcome Impact"])


def _extract_workspace_id(workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")) -> str:
    if not workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header 'X-Workspace-ID' is required.",
        )
    return workspace_id


# =============================================================================
# Objectives Routes
# =============================================================================

@objectives_router.post("", response_model=ObjectiveResponse, status_code=status.HTTP_201_CREATED)
async def create_objective(
    data: ObjectiveCreate,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    obj = await svc.create_objective(workspace_id, str(current_user.id), data)
    return obj


@objectives_router.get("", response_model=List[ObjectiveResponse])
async def list_objectives(
    project_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    objective_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.list_objectives(workspace_id, project_id, status, objective_type, limit, offset)


@objectives_router.get("/{objective_id}", response_model=ObjectiveDetailResponse)
async def get_objective(
    objective_id: str,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    obj = await svc.get_objective(objective_id, workspace_id)
    health = await svc.get_objective_health(objective_id, workspace_id)
    return ObjectiveDetailResponse(
        id=obj.id,
        workspace_id=obj.workspace_id,
        project_id=obj.project_id,
        name=obj.name,
        description=obj.description,
        objective_type=obj.objective_type,
        status=obj.status,
        priority=obj.priority,
        owner_user_id=obj.owner_user_id,
        created_by=obj.created_by,
        requirements=obj.requirements or {},
        start_at=obj.start_at,
        target_at=obj.target_at,
        completed_at=obj.completed_at,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
        targets=[OutcomeTargetResponse.model_validate(t) for t in obj.targets],
        milestones=[OutcomeMilestoneResponse.model_validate(m) for m in obj.milestones],
        outcomes=[OutcomeResponse.model_validate(o) for o in obj.outcomes],
        health=health,
    )


@objectives_router.patch("/{objective_id}", response_model=ObjectiveResponse)
async def update_objective(
    objective_id: str,
    data: ObjectiveUpdate,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.update_objective(objective_id, workspace_id, data)


@objectives_router.delete("/{objective_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_objective(
    objective_id: str,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    await svc.delete_objective(objective_id, workspace_id)
    return None


@objectives_router.post("/{objective_id}/targets", response_model=OutcomeTargetResponse, status_code=status.HTTP_201_CREATED)
async def create_objective_target(
    objective_id: str,
    data: OutcomeTargetCreate,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.create_target(objective_id, workspace_id, data)


@objectives_router.get("/{objective_id}/targets", response_model=List[OutcomeTargetResponse])
async def list_objective_targets(
    objective_id: str,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.list_targets(objective_id, workspace_id)


@objectives_router.post("/{objective_id}/milestones", response_model=OutcomeMilestoneResponse, status_code=status.HTTP_201_CREATED)
async def create_objective_milestone(
    objective_id: str,
    data: OutcomeMilestoneCreate,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.create_milestone(objective_id, workspace_id, data)


@objectives_router.get("/{objective_id}/milestones", response_model=List[OutcomeMilestoneResponse])
async def list_objective_milestones(
    objective_id: str,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.list_milestones(objective_id, workspace_id)


@objectives_router.get("/{objective_id}/health", response_model=OutcomeHealthResponse)
async def get_objective_health(
    objective_id: str,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.get_objective_health(objective_id, workspace_id)


@objectives_router.get("/{objective_id}/work-map", response_model=OutcomeWorkMapResponse)
async def get_objective_work_map(
    objective_id: str,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.get_objective_work_map(objective_id, workspace_id)


@objectives_router.get("/{objective_id}/recommendations", response_model=List[OutcomeRecommendationResponse])
async def get_objective_recommendations(
    objective_id: str,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.get_objective_recommendations(objective_id, workspace_id)


# =============================================================================
# Targets Routes
# =============================================================================

@targets_router.get("/{target_id}", response_model=OutcomeTargetResponse)
async def get_target(
    target_id: str,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.get_target(target_id, workspace_id)


@targets_router.patch("/{target_id}", response_model=OutcomeTargetResponse)
async def update_target(
    target_id: str,
    data: OutcomeTargetUpdate,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.update_target(target_id, workspace_id, data)


# =============================================================================
# Outcomes Routes
# =============================================================================

@outcomes_router.post("", response_model=OutcomeResponse, status_code=status.HTTP_201_CREATED)
async def create_outcome(
    data: OutcomeCreate,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.create_outcome(workspace_id, str(current_user.id), data)


@outcomes_router.get("", response_model=List[OutcomeResponse])
async def list_outcomes(
    project_id: Optional[str] = Query(None),
    objective_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    outcome_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.list_outcomes(workspace_id, project_id, objective_id, status, outcome_type, limit, offset)


@outcomes_router.get("/{outcome_id}", response_model=OutcomeDetailResponse)
async def get_outcome(
    outcome_id: str,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    outcome = await svc.get_outcome(outcome_id, workspace_id)
    health = await svc.get_outcome_health(outcome_id, workspace_id)
    return OutcomeDetailResponse(
        id=outcome.id,
        workspace_id=outcome.workspace_id,
        project_id=outcome.project_id,
        objective_id=outcome.objective_id,
        name=outcome.name,
        description=outcome.description,
        outcome_type=outcome.outcome_type,
        status=outcome.status,
        confidence=outcome.confidence,
        owner_user_id=outcome.owner_user_id,
        created_by=outcome.created_by,
        requirements=outcome.requirements or {},
        observed_at=outcome.observed_at,
        verified_at=outcome.verified_at,
        verified_by=outcome.verified_by,
        created_at=outcome.created_at,
        updated_at=outcome.updated_at,
        objective=ObjectiveResponse.model_validate(outcome.objective) if outcome.objective else None,
        evidence=[OutcomeEvidenceResponse.model_validate(e) for e in outcome.evidence],
        work_links=[OutcomeWorkLinkResponse.model_validate(wl) for wl in outcome.work_links],
        measurements=[OutcomeMeasurementResponse.model_validate(m) for m in outcome.measurements],
        attributions=[OutcomeAttributionResponse.model_validate(a) for a in outcome.attributions],
        impact_analyses=[ImpactAnalysisResponse.model_validate(i) for i in outcome.impact_analyses],
        health=health,
    )


@outcomes_router.patch("/{outcome_id}", response_model=OutcomeResponse)
async def update_outcome(
    outcome_id: str,
    data: OutcomeUpdate,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.update_outcome(outcome_id, workspace_id, data)


@outcomes_router.delete("/{outcome_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_outcome(
    outcome_id: str,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    await svc.delete_outcome(outcome_id, workspace_id)
    return None


@outcomes_router.post("/{outcome_id}/evidence", response_model=OutcomeEvidenceResponse, status_code=status.HTTP_201_CREATED)
async def add_outcome_evidence(
    outcome_id: str,
    data: OutcomeEvidenceCreate,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.add_evidence(outcome_id, workspace_id, data)


@outcomes_router.get("/{outcome_id}/evidence", response_model=List[OutcomeEvidenceResponse])
async def list_outcome_evidence(
    outcome_id: str,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.list_evidence(outcome_id, workspace_id)


@outcomes_router.post("/{outcome_id}/measurements", response_model=OutcomeMeasurementResponse, status_code=status.HTTP_201_CREATED)
async def add_outcome_measurement(
    outcome_id: str,
    data: OutcomeMeasurementCreate,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.add_measurement(outcome_id, workspace_id, data)


@outcomes_router.get("/{outcome_id}/measurements", response_model=List[OutcomeMeasurementResponse])
async def list_outcome_measurements(
    outcome_id: str,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.list_measurements(outcome_id, workspace_id)


@outcomes_router.post("/{outcome_id}/work", response_model=OutcomeWorkLinkResponse, status_code=status.HTTP_201_CREATED)
async def add_outcome_work_link(
    outcome_id: str,
    data: OutcomeWorkLinkCreate,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.add_work_link(outcome_id, workspace_id, data)


@outcomes_router.get("/{outcome_id}/work", response_model=List[OutcomeWorkLinkResponse])
async def list_outcome_work_links(
    outcome_id: str,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.list_work_links(outcome_id, workspace_id)


@outcomes_router.post("/{outcome_id}/verify", response_model=OutcomeResponse)
async def verify_outcome(
    outcome_id: str,
    data: OutcomeVerifyRequest,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.verify_outcome(outcome_id, workspace_id, str(current_user.id), data)


@outcomes_router.post("/{outcome_id}/dispute", response_model=OutcomeResponse)
async def dispute_outcome(
    outcome_id: str,
    data: OutcomeDisputeRequest,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.dispute_outcome(outcome_id, workspace_id, str(current_user.id), data)


@outcomes_router.post("/{outcome_id}/attributions", response_model=OutcomeAttributionResponse, status_code=status.HTTP_201_CREATED)
async def add_outcome_attribution(
    outcome_id: str,
    data: OutcomeAttributionCreate,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.add_attribution(outcome_id, workspace_id, data)


@outcomes_router.get("/{outcome_id}/attributions", response_model=List[OutcomeAttributionResponse])
async def list_outcome_attributions(
    outcome_id: str,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.list_attributions(outcome_id, workspace_id)


@outcomes_router.post("/{outcome_id}/impact", response_model=ImpactAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def add_outcome_impact(
    outcome_id: str,
    data: ImpactAnalysisCreate,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.add_impact_analysis(outcome_id, workspace_id, data)


@outcomes_router.get("/{outcome_id}/impact", response_model=List[ImpactAnalysisResponse])
async def list_outcome_impact(
    outcome_id: str,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.list_impact_analyses(outcome_id, workspace_id)


@outcomes_router.get("/{outcome_id}/health", response_model=OutcomeHealthResponse)
async def get_outcome_health(
    outcome_id: str,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.get_outcome_health(outcome_id, workspace_id)


@outcomes_router.get("/{outcome_id}/graph", response_model=OutcomeWorkMapResponse)
async def get_outcome_graph(
    outcome_id: str,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.get_outcome_work_map(outcome_id, workspace_id)


@outcomes_router.get("/{outcome_id}/recommendations", response_model=List[OutcomeRecommendationResponse])
async def get_outcome_recommendations(
    outcome_id: str,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.get_outcome_recommendations(outcome_id, workspace_id)


# =============================================================================
# Decisions Routes
# =============================================================================

@decisions_router.post("", response_model=WorkDecisionResponse, status_code=status.HTTP_201_CREATED)
async def create_decision(
    data: WorkDecisionCreate,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.create_decision(workspace_id, str(current_user.id), data)


@decisions_router.get("", response_model=List[WorkDecisionResponse])
async def list_decisions(
    project_id: Optional[str] = Query(None),
    objective_id: Optional[str] = Query(None),
    outcome_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.list_decisions(workspace_id, project_id, objective_id, outcome_id, status, limit, offset)


@decisions_router.get("/{decision_id}", response_model=WorkDecisionResponse)
async def get_decision(
    decision_id: str,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.get_decision(decision_id, workspace_id)


@decisions_router.patch("/{decision_id}", response_model=WorkDecisionResponse)
async def update_decision(
    decision_id: str,
    data: WorkDecisionUpdate,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.update_decision(decision_id, workspace_id, data)


@decisions_router.post("/{decision_id}/approve", response_model=WorkDecisionResponse)
async def approve_decision(
    decision_id: str,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.approve_decision(decision_id, workspace_id, str(current_user.id))


@decisions_router.post("/{decision_id}/reject", response_model=WorkDecisionResponse)
async def reject_decision(
    decision_id: str,
    reason: Optional[str] = Query(None),
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.reject_decision(decision_id, workspace_id, str(current_user.id), reason)


# =============================================================================
# Impact Routes
# =============================================================================

@impact_router.get("/{outcome_id}", response_model=List[ImpactAnalysisResponse])
async def get_impact_for_outcome(
    outcome_id: str,
    workspace_id: str = Depends(_extract_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OutcomeService(db)
    return await svc.list_impact_analyses(outcome_id, workspace_id)
