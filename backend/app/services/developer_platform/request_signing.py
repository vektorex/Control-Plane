"""
HMAC Request Signing and Webhook Signature Verification.
Step 37: Public API, Developer Platform & SDK Layer.
"""
import hashlib
import hmac
import time
from typing import Optional, Tuple


class RequestSigner:
    """Computes and verifies HMAC-SHA256 signatures for webhook delivery."""

    HEADER_NAME = "X-AWL-Signature"

    @classmethod
    def compute_signature(cls, payload: str, secret: str, timestamp: Optional[int] = None) -> Tuple[str, int]:
        """
        Computes HMAC-SHA256 signature for payload.
        Returns (signature_header_value, timestamp).
        Header format: t={timestamp},v1={hex_digest}
        """
        ts = timestamp if timestamp is not None else int(time.time())
        signed_payload = f"{ts}.{payload}".encode("utf-8")
        computed = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
        header_val = f"t={ts},v1={computed}"
        return header_val, ts

    @classmethod
    def generate_signature(cls, payload: str, secret: str, timestamp: Optional[int] = None) -> str:
        """Convenience method returning signature header value directly."""
        header_val, _ = cls.compute_signature(payload, secret, timestamp)
        return header_val

    @classmethod
    def verify_signature(
        cls,
        payload: str,
        signature_header: str,
        secret: str,
        tolerance_seconds: int = 300,
    ) -> bool:
        """
        Verifies signature header against payload and secret.
        Uses constant-time comparison and checks against replay window.
        """
        if not signature_header or not secret:
            return False

        # Parse header: t=12345,v1=abcdef...
        parts = {}
        for item in signature_header.split(","):
            if "=" in item:
                k, v = item.strip().split("=", 1)
                parts[k] = v

        ts_str = parts.get("t")
        sig = parts.get("v1")
        if not ts_str or not sig:
            return False

        try:
            timestamp = int(ts_str)
        except ValueError:
            return False

        # Check timestamp against replay tolerance
        now = int(time.time())
        if abs(now - timestamp) > tolerance_seconds:
            return False

        # Compute expected signature
        signed_payload = f"{timestamp}.{payload}".encode("utf-8")
        expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()

        return hmac.compare_digest(sig, expected)
