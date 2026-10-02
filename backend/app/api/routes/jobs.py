"""
API routes for Durable Background Job System.
"""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.jobs.schemas import (
    JobCreateRequest,
    JobEventListResponse,
    JobListResponse,
    JobResponse,
    JobStatsResponse,
)
from backend.app.services.jobs.service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


def get_job_service(session: AsyncSession = Depends(get_db)) -> JobService:
    return JobService(session=session)


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_job(
    request: JobCreateRequest,
    workspace_id: Optional[UUID] = Query(None, description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: JobService = Depends(get_job_service),
) -> JobResponse:
    """Enqueues a durable background job."""
    ws_id = workspace_id or user.workspace_id
    job_resp, _ = await service.create_job(
        workspace_id=ws_id,
        request=request,
        user=user,
    )
    return job_resp


@router.get(
    "",
    response_model=JobListResponse,
)
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter by job status"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    parent_job_id: Optional[UUID] = Query(None, description="Filter by parent job ID"),
    created_from: Optional[datetime] = Query(None, description="Created at or after ISO timestamp"),
    created_to: Optional[datetime] = Query(None, description="Created at or before ISO timestamp"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    workspace_id: Optional[UUID] = Query(None, description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: JobService = Depends(get_job_service),
) -> JobListResponse:
    """Lists durable background jobs for the authenticated workspace."""
    ws_id = workspace_id or user.workspace_id
    return await service.list_jobs(
        workspace_id=ws_id,
        job_type=job_type,
        status=status,
        project_id=project_id,
        parent_job_id=parent_job_id,
        created_from=created_from,
        created_to=created_to,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/operations/stats",
    response_model=JobStatsResponse,
)
async def get_job_stats(
    workspace_id: Optional[UUID] = Query(None, description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: JobService = Depends(get_job_service),
) -> JobStatsResponse:
    """Returns operational queue health metrics."""
    ws_id = workspace_id or user.workspace_id
    return await service.get_stats(workspace_id=ws_id)


@router.get(
    "/{job_id}",
    response_model=JobResponse,
)
async def get_job(
    job_id: UUID,
    workspace_id: Optional[UUID] = Query(None, description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: JobService = Depends(get_job_service),
) -> JobResponse:
    """Retrieves full status, attempts, lease, and result details for a specific job."""
    ws_id = workspace_id or user.workspace_id
    return await service.get_job(job_id=job_id, workspace_id=ws_id)


@router.post(
    "/{job_id}/cancel",
    response_model=JobResponse,
)
async def cancel_job(
    job_id: UUID,
    reason: Optional[str] = Query(None, description="Optional cancellation reason"),
    workspace_id: Optional[UUID] = Query(None, description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: JobService = Depends(get_job_service),
) -> JobResponse:
    """Requests cooperative cancellation of a background job."""
    ws_id = workspace_id or user.workspace_id
    return await service.cancel_job(
        job_id=job_id,
        workspace_id=ws_id,
        user=user,
        reason=reason,
    )


@router.post(
    "/{job_id}/retry",
    response_model=JobResponse,
)
async def retry_job(
    job_id: UUID,
    workspace_id: Optional[UUID] = Query(None, description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: JobService = Depends(get_job_service),
) -> JobResponse:
    """Manually re-enqueues a failed or cancelled background job."""
    ws_id = workspace_id or user.workspace_id
    return await service.retry_job(
        job_id=job_id,
        workspace_id=ws_id,
        user=user,
    )


@router.get(
    "/{job_id}/events",
    response_model=JobEventListResponse,
)
async def list_job_events(
    job_id: UUID,
    workspace_id: Optional[UUID] = Query(None, description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: JobService = Depends(get_job_service),
) -> JobEventListResponse:
    """Returns chronological audit event history for a job."""
    ws_id = workspace_id or user.workspace_id
    return await service.list_job_events(job_id=job_id, workspace_id=ws_id)
