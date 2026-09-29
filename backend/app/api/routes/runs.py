from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.repositories.run import RunRepository
from backend.app.schemas.run import RunResponse
from backend.app.services.observability.schemas import (
    ExecutionTraceEventResponse,
    RunTelemetryResponse,
    UsageRecordResponse,
)
from backend.app.services.observability.service import ObservabilityService

router = APIRouter(prefix="/runs", tags=["Execution Runs"])


@router.get("/{run_id}", response_model=RunResponse)
async def get_run_detail(
    run_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> RunResponse:
    """
    Retrieve run execution detail, input snapshot, token metrics, and output.
    Enforces multi-tenant ownership: returns 404 if the run belongs to another user.
    """
    repo = RunRepository(session)
    run = await repo.get_by_id_and_owner_or_raise(run_id, user.id)
    return RunResponse.model_validate(run)


@router.get("/{run_id}/trace", response_model=List[ExecutionTraceEventResponse])
async def get_run_trace(
    run_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[ExecutionTraceEventResponse]:
    """
    Retrieve ordered execution trace events for a specific run.
    Enforces ownership isolation. Never exposes hidden chain-of-thought.
    """
    run_repo = RunRepository(session)
    run = await run_repo.get_by_id_and_owner_or_raise(run_id, user.id)
    # Get workspace id from task -> project -> workspace
    ws_id = run.task.project.workspace_id if (run.task and run.task.project) else None
    if not ws_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace context for run not found.")

    obs_service = ObservabilityService(session)
    return await obs_service.get_run_trace_events(run_id, ws_id)


@router.get("/{run_id}/usage", response_model=List[UsageRecordResponse])
async def get_run_usage(
    run_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[UsageRecordResponse]:
    """
    Retrieve granular LLM usage records for a run across planning, generation, evaluation, and revision.
    """
    run_repo = RunRepository(session)
    run = await run_repo.get_by_id_and_owner_or_raise(run_id, user.id)
    ws_id = run.task.project.workspace_id if (run.task and run.task.project) else None
    if not ws_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace context for run not found.")

    obs_service = ObservabilityService(session)
    return await obs_service.get_run_usage(run_id, ws_id)


@router.get("/{run_id}/telemetry", response_model=Optional[RunTelemetryResponse])
async def get_run_telemetry(
    run_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Optional[RunTelemetryResponse]:
    """
    Retrieve consolidated execution telemetry record for a run.
    """
    run_repo = RunRepository(session)
    run = await run_repo.get_by_id_and_owner_or_raise(run_id, user.id)
    ws_id = run.task.project.workspace_id if (run.task and run.task.project) else None
    if not ws_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace context for run not found.")

    obs_service = ObservabilityService(session)
    return await obs_service.get_run_telemetry(run_id, ws_id)

