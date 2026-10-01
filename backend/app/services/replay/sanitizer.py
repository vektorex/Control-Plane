import json
import re
from typing import Any, Dict, List, Optional, Set, Union
from backend.app.config import settings
from backend.app.services.replay.errors import SnapshotSanitizationError

# Key substrings that indicate sensitive credentials
SENSITIVE_KEY_PATTERNS = {
    "api_key",
    "apikey",
    "token",
    "secret",
    "authorization",
    "auth_header",
    "password",
    "passwd",
    "cookie",
    "bearer",
    "private_key",
    "privkey",
    "credential",
    "database_url",
    "db_url",
    "access_token",
    "refresh_token",
    "client_secret",
    "webhook_url",
    "signature",
}

# Regex patterns matching common secret formats within text
SENSITIVE_VALUE_REGEXES = [
    re.compile(r"sk-[a-zA-Z0-9_\-]{16,}", re.IGNORECASE),  # OpenAI/standard API keys
    re.compile(r"ghp_[a-zA-Z0-9]{20,}", re.IGNORECASE),   # GitHub personal access tokens
    re.compile(r"gho_[a-zA-Z0-9]{20,}", re.IGNORECASE),   # GitHub OAuth tokens
    re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE),  # Bearer tokens
    re.compile(r"eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]+"),  # JWTs
    re.compile(r"-----BEGIN\s+[A-Z ]*PRIVATE KEY-----[\s\S]*?-----END\s+[A-Z ]*PRIVATE KEY-----"),  # PEM keys
]

REDACTED_PLACEHOLDER = "[REDACTED]"
TRUNCATED_PLACEHOLDER = "... [TRUNCATED DUE TO SIZE LIMIT]"


def sanitize_string_value(val: str, max_str_chars: int = 100000) -> str:
    """Sanitizes regex secret patterns in a string and truncates oversized strings."""
    if not val:
        return val

    # Redact matched secret regex patterns
    sanitized = val
    for pattern in SENSITIVE_VALUE_REGEXES:
        sanitized = pattern.sub(REDACTED_PLACEHOLDER, sanitized)

    # Truncate string if oversized
    if len(sanitized) > max_str_chars:
        sanitized = sanitized[:max_str_chars] + TRUNCATED_PLACEHOLDER

    return sanitized


def sanitize_replay_data(item: Any, depth: int = 0, max_depth: int = 20) -> Any:
    """
    Recursively scrubs sensitive keys, credentials, and tokens from arbitrary data structures.
    """
    if depth > max_depth:
        return "[MAX_DEPTH_EXCEEDED]"

    if isinstance(item, dict):
        sanitized_dict: Dict[str, Any] = {}
        for k, v in item.items():
            key_lower = str(k).lower()
            if any(sens in key_lower for sens in SENSITIVE_KEY_PATTERNS):
                sanitized_dict[k] = REDACTED_PLACEHOLDER
            else:
                sanitized_dict[k] = sanitize_replay_data(v, depth + 1, max_depth)
        return sanitized_dict

    elif isinstance(item, list):
        return [sanitize_replay_data(elem, depth + 1, max_depth) for elem in item]

    elif isinstance(item, str):
        return sanitize_string_value(item)

    elif isinstance(item, (int, float, bool)) or item is None:
        return item

    else:
        # Fallback string representation
        return sanitize_string_value(str(item))


def sanitize_replay_snapshot(snapshot_data: Any, max_bytes: Optional[int] = None) -> Dict[str, Any]:
    """
    Central sanitizer for replay execution snapshots.
    Ensures zero secrets enter replay persistence and enforces MAX_REPLAY_SNAPSHOT_BYTES.
    """
    limit_bytes = max_bytes or getattr(settings, "MAX_REPLAY_SNAPSHOT_BYTES", 5000000)

    try:
        sanitized = sanitize_replay_data(snapshot_data)

        # Check total byte size
        serialized = json.dumps(sanitized, default=str)
        if len(serialized.encode("utf-8")) > limit_bytes:
            # Further truncate context and trace fields to fit within limit
            if isinstance(sanitized, dict):
                if "relevant_context_metadata" in sanitized:
                    sanitized["relevant_context_metadata"] = {
                        "notice": "Context metadata truncated to satisfy snapshot size limit",
                        "summary": str(sanitized.get("relevant_context_metadata"))[:10000] + TRUNCATED_PLACEHOLDER,
                    }
                if "trace_metadata" in sanitized:
                    sanitized["trace_metadata"] = {
                        "notice": "Trace metadata truncated to satisfy snapshot size limit",
                    }
            serialized = json.dumps(sanitized, default=str)

        if len(serialized.encode("utf-8")) > limit_bytes:
            raise SnapshotSanitizationError(
                f"Execution snapshot exceeds maximum allowable size of {limit_bytes} bytes even after sanitization."
            )

        return sanitized

    except Exception as exc:
        if isinstance(exc, SnapshotSanitizationError):
            raise
        raise SnapshotSanitizationError(f"Failed to sanitize execution snapshot: {exc}")
