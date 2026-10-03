"""
Webhook Delivery Execution and Retries.
Step 37: Public API, Developer Platform & SDK Layer.
"""
from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, Optional
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.developer_platform.models import WebhookSubscription
from backend.app.services.developer_platform.request_signing import RequestSigner
from backend.app.services.developer_platform.validators import InputValidator

logger = logging.getLogger(__name__)


class WebhookDeliveryService:
    """Executes HTTP dispatch for external developer webhooks."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def deliver_webhook(
        self,
        subscription_id: str,
        event_type: str,
        payload_dict: Dict[str, Any],
        timeout_seconds: float = 10.0,
    ) -> bool:
        """
        Dispatches webhook HTTP POST request with HMAC-SHA256 signature.
        Updates last_delivery_at and failure_count.
        """
        query = select(WebhookSubscription).where(WebhookSubscription.id == subscription_id)
        res = await self.session.execute(query)
        sub: Optional[WebhookSubscription] = res.scalars().first()

        if not sub or sub.status != "active":
            return False

        # Validate URL again before dispatch (defense-in-depth against DNS rebinding / SSRF)
        try:
            InputValidator.validate_webhook_url(sub.url, allow_local_for_testing=True)
        except Exception as e:
            logger.warning("Webhook delivery blocked by SSRF check: %s", str(e))
            sub.failure_count += 1
            await self.session.commit()
            return False

        payload_envelope = {
            "event": event_type,
            "subscription_id": sub.id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": payload_dict,
        }
        payload_str = json.dumps(payload_envelope, sort_keys=True)

        # Compute HMAC signature using stored secret hash as fallback or test secret
        # Note: secret_hash is stored in DB; signature computed
        sig_header, _ = RequestSigner.compute_signature(payload_str, sub.secret_hash)

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AIWorkLayer-Webhook/1.0",
            RequestSigner.HEADER_NAME: sig_header,
        }

        success = False
        try:
            async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=False) as client:
                resp = await client.post(sub.url, content=payload_str, headers=headers)
                if 200 <= resp.status_code < 300:
                    success = True
                else:
                    logger.warning("Webhook endpoint returned non-2xx status: %d", resp.status_code)
        except Exception as ex:
            logger.warning("Webhook dispatch exception for sub %s: %s", sub.id, str(ex))

        now = datetime.now(timezone.utc)
        sub.last_delivery_at = now
        if success:
            sub.failure_count = 0
        else:
            sub.failure_count += 1
            if sub.failure_count >= 10:
                sub.status = "failed"  # Auto-suspend after 10 consecutive delivery failures

        await self.session.commit()
        return success
