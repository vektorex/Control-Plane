"""
REST API routes for Step 35: AI Reliability, Resilience & Chaos Engineering Layer.
Thin endpoints delegating strictly to ReliabilityService and domain engines.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.reliability.bulkhead import BulkheadRegistry
from backend.app.services.reliability.circuit_breaker import CircuitBreakerRegistry
from backend.app.services.reliability.exceptions import (
    ChaosExperimentAbortedError,
    CheckpointNotFoundError,
    ComponentNotFoundError,
    InvalidChaosActionError,
    ProductionChaosBlockedError,
    ReliabilityError,
    ResumePreconditionFailedError,
    UnauthorizedChaosExecutionError,
)
from backend.app.services.reliability.schemas import (
    ChaosExperimentCreate,
    ChaosExperimentResponse,
    ChaosExperimentSafetySummary,
    ChaosExperimentUpdate,
    ChaosObservationResponse,
    ChaosRunResponse,
    CheckpointResumeRequest,
    CheckpointResumeResponse,
    DependencyHealthResponse,
    ExecutionCheckpointResponse,
    ReliabilityBudgetResponse,
    ReliabilityComponentResponse,
    ReliabilityObjectiveCreate,
    ReliabilityObjectiveResponse,
    ReliabilityTelemetryResponse,
    SystemHealthOverviewResponse,
)
from backend.app.services.reliability.service import ReliabilityService

router = APIRouter(prefix="/reliability", tags=["Reliability, Resilience & Chaos"])


# ---------------------------------------------------------------------------
# 1. Health & Components
# ---------------------------------------------------------------------------
@router.get("/health", response_model=Dict[str, Any])
async def get_system_health(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve overall system health and status across all registered components."""
    svc = ReliabilityService(session)
    return await svc.health.get_system_health()


@router.get("/overview", response_model=SystemHealthOverviewResponse)
async def get_reliability_overview(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve system overview metrics (healthy, degraded, unavailable counts, active checkpoints)."""
    svc = ReliabilityService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else None
    return await svc.repository.get_overview_counts(organization_id=org_id)


@router.get("/components", response_model=List[ReliabilityComponentResponse])
async def list_components(
    component_type: Optional[str] = None,
    health_status: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List registered components and their operational health states."""
    svc = ReliabilityService(session)
    return await svc.health.list_components(
        component_type=component_type,
        health_status=health_status,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/components/{component_id}", response_model=ReliabilityComponentResponse)
async def get_component(
    component_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve details of a single component."""
    svc = ReliabilityService(session)
    try:
        return await svc.health.get_component(component_id)
    except ComponentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/dependencies", response_model=List[DependencyHealthResponse])
async def list_dependencies(
    component_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List lightweight dependency health checks."""
    svc = ReliabilityService(session)
    return await svc.health.list_dependencies(
        component_id=component_id,
        status=status,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# 2. Execution Checkpoints & Resumption
# ---------------------------------------------------------------------------
@router.get("/checkpoints", response_model=List[ExecutionCheckpointResponse])
async def list_checkpoints(
    run_id: Optional[str] = None,
    workflow_run_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List execution checkpoints within user's organization scope."""
    svc = ReliabilityService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else None
    return await svc.checkpoints.list_checkpoints(
        organization_id=org_id,
        run_id=run_id,
        workflow_run_id=workflow_run_id,
        limit=limit,
        offset=offset,
    )


@router.get("/checkpoints/{checkpoint_id}", response_model=ExecutionCheckpointResponse)
async def get_checkpoint(
    checkpoint_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve an execution checkpoint."""
    svc = ReliabilityService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else None
    try:
        return await svc.checkpoints.get_checkpoint(checkpoint_id, organization_id=org_id)
    except CheckpointNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/checkpoints/{checkpoint_id}/resume", response_model=CheckpointResumeResponse)
async def resume_from_checkpoint(
    checkpoint_id: str,
    request: CheckpointResumeRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Safely resume an interrupted execution from a checkpoint boundary."""
    svc = ReliabilityService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    try:
        return await svc.resume.resume_from_checkpoint(
            checkpoint_id=checkpoint_id,
            organization_id=org_id,
            request=request,
        )
    except (ResumePreconditionFailedError, CheckpointNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# 3. Objectives & Failure Budgets
# ---------------------------------------------------------------------------
@router.get("/objectives", response_model=List[ReliabilityObjectiveResponse])
async def list_objectives(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List configured SLOs and performance targets."""
    svc = ReliabilityService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else None
    return await svc.repository.list_objectives(organization_id=org_id)


@router.get("/budgets", response_model=List[ReliabilityBudgetResponse])
async def list_budgets(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List operational failure budgets."""
    svc = ReliabilityService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    return await svc.repository.list_budgets(organization_id=org_id)


# ---------------------------------------------------------------------------
# 4. Chaos Engineering Experiments
# ---------------------------------------------------------------------------
@router.get("/experiments", response_model=List[ChaosExperimentResponse])
async def list_experiments(
    environment: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List chaos experiments."""
    svc = ReliabilityService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else None
    return await svc.experiments.list_experiments(
        organization_id=org_id,
        environment=environment,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.post("/experiments", response_model=ChaosExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    payload: ChaosExperimentCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new controlled chaos experiment in test/sandbox environment."""
    svc = ReliabilityService(session)
    user_id = str(current_user.id)
    role = getattr(current_user, "role", "admin")
    try:
        return await svc.experiments.create_experiment(
            data=payload,
            creator_id=user_id,
            creator_role=role,
        )
    except (InvalidChaosActionError, ProductionChaosBlockedError, UnauthorizedChaosExecutionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/experiments/{experiment_id}", response_model=ChaosExperimentResponse)
async def get_experiment(
    experiment_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve single chaos experiment details with runs and observations."""
    svc = ReliabilityService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else None
    try:
        return await svc.experiments.get_experiment(experiment_id, organization_id=org_id)
    except ReliabilityError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/experiments/{experiment_id}/safety-summary", response_model=ChaosExperimentSafetySummary)
async def get_experiment_safety_summary(
    experiment_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Inspect blast radius, environment restrictions, and HITL authorization requirements."""
    svc = ReliabilityService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    try:
        return await svc.experiments.get_safety_summary(experiment_id, organization_id=org_id)
    except ReliabilityError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/experiments/{experiment_id}/approve", response_model=ChaosExperimentResponse)
async def approve_experiment(
    experiment_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a planned chaos experiment."""
    svc = ReliabilityService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    user_id = str(current_user.id)
    try:
        return await svc.experiments.approve_experiment(
            experiment_id=experiment_id,
            organization_id=org_id,
            approver_id=user_id,
        )
    except ProductionChaosBlockedError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ReliabilityError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/experiments/{experiment_id}/run", response_model=ChaosRunResponse)
async def run_experiment(
    experiment_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute a controlled chaos experiment run."""
    svc = ReliabilityService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    user_id = str(current_user.id)
    role = getattr(current_user, "role", "admin")
    try:
        return await svc.experiments.run_experiment(
            experiment_id=experiment_id,
            organization_id=org_id,
            actor_id=user_id,
            actor_role=role,
        )
    except ProductionChaosBlockedError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ReliabilityError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/experiments/{experiment_id}/abort", response_model=ChaosExperimentResponse)
async def abort_experiment(
    experiment_id: str,
    reason: str = Query("Operator manual abort"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Immediately abort an in-flight or planned chaos experiment."""
    svc = ReliabilityService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    try:
        return await svc.experiments.abort_experiment(
            experiment_id=experiment_id,
            organization_id=org_id,
            reason=reason,
        )
    except ReliabilityError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ---------------------------------------------------------------------------
# 5. Telemetry & Internal States
# ---------------------------------------------------------------------------
@router.get("/telemetry", response_model=ReliabilityTelemetryResponse)
async def get_telemetry(
    days: int = Query(30, ge=1, le=90),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve operational reliability telemetry."""
    svc = ReliabilityService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else None
    return await svc.repository.get_telemetry(days=days, organization_id=org_id)


@router.get("/bulkheads", response_model=Dict[str, Dict[str, int]])
async def get_bulkhead_capacity(
    current_user: User = Depends(get_current_user),
):
    """Retrieve concurrency isolation capacity and active slots per subsystem."""
    return BulkheadRegistry.get_capacity_metrics()


@router.get("/circuits", response_model=Dict[str, Dict[str, Any]])
async def get_circuit_breakers(
    current_user: User = Depends(get_current_user),
):
    """Retrieve circuit breaker statuses across external dependencies."""
    return CircuitBreakerRegistry.get_all_statuses()
