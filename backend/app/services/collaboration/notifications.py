"""
Collaboration Notification Dispatcher for Step 39: Collaboration.
Integrates with Step 25 NotificationService to notify users for mentions, assignments, and approvals.
"""
from datetime import datetime, timezone
import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.notifications.service import NotificationService

logger = logging.getLogger(__name__)


class CollaborationNotificationService:
    """Dispatches sanitized collaboration notifications with storm prevention."""

    def __init__(self, session: AsyncSession):
        self.db = session
        self.notif_service = NotificationService(session)

    async def notify_mention(
        self,
        workspace_id: str,
        mentioned_user_id: str,
        author_id: str,
        resource_type: str,
        resource_id: str,
        session_id: str,
    ) -> None:
        """Notifies a user that they were mentioned in a collaboration comment."""
        try:
            ws_uuid = UUID(workspace_id) if isinstance(workspace_id, str) else workspace_id
            user_uuid = UUID(mentioned_user_id) if isinstance(mentioned_user_id, str) else mentioned_user_id
            await self.notif_service.create_notification(
                workspace_id=ws_uuid,
                user_id=user_uuid,
                event_type="collaboration.mention",
                title="New mention in collaboration workspace",
                body=f"You were mentioned in a discussion regarding {resource_type} '{resource_id}'.",
                metadata={
                    "session_id": session_id,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "author_id": author_id,
                },
            )
        except Exception as e:
            logger.warning("Failed to dispatch collaboration mention notification: %s", e)

    async def notify_assignment(
        self,
        workspace_id: str,
        assigned_to: str,
        assigned_by: str,
        assignment_type: str,
        resource_type: str,
        resource_id: str,
        session_id: str,
    ) -> None:
        """Notifies a user of a new review or approval assignment."""
        try:
            ws_uuid = UUID(workspace_id) if isinstance(workspace_id, str) else workspace_id
            user_uuid = UUID(assigned_to) if isinstance(assigned_to, str) else assigned_to
            await self.notif_service.create_notification(
                workspace_id=ws_uuid,
                user_id=user_uuid,
                event_type="collaboration.assignment",
                title=f"New collaboration assignment: {assignment_type}",
                body=f"You have been assigned a {assignment_type} task for {resource_type} '{resource_id}'.",
                metadata={
                    "session_id": session_id,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "assigned_by": assigned_by,
                    "assignment_type": assignment_type,
                },
            )
        except Exception as e:
            logger.warning("Failed to dispatch collaboration assignment notification: %s", e)

    async def notify_approval_requested(
        self,
        workspace_id: str,
        reviewer_ids: List[str],
        resource_type: str,
        resource_id: str,
        session_id: str,
    ) -> None:
        """Notifies designated reviewers that their approval is requested."""
        for uid in reviewer_ids:
            try:
                ws_uuid = UUID(workspace_id) if isinstance(workspace_id, str) else workspace_id
                user_uuid = UUID(uid) if isinstance(uid, str) else uid
                await self.notif_service.create_notification(
                    workspace_id=ws_uuid,
                    user_id=user_uuid,
                    event_type="collaboration.approval_request",
                    title="Collaboration approval requested",
                    body=f"Your review and approval are requested for {resource_type} '{resource_id}'.",
                    metadata={
                        "session_id": session_id,
                        "resource_type": resource_type,
                        "resource_id": resource_id,
                    },
                )
            except Exception as e:
                logger.warning("Failed to dispatch approval request notification for user %s: %s", uid, e)
