"""
Repository for Step 25 Notifications, Deliveries, Webhook Endpoints, and Preferences.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select, and_, or_, func, desc, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.notification import (
    Notification,
    NotificationDelivery,
    WebhookEndpoint,
    NotificationPreference,
)
from backend.app.services.notifications.constants import (
    NotificationStatus,
    DeliveryStatus,
)


class NotificationRepository:
    """Persistence operations for notifications and external deliveries."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # -------------------------------------------------------------------------
    # Notification CRUD & Queries
    # -------------------------------------------------------------------------

    async def create_notification(
        self,
        workspace_id: UUID,
        event_type: str,
        title: str,
        body: str,
        severity: str = "info",
        status: str = "unread",
        project_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        now = datetime.now(timezone.utc)
        notification = Notification(
            workspace_id=workspace_id,
            project_id=project_id,
            user_id=user_id,
            event_type=event_type,
            title=title,
            body=body,
            severity=severity,
            status=status,
            source_type=source_type,
            source_id=source_id,
            metadata_json=metadata_json or {},
            created_at=now,
            updated_at=now,
        )
        self.session.add(notification)
        await self.session.flush()
        return notification

    async def get_by_id(
        self,
        notification_id: UUID,
        workspace_id: Optional[UUID] = None,
    ) -> Optional[Notification]:
        stmt = select(Notification).where(Notification.id == notification_id)
        if workspace_id:
            stmt = stmt.where(Notification.workspace_id == workspace_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_notifications(
        self,
        workspace_id: UUID,
        user_id: Optional[UUID] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
        source_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Notification], int]:
        filters = [Notification.workspace_id == workspace_id]
        if user_id:
            filters.append(or_(Notification.user_id == user_id, Notification.user_id == None))
        if status and status != "all":
            filters.append(Notification.status == status)
        if severity and severity != "all":
            filters.append(Notification.severity == severity)
        if event_type and event_type != "all":
            filters.append(Notification.event_type == event_type)
        if source_type and source_type != "all":
            filters.append(Notification.source_type == source_type)

        count_stmt = select(func.count(Notification.id)).where(and_(*filters))
        count_res = await self.session.execute(count_stmt)
        total = count_res.scalar() or 0

        stmt = (
            select(Notification)
            .where(and_(*filters))
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all()), total

    async def get_unread_count(
        self,
        workspace_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> int:
        filters = [
            Notification.workspace_id == workspace_id,
            Notification.status == NotificationStatus.UNREAD.value,
        ]
        if user_id:
            filters.append(or_(Notification.user_id == user_id, Notification.user_id == None))
        stmt = select(func.count(Notification.id)).where(and_(*filters))
        res = await self.session.execute(stmt)
        return res.scalar() or 0

    async def mark_as_read(
        self,
        notification_id: UUID,
        workspace_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> Optional[Notification]:
        notif = await self.get_by_id(notification_id, workspace_id)
        if not notif:
            return None
        now = datetime.now(timezone.utc)
        notif.status = NotificationStatus.READ.value
        notif.read_at = now
        notif.updated_at = now
        await self.session.flush()
        return notif

    async def mark_all_as_read(
        self,
        workspace_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> int:
        now = datetime.now(timezone.utc)
        filters = [
            Notification.workspace_id == workspace_id,
            Notification.status == NotificationStatus.UNREAD.value,
        ]
        if user_id:
            filters.append(or_(Notification.user_id == user_id, Notification.user_id == None))

        stmt = (
            update(Notification)
            .where(and_(*filters))
            .values(
                status=NotificationStatus.READ.value,
                read_at=now,
                updated_at=now,
            )
        )
        res = await self.session.execute(stmt)
        return res.rowcount

    async def archive_notification(
        self,
        notification_id: UUID,
        workspace_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> Optional[Notification]:
        notif = await self.get_by_id(notification_id, workspace_id)
        if not notif:
            return None
        now = datetime.now(timezone.utc)
        notif.status = NotificationStatus.ARCHIVED.value
        notif.updated_at = now
        await self.session.flush()
        return notif

    # -------------------------------------------------------------------------
    # Webhook Endpoints
    # -------------------------------------------------------------------------

    async def create_webhook_endpoint(
        self,
        workspace_id: UUID,
        name: str,
        url: str,
        secret_reference: str,
        subscribed_events: Optional[List[str]] = None,
        active: bool = True,
    ) -> WebhookEndpoint:
        ep = WebhookEndpoint(
            workspace_id=workspace_id,
            name=name,
            url=url,
            secret_reference=secret_reference,
            subscribed_events=subscribed_events or ["*"],
            active=active,
        )
        self.session.add(ep)
        await self.session.flush()
        return ep

    async def get_webhook_endpoint(
        self,
        endpoint_id: UUID,
        workspace_id: UUID,
    ) -> Optional[WebhookEndpoint]:
        stmt = select(WebhookEndpoint).where(
            WebhookEndpoint.id == endpoint_id,
            WebhookEndpoint.workspace_id == workspace_id,
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_webhook_endpoints(self, workspace_id: UUID) -> List[WebhookEndpoint]:
        stmt = (
            select(WebhookEndpoint)
            .where(WebhookEndpoint.workspace_id == workspace_id)
            .order_by(WebhookEndpoint.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def update_webhook_endpoint(
        self,
        endpoint_id: UUID,
        workspace_id: UUID,
        name: Optional[str] = None,
        url: Optional[str] = None,
        active: Optional[bool] = None,
        subscribed_events: Optional[List[str]] = None,
    ) -> Optional[WebhookEndpoint]:
        ep = await self.get_webhook_endpoint(endpoint_id, workspace_id)
        if not ep:
            return None
        if name is not None:
            ep.name = name
        if url is not None:
            ep.url = url
        if active is not None:
            ep.active = active
        if subscribed_events is not None:
            ep.subscribed_events = subscribed_events
        ep.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return ep

    async def delete_webhook_endpoint(
        self,
        endpoint_id: UUID,
        workspace_id: UUID,
    ) -> bool:
        ep = await self.get_webhook_endpoint(endpoint_id, workspace_id)
        if not ep:
            return False
        await self.session.delete(ep)
        await self.session.flush()
        return True

    async def rotate_webhook_secret(
        self,
        endpoint_id: UUID,
        workspace_id: UUID,
        new_secret: str,
    ) -> Optional[WebhookEndpoint]:
        ep = await self.get_webhook_endpoint(endpoint_id, workspace_id)
        if not ep:
            return None
        ep.secret_reference = new_secret
        ep.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return ep

    async def get_active_endpoints_for_event(
        self,
        workspace_id: UUID,
        event_type: str,
    ) -> List[WebhookEndpoint]:
        stmt = select(WebhookEndpoint).where(
            WebhookEndpoint.workspace_id == workspace_id,
            WebhookEndpoint.active == True,
        )
        res = await self.session.execute(stmt)
        all_active = list(res.scalars().all())
        # Filter for endpoints subscribed to this event or "*"
        return [
            ep for ep in all_active
            if "*" in ep.subscribed_events or event_type in ep.subscribed_events
        ]

    # -------------------------------------------------------------------------
    # Notification Deliveries
    # -------------------------------------------------------------------------

    async def create_delivery(
        self,
        notification_id: UUID,
        workspace_id: UUID,
        channel: str,
        destination: str,
        max_attempts: int = 3,
    ) -> NotificationDelivery:
        # Check idempotency: if delivery already queued or sent for this notification + channel + destination
        existing_stmt = select(NotificationDelivery).where(
            NotificationDelivery.notification_id == notification_id,
            NotificationDelivery.channel == channel,
            NotificationDelivery.destination == destination,
        )
        existing = (await self.session.execute(existing_stmt)).scalar_one_or_none()
        if existing:
            return existing

        now = datetime.now(timezone.utc)
        delivery = NotificationDelivery(
            notification_id=notification_id,
            workspace_id=workspace_id,
            channel=channel,
            destination=destination,
            status=DeliveryStatus.QUEUED.value,
            attempt_count=0,
            max_attempts=max_attempts,
            scheduled_at=now,
            created_at=now,
            updated_at=now,
        )
        self.session.add(delivery)
        await self.session.flush()
        return delivery

    async def get_delivery(
        self,
        delivery_id: UUID,
        workspace_id: UUID,
    ) -> Optional[NotificationDelivery]:
        stmt = select(NotificationDelivery).where(
            NotificationDelivery.id == delivery_id,
            NotificationDelivery.workspace_id == workspace_id,
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_deliveries(
        self,
        workspace_id: UUID,
        notification_id: Optional[UUID] = None,
        channel: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[NotificationDelivery], int]:
        filters = [NotificationDelivery.workspace_id == workspace_id]
        if notification_id:
            filters.append(NotificationDelivery.notification_id == notification_id)
        if channel and channel != "all":
            filters.append(NotificationDelivery.channel == channel)
        if status and status != "all":
            filters.append(NotificationDelivery.status == status)

        count_stmt = select(func.count(NotificationDelivery.id)).where(and_(*filters))
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = (
            select(NotificationDelivery)
            .where(and_(*filters))
            .order_by(NotificationDelivery.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all()), total

    # -------------------------------------------------------------------------
    # Notification Preferences
    # -------------------------------------------------------------------------

    async def get_preferences(
        self,
        workspace_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> List[NotificationPreference]:
        stmt = select(NotificationPreference).where(
            NotificationPreference.workspace_id == workspace_id,
            NotificationPreference.user_id == user_id,
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def upsert_preference(
        self,
        workspace_id: UUID,
        user_id: Optional[UUID],
        event_type: str,
        channel: str,
        enabled: bool,
    ) -> NotificationPreference:
        stmt = select(NotificationPreference).where(
            NotificationPreference.workspace_id == workspace_id,
            NotificationPreference.user_id == user_id,
            NotificationPreference.event_type == event_type,
            NotificationPreference.channel == channel,
        )
        pref = (await self.session.execute(stmt)).scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if pref:
            pref.enabled = enabled
            pref.updated_at = now
        else:
            pref = NotificationPreference(
                workspace_id=workspace_id,
                user_id=user_id,
                event_type=event_type,
                channel=channel,
                enabled=enabled,
                created_at=now,
                updated_at=now,
            )
            self.session.add(pref)
        await self.session.flush()
        return pref
