"""
API endpoints for AI Execution Replay & Debugging Studio (Step 21).

Provides routes for:
- Execution run replay (inspect, dry-run, live replay, step replay)
- Workflow run replay
- Replay listing and inspection
- Replay trace timeline events
- Output comparison (factual diffs)
- Replay cancellation
- Failure diagnostics and error analysis
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.replay.schemas import (
    ReplayMode,
    ReplayRunCreateRequest,
    ReplayStepRequest,
    ReplayRunResponse,
    ReplayListResponse,
    ReplayComparisonResult,
    ReplayEligibility,
    FailureInsights,
)
from backend.app.services.replay.service import ReplayService
from backend.app.services.replay.errors import (
    ReplayError,
    ReplayNotFoundError,
    ReplayEligibilityError,
    ReplayPermissionDeniedError,
)

router = APIRouter(tags=["AI Execution Replay & Debugging"])


def _resolve_workspace_id(
    user: User,
    header_ws_id: Optional[str] = None,
    query_ws_id: Optional[UUID] = None,
) -> UUID:
    """Extracts and verifies active workspace ID for the request."""
    if query_ws_id:
        return query_ws_id
    if header_ws_id:
        try:
            return UUID(header_ws_id)
        except ValueError:
            pass
    if getattr(user, "default_workspace_id", None):
        return user.default_workspace_id
    if getattr(user, "workspaces", None) and len(user.workspaces) > 0:
        return user.workspaces[0].id
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Workspace context could not be resolved. Please specify 'X-Workspace-Id' header.",
    )


# ---------------------------------------------------------------------------
# Run Replay Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/runs/{run_id}/replay/inspect",
    response_model=ReplayRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Inspect historical execution snapshot",
    description="Read-only inspection of the historical execution without any re-execution or side effects.",
)
async def inspect_run_replay(
    run_id: UUID,
    workspace_id: Optional[UUID] = Query(None, alias="workspace_id"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ReplayRunResponse:
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    service = ReplayService()
    try:
        req = ReplayRunCreateRequest(mode=ReplayMode.INSPECT, dry_run=True)
        replay = await service.create_replay(
            run_id=run_id,
            request=req,
            workspace_id=ws_id,
            user=user,
            session=session,
        )
        return ReplayRunResponse.model_validate(replay)
    except ReplayNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ReplayEligibilityError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except ReplayError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/runs/{run_id}/replay/dry-run",
    response_model=ReplayRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate run execution in safe dry-run mode",
    description="Simulate execution without performing any external side-effects (connector writes, tool writes).",
)
async def dry_run_replay(
    run_id: UUID,
    body: Optional[ReplayRunCreateRequest] = None,
    workspace_id: Optional[UUID] = Query(None, alias="workspace_id"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ReplayRunResponse:
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    service = ReplayService()
    req = body or ReplayRunCreateRequest(mode=ReplayMode.DRY_RUN, dry_run=True)
    req.mode = ReplayMode.DRY_RUN
    req.dry_run = True

    try:
        replay = await service.create_replay(
            run_id=run_id,
            request=req,
            workspace_id=ws_id,
            user=user,
            session=session,
        )
        return ReplayRunResponse.model_validate(replay)
    except ReplayNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ReplayEligibilityError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except ReplayError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/runs/{run_id}/replay",
    status_code=status.HTTP_200_OK,
    summary="Replay run execution",
    description="Re-execute eligible AI computation. External side effects remain dry-run by default unless approved.",
)
async def execute_run_replay(
    run_id: UUID,
    body: Optional[ReplayRunCreateRequest] = None,
    mode: Optional[str] = Query("sync", description="Execution mode: sync or async"),
    workspace_id: Optional[UUID] = Query(None, alias="workspace_id"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    service = ReplayService()
    req = body or ReplayRunCreateRequest(mode=ReplayMode.REPLAY, dry_run=True)

    try:
        replay = await service.create_replay(
            run_id=run_id,
            request=req,
            workspace_id=ws_id,
            user=user,
            session=session,
        )
        if mode == "async":
            from fastapi.responses import JSONResponse
            from backend.app.services.jobs.service import JobService
            from backend.app.services.jobs.schemas import JobCreateRequest
            from backend.app.services.jobs.constants import JobType, JobPriority

            job_service = JobService(session)
            job_resp, _ = await job_service.create_job(
                workspace_id=ws_id,
                request=JobCreateRequest(
                    job_type=JobType.REPLAY_RUN,
                    priority=JobPriority.NORMAL,
                    payload={
                        "replay_id": str(replay.id),
                        "run_id": str(run_id),
                        "workspace_id": str(ws_id),
                    },
                    idempotency_key=f"replay_{replay.id}",
                ),
                user_id=user.id,
            )
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "job_id": str(job_resp.id),
                    "status": job_resp.status,
                    "job_type": job_resp.job_type,
                    "created_at": job_resp.created_at.isoformat() if job_resp.created_at else None,
                    "available_at": job_resp.available_at.isoformat() if job_resp.available_at else None,
                    "poll_url": f"/api/jobs/{job_resp.id}",
                    "cancel_url": f"/api/jobs/{job_resp.id}/cancel",
                },
            )
        return ReplayRunResponse.model_validate(replay)
    except ReplayNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ReplayEligibilityError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except ReplayError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/runs/{run_id}/replay/eligibility",
    response_model=ReplayEligibility,
    status_code=status.HTTP_200_OK,
    summary="Check run replay eligibility",
)
async def check_run_eligibility(
    run_id: UUID,
    workspace_id: Optional[UUID] = Query(None, alias="workspace_id"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ReplayEligibility:
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    service = ReplayService()
    try:
        return await service.check_run_eligibility(run_id, ws_id, session)
    except ReplayNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/runs/{run_id}/steps/{step_id}/replay",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Replay an individual execution step safely",
)
async def replay_step(
    run_id: UUID,
    step_id: str,
    body: Optional[ReplayStepRequest] = None,
    workspace_id: Optional[UUID] = Query(None, alias="workspace_id"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    service = ReplayService()
    req = body or ReplayStepRequest(dry_run=True)
    try:
        return await service.replay_step(
            run_id=run_id,
            step_id=step_id,
            request=req,
            workspace_id=ws_id,
            user=user,
            session=session,
        )
    except ReplayNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ReplayError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/runs/{run_id}/failure-insights",
    response_model=FailureInsights,
    status_code=status.HTTP_200_OK,
    summary="Get factual failure diagnostics for a run",
)
async def get_run_failure_insights(
    run_id: UUID,
    workspace_id: Optional[UUID] = Query(None, alias="workspace_id"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> FailureInsights:
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    service = ReplayService()
    try:
        return await service.get_failure_diagnostics(run_id, ws_id, session)
    except ReplayNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# ---------------------------------------------------------------------------
# Workflow Replay Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/workflow-runs/{workflow_run_id}/replay/inspect",
    response_model=ReplayRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Inspect historical workflow run snapshot",
)
async def inspect_workflow_replay(
    workflow_run_id: UUID,
    workspace_id: Optional[UUID] = Query(None, alias="workspace_id"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ReplayRunResponse:
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    service = ReplayService()
    req = ReplayRunCreateRequest(mode=ReplayMode.INSPECT, dry_run=True)
    try:
        replay = await service.create_workflow_replay(
            workflow_run_id=workflow_run_id,
            request=req,
            workspace_id=ws_id,
            user=user,
            session=session,
        )
        return ReplayRunResponse.model_validate(replay)
    except ReplayNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ReplayEligibilityError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except ReplayError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/workflow-runs/{workflow_run_id}/replay/dry-run",
    response_model=ReplayRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate workflow replay in safe dry-run mode",
)
async def dry_run_workflow_replay(
    workflow_run_id: UUID,
    body: Optional[ReplayRunCreateRequest] = None,
    workspace_id: Optional[UUID] = Query(None, alias="workspace_id"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ReplayRunResponse:
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    service = ReplayService()
    req = body or ReplayRunCreateRequest(mode=ReplayMode.DRY_RUN, dry_run=True)
    req.mode = ReplayMode.DRY_RUN
    req.dry_run = True

    try:
        replay = await service.create_workflow_replay(
            workflow_run_id=workflow_run_id,
            request=req,
            workspace_id=ws_id,
            user=user,
            session=session,
        )
        return ReplayRunResponse.model_validate(replay)
    except ReplayNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ReplayEligibilityError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except ReplayError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/workflow-runs/{workflow_run_id}/replay",
    status_code=status.HTTP_200_OK,
    summary="Replay workflow execution",
)
async def execute_workflow_replay(
    workflow_run_id: UUID,
    body: Optional[ReplayRunCreateRequest] = None,
    mode: Optional[str] = Query("sync", description="Execution mode: sync or async"),
    workspace_id: Optional[UUID] = Query(None, alias="workspace_id"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    service = ReplayService()
    req = body or ReplayRunCreateRequest(mode=ReplayMode.REPLAY, dry_run=True)

    try:
        replay = await service.create_workflow_replay(
            workflow_run_id=workflow_run_id,
            request=req,
            workspace_id=ws_id,
            user=user,
            session=session,
        )
        if mode == "async":
            from fastapi.responses import JSONResponse
            from backend.app.services.jobs.service import JobService
            from backend.app.services.jobs.schemas import JobCreateRequest
            from backend.app.services.jobs.constants import JobType, JobPriority

            job_service = JobService(session)
            job_resp, _ = await job_service.create_job(
                workspace_id=ws_id,
                request=JobCreateRequest(
                    job_type=JobType.REPLAY_RUN,
                    priority=JobPriority.NORMAL,
                    payload={
                        "replay_id": str(replay.id),
                        "workflow_run_id": str(workflow_run_id),
                        "workspace_id": str(ws_id),
                    },
                    idempotency_key=f"replay_wf_{replay.id}",
                ),
                user_id=user.id,
            )
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "job_id": str(job_resp.id),
                    "status": job_resp.status,
                    "job_type": job_resp.job_type,
                    "created_at": job_resp.created_at.isoformat() if job_resp.created_at else None,
                    "available_at": job_resp.available_at.isoformat() if job_resp.available_at else None,
                    "poll_url": f"/api/jobs/{job_resp.id}",
                    "cancel_url": f"/api/jobs/{job_resp.id}/cancel",
                },
            )
        return ReplayRunResponse.model_validate(replay)
    except ReplayNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ReplayEligibilityError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except ReplayError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ---------------------------------------------------------------------------
# Replays Management Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/replays",
    response_model=ReplayListResponse,
    status_code=status.HTTP_200_OK,
    summary="List replays for active workspace",
)
async def list_replays(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    mode_filter: Optional[str] = Query(None, alias="mode"),
    original_run_id: Optional[UUID] = Query(None, alias="original_run_id"),
    workflow_run_id: Optional[UUID] = Query(None, alias="workflow_run_id"),
    workspace_id: Optional[UUID] = Query(None, alias="workspace_id"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ReplayListResponse:
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    service = ReplayService()
    replays, total = await service.list_replays(
        workspace_id=ws_id,
        session=session,
        page=page,
        limit=limit,
        status=status_filter,
        mode=mode_filter,
        original_run_id=original_run_id,
        workflow_run_id=workflow_run_id,
    )
    return ReplayListResponse(
        replays=[ReplayRunResponse.model_validate(r) for r in replays],
        total=total,
        page=page,
        limit=limit,
    )


@router.get(
    "/replays/{replay_id}",
    response_model=ReplayRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Get replay execution details",
)
async def get_replay_detail(
    replay_id: UUID,
    workspace_id: Optional[UUID] = Query(None, alias="workspace_id"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ReplayRunResponse:
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    service = ReplayService()
    try:
        replay = await service.get_replay(replay_id, ws_id, session)
        return ReplayRunResponse.model_validate(replay)
    except ReplayNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/replays/{replay_id}/trace",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get timeline trace events for replay",
)
async def get_replay_trace(
    replay_id: UUID,
    workspace_id: Optional[UUID] = Query(None, alias="workspace_id"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    service = ReplayService()
    try:
        return await service.get_replay_trace(replay_id, ws_id, session)
    except ReplayNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/replays/{replay_id}/cancel",
    response_model=ReplayRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel in-flight replay run",
)
async def cancel_replay(
    replay_id: UUID,
    workspace_id: Optional[UUID] = Query(None, alias="workspace_id"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ReplayRunResponse:
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    service = ReplayService()
    try:
        cancelled = await service.cancel_replay(replay_id, ws_id, user, session)
        return ReplayRunResponse.model_validate(cancelled)
    except ReplayNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/replays/{replay_id}/compare",
    response_model=ReplayComparisonResult,
    status_code=status.HTTP_200_OK,
    summary="Get factual diff comparison between original and replay executions",
)
async def compare_replay(
    replay_id: UUID,
    workspace_id: Optional[UUID] = Query(None, alias="workspace_id"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ReplayComparisonResult:
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    service = ReplayService()
    try:
        return await service.compare_replay(replay_id, ws_id, session)
    except ReplayNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
