import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.repositories.workspace import WorkspaceRepository
from backend.app.services.observability.schemas import (
    AnalyticsEvaluationResponse,
    AnalyticsLatencyResponse,
    AnalyticsModelResponse,
    AnalyticsOverviewResponse,
    AnalyticsProviderResponse,
    AnalyticsUsageResponse,
    ObservabilityCleanupResponse,
)
from backend.app.services.observability.service import ObservabilityService

router = APIRouter(prefix="/analytics", tags=["Observability & Analytics"])
admin_router = APIRouter(prefix="/admin/observability", tags=["Observability Admin"])


async def _resolve_user_workspace(user: User, workspace_id: Optional[uuid.UUID], session: AsyncSession) -> uuid.UUID:
    """
    Validates and resolves active workspace id for the user to guarantee workspace isolation.
    """
    ws_repo = WorkspaceRepository(session)
    if workspace_id:
        ws = await ws_repo.get_by_id_and_owner_or_raise(workspace_id, user.id)
        return ws.id
    
    # Fallback to user's first workspace
    workspaces = await ws_repo.list_by_owner(user.id)
    if not workspaces:
        # Create or fetch default workspace
        ws = await ws_repo.get_or_create_default_workspace(user.id, user.email)
        return ws.id
    return workspaces[0].id


def _build_filter_dict(
    project_id: Optional[uuid.UUID] = None,
    task_id: Optional[uuid.UUID] = None,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    return {
        "project_id": project_id,
        "task_id": task_id,
        "model": model,
        "provider": provider,
        "status": status,
        "start_date": start_date,
        "end_date": end_date,
    }


@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def get_overview_analytics(
    workspace_id: Optional[uuid.UUID] = Query(None),
    project_id: Optional[uuid.UUID] = Query(None),
    task_id: Optional[uuid.UUID] = Query(None),
    model: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AnalyticsOverviewResponse:
    """
    Retrieve high-level workspace analytics including total runs, success rates,
    total tokens, estimated costs, latency metrics, and evaluation statistics.
    """
    ws_id = await _resolve_user_workspace(user, workspace_id, session)
    filters = _build_filter_dict(project_id, task_id, model, provider, status, start_date, end_date)
    obs_service = ObservabilityService(session)
    return await obs_service.get_overview_analytics(ws_id, filters)


@router.get("/usage", response_model=AnalyticsUsageResponse)
async def get_usage_analytics(
    workspace_id: Optional[uuid.UUID] = Query(None),
    project_id: Optional[uuid.UUID] = Query(None),
    task_id: Optional[uuid.UUID] = Query(None),
    model: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AnalyticsUsageResponse:
    """
    Retrieve daily aggregated token consumption and estimated cost data points.
    """
    ws_id = await _resolve_user_workspace(user, workspace_id, session)
    filters = _build_filter_dict(project_id, task_id, model, provider, status, start_date, end_date)
    obs_service = ObservabilityService(session)
    return await obs_service.get_usage_analytics(ws_id, filters)


@router.get("/models", response_model=AnalyticsModelResponse)
async def get_models_analytics(
    workspace_id: Optional[uuid.UUID] = Query(None),
    project_id: Optional[uuid.UUID] = Query(None),
    task_id: Optional[uuid.UUID] = Query(None),
    provider: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AnalyticsModelResponse:
    """
    Retrieve factual operational performance statistics grouped by LLM model.
    """
    ws_id = await _resolve_user_workspace(user, workspace_id, session)
    filters = _build_filter_dict(project_id, task_id, None, provider, status, start_date, end_date)
    obs_service = ObservabilityService(session)
    return await obs_service.get_models_analytics(ws_id, filters)


@router.get("/providers", response_model=AnalyticsProviderResponse)
async def get_providers_analytics(
    workspace_id: Optional[uuid.UUID] = Query(None),
    project_id: Optional[uuid.UUID] = Query(None),
    task_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AnalyticsProviderResponse:
    """
    Retrieve operational usage and reliability metrics grouped by LLM provider.
    """
    ws_id = await _resolve_user_workspace(user, workspace_id, session)
    filters = _build_filter_dict(project_id, task_id, None, None, status, start_date, end_date)
    obs_service = ObservabilityService(session)
    return await obs_service.get_providers_analytics(ws_id, filters)


@router.get("/latency", response_model=AnalyticsLatencyResponse)
async def get_latency_analytics(
    workspace_id: Optional[uuid.UUID] = Query(None),
    project_id: Optional[uuid.UUID] = Query(None),
    task_id: Optional[uuid.UUID] = Query(None),
    model: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AnalyticsLatencyResponse:
    """
    Retrieve overall and stage-by-stage latency distributions (average, p50, p95).
    """
    ws_id = await _resolve_user_workspace(user, workspace_id, session)
    filters = _build_filter_dict(project_id, task_id, model, provider, None, start_date, end_date)
    obs_service = ObservabilityService(session)
    return await obs_service.get_latency_analytics(ws_id, filters)


@router.get("/evaluations", response_model=AnalyticsEvaluationResponse)
async def get_evaluations_analytics(
    workspace_id: Optional[uuid.UUID] = Query(None),
    project_id: Optional[uuid.UUID] = Query(None),
    task_id: Optional[uuid.UUID] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AnalyticsEvaluationResponse:
    """
    Retrieve verification engine statistics (passed, warnings, failures, revisions).
    """
    ws_id = await _resolve_user_workspace(user, workspace_id, session)
    filters = _build_filter_dict(project_id, task_id, None, None, None, start_date, end_date)
    obs_service = ObservabilityService(session)
    return await obs_service.get_evaluations_analytics(ws_id, filters)


@admin_router.post("/cleanup", response_model=ObservabilityCleanupResponse)
async def cleanup_observability_data(
    workspace_id: Optional[uuid.UUID] = Query(None),
    retention_days: Optional[int] = Query(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ObservabilityCleanupResponse:
    """
    Cleans up telemetry, trace events, and usage records older than retention policy.
    Enforces workspace isolation and never deletes Tasks, Runs, Documents, or Evaluation records.
    """
    ws_id = await _resolve_user_workspace(user, workspace_id, session)
    obs_service = ObservabilityService(session)
    return await obs_service.cleanup_retention(ws_id, retention_days=retention_days)
