"""
Internal API Routes for Step 44:
AI Work Planning, Capacity & Resource Optimization Layer.
Mounted under:
  /api/work-plans
  /api/planning
  /api/planning-scenarios
  /api/resources
  /api/capacity
  /api/reservations
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.planning.errors import (
    PlanningError,
    PlanNotFoundError,
    PlanVersionNotFoundError,
    ResourceNotFoundError,
    PlanStaleError,
    DependencyCycleError,
    HardConstraintViolationError,
    CapacityExceededError,
    UnauthorizedCapacityReservationError,
    PrivacyViolationError,
    FabricatedCapacityError,
    SubjectiveRankingForbiddenError,
    HiddenAggregateScoreForbiddenError,
    PlanningTenantViolationError,
    ImmutableVersionError,
    DirectExecutionForbiddenError,
)
from backend.app.services.planning.schemas import (
    CapacityForecastResponse,
    CapacityReservationCreate,
    CapacityReservationResponse,
    PlanGenerationRequest,
    PlanGenerationResult,
    PlanValidationResult,
    PlanningBlockerResponse,
    PlanningConstraintCreate,
    PlanningConstraintResponse,
    PlanningDependencyCreate,
    PlanningDependencyResponse,
    PlanningItemCreate,
    PlanningItemResponse,
    PlanningRecommendationResponse,
    PlanningScenarioCreate,
    PlanningScenarioResponse,
    ResourceAvailabilityCreate,
    ResourceAvailabilityResponse,
    ScheduleCandidateResponse,
    WorkPlanCreate,
    WorkPlanResponse,
    WorkPlanUpdate,
    WorkPlanVersionResponse,
    WorkResourceCreate,
    WorkResourceResponse,
    WorkloadSnapshotResponse,
    PlanProgressResponse,
    PlanConflictsResponse,
)
from backend.app.services.planning.service import PlanningService

work_plans_router = APIRouter(prefix="/work-plans", tags=["Work Plans"])
planning_router = APIRouter(prefix="/planning", tags=["Planning"])
planning_scenarios_router = APIRouter(prefix="/planning-scenarios", tags=["Planning Scenarios"])
resources_router = APIRouter(prefix="/resources", tags=["Work Resources"])
capacity_router = APIRouter(prefix="/capacity", tags=["Capacity"])
reservations_router = APIRouter(prefix="/reservations", tags=["Capacity Reservations"])


def _extract_workspace(
    current_user: User,
    x_workspace_id: Optional[str],
) -> str:
    ws_id = x_workspace_id or getattr(current_user, "default_workspace_id", None)
    if not ws_id:
        return str(current_user.id)
    return str(ws_id)


def _handle_planning_exception(ex: Exception):
    if isinstance(ex, PlanningError):
        raise HTTPException(
            status_code=ex.status_code,
            detail={"code": ex.code, "message": ex.message, "details": ex.details},
        )
    raise ex


# ---------------------------------------------------------------------------
# Work Plans Endpoints
# ---------------------------------------------------------------------------

@work_plans_router.post("", response_model=WorkPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_work_plan(
    data: WorkPlanCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        plan = await svc.create_plan(ws_id, str(current_user.id), data)
        return WorkPlanResponse.model_validate(plan)
    except Exception as ex:
        _handle_planning_exception(ex)


@work_plans_router.get("", response_model=List[WorkPlanResponse])
async def list_work_plans(
    project_id: Optional[str] = Query(None),
    objective_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    plans = await svc.list_plans(ws_id, project_id, objective_id, status_filter, limit, offset)
    return [WorkPlanResponse.model_validate(p) for p in plans]


@work_plans_router.get("/{plan_id}", response_model=WorkPlanResponse)
async def get_work_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        plan = await svc.get_plan(plan_id, ws_id)
        return WorkPlanResponse.model_validate(plan)
    except Exception as ex:
        _handle_planning_exception(ex)


@work_plans_router.patch("/{plan_id}", response_model=WorkPlanResponse)
async def update_work_plan(
    plan_id: str,
    data: WorkPlanUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        plan = await svc.update_plan(plan_id, ws_id, data)
        return WorkPlanResponse.model_validate(plan)
    except Exception as ex:
        _handle_planning_exception(ex)


@work_plans_router.post("/{plan_id}/versions", response_model=WorkPlanVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_work_plan_version(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        ver = await svc.create_version(plan_id, ws_id, str(current_user.id))
        return WorkPlanVersionResponse.model_validate(ver)
    except Exception as ex:
        _handle_planning_exception(ex)


@work_plans_router.get("/{plan_id}/versions", response_model=List[WorkPlanVersionResponse])
async def list_work_plan_versions(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        versions = await svc.list_versions(plan_id, ws_id)
        return [WorkPlanVersionResponse.model_validate(v) for v in versions]
    except Exception as ex:
        _handle_planning_exception(ex)


@work_plans_router.post("/{plan_id}/plan", response_model=PlanGenerationResult)
async def generate_plan(
    plan_id: str,
    req: PlanGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        res = await svc.generate_plan(plan_id, ws_id, req)
        return PlanGenerationResult(
            work_plan_id=res["work_plan_id"],
            version=res["version"],
            items_count=res["items_count"],
            dependencies_count=res["dependencies_count"],
            candidates_count=res["candidates_count"],
            blockers_count=res["blockers_count"],
            recommendations_count=res["recommendations_count"],
            candidates=[ScheduleCandidateResponse.model_validate(c) for c in res["candidates"]],
        )
    except Exception as ex:
        _handle_planning_exception(ex)


@work_plans_router.post("/{plan_id}/validate", response_model=PlanValidationResult)
async def validate_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        res = await svc.validate_plan(plan_id, ws_id)
        return PlanValidationResult(
            is_valid=res["is_valid"],
            is_stale=res["is_stale"],
            cycle_detected=res["cycle_detected"],
            hard_violations=res["hard_violations"],
            soft_violations=res["soft_violations"],
            blockers=[PlanningBlockerResponse.model_validate(b) for b in res["blockers"] if isinstance(b, dict) and "id" in b],
            conflicts=res["conflicts"],
        )
    except Exception as ex:
        _handle_planning_exception(ex)


@work_plans_router.post("/{plan_id}/activate", response_model=WorkPlanResponse)
async def activate_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        plan = await svc.activate_plan(plan_id, ws_id)
        return WorkPlanResponse.model_validate(plan)
    except Exception as ex:
        _handle_planning_exception(ex)


@work_plans_router.post("/{plan_id}/pause", response_model=WorkPlanResponse)
async def pause_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        plan = await svc.pause_plan(plan_id, ws_id)
        return WorkPlanResponse.model_validate(plan)
    except Exception as ex:
        _handle_planning_exception(ex)


@work_plans_router.post("/{plan_id}/items", response_model=PlanningItemResponse, status_code=status.HTTP_201_CREATED)
async def add_planning_item(
    plan_id: str,
    data: PlanningItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        item = await svc.add_item(plan_id, ws_id, data)
        return PlanningItemResponse.model_validate(item)
    except Exception as ex:
        _handle_planning_exception(ex)


@work_plans_router.post("/{plan_id}/dependencies", response_model=PlanningDependencyResponse, status_code=status.HTTP_201_CREATED)
async def add_planning_dependency(
    plan_id: str,
    data: PlanningDependencyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        dep = await svc.add_dependency(plan_id, ws_id, data)
        return PlanningDependencyResponse.model_validate(dep)
    except Exception as ex:
        _handle_planning_exception(ex)


@work_plans_router.get("/{plan_id}/dependencies", response_model=List[PlanningDependencyResponse])
async def get_plan_dependencies(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        plan = await svc.get_plan(plan_id, ws_id)
        latest_ver = await svc.repo.get_latest_version(plan.id)
        if not latest_ver:
            return []
        deps = await svc.repo.list_dependencies_for_version(latest_ver.id)
        return [PlanningDependencyResponse.model_validate(d) for d in deps]
    except Exception as ex:
        _handle_planning_exception(ex)


@work_plans_router.get("/{plan_id}/resources", response_model=List[WorkResourceResponse])
async def get_plan_resources(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        await svc.get_plan(plan_id, ws_id)
        res_list = await svc.list_resources(ws_id)
        return [WorkResourceResponse.model_validate(r) for r in res_list]
    except Exception as ex:
        _handle_planning_exception(ex)


@work_plans_router.get("/{plan_id}/conflicts", response_model=PlanConflictsResponse)
async def get_plan_conflicts(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        conflicts_data = await svc.detect_conflicts(plan_id, ws_id)
        return PlanConflictsResponse(**conflicts_data)
    except Exception as ex:
        _handle_planning_exception(ex)


@work_plans_router.get("/{plan_id}/progress", response_model=PlanProgressResponse)
async def get_plan_progress(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        prog = await svc.get_plan_progress(plan_id, ws_id)
        return PlanProgressResponse(**prog)
    except Exception as ex:
        _handle_planning_exception(ex)


@work_plans_router.get("/{plan_id}/blockers", response_model=List[PlanningBlockerResponse])
async def get_plan_blockers(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        plan = await svc.get_plan(plan_id, ws_id)
        latest_ver = await svc.repo.get_latest_version(plan.id)
        if not latest_ver:
            return []
        blockers = await svc.repo.list_blockers_for_version(latest_ver.id)
        return [PlanningBlockerResponse.model_validate(b) for b in blockers]
    except Exception as ex:
        _handle_planning_exception(ex)


# ---------------------------------------------------------------------------
# Resources & Capacity Endpoints
# ---------------------------------------------------------------------------

@resources_router.post("", response_model=WorkResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    data: WorkResourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        res = await svc.register_resource(ws_id, data)
        return WorkResourceResponse.model_validate(res)
    except Exception as ex:
        _handle_planning_exception(ex)


@resources_router.get("", response_model=List[WorkResourceResponse])
async def list_resources(
    resource_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    resources = await svc.list_resources(ws_id, resource_type, status_filter)
    return [WorkResourceResponse.model_validate(r) for r in resources]


@resources_router.get("/{resource_id}", response_model=WorkResourceResponse)
async def get_resource(
    resource_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        res = await svc.get_resource(resource_id, ws_id)
        return WorkResourceResponse.model_validate(res)
    except Exception as ex:
        _handle_planning_exception(ex)


@resources_router.get("/{resource_id}/capacity")
async def get_resource_capacity(
    resource_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        return await svc.get_resource_capacity(resource_id, ws_id)
    except Exception as ex:
        _handle_planning_exception(ex)


@resources_router.post("/{resource_id}/availability", response_model=ResourceAvailabilityResponse, status_code=status.HTTP_201_CREATED)
async def add_resource_availability(
    resource_id: str,
    data: ResourceAvailabilityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        avail = await svc.add_availability(resource_id, ws_id, data)
        return ResourceAvailabilityResponse.model_validate(avail)
    except Exception as ex:
        _handle_planning_exception(ex)


# ---------------------------------------------------------------------------
# Reservations & Capacity Endpoints
# ---------------------------------------------------------------------------

@reservations_router.post("", response_model=CapacityReservationResponse, status_code=status.HTTP_201_CREATED)
async def create_capacity_reservation(
    data: CapacityReservationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        res = await svc.create_reservation(ws_id, str(current_user.id), data)
        return CapacityReservationResponse.model_validate(res)
    except Exception as ex:
        _handle_planning_exception(ex)


@reservations_router.get("", response_model=List[CapacityReservationResponse])
async def list_capacity_reservations(
    resource_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    if resource_id:
        reserves = await svc.repo.list_reservations_for_resource(resource_id)
        return [CapacityReservationResponse.model_validate(r) for r in reserves]
    return []


# ---------------------------------------------------------------------------
# Planning Scenarios & Global Planning Endpoints
# ---------------------------------------------------------------------------

@planning_scenarios_router.post("", response_model=PlanningScenarioResponse, status_code=status.HTTP_201_CREATED)
async def create_planning_scenario(
    data: PlanningScenarioCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        sc = await svc.create_scenario(ws_id, str(current_user.id), data)
        return PlanningScenarioResponse.model_validate(sc)
    except Exception as ex:
        _handle_planning_exception(ex)


@planning_scenarios_router.get("/{scenario_id}", response_model=PlanningScenarioResponse)
async def get_planning_scenario(
    scenario_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        sc = await svc.repo.get_scenario(scenario_id, ws_id)
        if not sc:
            raise PlanNotFoundError(scenario_id)
        return PlanningScenarioResponse.model_validate(sc)
    except Exception as ex:
        _handle_planning_exception(ex)


@planning_scenarios_router.post("/{scenario_id}/run", response_model=PlanningScenarioResponse)
async def run_planning_scenario(
    scenario_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    try:
        sc = await svc.run_scenario(scenario_id, ws_id)
        return PlanningScenarioResponse.model_validate(sc)
    except Exception as ex:
        _handle_planning_exception(ex)


@planning_router.get("/recommendations", response_model=List[PlanningRecommendationResponse])
async def get_planning_recommendations(
    work_plan_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    recs = await svc.list_recommendations(ws_id, work_plan_id)
    return [PlanningRecommendationResponse.model_validate(r) for r in recs]


@planning_router.get("/forecast", response_model=CapacityForecastResponse)
async def get_capacity_forecast(
    horizon_days: int = Query(14, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    forecast = await svc.get_forecast(ws_id, horizon_days)
    return CapacityForecastResponse(**forecast)


@planning_router.get("/workload", response_model=List[WorkloadSnapshotResponse])
async def get_workload_snapshots(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None),
):
    ws_id = _extract_workspace(current_user, x_workspace_id)
    svc = PlanningService(db)
    workloads = await svc.get_workload(ws_id)
    return [WorkloadSnapshotResponse(**w) for w in workloads]
