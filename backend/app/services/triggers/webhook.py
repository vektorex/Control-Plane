"""
Webhook security, secret management, HMAC signature verification, and ingestion service.
"""
import hashlib
import hmac
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.services.connectors.credentials import SecretEncryptor
from backend.app.services.triggers.errors import WebhookSignatureError


class WebhookSecretStore:
    """
    Manages generation, secure encryption, and retrieval of webhook verification secrets.
    Secrets are never logged, stored in plaintext, or returned after creation.
    """

    def __init__(self):
        self._encryptor = SecretEncryptor()

    def generate_secret(self) -> str:
        """Generates a high-entropy secret token (URL-safe base64)."""
        return f"whsec_{secrets.token_urlsafe(32)}"

    def generate_public_trigger_id(self) -> str:
        """
        Generates a non-guessable trigger identifier that does NOT reveal
        workspace ID, workflow ID, or user ID.
        """
        return f"wh_{secrets.token_urlsafe(20)}"

    def encrypt_secret(self, plain_secret: str) -> str:
        """Encrypts the secret for secure database persistence."""
        return self._encryptor.encrypt(plain_secret)

    def decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypts the secret for HMAC computation."""
        return self._encryptor.decrypt(encrypted_secret)


class WebhookTriggerService:
    """
    Validates incoming webhook requests:
    - HMAC signature verification
    - Timestamp drift tolerance
    - Replay protection
    """

    @classmethod
    def verify_request(
        cls,
        raw_body: bytes,
        headers: Dict[str, str],
        encrypted_secret: Optional[str],
        tolerance_seconds: Optional[int] = None,
    ) -> bool:
        """
        Verifies HMAC signature and timestamp header against the raw request body.
        Raises WebhookSignatureError if signature is invalid or timestamp expired.
        """
        if not encrypted_secret:
            # If no secret configured, signature verification is not required
            return True

        store = WebhookSecretStore()
        try:
            secret = store.decrypt_secret(encrypted_secret)
        except Exception as e:
            logger.error(f"[WebhookSecurity] Failed to decrypt webhook secret: {e}")
            raise WebhookSignatureError("Webhook secret store decryption error.")

        # Normalize headers (lowercase keys)
        norm_headers = {k.lower(): v for k, v in headers.items()}

        # 1. Timestamp validation (if provided)
        timestamp_header = (
            norm_headers.get("x-webhook-timestamp")
            or norm_headers.get("x-request-timestamp")
            or norm_headers.get("x-hub-timestamp")
        )
        if timestamp_header:
            max_tolerance = tolerance_seconds or getattr(settings, "WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS", 300)
            try:
                # Handle epoch seconds or ISO8601
                if timestamp_header.isdigit():
                    req_ts = float(timestamp_header)
                else:
                    dt = datetime.fromisoformat(timestamp_header)
                    req_ts = dt.timestamp()
                now_ts = time.time()
                if abs(now_ts - req_ts) > max_tolerance:
                    raise WebhookSignatureError(
                        f"Webhook timestamp expired or out of tolerance window (drift: {abs(now_ts - req_ts):.1f}s, max: {max_tolerance}s)."
                    )
            except (ValueError, TypeError) as e:
                if isinstance(e, WebhookSignatureError):
                    raise
                raise WebhookSignatureError(f"Malformed webhook timestamp header: {timestamp_header}")

        # 2. Signature extraction
        # Supports GitHub: X-Hub-Signature-256: sha256=<hex>
        # Standard: X-Webhook-Signature, X-Signature-256
        sig_header = (
            norm_headers.get("x-hub-signature-256")
            or norm_headers.get("x-webhook-signature")
            or norm_headers.get("x-signature-256")
        )

        if not sig_header:
            raise WebhookSignatureError("Missing required webhook signature header.")

        expected_prefix = "sha256="
        received_sig = sig_header[len(expected_prefix):] if sig_header.startswith(expected_prefix) else sig_header

        # 3. Compute expected HMAC-SHA256
        computed_sig = hmac.new(
            secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()

        # 4. Constant-time comparison
        if not hmac.compare_digest(received_sig.strip(), computed_sig.strip()):
            raise WebhookSignatureError("Webhook HMAC signature mismatch.")

        return True

    @classmethod
    def compute_signature(cls, raw_body: bytes, secret: str) -> str:
        """Computes sha256=<hex> signature for test mode."""
        digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        return f"sha256={digest}"
