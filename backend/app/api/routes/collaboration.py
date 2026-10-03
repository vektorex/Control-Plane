"""
REST and Real-Time SSE API routes for Step 39:
MULTI-USER COLLABORATION, SHARED AI WORKSPACES & REAL-TIME CO-EXECUTION LAYER.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.events.stream import EventStreamService
from backend.app.services.collaboration.exceptions import (
    AnnotationNotFoundError,
    AssignmentNotFoundError,
    CoExecutionError,
    CollaborationException,
    CommentNotFoundError,
    ConflictError,
    LockConflictError,
    ParticipantNotFoundError,
    SessionNotFoundError,
    UnauthorizedSessionAccessError,
)
from backend.app.services.collaboration.schemas import (
    CoExecutionInitiateRequest,
    CoExecutionSessionResponse,
    CollaborationActivityResponse,
    CollaborationAnnotationCreate,
    CollaborationAnnotationResponse,
    CollaborationAnnotationUpdate,
    CollaborationAssignmentCreate,
    CollaborationAssignmentResponse,
    CollaborationAssignmentUpdate,
    CollaborationCommentCreate,
    CollaborationCommentResponse,
    CollaborationCommentUpdate,
    CollaborationDecisionCreate,
    CollaborationDecisionResponse,
    CollaborationLockAcquireRequest,
    CollaborationLockResponse,
    CollaborationMentionCreateRequest,
    CollaborationParticipantResponse,
    CollaborationSessionCreate,
    CollaborationSessionJoinRequest,
    CollaborationSessionResponse,
    CollaborationSessionUpdate,
    CollaborativeStateResponse,
    CollaborativeStateUpdateRequest,
    PresenceHeartbeatRequest,
    PresenceStateResponse,
)
from backend.app.services.collaboration.service import CollaborationService

router = APIRouter(prefix="/collaboration", tags=["Collaboration"])


def _handle_collaboration_error(e: Exception) -> None:
    """Translates collaboration domain exceptions to proper HTTP error responses."""
    if isinstance(e, ConflictError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": e.message,
                "current_version": e.current_version,
                "expected_version": e.expected_version,
                "resource_id": e.resource_id,
            },
        )
    if isinstance(e, LockConflictError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": e.message, "resource_id": e.resource_id, "locked_by": e.owner_id},
        )
    if isinstance(e, (SessionNotFoundError, CommentNotFoundError, AssignmentNotFoundError, AnnotationNotFoundError, ParticipantNotFoundError)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    if isinstance(e, UnauthorizedSessionAccessError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    if isinstance(e, CoExecutionError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if isinstance(e, CollaborationException):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    raise e


# =============================================================================
# Session Endpoints
# =============================================================================

@router.post("/sessions", response_model=CollaborationSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: CollaborationSessionCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Creates a new collaboration session bound to a platform resource."""
    svc = CollaborationService(session)
    try:
        return await svc.create_session(
            organization_id=str(user.organization_id),
            workspace_id=data.workspace_id,
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            created_by=str(user.id),
            project_id=data.project_id,
            expires_at=data.expires_at,
        )
    except Exception as e:
        _handle_collaboration_error(e)


@router.get("/sessions", response_model=List[CollaborationSessionResponse])
async def list_sessions(
    workspace_id: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Lists collaboration sessions scoped to the authenticated organization."""
    svc = CollaborationService(session)
    try:
        return await svc.list_sessions(
            organization_id=str(user.organization_id),
            workspace_id=workspace_id,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        _handle_collaboration_error(e)


@router.get("/sessions/{id}", response_model=CollaborationSessionResponse)
async def get_session(
    id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Retrieves a single collaboration session."""
    svc = CollaborationService(session)
    try:
        return await svc.get_session(id, user_organization_id=str(user.organization_id))
    except Exception as e:
        _handle_collaboration_error(e)


@router.patch("/sessions/{id}", response_model=CollaborationSessionResponse)
async def update_session(
    id: str,
    data: CollaborationSessionUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Updates session status."""
    svc = CollaborationService(session)
    try:
        return await svc.update_session(
            session_id=id,
            status=data.status,
            user_organization_id=str(user.organization_id),
        )
    except Exception as e:
        _handle_collaboration_error(e)


@router.post("/sessions/{id}/close", response_model=CollaborationSessionResponse)
async def close_session(
    id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Closes session: marks presence offline, terminates realtime stream; audit and history remain."""
    svc = CollaborationService(session)
    try:
        return await svc.close_session(
            session_id=id,
            closed_by=str(user.id),
            user_organization_id=str(user.organization_id),
        )
    except Exception as e:
        _handle_collaboration_error(e)


# =============================================================================
# Participants & Presence Endpoints
# =============================================================================

@router.post("/sessions/{id}/join", response_model=CollaborationParticipantResponse)
async def join_session(
    id: str,
    data: Optional[CollaborationSessionJoinRequest] = None,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Joins a collaboration session with an assigned collaboration role."""
    svc = CollaborationService(session)
    role = data.role if data else "editor"
    try:
        return await svc.join_session(
            session_id=id,
            user_id=str(user.id),
            user_organization_id=str(user.organization_id),
            role=role,
        )
    except Exception as e:
        _handle_collaboration_error(e)


@router.post("/sessions/{id}/heartbeat", response_model=PresenceStateResponse)
async def record_heartbeat(
    id: str,
    data: PresenceHeartbeatRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Sends a lightweight presence heartbeat."""
    svc = CollaborationService(session)
    try:
        return await svc.record_heartbeat(
            session_id=id,
            user_id=str(user.id),
            user_organization_id=str(user.organization_id),
            status=data.status,
            cursor_context=data.cursor_context,
            active_resource=data.active_resource,
        )
    except Exception as e:
        _handle_collaboration_error(e)


@router.post("/sessions/{id}/leave", response_model=CollaborationParticipantResponse)
async def leave_session(
    id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Leaves a collaboration session."""
    svc = CollaborationService(session)
    try:
        return await svc.leave_session(
            session_id=id,
            user_id=str(user.id),
            user_organization_id=str(user.organization_id),
        )
    except Exception as e:
        _handle_collaboration_error(e)


@router.get("/sessions/{id}/participants", response_model=List[CollaborationParticipantResponse])
async def list_participants(
    id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Lists participants of a session."""
    svc = CollaborationService(session)
    try:
        return await svc.list_participants(
            session_id=id,
            user_organization_id=str(user.organization_id),
        )
    except Exception as e:
        _handle_collaboration_error(e)


# =============================================================================
# Activity Feed
# =============================================================================

@router.get("/sessions/{id}/activity", response_model=List[CollaborationActivityResponse])
async def list_activity(
    id: str,
    activity_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Retrieves session activity timeline."""
    svc = CollaborationService(session)
    try:
        return await svc.list_activity(
            session_id=id,
            user_organization_id=str(user.organization_id),
            limit=limit,
            offset=offset,
            activity_type=activity_type,
        )
    except Exception as e:
        _handle_collaboration_error(e)


# =============================================================================
# Comments & Mentions
# =============================================================================

@router.get("/sessions/{id}/comments", response_model=List[CollaborationCommentResponse])
async def list_comments(
    id: str,
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    include_deleted: bool = Query(False),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Lists threaded comments for a session."""
    svc = CollaborationService(session)
    try:
        return await svc.list_comments(
            session_id=id,
            user_organization_id=str(user.organization_id),
            resource_type=resource_type,
            resource_id=resource_id,
            include_deleted=include_deleted,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        _handle_collaboration_error(e)


@router.post("/sessions/{id}/comments", response_model=CollaborationCommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    id: str,
    data: CollaborationCommentCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Adds a sanitized comment with optional threaded parent and @mentions."""
    svc = CollaborationService(session)
    try:
        return await svc.add_comment(
            session_id=id,
            author_id=str(user.id),
            user_organization_id=str(user.organization_id),
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            body=data.body,
            parent_comment_id=data.parent_comment_id,
            author_type="user",
        )
    except Exception as e:
        _handle_collaboration_error(e)


@router.patch("/comments/{id}", response_model=CollaborationCommentResponse)
async def update_comment(
    id: str,
    data: CollaborationCommentUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Updates comment content or status (active, resolved)."""
    svc = CollaborationService(session)
    try:
        return await svc.update_comment(
            comment_id=id,
            user_id=str(user.id),
            user_organization_id=str(user.organization_id),
            body=data.body,
            status=data.status,
        )
    except Exception as e:
        _handle_collaboration_error(e)


@router.delete("/comments/{id}", response_model=CollaborationCommentResponse)
async def delete_comment(
    id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Soft-deletes a comment preserving audit history."""
    svc = CollaborationService(session)
    try:
        return await svc.delete_comment(
            comment_id=id,
            user_id=str(user.id),
            user_organization_id=str(user.organization_id),
        )
    except Exception as e:
        _handle_collaboration_error(e)


@router.post("/sessions/{id}/mentions")
async def create_mention(
    id: str,
    data: CollaborationMentionCreateRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Explicitly notifies a mentioned user within an existing comment."""
    svc = CollaborationService(session)
    try:
        sess = await svc.get_session(id, user_organization_id=str(user.organization_id))
        await svc.notifications.notify_mention(
            workspace_id=sess.workspace_id,
            mentioned_user_id=data.user_handle_or_id,
            author_id=str(user.id),
            resource_type=sess.resource_type,
            resource_id=sess.resource_id,
            session_id=id,
        )
        return {"status": "ok", "comment_id": data.comment_id, "mentioned": data.user_handle_or_id}
    except Exception as e:
        _handle_collaboration_error(e)


# =============================================================================
# Assignments
# =============================================================================

@router.get("/sessions/{id}/assignments", response_model=List[CollaborationAssignmentResponse])
async def list_assignments(
    id: str,
    status: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Lists actionable assignments for a session."""
    svc = CollaborationService(session)
    try:
        return await svc.list_assignments(
            session_id=id,
            user_organization_id=str(user.organization_id),
            status=status,
            assigned_to=assigned_to,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        _handle_collaboration_error(e)


@router.post("/sessions/{id}/assignments", response_model=CollaborationAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    id: str,
    data: CollaborationAssignmentCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Creates a new assignment."""
    svc = CollaborationService(session)
    try:
        return await svc.create_assignment(
            session_id=id,
            assigned_by=str(user.id),
            assigned_to=data.assigned_to,
            assignment_type=data.assignment_type,
            user_organization_id=str(user.organization_id),
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            due_at=data.due_at,
        )
    except Exception as e:
        _handle_collaboration_error(e)


@router.patch("/assignments/{id}", response_model=CollaborationAssignmentResponse)
async def update_assignment(
    id: str,
    data: CollaborationAssignmentUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Updates assignment status (accepted, completed, cancelled) or due date."""
    svc = CollaborationService(session)
    try:
        return await svc.update_assignment(
            assignment_id=id,
            user_id=str(user.id),
            user_organization_id=str(user.organization_id),
            status=data.status,
            due_at=data.due_at,
        )
    except Exception as e:
        _handle_collaboration_error(e)


# =============================================================================
# Annotations
# =============================================================================

@router.get("/sessions/{id}/annotations", response_model=List[CollaborationAnnotationResponse])
async def list_annotations(
    id: str,
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    annotation_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Lists targeted annotations for a session."""
    svc = CollaborationService(session)
    try:
        return await svc.list_annotations(
            session_id=id,
            user_organization_id=str(user.organization_id),
            resource_type=resource_type,
            resource_id=resource_id,
            annotation_type=annotation_type,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        _handle_collaboration_error(e)


@router.post("/sessions/{id}/annotations", response_model=CollaborationAnnotationResponse, status_code=status.HTTP_201_CREATED)
async def create_annotation(
    id: str,
    data: CollaborationAnnotationCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Creates a targeted annotation."""
    svc = CollaborationService(session)
    try:
        return await svc.add_annotation(
            session_id=id,
            author_id=str(user.id),
            user_organization_id=str(user.organization_id),
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            annotation_type=data.annotation_type,
            target=data.target,
            content=data.content,
        )
    except Exception as e:
        _handle_collaboration_error(e)


@router.patch("/annotations/{id}", response_model=CollaborationAnnotationResponse)
async def update_annotation(
    id: str,
    data: CollaborationAnnotationUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Updates annotation content or status."""
    svc = CollaborationService(session)
    try:
        return await svc.update_annotation(
            annotation_id=id,
            user_id=str(user.id),
            user_organization_id=str(user.organization_id),
            content=data.content,
            status=data.status,
        )
    except Exception as e:
        _handle_collaboration_error(e)


# =============================================================================
# Shared Decisions
# =============================================================================

@router.get("/sessions/{id}/decisions", response_model=List[CollaborationDecisionResponse])
async def list_decisions(
    id: str,
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Lists collaborative decisions recorded in a session."""
    svc = CollaborationService(session)
    try:
        return await svc.list_decisions(
            session_id=id,
            user_organization_id=str(user.organization_id),
            limit=limit,
        )
    except Exception as e:
        _handle_collaboration_error(e)


@router.post("/sessions/{id}/decisions", response_model=CollaborationDecisionResponse, status_code=status.HTTP_201_CREATED)
async def record_decision(
    id: str,
    data: CollaborationDecisionCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Records a collaborative decision."""
    svc = CollaborationService(session)
    try:
        return await svc.record_decision(
            session_id=id,
            created_by=str(user.id),
            decision_type=data.decision_type,
            decision_data=data.decision,
            user_organization_id=str(user.organization_id),
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            supersedes_id=data.supersedes_id,
        )
    except Exception as e:
        _handle_collaboration_error(e)


# =============================================================================
# Co-Execution & Run Controls
# =============================================================================

@router.post("/sessions/{id}/run", response_model=CoExecutionSessionResponse, status_code=status.HTTP_201_CREATED)
async def initiate_run(
    id: str,
    data: CoExecutionInitiateRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Initiates an AI co-execution run synthesizing approved collaboration context."""
    svc = CollaborationService(session)
    try:
        return await svc.initiate_co_execution(
            session_id=id,
            user_id=str(user.id),
            user_organization_id=str(user.organization_id),
            mode=data.mode,
            task_id=data.task_id,
            workflow_id=data.workflow_id,
            inputs=data.inputs,
            include_comments=data.include_comments,
            include_annotations=data.include_annotations,
            comment_ids=data.comment_ids,
        )
    except Exception as e:
        _handle_collaboration_error(e)


@router.post("/runs/{run_id}/pause", response_model=CoExecutionSessionResponse)
async def pause_run(
    run_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Pauses a collaborative execution run."""
    svc = CollaborationService(session)
    try:
        return await svc.pause_co_execution(
            co_session_id=run_id,
            user_id=str(user.id),
            user_organization_id=str(user.organization_id),
        )
    except Exception as e:
        _handle_collaboration_error(e)


@router.post("/runs/{run_id}/resume", response_model=CoExecutionSessionResponse)
async def resume_run(
    run_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Resumes a paused collaborative execution run."""
    svc = CollaborationService(session)
    try:
        return await svc.resume_co_execution(
            co_session_id=run_id,
            user_id=str(user.id),
            user_organization_id=str(user.organization_id),
        )
    except Exception as e:
        _handle_collaboration_error(e)


@router.post("/runs/{run_id}/cancel", response_model=CoExecutionSessionResponse)
async def cancel_run(
    run_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Cancels a collaborative execution run."""
    svc = CollaborationService(session)
    try:
        return await svc.cancel_co_execution(
            co_session_id=run_id,
            user_id=str(user.id),
            user_organization_id=str(user.organization_id),
        )
    except Exception as e:
        _handle_collaboration_error(e)


# =============================================================================
# Collaborative State, Optimistic Concurrency & Advisory Locks
# =============================================================================

@router.get("/sessions/{id}/state", response_model=Optional[CollaborativeStateResponse])
async def get_state(
    id: str,
    resource_type: str = Query(...),
    resource_id: str = Query(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Retrieves current versioned collaborative state."""
    svc = CollaborationService(session)
    try:
        return await svc.get_state(
            session_id=id,
            resource_type=resource_type,
            resource_id=resource_id,
            user_organization_id=str(user.organization_id),
        )
    except Exception as e:
        _handle_collaboration_error(e)


@router.put("/sessions/{id}/state", response_model=CollaborativeStateResponse)
async def update_state(
    id: str,
    data: CollaborativeStateUpdateRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Updates collaborative state using optimistic concurrency.
    Throws 409 Conflict if expected_version does not match current version.
    """
    svc = CollaborationService(session)
    try:
        return await svc.update_state(
            session_id=id,
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            expected_version=data.expected_version,
            new_state=data.state,
            actor_id=str(user.id),
            user_organization_id=str(user.organization_id),
        )
    except Exception as e:
        _handle_collaboration_error(e)


@router.post("/sessions/{id}/lock", response_model=CollaborationLockResponse)
async def acquire_lock(
    id: str,
    data: CollaborationLockAcquireRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Acquires a short-lived auto-expiring advisory lock for a resource."""
    svc = CollaborationService(session)
    try:
        return await svc.acquire_lock(
            session_id=id,
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            user_id=str(user.id),
            user_organization_id=str(user.organization_id),
            ttl_seconds=data.ttl_seconds,
        )
    except Exception as e:
        _handle_collaboration_error(e)


@router.delete("/sessions/{id}/lock")
async def release_lock(
    id: str,
    resource_type: str = Query(...),
    resource_id: str = Query(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Releases an advisory lock."""
    svc = CollaborationService(session)
    try:
        success = await svc.release_lock(
            session_id=id,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=str(user.id),
            user_organization_id=str(user.organization_id),
        )
        return {"status": "released" if success else "not_held"}
    except Exception as e:
        _handle_collaboration_error(e)


# =============================================================================
# Real-Time SSE Stream (Reuses Step 26 Event Bus)
# =============================================================================

@router.get("/sessions/{id}/events")
async def stream_collaboration_events(
    id: str,
    last_event_id: Optional[str] = Header(None, alias="Last-Event-ID"),
    after: Optional[UUID] = Query(None, description="Event ID to resume streaming from"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Subscribes to live Server-Sent Events (SSE) for a collaboration session.
    Reuses Step 26 Unified Event Bus and PostgreSQL event stream.
    Requires participant authorization; tenant-scoped.
    """
    svc = CollaborationService(session)
    try:
        collab_session = await svc.get_session(id, user_organization_id=str(user.organization_id))
    except Exception as e:
        _handle_collaboration_error(e)

    effective_after = None
    if last_event_id:
        try:
            effective_after = UUID(last_event_id)
        except ValueError:
            pass
    elif after:
        effective_after = after

    generator = EventStreamService.stream_events(
        workspace_id=UUID(collab_session.workspace_id),
        user_id=user.id,
        project_id=UUID(collab_session.project_id) if collab_session.project_id else None,
        event_type_pattern="collaboration.*",
        aggregate_type="collaboration",
        aggregate_id=id,
        last_event_id=effective_after,
    )

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# =============================================================================
# Workspace Summary
# =============================================================================

@router.get("/workspace/summary")
async def get_workspace_collaboration_summary(
    workspace_id: str = Query(...),
    resource_type: str = Query(...),
    resource_id: str = Query(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Summarizes active collaboration context (presence, open comments, pending assignments)."""
    svc = CollaborationService(session)
    try:
        return await svc.workspace.get_workspace_collaboration_summary(
            organization_id=str(user.organization_id),
            workspace_id=workspace_id,
            resource_type=resource_type,
            resource_id=resource_id,
        )
    except Exception as e:
        _handle_collaboration_error(e)
