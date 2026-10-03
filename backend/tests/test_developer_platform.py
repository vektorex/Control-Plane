import pytest
import hmac
import hashlib
import time
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from backend.app.services.developer_platform.api_keys import APIKeyManager
from backend.app.services.developer_platform.environments import EnvironmentManager
from backend.app.services.developer_platform.scopes import ScopeRegistry, PUBLIC_SCOPES
from backend.app.services.developer_platform.request_signing import RequestSigner
from backend.app.services.developer_platform.validators import InputValidator
from backend.app.services.developer_platform.rate_limits import RateLimiter, APIRateLimiter
from backend.app.services.developer_platform.quotas import QuotaEnforcer
from backend.app.services.developer_platform.idempotency import IdempotencyManager
from backend.app.services.developer_platform.errors import (
    AuthenticationFailedError,
    CredentialExpiredError,
    CredentialRevokedError,
    ScopeDeniedError,
    ResourceScopeViolationError,
    EnvironmentMismatchError,
    RateLimitExceededError,
    QuotaExceededError,
    IdempotencyConflictError,
    SSRFBlockedError,
)
from backend.app.services.developer_platform.authentication import APIPrincipal


class TestAPIKeysAndEnvironments:
    """Test cryptographic key generation, prefixing, hashing, and verification."""

    def test_key_generation_formats(self):
        for env, prefix in [("development", "awl_dev_"), ("staging", "awl_stg_"), ("production", "awl_prod_")]:
            raw_key, key_prefix, key_hash = APIKeyManager.generate_key(env)
            assert raw_key.startswith(prefix)
            assert key_prefix.startswith(prefix)
            assert len(raw_key) > 30
            assert APIKeyManager.verify_key(raw_key, key_hash) is True
            # Tampered key fails
            assert APIKeyManager.verify_key(raw_key + "x", key_hash) is False

    def test_unknown_environment_prefix_fallback(self):
        raw_key, key_prefix, key_hash = APIKeyManager.generate_key("custom")
        assert raw_key.startswith("awl_dev_")
        assert APIKeyManager.verify_key(raw_key, key_hash) is True

    def test_environment_matching(self):
        assert EnvironmentManager.validate_environment("development") is True
        assert EnvironmentManager.validate_environment("production") is True
        assert EnvironmentManager.validate_environment("invalid") is False

        # Enforce key-environment match
        EnvironmentManager.enforce_isolation("development", "development")
        EnvironmentManager.enforce_isolation("production", "production")

        # Mismatch raises EnvironmentMismatchError
        with pytest.raises(EnvironmentMismatchError):
            EnvironmentManager.enforce_isolation("development", "production")
        with pytest.raises(EnvironmentMismatchError):
            EnvironmentManager.enforce_isolation("staging", "production")


class TestScopesAndPrivilegeEscalation:
    """Test scope validation, mapping to internal permissions, and escalation checks."""

    def test_scope_registry_completeness(self):
        assert len(PUBLIC_SCOPES) >= 20
        assert "tasks:run" in PUBLIC_SCOPES
        assert "workflows:run" in PUBLIC_SCOPES
        assert "models:read" in PUBLIC_SCOPES
        assert "webhooks:manage" in PUBLIC_SCOPES

    def test_scope_translation(self):
        assert ScopeRegistry.to_internal_permission("tasks:run") == "task.run"
        assert ScopeRegistry.to_internal_permission("workflows:run") == "workflow.run"
        assert ScopeRegistry.to_internal_permission("models:read") == "task.read"

    def test_scope_validation_unknown_scope(self):
        invalid = ScopeRegistry.validate_scopes(["tasks:run", "invalid:scope"])
        assert len(invalid) == 1
        assert "invalid:scope" in invalid

    def test_privilege_escalation_detection(self):
        # A non-admin user cannot assign sensitive scopes like tasks:run
        allowed_user_perms = {"task.read"}
        disallowed = ScopeRegistry.check_privilege_escalation(["tasks:run"], allowed_user_perms, is_org_admin=False)
        assert len(disallowed) > 0
        assert "tasks:run" in disallowed[0]

        # An org admin CAN assign tasks:run
        admin_disallowed = ScopeRegistry.check_privilege_escalation(["tasks:run"], allowed_user_perms, is_org_admin=True)
        assert len(admin_disallowed) == 0


class TestRequestSigningAndWebhooks:
    """Test HMAC-SHA256 signature generation, verification, replay window, and SSRF prevention."""

    def test_signature_roundtrip(self):
        secret = "whsec_test_secret_key_1234567890"
        payload = '{"event": "run.completed", "run_id": "run_123"}'
        timestamp = int(time.time())

        header = RequestSigner.generate_signature(payload, secret, timestamp)
        assert header.startswith(f"t={timestamp},v1=")

        # Valid signature succeeds
        valid = RequestSigner.verify_signature(payload, header, secret, tolerance_seconds=300)
        assert valid is True

    def test_signature_tampered_payload_fails(self):
        secret = "whsec_test_secret_key_1234567890"
        payload = '{"event": "run.completed", "run_id": "run_123"}'
        tampered = '{"event": "run.completed", "run_id": "run_456"}'
        header = RequestSigner.generate_signature(payload, secret)

        valid = RequestSigner.verify_signature(tampered, header, secret)
        assert valid is False

    def test_signature_stale_timestamp_fails(self):
        secret = "whsec_test_secret_key_1234567890"
        payload = '{"event": "run.completed"}'
        old_timestamp = int(time.time()) - 600  # 10 minutes ago

        header = RequestSigner.generate_signature(payload, secret, old_timestamp)
        valid = RequestSigner.verify_signature(payload, header, secret, tolerance_seconds=300)
        assert valid is False

    def test_webhook_ssrf_blocking(self):
        # Internal / private IPs must be blocked
        blocked_urls = [
            "http://127.0.0.1/webhook",
            "http://localhost:8000/webhook",
            "http://10.0.0.5/api",
            "http://192.168.1.1/events",
            "http://169.254.169.254/latest/meta-data/",
            "ftp://external.com/file",
        ]
        for url in blocked_urls:
            with pytest.raises(SSRFBlockedError):
                InputValidator.validate_webhook_url(url)

        # Public HTTPS URLs are permitted
        valid_urls = [
            "https://api.example.com/webhooks/awl",
            "https://hooks.slack.com/services/T00/B00/X00",
        ]
        for url in valid_urls:
            # Does not raise
            InputValidator.validate_webhook_url(url)


class TestRateLimiterAndQuotas:
    """Test rate limiting sliding window and quota enforcement."""

    @pytest.mark.asyncio
    async def test_rate_limiter_rpm_enforcement(self):
        await APIRateLimiter.reset_all()
        key_id = str(uuid4())
        app_id = str(uuid4())
        org_id = str(uuid4())

        # Execute 5 requests within limit of 5
        for i in range(5):
            res = await APIRateLimiter.check_rate_limit(
                organization_id=org_id,
                application_id=app_id,
                credential_id=key_id,
                endpoint="/api/v1/tasks/run",
                rpm_limit=5,
            )
            assert res.allowed is True
            headers = res.to_headers()
            assert headers["X-RateLimit-Limit"] == "5"

        # 6th request must be rejected (allowed=False) with Retry-After header
        res_blocked = await APIRateLimiter.check_rate_limit(
            organization_id=org_id,
            application_id=app_id,
            credential_id=key_id,
            endpoint="/api/v1/tasks/run",
            rpm_limit=5,
        )
        assert res_blocked.allowed is False
        blocked_headers = res_blocked.to_headers()
        assert "Retry-After" in blocked_headers
        assert int(blocked_headers["Retry-After"]) >= 1


class TestIdempotency:
    """Test idempotency fingerprinting and conflict detection."""

    def test_fingerprint_generation(self):
        endpoint = "/api/v1/tasks/123/runs"
        body1 = {"input": "test prompt", "stream": False}
        body2 = {"stream": False, "input": "test prompt"}  # same content, different key order
        body3 = {"input": "different prompt", "stream": False}

        fp1 = IdempotencyManager.compute_fingerprint("POST", endpoint, body1)
        fp2 = IdempotencyManager.compute_fingerprint("POST", endpoint, body2)
        fp3 = IdempotencyManager.compute_fingerprint("POST", endpoint, body3)

        assert fp1 == fp2  # Deterministic sorting
        assert fp1 != fp3


class TestPayloadSanitization:
    """Test anti-code and template injection protection on public inputs."""

    def test_dangerous_payload_rejection(self):
        from backend.app.services.developer_platform.errors import PublicAPIException

        dangerous_inputs = [
            {"input": "__import__('os').system('rm -rf /')"},
            {"code": "exec('import sys')"},
            {"template": "{{ __class__ }}"},
        ]
        for payload in dangerous_inputs:
            with pytest.raises(PublicAPIException):
                InputValidator.validate_workflow_inputs(payload)

    def test_safe_payload_acceptance(self):
        safe_payload = {
            "query": "What are the quarterly financial results?",
            "filter_year": 2026,
            "options": {"detailed": True, "tags": ["finance", "audit"]},
        }
        # Does not raise
        InputValidator.validate_workflow_inputs(safe_payload)


class TestPythonSDKContracts:
    """Test Python SDK logic without requiring live server."""

    def test_python_sdk_webhook_verification(self):
        import sys
        if "sdk/python" not in sys.path:
            sys.path.insert(0, "sdk/python")
        from ai_work_layer.webhooks import verify_webhook_signature

        secret = "sdk_test_secret_abc"
        payload = '{"event": "task.completed"}'
        timestamp = int(time.time())

        # Compute HMAC: t={ts}.{payload}
        signed_payload = f"{timestamp}.{payload}".encode("utf-8")
        expected_sig = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
        sig_header = f"t={timestamp},v1={expected_sig}"

        assert verify_webhook_signature(payload, sig_header, secret) is True
        assert verify_webhook_signature(payload + "tampered", sig_header, secret) is False

    def test_python_sdk_exceptions(self):
        import sys
        if "sdk/python" not in sys.path:
            sys.path.insert(0, "sdk/python")
        from ai_work_layer.exceptions import (
            AuthenticationError,
            RateLimitError,
            GovernanceError,
            APIError,
        )

        err = AuthenticationError("Invalid API Key", request_id="req_123")
        assert err.status_code == 401
        assert err.request_id == "req_123"
        assert isinstance(err, APIError)

        rate_err = RateLimitError("Rate limit exceeded", retry_after=30)
        assert rate_err.status_code == 429
        assert rate_err.retry_after == 30
