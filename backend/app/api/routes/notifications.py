"""
REST API endpoints for User In-App Notifications (Step 18).
"""
import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.hitl.notifications import NotificationService
from backend.app.services.hitl.schemas import NotificationResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


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


@router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(False, description="Filter for unread notifications only"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    List in-app notifications for the authenticated user in the current workspace.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    notifications = await NotificationService.list_notifications(
        session=db,
        workspace_id=ws_id,
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
    )
    return [NotificationResponse.model_validate(n) for n in notifications]


@router.post("/{notification_id}/read", response_model=dict)
async def mark_notification_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark a specific notification as read.
    """
    updated = await NotificationService.mark_as_read(
        session=db,
        notification_id=notification_id,
        user_id=current_user.id,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification '{notification_id}' not found or not owned by user.",
        )
    return {"status": "success", "id": str(notification_id), "read": True}


@router.post("/read-all", response_model=dict)
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Mark all unread notifications for the user as read.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    count = await NotificationService.mark_all_as_read(
        session=db,
        workspace_id=ws_id,
        user_id=current_user.id,
    )
    return {"status": "success", "count": count}
