"""
Webhook Signature Verification for Python SDK.
Uses HMAC-SHA256 and constant-time comparison.
"""
import hashlib
import hmac
import time
from typing import Union


def verify_webhook_signature(
    payload: Union[str, bytes],
    signature_header: str,
    secret: str,
    tolerance_seconds: int = 300,
) -> bool:
    """
    Verifies that incoming webhook request was genuinely dispatched by AI Work Layer.
    Verifies timestamp against replay tolerance and uses hmac.compare_digest.
    """
    if not payload or not signature_header or not secret:
        return False

    parts = {}
    for segment in signature_header.split(","):
        if "=" in segment:
            k, v = segment.strip().split("=", 1)
            parts[k] = v

    ts_str = parts.get("t")
    sig = parts.get("v1")
    if not ts_str or not sig:
        return False

    try:
        timestamp = int(ts_str)
    except ValueError:
        return False

    # Check replay tolerance window
    now = int(time.time())
    if abs(now - timestamp) > tolerance_seconds:
        return False

    # Compute expected signature
    if isinstance(payload, bytes):
        payload_bytes = payload
    else:
        payload_bytes = payload.encode("utf-8")

    signed_data = f"{timestamp}.".encode("utf-8") + payload_bytes
    expected = hmac.new(secret.encode("utf-8"), signed_data, hashlib.sha256).hexdigest()

    return hmac.compare_digest(sig, expected)
