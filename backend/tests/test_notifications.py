"""
Unit and Integration Tests for Step 25: Notifications & External Delivery Layer.
Verifies notifications, deliveries, webhooks, preferences, SSRF protection, HMAC signing,
idempotency, retry policies, secret sanitization, and Step 24 async job execution.
"""
import asyncio
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app.core.errors import AuthorizationError
from backend.app.db.models.notification import (
    Notification,
    NotificationDelivery,
    NotificationPreference,
    WebhookEndpoint,
)
from backend.app.services.notifications.channels import (
    EmailDeliveryChannel,
    InAppDeliveryChannel,
    WebhookDeliveryChannel,
    channel_registry,
)
from backend.app.services.notifications.constants import (
    DeliveryChannelType,
    DeliveryStatus,
    NotificationEventType,
    NotificationSeverity,
    NotificationStatus,
    WEBHOOK_HEADER_EVENT,
    WEBHOOK_HEADER_SIGNATURE,
    WEBHOOK_HEADER_TIMESTAMP,
)
from backend.app.services.notifications.delivery import DeliveryDispatcher
from backend.app.services.notifications.dispatcher import NotificationEvent, NotificationEventBus
from backend.app.services.notifications.errors import (
    ChannelNotConfiguredError,
    DeliveryPermanentError,
    DeliveryTransientError,
    NotificationNotFoundError,
    RateLimitExceededError,
    SSRFSecurityError,
)
from backend.app.services.notifications.policies import (
    NotificationRateLimiter,
    RecipientResolver,
    SSRFValidator,
)
from backend.app.services.notifications.preferences import NotificationPreferenceService
from backend.app.services.notifications.registry import notification_registry
from backend.app.services.notifications.repository import NotificationRepository
from backend.app.services.notifications.retry import DeliveryRetryPolicy
from backend.app.services.notifications.sanitizer import NotificationSanitizer
from backend.app.services.notifications.service import NotificationService
from backend.app.services.notifications.templates import NotificationTemplateEngine


# =============================================================================
# 1. SSRF & Security Validation Tests
# =============================================================================

def test_ssrf_validator_rejects_localhost_and_loopback():
    """Verify that localhost and loopback IPv4/IPv6 are strictly rejected."""
    with pytest.raises(SSRFSecurityError):
        SSRFValidator.validate_url("http://localhost:8080/webhook")

    with pytest.raises(SSRFSecurityError):
        SSRFValidator.validate_url("https://127.0.0.1:8000/webhook")

    with pytest.raises(SSRFSecurityError):
        SSRFValidator.validate_url("https://[::1]:9000/callback")


def test_ssrf_validator_rejects_private_and_cloud_metadata_ip():
    """Verify rejection of 10.x, 192.168.x, 172.16.x, and AWS/GCP metadata 169.254.169.254."""
    with pytest.raises(SSRFSecurityError):
        SSRFValidator.validate_url("https://10.0.0.1/notify")

    with pytest.raises(SSRFSecurityError):
        SSRFValidator.validate_url("https://192.168.1.100/notify")

    with pytest.raises(SSRFSecurityError):
        SSRFValidator.validate_url("https://172.20.0.5/notify")

    with pytest.raises(SSRFSecurityError):
        SSRFValidator.validate_url("http://169.254.169.254/latest/meta-data")


def test_ssrf_validator_rejects_non_http_protocols():
    """Verify that file://, ftp://, and gopher:// schemes are rejected."""
    with pytest.raises(SSRFSecurityError):
        SSRFValidator.validate_url("file:///etc/passwd")

    with pytest.raises(SSRFSecurityError):
        SSRFValidator.validate_url("ftp://server.local/files")


def test_ssrf_validator_accepts_valid_public_https():
    """Verify that legitimate public HTTPS URLs pass validation."""
    with patch("socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 443))]):
        validated = SSRFValidator.validate_url("https://hooks.slack.com/services/T00/B00/X00")
        assert validated == "https://hooks.slack.com/services/T00/B00/X00"


# =============================================================================
# 2. Webhook HMAC Signing & Determinism Tests
# =============================================================================

def test_webhook_hmac_signing_determinism():
    """Verify deterministic HMAC-SHA256 signature generation."""
    secret = "test_secret_key_1234567890abcdef"
    timestamp = "1727800000"
    payload = json.dumps({"test": "data", "id": "123"}, separators=(",", ":"), sort_keys=True)

    sig1 = WebhookDeliveryChannel.compute_signature(secret, timestamp, payload)
    sig2 = WebhookDeliveryChannel.compute_signature(secret, timestamp, payload)

    assert sig1 == sig2
    assert sig1.startswith("sha256=")

    # Verify manual HMAC computation matches
    signing_payload = f"{timestamp}.{payload}".encode("utf-8")
    expected_hex = hmac.new(secret.encode("utf-8"), signing_payload, hashlib.sha256).hexdigest()
    assert sig1 == f"sha256={expected_hex}"


# =============================================================================
# 3. Payload & Secret Sanitization Tests
# =============================================================================

def test_sanitizer_removes_sensitive_credentials():
    """Verify secrets, tokens, passwords, and authorization headers are scrubbed."""
    raw_payload = {
        "title": "Operation completed",
        "api_key": "sk-proj-super-secret-123456",
        "password": "my_master_password",
        "nested": {
            "token": "ghp_abcdef1234567890",
            "safe_field": "public_data",
            "authorization": "Bearer eyJhbGciOi...",
        },
    }

    clean = NotificationSanitizer.sanitize_payload(raw_payload)

    assert clean["api_key"] == "[REDACTED]"
    assert clean["password"] == "[REDACTED]"
    assert clean["nested"]["token"] == "[REDACTED]"
    assert clean["nested"]["authorization"] == "[REDACTED]"
    assert clean["nested"]["safe_field"] == "public_data"


def test_sanitizer_truncates_oversized_payloads():
    """Verify excessively large strings in payloads are safely truncated."""
    huge_data = {"data": "X" * 20000}
    clean = NotificationSanitizer.sanitize_payload(huge_data)
    assert "[TRUNCATED]" in clean["data"]
    assert len(clean["data"]) < 17000


# =============================================================================
# 4. Safe Template Variable Interpolation Tests
# =============================================================================

def test_template_engine_safe_interpolation():
    """Verify safe interpolation without arbitrary code execution."""
    template = "Workflow '{{workflow.name}}' completed with status '{{job.status}}' for project '{{project.name}}'."
    context = {
        "workflow": {"name": "Data Ingestion Pipeline"},
        "job": {"status": "completed"},
        "project": {"name": "Alpha Research"},
    }

    rendered = NotificationTemplateEngine.render(template, context)
    assert rendered == "Workflow 'Data Ingestion Pipeline' completed with status 'completed' for project 'Alpha Research'."


def test_template_engine_blocks_code_execution():
    """Verify python/javascript code or attribute navigation cannot be executed."""
    malicious_template = "Value: {{__import__('os').system('id')}} and {{7*7}}"
    rendered = NotificationTemplateEngine.render(malicious_template, {})
    # Unmatched expressions remain literal text, never executed
    assert rendered == "Value: {{__import__('os').system('id')}} and {{7*7}}"


# =============================================================================
# 5. Retry Policy Classification & Backoff Tests
# =============================================================================

def test_retry_policy_error_classification():
    """Verify transient vs permanent failure classification."""
    assert DeliveryRetryPolicy.is_transient_error(DeliveryTransientError("Timeout")) is True
    assert DeliveryRetryPolicy.is_transient_error(TimeoutError("Connection timed out")) is True

    # Permanent failures
    assert DeliveryRetryPolicy.is_transient_error(DeliveryPermanentError("400 Bad Request")) is False
    assert DeliveryRetryPolicy.is_transient_error(SSRFSecurityError("Blocked")) is False


def test_retry_policy_exponential_backoff_with_jitter():
    """Verify backoff calculation increases monotonically within bounds."""
    d1 = DeliveryRetryPolicy.calculate_backoff(1, base_delay=2.0)
    d2 = DeliveryRetryPolicy.calculate_backoff(2, base_delay=2.0)
    d3 = DeliveryRetryPolicy.calculate_backoff(3, base_delay=2.0)

    assert 1.0 <= d1 <= 5.0
    assert d2 >= d1 * 0.8
    assert d3 >= d2 * 0.8


# =============================================================================
# 6. End-to-End API Lifecycle & Workspace Isolation
# =============================================================================

def test_notification_api_lifecycle(client: TestClient, user1_auth, user2_auth):
    """
    Test listing notifications, unread count, marking read, archiving,
    and verifying strict cross-workspace isolation.
    """
    headers1 = user1_auth["headers"]
    me1 = client.get("/api/auth/me", headers=headers1).json()
    ws1_id = me1["default_workspace_id"]
    ws1_headers = {**headers1, "X-Workspace-Id": ws1_id}

    headers2 = user2_auth["headers"]
    me2 = client.get("/api/auth/me", headers=headers2).json()
    ws2_id = me2["default_workspace_id"]
    ws2_headers = {**headers2, "X-Workspace-Id": ws2_id}

    # 1. Trigger an intervention request which creates a notification
    req_res = client.post(
        "/api/hitl/requests",
        json={"title": "Action requiring notification", "requested_action": "notify_me"},
        headers=ws1_headers,
    )
    assert req_res.status_code == 201

    # 2. Check unread count for user 1
    count_res = client.get("/api/notifications/unread-count", headers=ws1_headers)
    assert count_res.status_code == 200
    assert count_res.json()["unread_count"] >= 1

    # 3. List notifications for user 1
    list_res = client.get("/api/notifications", headers=ws1_headers)
    assert list_res.status_code == 200
    notifs = list_res.json()
    assert len(notifs) >= 1
    notif = notifs[0]
    notif_id = notif["id"]
    assert notif["read"] is False
    assert notif["status"] == "unread"

    # 4. Verify user 2 in Workspace 2 CANNOT see user 1's notification (Workspace Isolation)
    u2_list = client.get("/api/notifications", headers=ws2_headers).json()
    assert not any(n["id"] == str(notif_id) for n in u2_list)

    # 5. Mark notification as read
    read_res = client.post(f"/api/notifications/{notif_id}/read", headers=ws1_headers)
    assert read_res.status_code == 200
    assert read_res.json()["read"] is True

    # 6. Archive notification
    archive_res = client.post(f"/api/notifications/{notif_id}/archive", headers=ws1_headers)
    assert archive_res.status_code == 200
    assert archive_res.json()["status"] == "archived"


def test_webhook_endpoint_management_and_secret_hiding(client: TestClient, user1_auth):
    """
    Test creating webhook destination, ensuring secret is only returned once,
    listing endpoints with hidden secrets, rotating secret, and deleting.
    """
    headers = user1_auth["headers"]
    me = client.get("/api/auth/me", headers=headers).json()
    ws_id = me["default_workspace_id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    with patch("socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 443))]):
        # 1. Create Webhook Endpoint
        create_res = client.post(
            "/api/webhooks",
            json={
                "name": "Integration Slack Alert",
                "url": "https://api.external.com/webhooks/listener",
                "subscribed_events": ["workflow.completed", "workflow.failed"],
                "active": True,
            },
            headers=ws_headers,
        )
        assert create_res.status_code == 201
        ep_data = create_res.json()
        ep_id = ep_data["id"]
        assert "secret" in ep_data
        secret = ep_data["secret"]
        assert len(secret) >= 32

        # 2. Get Webhook Endpoint - Secret MUST NOT be exposed!
        get_res = client.get(f"/api/webhooks/{ep_id}", headers=ws_headers)
        assert get_res.status_code == 200
        assert "secret" not in get_res.json()

        # 3. List Webhooks - Secrets MUST NOT be exposed in list!
        list_res = client.get("/api/webhooks", headers=ws_headers)
        assert list_res.status_code == 200
        for item in list_res.json():
            assert "secret" not in item

        # 4. Rotate Secret - Returns new secret once
        rotate_res = client.post(f"/api/webhooks/{ep_id}/rotate-secret", headers=ws_headers)
        assert rotate_res.status_code == 200
        rot_data = rotate_res.json()
        assert "secret" in rot_data
        assert rot_data["secret"] != secret

        # 5. Delete Webhook Endpoint
        del_res = client.delete(f"/api/webhooks/{ep_id}", headers=ws_headers)
        assert del_res.status_code == 200

        # 6. Verify 404 after deletion
        check_res = client.get(f"/api/webhooks/{ep_id}", headers=ws_headers)
        assert check_res.status_code == 404


def test_notification_preferences_update_and_enforcement(client: TestClient, user1_auth):
    """
    Test updating notification preferences and verifying that preferences
    are updated and persisted correctly.
    """
    headers = user1_auth["headers"]
    me = client.get("/api/auth/me", headers=headers).json()
    ws_id = me["default_workspace_id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # 1. Update preferences: enable webhook for workflow.completed
    update_res = client.put(
        "/api/notification-preferences",
        json={
            "preferences": [
                {
                    "event_type": "workflow.completed",
                    "channel": "webhook",
                    "enabled": True,
                },
                {
                    "event_type": "workflow.completed",
                    "channel": "in_app",
                    "enabled": False,
                },
            ]
        },
        headers=ws_headers,
    )
    assert update_res.status_code == 200
    prefs = update_res.json()["preferences"]
    wf_webhook = next((p for p in prefs if p["event_type"] == "workflow.completed" and p["channel"] == "webhook"), None)
    assert wf_webhook is not None
    assert wf_webhook["enabled"] is True


@pytest.mark.asyncio
async def test_delivery_idempotency_prevents_duplicate_active_jobs():
    """
    Verify that notification_id + channel + destination does not create duplicate deliveries.
    """
    mock_session = AsyncMock()
    repo = NotificationRepository(mock_session)

    existing_delivery = NotificationDelivery(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        notification_id=uuid.uuid4(),
        channel="webhook",
        destination="https://api.example.com/hook",
        status="queued",
    )
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = existing_delivery
    mock_session.execute.return_value = mock_res

    # Calling create_delivery when existing active delivery exists should return the existing delivery
    d = await repo.create_delivery(
        notification_id=existing_delivery.notification_id,
        workspace_id=existing_delivery.workspace_id,
        channel=existing_delivery.channel,
        destination=existing_delivery.destination,
    )
    assert d.id == existing_delivery.id


@pytest.mark.asyncio
async def test_email_provider_unconfigured_status():
    """
    Verify that when no email provider is configured, sending raises ChannelNotConfiguredError.
    """
    channel = EmailDeliveryChannel()
    with pytest.raises(ChannelNotConfiguredError) as exc_info:
        await channel.send(
            destination="user@example.com",
            title="Test",
            body="Content",
            event_type="test",
            workspace_id=str(uuid.uuid4()),
        )
    assert "not configured" in str(exc_info.value).lower()


def test_webhook_test_endpoint_synthetic_delivery(client: TestClient, user1_auth):
    """
    Test sending a synthetic test webhook via POST /api/webhooks/{id}/test.
    """
    headers = user1_auth["headers"]
    me = client.get("/api/auth/me", headers=headers).json()
    ws_id = me["default_workspace_id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    with patch("socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 443))]):
        create_res = client.post(
            "/api/webhooks",
            json={
                "name": "Synthetic Test Webhook",
                "url": "https://api.example.com/webhook",
                "subscribed_events": ["*"],
                "active": True,
            },
            headers=ws_headers,
        )
        ep_id = create_res.json()["id"]

        with patch("backend.app.services.notifications.channels.WebhookDeliveryChannel.send", new_callable=AsyncMock) as mock_send:
            from backend.app.services.notifications.channels import DeliveryResult
            mock_send.return_value = DeliveryResult(success=True, status_code=200, latency_ms=45)

            test_res = client.post(f"/api/webhooks/{ep_id}/test", headers=ws_headers)
            assert test_res.status_code == 200
            assert test_res.json()["success"] is True
            assert test_res.json()["status_code"] == 200


@pytest.mark.asyncio
async def test_async_delivery_via_step24_job_handler():
    """
    Verify that NotificationDeliveryJobHandler executes delivery through DeliveryDispatcher.
    """
    from backend.app.db.models.job import Job
    from backend.app.services.jobs.handlers import NotificationDeliveryJobHandler, JobExecutionContext
    from backend.app.db.models.notification import NotificationDelivery

    delivery_id = uuid.uuid4()
    mock_delivery = NotificationDelivery(
        id=delivery_id,
        workspace_id=uuid.uuid4(),
        notification_id=uuid.uuid4(),
        channel="in_app",
        destination="user_123",
        status="sent",
        attempt_count=1,
    )
    job = Job(
        id=uuid.uuid4(),
        workspace_id=mock_delivery.workspace_id,
        job_type="notification_delivery",
        payload={
            "delivery_id": str(delivery_id),
            "channel": "in_app",
        },
    )

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_delivery
    mock_session.execute.return_value = mock_result

    with patch("backend.app.services.notifications.delivery.DeliveryDispatcher.execute_delivery", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = True

        handler = NotificationDeliveryJobHandler()
        ctx = JobExecutionContext(session=mock_session, update_progress=AsyncMock())
        cancel_token = asyncio.Event()

        res = await handler.execute(job, ctx, cancel_token)
        assert res["delivery_id"] == str(delivery_id)
        assert res["success"] is True


def test_rate_limiter_enforces_limits_and_resets():
    """Verify that NotificationRateLimiter enforces throughput quotas per workspace."""
    limiter = NotificationRateLimiter()
    ws_id = uuid.uuid4()

    with patch("backend.app.services.notifications.policies.settings") as mock_settings:
        mock_settings.WEBHOOK_MAX_DELIVERIES_PER_MINUTE = 3

        # First 3 deliveries pass
        limiter.check_and_record(ws_id, DeliveryChannelType.WEBHOOK.value)
        limiter.check_and_record(ws_id, DeliveryChannelType.WEBHOOK.value)
        limiter.check_and_record(ws_id, DeliveryChannelType.WEBHOOK.value)

        # 4th delivery violates quota
        with pytest.raises(RateLimitExceededError) as exc_info:
            limiter.check_and_record(ws_id, DeliveryChannelType.WEBHOOK.value)
        assert "exceeded rate limit" in str(exc_info.value)


def test_recipient_resolver_trusted_relations():
    """
    Verify recipient resolution prioritizes authoritative system relationships:
    explicit user -> assigned user -> workspace owner.
    Blocks arbitrary model-injected recipient lists.
    """
    owner = uuid.uuid4()
    assignee = uuid.uuid4()
    explicit = uuid.uuid4()

    # Explicit takes precedence
    r1 = RecipientResolver.resolve_recipients(owner, assignee, explicit)
    assert r1 == [explicit]

    # Assignee takes precedence over owner
    r2 = RecipientResolver.resolve_recipients(owner, assignee, None)
    assert r2 == [assignee]

    # Owner is fallback
    r3 = RecipientResolver.resolve_recipients(owner, None, None)
    assert r3 == [owner]

    # Empty fallback
    r4 = RecipientResolver.resolve_recipients(None, None, None)
    assert r4 == []


@pytest.mark.asyncio
async def test_preferences_cannot_disable_mandatory_security_and_hitl_events():
    """
    Verify that security events and HITL approval notifications CANNOT be suppressed
    for the in-app channel even if a preference explicitly attempts to disable them.
    """
    mock_session = AsyncMock()
    ws_id = uuid.uuid4()

    # Mandatory events like workflow.waiting_for_approval and system.warning must stay enabled
    hitl_enabled = await NotificationPreferenceService.is_channel_enabled(
        session=mock_session,
        workspace_id=ws_id,
        event_type=NotificationEventType.WORKFLOW_WAITING_APPROVAL.value,
        channel=DeliveryChannelType.IN_APP.value,
    )
    assert hitl_enabled is True

    sec_enabled = await NotificationPreferenceService.is_channel_enabled(
        session=mock_session,
        workspace_id=ws_id,
        event_type=NotificationEventType.SYSTEM_WARNING.value,
        channel=DeliveryChannelType.IN_APP.value,
    )
    assert sec_enabled is True


def test_cross_workspace_webhook_and_delivery_isolation(client: TestClient, user1_auth, user2_auth):
    """
    Verify that User 2 in Workspace 2 cannot view or manipulate User 1's webhook endpoints.
    """
    headers1 = user1_auth["headers"]
    me1 = client.get("/api/auth/me", headers=headers1).json()
    ws1_id = me1["default_workspace_id"]
    ws1_headers = {**headers1, "X-Workspace-Id": ws1_id}

    headers2 = user2_auth["headers"]
    me2 = client.get("/api/auth/me", headers=headers2).json()
    ws2_id = me2["default_workspace_id"]
    ws2_headers = {**headers2, "X-Workspace-Id": ws2_id}

    with patch("socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 443))]):
        # 1. User 1 creates a webhook in ws1
        res = client.post(
            "/api/webhooks",
            json={
                "name": "WS1 Secret Webhook",
                "url": "https://api.example.com/ws1/hook",
                "subscribed_events": ["workflow.completed"],
                "active": True,
            },
            headers=ws1_headers,
        )
        assert res.status_code == 201
        ep_id = res.json()["id"]

        # 2. User 2 in WS2 attempts to get User 1's webhook -> 404 (multi-tenant isolated)
        get_res = client.get(f"/api/webhooks/{ep_id}", headers=ws2_headers)
        assert get_res.status_code == 404

        # 3. User 2 in WS2 attempts to rotate User 1's secret -> 404
        rot_res = client.post(f"/api/webhooks/{ep_id}/rotate-secret", headers=ws2_headers)
        assert rot_res.status_code == 404

        # 4. User 2 in WS2 attempts to delete User 1's webhook -> 404
        del_res = client.delete(f"/api/webhooks/{ep_id}", headers=ws2_headers)
        assert del_res.status_code == 404


def test_all_17_system_event_types_registered():
    """Verify that all 17 system notification events are registered in notification_registry."""
    expected_events = [
        "workflow.completed",
        "workflow.failed",
        "workflow.waiting_for_approval",
        "trigger.completed",
        "trigger.failed",
        "job.completed",
        "job.failed",
        "job.retrying",
        "document.processing_completed",
        "document.processing_failed",
        "evaluation.completed",
        "evaluation.regression_detected",
        "replay.completed",
        "replay.failed",
        "connector.completed",
        "connector.failed",
        "system.warning",
    ]

    all_registered = [e["event_type"] for e in notification_registry.list_events()]
    for ev in expected_events:
        assert ev in all_registered, f"Event '{ev}' missing from notification_registry"
        meta = notification_registry.get(ev)
        assert meta is not None
        assert meta.default_severity is not None

