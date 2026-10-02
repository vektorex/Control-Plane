"""
DeliveryDispatcher: Core delivery runner executing channel transmission,
retry backoff scheduling, and telemetry recording.
"""
import asyncio
from datetime import datetime, timezone, timedelta
import logging
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.notification import (
    Notification,
    NotificationDelivery,
    WebhookEndpoint,
)
from backend.app.services.notifications.channels import channel_registry
from backend.app.services.notifications.constants import (
    DeliveryChannelType,
    DeliveryStatus,
)
from backend.app.services.notifications.errors import (
    DeliveryError,
    DeliveryPermanentError,
)
from backend.app.services.notifications.policies import NotificationRateLimiter
from backend.app.services.notifications.retry import DeliveryRetryPolicy

logger = logging.getLogger(__name__)
rate_limiter = NotificationRateLimiter()


class DeliveryDispatcher:
    """
    Executes an individual delivery record asynchronously through the appropriate channel.
    Manages retry state transitions and integrates with Observability traces.
    """

    @classmethod
    async def execute_delivery(
        cls,
        delivery_id: UUID,
        session: AsyncSession,
        cancellation_token: Optional[asyncio.Event] = None,
    ) -> bool:
        """
        Executes transmission for delivery_id. Returns True if successfully sent, False otherwise.
        """
        now = datetime.now(timezone.utc)

        # 1. Load delivery record
        delivery_stmt = select(NotificationDelivery).where(NotificationDelivery.id == delivery_id)
        delivery_res = await session.execute(delivery_stmt)
        delivery = delivery_res.scalar_one_or_none()

        if not delivery:
            logger.warning(f"[DeliveryDispatcher] Delivery {delivery_id} not found.")
            return False

        if delivery.status in (DeliveryStatus.SENT.value, DeliveryStatus.CANCELLED.value):
            return delivery.status == DeliveryStatus.SENT.value

        if cancellation_token and cancellation_token.is_set():
            delivery.status = DeliveryStatus.CANCELLED.value
            delivery.updated_at = now
            await session.commit()
            return False

        # 2. Load associated notification
        notif_stmt = select(Notification).where(Notification.id == delivery.notification_id)
        notif_res = await session.execute(notif_stmt)
        notification = notif_res.scalar_one_or_none()

        if not notification:
            delivery.status = DeliveryStatus.FAILED.value
            delivery.error_code = "NOTIFICATION_NOT_FOUND"
            delivery.error_message = "Parent notification record missing."
            delivery.updated_at = now
            await session.commit()
            return False

        # 3. Rate limiting check
        try:
            rate_limiter.check_and_record(delivery.workspace_id, delivery.channel)
        except Exception as rl_err:
            logger.warning(f"[DeliveryDispatcher] Rate limit exceeded for {delivery.workspace_id}: {rl_err}")
            delivery.status = DeliveryStatus.RETRYING.value
            delivery.error_code = "RATE_LIMIT_EXCEEDED"
            delivery.error_message = str(rl_err)
            delivery.scheduled_at = now + timedelta(seconds=15)
            delivery.updated_at = now
            await session.commit()
            return False

        # 4. Check channel registry
        if not channel_registry.has_channel(delivery.channel):
            delivery.status = DeliveryStatus.FAILED.value
            delivery.error_code = "UNKNOWN_CHANNEL"
            delivery.error_message = f"Channel '{delivery.channel}' is not registered."
            delivery.updated_at = now
            await session.commit()
            return False

        channel = channel_registry.get(delivery.channel)

        # 5. Extract secret if webhook
        secret = None
        webhook_ep = None
        if delivery.channel == DeliveryChannelType.WEBHOOK.value:
            # Look up WebhookEndpoint by url matching destination
            ep_stmt = select(WebhookEndpoint).where(
                WebhookEndpoint.workspace_id == delivery.workspace_id,
                WebhookEndpoint.url == delivery.destination,
            )
            ep_res = await session.execute(ep_stmt)
            webhook_ep = ep_res.scalar_one_or_none()
            if webhook_ep:
                if not webhook_ep.active:
                    delivery.status = DeliveryStatus.FAILED.value
                    delivery.error_code = "ENDPOINT_DISABLED"
                    delivery.error_message = "Webhook endpoint is disabled."
                    delivery.updated_at = now
                    await session.commit()
                    return False
                secret = webhook_ep.secret_reference

        # 6. Execute transmission
        delivery.status = DeliveryStatus.SENDING.value
        delivery.attempt_count += 1
        delivery.updated_at = now
        await session.commit()

        try:
            result = await channel.send(
                destination=delivery.destination,
                title=notification.title,
                body=notification.body,
                event_type=notification.event_type,
                workspace_id=str(notification.workspace_id),
                source_type=notification.source_type,
                source_id=notification.source_id,
                metadata=notification.metadata_json,
                secret=secret,
            )

            # Success
            delivery.status = DeliveryStatus.SENT.value
            delivery.sent_at = datetime.now(timezone.utc)
            delivery.provider_message_id = result.provider_message_id
            delivery.error_code = None
            delivery.error_message = None
            delivery.updated_at = datetime.now(timezone.utc)

            if webhook_ep:
                webhook_ep.last_success_at = delivery.sent_at

            await session.commit()
            logger.info(f"[DeliveryDispatcher] Delivery {delivery.id} sent successfully via {delivery.channel}.")
            return True

        except Exception as exc:
            err_now = datetime.now(timezone.utc)
            is_transient = DeliveryRetryPolicy.is_transient_error(exc)
            err_code = getattr(exc, "error_code", "DELIVERY_FAILED")
            err_msg = str(exc)

            if is_transient and delivery.attempt_count < delivery.max_attempts:
                # Schedule retry with jittered exponential backoff
                delay = DeliveryRetryPolicy.calculate_backoff(delivery.attempt_count)
                delivery.status = DeliveryStatus.RETRYING.value
                delivery.scheduled_at = err_now + timedelta(seconds=delay)
                delivery.error_code = err_code
                delivery.error_message = err_msg
                delivery.updated_at = err_now
                logger.info(
                    f"[DeliveryDispatcher] Delivery {delivery.id} failed transiently ({err_code}). Retrying in {delay:.1f}s (attempt {delivery.attempt_count}/{delivery.max_attempts})"
                )
            else:
                # Permanent failure
                delivery.status = DeliveryStatus.FAILED.value
                delivery.error_code = err_code
                delivery.error_message = err_msg
                delivery.updated_at = err_now
                if webhook_ep:
                    webhook_ep.last_failure_at = err_now
                logger.warning(
                    f"[DeliveryDispatcher] Delivery {delivery.id} failed permanently: {err_code} - {err_msg}"
                )

            await session.commit()
            return False
