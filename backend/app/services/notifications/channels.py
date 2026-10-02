"""
DeliveryChannel abstractions and concrete implementations for Step 25:
- InAppDeliveryChannel
- WebhookDeliveryChannel (with SSRF validation and HMAC-SHA256 signing)
- EmailDeliveryChannel (provider-agnostic)
"""
import abc
import hashlib
import hmac
import json
import logging
import re
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional, Tuple
import httpx

from backend.app.config import settings
from backend.app.services.notifications.constants import (
    DeliveryChannelType,
    WEBHOOK_HEADER_EVENT,
    WEBHOOK_HEADER_SIGNATURE,
    WEBHOOK_HEADER_TIMESTAMP,
)
from backend.app.services.notifications.errors import (
    ChannelNotConfiguredError,
    DeliveryPermanentError,
    DeliveryTransientError,
    NotificationValidationError,
    SSRFSecurityError,
)
from backend.app.services.notifications.policies import SSRFValidator
from backend.app.services.notifications.sanitizer import NotificationSanitizer
from backend.app.services.notifications.templates import NotificationTemplateEngine

logger = logging.getLogger(__name__)


class DeliveryResult:
    """Normalized response from a delivery channel execution."""

    def __init__(
        self,
        success: bool,
        provider_message_id: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        status_code: Optional[int] = None,
        latency_ms: Optional[int] = None,
    ):
        self.success = success
        self.provider_message_id = provider_message_id
        self.error_code = error_code
        self.error_message = error_message
        self.status_code = status_code
        self.latency_ms = latency_ms


class DeliveryChannel(abc.ABC):
    """Abstract delivery channel."""

    @property
    @abc.abstractmethod
    def channel_name(self) -> str:
        pass

    @abc.abstractmethod
    def validate_destination(self, destination: str) -> None:
        """Validates destination syntax and security constraints."""
        pass

    @abc.abstractmethod
    async def send(
        self,
        destination: str,
        title: str,
        body: str,
        event_type: str,
        workspace_id: str,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        secret: Optional[str] = None,
    ) -> DeliveryResult:
        """Executes actual external transmission to destination."""
        pass

    @abc.abstractmethod
    def supports_rich_content(self) -> bool:
        pass


class InAppDeliveryChannel(DeliveryChannel):
    """In-app delivery channel targeting the unified Notification record."""

    @property
    def channel_name(self) -> str:
        return DeliveryChannelType.IN_APP.value

    def validate_destination(self, destination: str) -> None:
        if not destination:
            raise NotificationValidationError("In-app destination must be a valid user ID or 'workspace'.")

    async def send(
        self,
        destination: str,
        title: str,
        body: str,
        event_type: str,
        workspace_id: str,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        secret: Optional[str] = None,
    ) -> DeliveryResult:
        # In-app delivery succeeds immediately as the database row represents the in-app state
        return DeliveryResult(success=True, provider_message_id=f"in_app_{int(time.time()*1000)}")

    def supports_rich_content(self) -> bool:
        return True


class WebhookDeliveryChannel(DeliveryChannel):
    """
    Secure outbound webhook channel.
    Enforces SSRF checking and applies HMAC-SHA256 signatures with timestamp anti-replay.
    """

    @property
    def channel_name(self) -> str:
        return DeliveryChannelType.WEBHOOK.value

    def validate_destination(self, destination: str) -> None:
        # Validate URL and resolve DNS against private networks
        allow_http = getattr(settings, "ENVIRONMENT", "development") == "development"
        SSRFValidator.validate_url(destination, allow_http=allow_http)

    @classmethod
    def compute_signature(cls, secret: str, timestamp: str, payload_str: str) -> str:
        """
        Deterministic HMAC-SHA256 signature calculation over '{timestamp}.{payload_str}'.
        """
        signing_payload = f"{timestamp}.{payload_str}".encode("utf-8")
        h = hmac.new(secret.encode("utf-8"), signing_payload, hashlib.sha256)
        return f"sha256={h.hexdigest()}"

    async def send(
        self,
        destination: str,
        title: str,
        body: str,
        event_type: str,
        workspace_id: str,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        secret: Optional[str] = None,
    ) -> DeliveryResult:
        # 1. SSRF validation check
        self.validate_destination(destination)

        # 2. Build sanitized payload conforming to specification
        event_id = f"evt_{hashlib.md5(f'{workspace_id}:{event_type}:{time.time()}'.encode()).hexdigest()[:16]}"
        timestamp = str(int(time.time()))

        raw_data = {
            "title": title,
            "body": body,
            **(metadata or {}),
        }
        webhook_payload = NotificationSanitizer.build_webhook_payload(
            event_id=event_id,
            event_type=event_type,
            timestamp=timestamp,
            workspace_id=str(workspace_id),
            source_type=source_type or "system",
            source_id=source_id or "system",
            data=raw_data,
        )

        payload_json = json.dumps(webhook_payload, separators=(",", ":"))
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AIWorkLayer-Webhook/1.0",
            WEBHOOK_HEADER_EVENT: event_type,
            WEBHOOK_HEADER_TIMESTAMP: timestamp,
        }

        if secret:
            sig = self.compute_signature(secret, timestamp, payload_json)
            headers[WEBHOOK_HEADER_SIGNATURE] = sig

        timeout = getattr(settings, "WEBHOOK_TIMEOUT_SECONDS", 10.0)
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
                resp = await client.post(destination, content=payload_json, headers=headers)
                latency = int((time.time() - start_time) * 1000)

                if resp.is_success:
                    return DeliveryResult(
                        success=True,
                        provider_message_id=resp.headers.get("x-request-id") or f"wh_{event_id}",
                        status_code=resp.status_code,
                        latency_ms=latency,
                    )

                # Remote returned non-2xx status
                status_code = resp.status_code
                if status_code == 429:
                    raise DeliveryTransientError(
                        f"Webhook destination rate limited (HTTP 429): {resp.text[:200]}",
                        error_code="WEBHOOK_RATE_LIMITED",
                    )
                elif status_code >= 500:
                    raise DeliveryTransientError(
                        f"Webhook destination error (HTTP {status_code}): {resp.text[:200]}",
                        error_code="WEBHOOK_REMOTE_SERVER_ERROR",
                    )
                else:
                    # 4xx client errors are permanent
                    raise DeliveryPermanentError(
                        f"Webhook rejected by destination (HTTP {status_code}): {resp.text[:200]}",
                        error_code="WEBHOOK_CLIENT_REJECTED",
                    )

        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as net_err:
            latency = int((time.time() - start_time) * 1000)
            raise DeliveryTransientError(
                f"Network failure delivering webhook to '{destination}': {net_err}",
                error_code="WEBHOOK_NETWORK_TIMEOUT",
            )

    def supports_rich_content(self) -> bool:
        return True


class EmailDeliveryChannel(DeliveryChannel):
    """
    Provider-agnostic email delivery channel.
    Supports SMTP, API providers, or simulated delivery if configured in mock mode.
    """

    EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[a-zA-Z0-9\.\-]+\.[a-zA-Z]{2,}$")

    @property
    def channel_name(self) -> str:
        return DeliveryChannelType.EMAIL.value

    def validate_destination(self, destination: str) -> None:
        if not destination or not self.EMAIL_REGEX.match(destination.strip()):
            raise NotificationValidationError(f"Invalid email address: '{destination}'")

    async def send(
        self,
        destination: str,
        title: str,
        body: str,
        event_type: str,
        workspace_id: str,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        secret: Optional[str] = None,
    ) -> DeliveryResult:
        self.validate_destination(destination)

        email_provider = getattr(settings, "EMAIL_PROVIDER", None)
        email_from = getattr(settings, "EMAIL_FROM", "notifications@aiworklayer.internal")

        # If no provider configured
        if not email_provider:
            raise ChannelNotConfiguredError(
                "email",
                "Set EMAIL_PROVIDER environment variable ('smtp' or 'mock') to enable email notifications.",
            )

        context = {
            "title": title,
            "body": body,
            "event_type": event_type,
            "source_type": source_type,
            "source_id": source_id,
            **(metadata or {}),
        }

        html_body = NotificationTemplateEngine.render_email_html(title, body, context)
        html_sanitized = NotificationSanitizer.sanitize_html(html_body)

        if email_provider == "mock":
            # Mock provider for testing and development
            logger.info(f"[EmailMock] Sent email to '{destination}' | Title: {title}")
            return DeliveryResult(
                success=True,
                provider_message_id=f"mock_mail_{int(time.time()*1000)}",
            )

        if email_provider == "smtp":
            smtp_host = getattr(settings, "EMAIL_SMTP_HOST", "localhost")
            smtp_port = getattr(settings, "EMAIL_SMTP_PORT", 587)

            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = title
                msg["From"] = email_from
                msg["To"] = destination
                msg.attach(MIMEText(body, "plain"))
                msg.attach(MIMEText(html_sanitized, "html"))

                # Synchronous SMTP dispatch in worker context
                with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                    server.sendmail(email_from, [destination], msg.as_string())

                return DeliveryResult(
                    success=True,
                    provider_message_id=f"smtp_{int(time.time()*1000)}",
                )
            except Exception as e:
                raise DeliveryTransientError(f"SMTP delivery failed: {e}", error_code="SMTP_DELIVERY_FAILED")

        raise ChannelNotConfiguredError("email", f"Unsupported provider: '{email_provider}'")

    def supports_rich_content(self) -> bool:
        return True


class ChannelRegistry:
    """Singleton registry of delivery channels."""

    def __init__(self):
        self._channels: Dict[str, DeliveryChannel] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register(InAppDeliveryChannel())
        self.register(WebhookDeliveryChannel())
        self.register(EmailDeliveryChannel())

    def register(self, channel: DeliveryChannel) -> None:
        self._channels[channel.channel_name] = channel

    def get(self, channel_name: str) -> DeliveryChannel:
        if channel_name not in self._channels:
            raise ChannelNotConfiguredError(channel_name, f"Channel '{channel_name}' is not registered.")
        return self._channels[channel_name]

    def has_channel(self, channel_name: str) -> bool:
        return channel_name in self._channels


channel_registry = ChannelRegistry()
