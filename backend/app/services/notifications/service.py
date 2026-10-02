"""
NotificationService: Unified notification orchestration, webhook management,
and asynchronous delivery dispatching via Step 24 JobService.
"""
import logging
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.notification import (
    Notification,
    NotificationDelivery,
    WebhookEndpoint,
    NotificationPreference,
)
from backend.app.db.models.user import User
from backend.app.services.notifications.constants import (
    DEFAULT_EVENT_SEVERITY,
    DeliveryChannelType,
    NotificationSeverity,
    NotificationStatus,
)
from backend.app.services.notifications.errors import (
    NotificationNotFoundError,
    NotificationValidationError,
    WebhookEndpointNotFoundError,
)
from backend.app.services.notifications.policies import SSRFValidator
from backend.app.services.notifications.preferences import NotificationPreferenceService
from backend.app.services.notifications.repository import NotificationRepository
from backend.app.services.notifications.sanitizer import NotificationSanitizer

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Central orchestration service managing notification lifecycle,
    preference enforcement, webhook endpoint configuration, and asynchronous delivery dispatch.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = NotificationRepository(session)

    # -------------------------------------------------------------------------
    # Notification Ingestion & Delivery Dispatching
    # -------------------------------------------------------------------------

    async def create_notification(
        self,
        workspace_id: UUID,
        event_type: str,
        title: str,
        body: str,
        severity: Optional[str] = None,
        project_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """
        Creates and stores a notification, evaluates recipient and channel preferences,
        and dispatches external delivery jobs asynchronously through Step 24 JobService.
        """
        # 1. Sanitize incoming content and determine severity
        clean_title = NotificationSanitizer.sanitize_payload(title)
        clean_body = NotificationSanitizer.sanitize_payload(body)
        clean_meta = NotificationSanitizer.sanitize_payload(metadata_json or {})

        eff_severity = severity or DEFAULT_EVENT_SEVERITY.get(event_type, NotificationSeverity.INFO.value)

        # 2. Persist notification entity
        notification = await self.repo.create_notification(
            workspace_id=workspace_id,
            project_id=project_id,
            user_id=user_id,
            event_type=event_type,
            title=str(clean_title),
            body=str(clean_body),
            severity=eff_severity,
            status=NotificationStatus.UNREAD.value,
            source_type=source_type,
            source_id=str(source_id) if source_id else None,
            metadata_json=clean_meta,
        )

        # 3. In-App Channel Delivery
        in_app_enabled = await NotificationPreferenceService.is_channel_enabled(
            session=self.session,
            workspace_id=workspace_id,
            event_type=event_type,
            channel=DeliveryChannelType.IN_APP.value,
            user_id=user_id,
        )
        if in_app_enabled:
            destination = str(user_id) if user_id else "workspace"
            await self.repo.create_delivery(
                notification_id=notification.id,
                workspace_id=workspace_id,
                channel=DeliveryChannelType.IN_APP.value,
                destination=destination,
            )

        # 4. Webhook Channel Delivery Dispatch
        webhook_enabled = await NotificationPreferenceService.is_channel_enabled(
            session=self.session,
            workspace_id=workspace_id,
            event_type=event_type,
            channel=DeliveryChannelType.WEBHOOK.value,
            user_id=user_id,
        )
        if webhook_enabled:
            endpoints = await self.repo.get_active_endpoints_for_event(workspace_id, event_type)
            for ep in endpoints:
                delivery = await self.repo.create_delivery(
                    notification_id=notification.id,
                    workspace_id=workspace_id,
                    channel=DeliveryChannelType.WEBHOOK.value,
                    destination=ep.url,
                )
                await self._enqueue_delivery_job(delivery)

        # 5. Email Channel Delivery Dispatch
        email_enabled = await NotificationPreferenceService.is_channel_enabled(
            session=self.session,
            workspace_id=workspace_id,
            event_type=event_type,
            channel=DeliveryChannelType.EMAIL.value,
            user_id=user_id,
        )
        if email_enabled and user_id:
            user = await self.session.get(User, user_id)
            if user and getattr(user, "email", None):
                delivery = await self.repo.create_delivery(
                    notification_id=notification.id,
                    workspace_id=workspace_id,
                    channel=DeliveryChannelType.EMAIL.value,
                    destination=user.email,
                )
                await self._enqueue_delivery_job(delivery)

        await self.session.commit()
        return notification

    async def _enqueue_delivery_job(self, delivery: NotificationDelivery) -> None:
        """
        Enqueues an asynchronous delivery execution job via Step 24 JobService.
        """
        try:
            from backend.app.services.jobs.service import JobService
            from backend.app.services.jobs.schemas import JobCreateRequest
            from backend.app.services.jobs.constants import JobType, JobPriority

            job_service = JobService(self.session)
            idempotency_key = f"notif_del_{delivery.id}"

            await job_service.create_job(
                workspace_id=delivery.workspace_id,
                request=JobCreateRequest(
                    job_type=JobType.NOTIFICATION_DELIVERY,
                    priority=JobPriority.HIGH if delivery.channel == "webhook" else JobPriority.NORMAL,
                    payload={
                        "delivery_id": str(delivery.id),
                        "notification_id": str(delivery.notification_id),
                        "workspace_id": str(delivery.workspace_id),
                        "channel": delivery.channel,
                        "destination": delivery.destination,
                    },
                    idempotency_key=idempotency_key,
                ),
            )
        except Exception as e:
            logger.warning(f"[NotificationService] Failed to enqueue async delivery job for {delivery.id}: {e}")

    # -------------------------------------------------------------------------
    # Notification In-App Read/Archive API Operations
    # -------------------------------------------------------------------------

    async def get_notification(self, notification_id: UUID, workspace_id: UUID) -> Notification:
        notif = await self.repo.get_by_id(notification_id, workspace_id)
        if not notif:
            raise NotificationNotFoundError(str(notification_id))
        return notif

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
        return await self.repo.list_notifications(
            workspace_id=workspace_id,
            user_id=user_id,
            status=status,
            severity=severity,
            event_type=event_type,
            source_type=source_type,
            limit=limit,
            offset=offset,
        )

    async def get_unread_count(self, workspace_id: UUID, user_id: Optional[UUID] = None) -> int:
        return await self.repo.get_unread_count(workspace_id=workspace_id, user_id=user_id)

    async def mark_as_read(
        self,
        notification_id: UUID,
        workspace_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> Notification:
        notif = await self.repo.mark_as_read(notification_id, workspace_id, user_id)
        if not notif:
            raise NotificationNotFoundError(str(notification_id))
        await self.session.commit()
        return notif

    async def mark_all_as_read(self, workspace_id: UUID, user_id: Optional[UUID] = None) -> int:
        count = await self.repo.mark_all_as_read(workspace_id, user_id)
        await self.session.commit()
        return count

    async def archive_notification(
        self,
        notification_id: UUID,
        workspace_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> Notification:
        notif = await self.repo.archive_notification(notification_id, workspace_id, user_id)
        if not notif:
            raise NotificationNotFoundError(str(notification_id))
        await self.session.commit()
        return notif

    # -------------------------------------------------------------------------
    # Webhook Management
    # -------------------------------------------------------------------------

    async def create_webhook_endpoint(
        self,
        workspace_id: UUID,
        name: str,
        url: str,
        subscribed_events: Optional[List[str]] = None,
        active: bool = True,
    ) -> Tuple[WebhookEndpoint, str]:
        """
        Creates a webhook destination endpoint, generating a secure 32-byte signing secret.
        Returns (endpoint, secret). The secret is only returned once upon creation.
        """
        SSRFValidator.validate_url(url)
        secret = secrets.token_hex(32)

        ep = await self.repo.create_webhook_endpoint(
            workspace_id=workspace_id,
            name=name,
            url=url,
            secret_reference=secret,
            subscribed_events=subscribed_events or ["*"],
            active=active,
        )
        await self.session.commit()
        return ep, secret

    async def get_webhook_endpoint(self, endpoint_id: UUID, workspace_id: UUID) -> WebhookEndpoint:
        ep = await self.repo.get_webhook_endpoint(endpoint_id, workspace_id)
        if not ep:
            raise WebhookEndpointNotFoundError(str(endpoint_id))
        return ep

    async def list_webhook_endpoints(self, workspace_id: UUID) -> List[WebhookEndpoint]:
        return await self.repo.list_webhook_endpoints(workspace_id)

    async def update_webhook_endpoint(
        self,
        endpoint_id: UUID,
        workspace_id: UUID,
        name: Optional[str] = None,
        url: Optional[str] = None,
        active: Optional[bool] = None,
        subscribed_events: Optional[List[str]] = None,
    ) -> WebhookEndpoint:
        if url:
            SSRFValidator.validate_url(url)
        ep = await self.repo.update_webhook_endpoint(
            endpoint_id=endpoint_id,
            workspace_id=workspace_id,
            name=name,
            url=url,
            active=active,
            subscribed_events=subscribed_events,
        )
        if not ep:
            raise WebhookEndpointNotFoundError(str(endpoint_id))
        await self.session.commit()
        return ep

    async def delete_webhook_endpoint(self, endpoint_id: UUID, workspace_id: UUID) -> bool:
        success = await self.repo.delete_webhook_endpoint(endpoint_id, workspace_id)
        if not success:
            raise WebhookEndpointNotFoundError(str(endpoint_id))
        await self.session.commit()
        return True

    async def rotate_webhook_secret(self, endpoint_id: UUID, workspace_id: UUID) -> Tuple[WebhookEndpoint, str]:
        new_secret = secrets.token_hex(32)
        ep = await self.repo.rotate_webhook_secret(endpoint_id, workspace_id, new_secret)
        if not ep:
            raise WebhookEndpointNotFoundError(str(endpoint_id))
        await self.session.commit()
        return ep, new_secret

    async def send_test_webhook(self, endpoint_id: UUID, workspace_id: UUID) -> Dict[str, Any]:
        """
        Sends a safe synthetic test payload to the configured webhook endpoint.
        Never sends live production execution data.
        """
        ep = await self.get_webhook_endpoint(endpoint_id, workspace_id)
        from backend.app.services.notifications.channels import WebhookDeliveryChannel

        channel = WebhookDeliveryChannel()
        synthetic_meta = {
            "test_mode": True,
            "ping": "pong",
            "environment": "test",
        }

        res = await channel.send(
            destination=ep.url,
            title="Webhook Endpoint Test Verification",
            body="Synthetic test event confirming secure webhook delivery and HMAC verification.",
            event_type="webhook.test",
            workspace_id=str(workspace_id),
            source_type="test",
            source_id="synthetic",
            metadata=synthetic_meta,
            secret=ep.secret_reference,
        )

        if res.success:
            ep.last_success_at = datetime.now(timezone.utc)
        else:
            ep.last_failure_at = datetime.now(timezone.utc)
        await self.session.commit()

        return {
            "success": res.success,
            "status_code": res.status_code,
            "error_message": res.error_message,
            "latency_ms": res.latency_ms,
            "endpoint_id": str(ep.id),
        }

    # -------------------------------------------------------------------------
    # Deliveries & Preferences
    # -------------------------------------------------------------------------

    async def list_deliveries(
        self,
        workspace_id: UUID,
        notification_id: Optional[UUID] = None,
        channel: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[NotificationDelivery], int]:
        return await self.repo.list_deliveries(
            workspace_id=workspace_id,
            notification_id=notification_id,
            channel=channel,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def get_delivery(self, delivery_id: UUID, workspace_id: UUID) -> NotificationDelivery:
        deliv = await self.repo.get_delivery(delivery_id, workspace_id)
        if not deliv:
            raise NotificationNotFoundError(f"Delivery '{delivery_id}' not found.")
        return deliv

    async def get_preferences(
        self,
        workspace_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> List[NotificationPreference]:
        return await self.repo.get_preferences(workspace_id=workspace_id, user_id=user_id)

    async def update_preferences(
        self,
        workspace_id: UUID,
        preferences: List[Dict[str, Any]],
        user_id: Optional[UUID] = None,
    ) -> List[NotificationPreference]:
        results = []
        for p in preferences:
            event_type = p.get("event_type", "*")
            channel = p.get("channel", DeliveryChannelType.IN_APP.value)
            enabled = bool(p.get("enabled", True))
            pref = await self.repo.upsert_preference(
                workspace_id=workspace_id,
                user_id=user_id,
                event_type=event_type,
                channel=channel,
                enabled=enabled,
            )
            results.append(pref)
        await self.session.commit()
        return results
