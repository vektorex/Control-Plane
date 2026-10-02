"""
REST and Server-Sent Events (SSE) endpoints for Step 26: Unified Event Bus.
Exposes live execution streaming, event history queries, and historical replays.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.events.filters import EventFilterValidator
from backend.app.services.events.policies import EventPolicyEngine
from backend.app.services.events.repository import EventRepository
from backend.app.services.events.sanitizer import EventSanitizer
from backend.app.services.events.schemas import (
    EventContract,
    EventReplayResponse,
)
from backend.app.services.events.stream import EventStreamService

events_router = APIRouter(prefix="/events", tags=["Events & Real-Time Bus"])


def _resolve_and_verify_workspace(
    user: User,
    header_ws_id: Optional[str] = None,
    query_ws_id: Optional[UUID] = None,
) -> UUID:
    """
    Resolves the workspace and asserts the authenticated user is a legitimate member.
    Rejects unauthorized access to other workspaces.
    """
    resolved_id = None
    if query_ws_id:
        resolved_id = query_ws_id
    elif header_ws_id:
        try:
            resolved_id = UUID(header_ws_id)
        except ValueError:
            pass

    if not resolved_id:
        if getattr(user, "default_workspace_id", None):
            resolved_id = user.default_workspace_id
        elif getattr(user, "workspaces", None) and len(user.workspaces) > 0:
            resolved_id = user.workspaces[0].id

    if not resolved_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required. Provide 'X-Workspace-Id' header or 'workspace_id' parameter.",
        )

    # Multi-tenant isolation verification
    allowed_ids = []
    if getattr(user, "default_workspace_id", None):
        allowed_ids.append(user.default_workspace_id)
    if getattr(user, "workspaces", None):
        allowed_ids.extend([w.id for w in user.workspaces])

    # Allow if superuser/admin or matched
    is_admin = getattr(user, "is_superuser", False) or getattr(user, "role", "") == "admin"
    if not is_admin and allowed_ids and resolved_id not in allowed_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are not authorized to access events in this workspace.",
        )

    return resolved_id


@events_router.get("/stream", response_class=StreamingResponse)
async def stream_events(
    workspace_id: Optional[UUID] = Query(None, description="Workspace to stream events for"),
    project_id: Optional[UUID] = Query(None, description="Optional project filter"),
    event_type: Optional[str] = Query(None, description="Event type filter e.g. 'job.*' or 'workflow.completed'"),
    aggregate_type: Optional[str] = Query(None, description="Aggregate type filter"),
    aggregate_id: Optional[str] = Query(None, description="Aggregate ID filter"),
    after: Optional[str] = Query(None, description="Cursor or event ID to replay from"),
    last_event_id: Optional[str] = Header(None, alias="Last-Event-ID"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
):
    """
    Server-Sent Events (SSE) real-time stream.
    Emits events matching authorized filters and provides keepalive heartbeats.
    Resumes automatically via Last-Event-ID header or 'after' parameter.
    """
    ws_id = _resolve_and_verify_workspace(user, x_workspace_id, workspace_id)

    # Validate event filter pattern to prevent SQL injection or regex DoS
    cleaned_pattern = None
    if event_type:
        cleaned_pattern = EventFilterValidator.validate_event_type_pattern(event_type)

    effective_after = last_event_id or after

    generator = EventStreamService.create_event_stream(
        workspace_id=ws_id,
        project_id=project_id,
        event_type_pattern=cleaned_pattern,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
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


@events_router.get("", response_model=List[EventContract])
async def list_events(
    workspace_id: Optional[UUID] = Query(None, description="Workspace filter"),
    project_id: Optional[UUID] = Query(None, description="Project filter"),
    event_type: Optional[str] = Query(None, description="Event type or wildcard filter"),
    aggregate_type: Optional[str] = Query(None, description="Aggregate type filter"),
    aggregate_id: Optional[str] = Query(None, description="Aggregate ID filter"),
    correlation_id: Optional[str] = Query(None, description="Correlation trace ID"),
    after: Optional[UUID] = Query(None, description="Pagination cursor after event ID"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Queries historical events with rich multi-tenant filtering.
    """
    ws_id = _resolve_and_verify_workspace(user, x_workspace_id, workspace_id)
    cleaned_pattern = EventFilterValidator.validate_event_type_pattern(event_type) if event_type else None

    repo = EventRepository(session)
    events = await repo.list_events(
        workspace_id=ws_id,
        project_id=project_id,
        event_type_pattern=cleaned_pattern,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        correlation_id=correlation_id,
        after_id=after,
        limit=limit,
    )

    return [EventSanitizer.to_contract(ev) for ev in events]


@events_router.get("/replay", response_model=EventReplayResponse)
async def replay_events(
    after: Optional[UUID] = Query(None, description="Event ID to replay from"),
    event_type: Optional[str] = Query(None, description="Optional event type filter"),
    limit: int = Query(50, ge=1, le=100, description="Max replay batch size"),
    workspace_id: Optional[UUID] = Query(None, description="Workspace ID"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Fetches a bounded batch of chronological events for replay / reconnection.
    """
    ws_id = _resolve_and_verify_workspace(user, x_workspace_id, workspace_id)
    cleaned_pattern = EventFilterValidator.validate_event_type_pattern(event_type) if event_type else None

    repo = EventRepository(session)
    replayed = await repo.replay_events(
        workspace_id=ws_id,
        after_id=after,
        event_type_pattern=cleaned_pattern,
        limit=limit,
    )

    contracts = [EventSanitizer.to_contract(ev) for ev in replayed]
    next_cursor = contracts[-1].id if len(contracts) >= limit else None

    return EventReplayResponse(
        events=contracts,
        has_more=len(contracts) >= limit,
        next_cursor=next_cursor,
        total_count=len(contracts),
    )


@events_router.get("/{event_id}", response_model=EventContract)
async def get_event(
    event_id: UUID,
    workspace_id: Optional[UUID] = Query(None, description="Workspace ID"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Retrieves details for a single event record by ID with workspace authorization.
    """
    ws_id = _resolve_and_verify_workspace(user, x_workspace_id, workspace_id)
    repo = EventRepository(session)
    event = await repo.get_by_id(event_id, workspace_id=ws_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event '{event_id}' not found.",
        )

    return EventSanitizer.to_contract(event)
