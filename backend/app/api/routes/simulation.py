"""
Internal API Routes for Step 41: AI Agent Simulation, Sandbox & Scenario Testing Layer.
Mounted under:
  /api/simulations
  /api/simulation-scenarios
  /api/simulation-suites
  /api/simulation-runs
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.simulation.errors import (
    SimulationError,
    SimulationNotFoundError,
    SimulationRunNotFoundError,
    SimulationScenarioNotFoundError,
    SimulationSuiteNotFoundError,
)
from backend.app.services.simulation.schemas import (
    SimulationComparisonRequest,
    SimulationComparisonResponse,
    SimulationCreate,
    SimulationDetailResponse,
    SimulationReportResponse,
    SimulationResponse,
    SimulationRunCreate,
    SimulationRunDetailResponse,
    SimulationRunResponse,
    SimulationScenarioCreate,
    SimulationScenarioResponse,
    SimulationScenarioUpdate,
    SimulationSuiteCreate,
    SimulationSuiteDetailResponse,
    SimulationSuiteResponse,
    SimulationSuiteRunRequest,
    SimulationSuiteRunResult,
    SimulationUpdate,
    SimulationVersionCreate,
    SimulationVersionResponse,
)
from backend.app.services.simulation.service import SimulationService


simulations_router = APIRouter(prefix="/simulations", tags=["Simulations"])
scenarios_router = APIRouter(prefix="/simulation-scenarios", tags=["Simulation Scenarios"])
suites_router = APIRouter(prefix="/simulation-suites", tags=["Simulation Suites"])
runs_router = APIRouter(prefix="/simulation-runs", tags=["Simulation Runs"])


def _extract_workspace_id(workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")) -> str:
    if not workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header 'X-Workspace-ID' is required.",
        )
    return workspace_id


# =============================================================================
# SIMULATION CRUD & VERSIONS
# =============================================================================

@simulations_router.post("", response_model=SimulationResponse, status_code=status.HTTP_201_CREATED)
async def create_simulation(
    req: SimulationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = SimulationService(db)
    sim, _ = await service.create_simulation(workspace_id, str(current_user.id), req)
    return sim


@simulations_router.get("", response_model=List[SimulationResponse])
async def list_simulations(
    project_id: Optional[str] = Query(None),
    target_type: Optional[str] = Query(None),
    target_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = SimulationService(db)
    sims, _ = await service.list_simulations(workspace_id, project_id, target_type, target_id, status, limit, offset)
    return sims


@simulations_router.get("/{simulation_id}", response_model=SimulationDetailResponse)
async def get_simulation(
    simulation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = SimulationService(db)
    sim = await service.get_simulation(simulation_id, workspace_id)
    return sim


@simulations_router.patch("/{simulation_id}", response_model=SimulationResponse)
async def update_simulation(
    simulation_id: str,
    req: SimulationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = SimulationService(db)
    sim = await service.update_simulation(simulation_id, workspace_id, req)
    return sim


@simulations_router.post("/{simulation_id}/versions", response_model=SimulationVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_simulation_version(
    simulation_id: str,
    req: SimulationVersionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = SimulationService(db)
    ver = await service.create_version(simulation_id, workspace_id, str(current_user.id), req)
    return ver


@simulations_router.post("/{simulation_id}/run", response_model=SimulationRunResponse)
async def run_simulation(
    simulation_id: str,
    req: SimulationRunCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = SimulationService(db)
    run = await service.run_simulation(simulation_id, workspace_id, str(current_user.id), req)
    return run


@simulations_router.get("/{simulation_id}/runs", response_model=List[SimulationRunResponse])
async def list_simulation_runs(
    simulation_id: str,
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = SimulationService(db)
    runs, _ = await service.list_runs(simulation_id=simulation_id, status=status, limit=limit, offset=offset)
    return runs


# =============================================================================
# SCENARIOS
# =============================================================================

@scenarios_router.post("", response_model=SimulationScenarioResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    req: SimulationScenarioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = SimulationService(db)
    return await service.create_scenario(workspace_id, req)


@scenarios_router.get("", response_model=List[SimulationScenarioResponse])
async def list_scenarios(
    scenario_type: Optional[str] = Query(None),
    simulation_version_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = SimulationService(db)
    scens, _ = await service.list_scenarios(workspace_id, scenario_type, simulation_version_id, limit, offset)
    return scens


@scenarios_router.get("/{scenario_id}", response_model=SimulationScenarioResponse)
async def get_scenario(
    scenario_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = SimulationService(db)
    return await service.get_scenario(scenario_id, workspace_id)


# =============================================================================
# SUITES
# =============================================================================

@suites_router.post("", response_model=SimulationSuiteResponse, status_code=status.HTTP_201_CREATED)
async def create_suite(
    req: SimulationSuiteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = SimulationService(db)
    return await service.create_suite(workspace_id, str(current_user.id), req)


@suites_router.get("", response_model=List[SimulationSuiteResponse])
async def list_suites(
    target_type: Optional[str] = Query(None),
    target_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = SimulationService(db)
    suites, _ = await service.list_suites(workspace_id, target_type, target_id, limit, offset)
    return suites


@suites_router.get("/{suite_id}", response_model=SimulationSuiteDetailResponse)
async def get_suite(
    suite_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = SimulationService(db)
    return await service.get_suite(suite_id, workspace_id)


@suites_router.post("/{suite_id}/run", response_model=SimulationSuiteRunResult)
async def run_suite(
    suite_id: str,
    req: SimulationSuiteRunRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = SimulationService(db)
    return await service.run_suite(suite_id, workspace_id, str(current_user.id), req)


# =============================================================================
# RUN DETAILS, TRACE, ASSERTIONS, SIDE EFFECTS, COMPARISON
# =============================================================================

@runs_router.get("/{run_id}", response_model=SimulationRunDetailResponse)
async def get_run_detail(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = SimulationService(db)
    run = await service.get_run(run_id)
    return run


@runs_router.get("/{run_id}/report")
async def get_run_report(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = SimulationService(db)
    return await service.get_run_report(run_id, workspace_id)


@runs_router.get("/{run_id}/side-effects")
async def get_run_side_effects(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = SimulationService(db)
    run = await service.get_run(run_id)
    return run.side_effects


@runs_router.get("/{run_id}/assertions")
async def get_run_assertions(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = SimulationService(db)
    run = await service.get_run(run_id)
    return run.assertion_results


@runs_router.get("/{run_id}/trace")
async def get_run_trace(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = SimulationService(db)
    run = await service.get_run(run_id)
    return {
        "run_id": run.id,
        "seed": run.seed,
        "tool_calls": run.tool_calls,
        "connector_calls": run.connector_calls,
        "side_effects": run.side_effects,
        "assertions": run.assertion_results,
    }


@runs_router.post("/{run_id}/compare", response_model=SimulationComparisonResponse)
async def compare_runs(
    run_id: str,
    req: SimulationComparisonRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = SimulationService(db)
    return await service.compare_runs(run_id, req.comparison_run_id, workspace_id)
