"""
Notification abstraction service for Human-in-the-Loop and execution alerts (Step 18).
Supports in-app persistence and extensibility for future webhooks/Slack.
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.hitl import HumanInterventionRequest, Notification
from backend.app.db.models.workspace import Workspace

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Manages user notifications for intervention requests, approvals, and execution alerts.
    """

    @classmethod
    async def create_notification(
        cls,
        session: AsyncSession,
        workspace_id: UUID,
        user_id: UUID,
        type: str,
        title: str,
        message: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
    ) -> Notification:
        notification = Notification(
            workspace_id=workspace_id,
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            reference_type=reference_type,
            reference_id=str(reference_id) if reference_id else None,
            read=False,
            created_at=datetime.now(timezone.utc),
        )
        session.add(notification)
        await session.flush()
        logger.info(f"[NotificationService] Notification '{notification.id}' created for user '{user_id}' ({type})")
        return notification

    @classmethod
    async def list_notifications(
        cls,
        session: AsyncSession,
        workspace_id: UUID,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[Notification]:
        filters = [
            Notification.workspace_id == workspace_id,
            Notification.user_id == user_id,
        ]
        if unread_only:
            filters.append(Notification.read == False)

        stmt = (
            select(Notification)
            .where(and_(*filters))
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def mark_as_read(
        cls,
        session: AsyncSession,
        notification_id: UUID,
        user_id: UUID,
    ) -> bool:
        stmt = (
            update(Notification)
            .where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id,
                )
            )
            .values(read=True)
        )
        res = await session.execute(stmt)
        await session.commit()
        return res.rowcount > 0

    @classmethod
    async def mark_all_as_read(
        cls,
        session: AsyncSession,
        workspace_id: UUID,
        user_id: UUID,
    ) -> int:
        stmt = (
            update(Notification)
            .where(
                and_(
                    Notification.workspace_id == workspace_id,
                    Notification.user_id == user_id,
                    Notification.read == False,
                )
            )
            .values(read=True)
        )
        res = await session.execute(stmt)
        await session.commit()
        return res.rowcount

    @classmethod
    async def notify_approval_required(
        cls,
        session: AsyncSession,
        intervention: HumanInterventionRequest,
    ) -> Optional[Notification]:
        """
        Dispatches notification to assigned user or workspace owner.
        """
        target_user_id = intervention.assigned_to
        if not target_user_id:
            # Fallback to workspace owner
            ws = await session.get(Workspace, intervention.workspace_id)
            if ws and ws.owner_user_id:
                target_user_id = ws.owner_user_id

        if not target_user_id:
            logger.warning(f"[NotificationService] No recipient for intervention {intervention.id}")
            return None

        return await cls.create_notification(
            session=session,
            workspace_id=intervention.workspace_id,
            user_id=target_user_id,
            type="approval_required",
            title=f"Approval Required: {intervention.title}",
            message=f"Action '{intervention.requested_action}' ({intervention.priority} priority) is waiting for human authorization.",
            reference_type="intervention",
            reference_id=str(intervention.id),
        )

    @classmethod
    async def notify_approval_resolved(
        cls,
        session: AsyncSession,
        intervention: HumanInterventionRequest,
        decision: str,
        resolved_by_user_id: UUID,
    ) -> Optional[Notification]:
        """
        Notifies requester that their intervention has been resolved.
        """
        if not intervention.requested_by or intervention.requested_by == resolved_by_user_id:
            return None

        return await cls.create_notification(
            session=session,
            workspace_id=intervention.workspace_id,
            user_id=intervention.requested_by,
            type="approval_resolved",
            title=f"Approval {decision.capitalize()}: {intervention.title}",
            message=f"Intervention request for '{intervention.requested_action}' was marked as {decision}.",
            reference_type="intervention",
            reference_id=str(intervention.id),
        )
