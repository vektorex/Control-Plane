"""
Developer Webhook Subscription Management.
Step 37: Public API, Developer Platform & SDK Layer.
"""
from datetime import datetime, timezone
import hashlib
import secrets
from typing import List, Optional, Tuple
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.developer_platform.errors import PublicAPIException, ResourceNotFoundError
from backend.app.services.developer_platform.models import DeveloperApplication, WebhookSubscription
from backend.app.services.developer_platform.schemas import (
    WebhookSubscriptionCreate,
    WebhookSubscriptionUpdate,
)
from backend.app.services.developer_platform.validators import InputValidator

VALID_WEBHOOK_EVENTS = {
    "run.completed",
    "run.failed",
    "workflow.completed",
    "workflow.failed",
    "artifact.processed",
    "evaluation.completed",
    "security.incident.created",
    "usage.threshold",
    "recovery.failure",
}


class WebhookService:
    """Manages external webhook subscriptions and event triggers."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_subscription(
        self,
        application_id: str,
        organization_id: str,
        data: WebhookSubscriptionCreate,
        allow_local_for_testing: bool = False,
    ) -> Tuple[WebhookSubscription, str]:
        """
        Creates a new webhook subscription.
        Returns (WebhookSubscription, plaintext_signing_secret).
        The signing secret is returned ONLY here and must never be stored.
        """
        # Verify application belongs to org
        app_q = select(DeveloperApplication).where(
            DeveloperApplication.id == application_id,
            DeveloperApplication.organization_id == organization_id,
        )
        app_res = await self.session.execute(app_q)
        app = app_res.scalars().first()
        if not app:
            raise ResourceNotFoundError("Developer application", application_id)

        # Validate URL and SSRF safety
        InputValidator.validate_webhook_url(data.url, allow_local_for_testing=allow_local_for_testing)

        # Validate subscribed events
        for ev in data.events:
            if ev not in VALID_WEBHOOK_EVENTS:
                raise PublicAPIException(f"Unsupported webhook event type: '{ev}'", status_code=400)

        # Generate signing secret (e.g., whsec_...)
        plaintext_secret = f"whsec_{secrets.token_hex(24)}"
        secret_hash = hashlib.sha256(plaintext_secret.encode("utf-8")).hexdigest()

        now = datetime.now(timezone.utc)
        sub = WebhookSubscription(
            id=str(uuid.uuid4()),
            application_id=application_id,
            organization_id=organization_id,
            url=data.url,
            status="active",
            events=list(set(data.events)),
            secret_hash=secret_hash,
            created_at=now,
            updated_at=now,
            failure_count=0,
        )
        self.session.add(sub)
        await self.session.commit()

        return sub, plaintext_secret

    async def get_subscription(self, subscription_id: str, organization_id: str) -> WebhookSubscription:
        """Retrieves a webhook subscription ensuring tenant ownership."""
        query = select(WebhookSubscription).where(
            WebhookSubscription.id == subscription_id,
            WebhookSubscription.organization_id == organization_id,
        )
        res = await self.session.execute(query)
        sub = res.scalars().first()
        if not sub:
            raise ResourceNotFoundError("Webhook subscription", subscription_id)
        return sub

    async def list_subscriptions(
        self,
        application_id: str,
        organization_id: str,
    ) -> List[WebhookSubscription]:
        """Lists webhooks for an application."""
        query = select(WebhookSubscription).where(
            WebhookSubscription.application_id == application_id,
            WebhookSubscription.organization_id == organization_id,
        ).order_by(WebhookSubscription.created_at.desc())
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def update_subscription(
        self,
        subscription_id: str,
        organization_id: str,
        data: WebhookSubscriptionUpdate,
        allow_local_for_testing: bool = False,
    ) -> WebhookSubscription:
        """Updates URL, events, or status of a subscription."""
        sub = await self.get_subscription(subscription_id, organization_id)
        if data.url is not None:
            InputValidator.validate_webhook_url(data.url, allow_local_for_testing=allow_local_for_testing)
            sub.url = data.url
        if data.events is not None:
            for ev in data.events:
                if ev not in VALID_WEBHOOK_EVENTS:
                    raise PublicAPIException(f"Unsupported webhook event type: '{ev}'", status_code=400)
            sub.events = list(set(data.events))
        if data.status is not None:
            sub.status = data.status
        sub.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        return sub

    async def delete_subscription(self, subscription_id: str, organization_id: str) -> None:
        """Deletes a webhook subscription."""
        sub = await self.get_subscription(subscription_id, organization_id)
        await self.session.delete(sub)
        await self.session.commit()

    async def trigger_event(
        self,
        organization_id: str,
        event_type: str,
        payload: dict,
    ) -> int:
        """
        Finds active webhook subscriptions matching event_type and enqueues delivery jobs.
        Returns the number of subscriptions queued.
        """
        query = select(WebhookSubscription).where(
            WebhookSubscription.organization_id == organization_id,
            WebhookSubscription.status == "active",
        )
        res = await self.session.execute(query)
        subs = res.scalars().all()

        enqueued_count = 0
        for sub in subs:
            if event_type in sub.events:
                # Enqueue delivery via Step 24 Jobs
                await self._enqueue_delivery_job(sub.id, event_type, payload)
                enqueued_count += 1

        return enqueued_count

    async def _enqueue_delivery_job(self, subscription_id: str, event_type: str, payload: dict) -> None:
        """Enqueues public_webhook_delivery background job."""
        try:
            from backend.app.services.jobs.service import JobService
            from backend.app.services.jobs.constants import JobType, JobPriority
            import uuid

            job_svc = JobService(self.session)
            await job_svc.create_job(
                job_type=JobType.PUBLIC_WEBHOOK_DELIVERY,
                organization_id=uuid.UUID(subscription_id),
                payload={
                    "subscription_id": subscription_id,
                    "event_type": event_type,
                    "payload": payload,
                },
                priority=JobPriority.NORMAL,
            )
        except Exception:
            pass
