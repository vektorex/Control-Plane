import json
import re
from typing import Any, Dict, List, Optional, Set, Union
from backend.app.config import settings


# Keys to completely remove or redact in metadata
REDACTED_KEYS: Set[str] = {
    "authorization",
    "auth",
    "bearer",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "apikey",
    "secret",
    "password",
    "cookie",
    "set-cookie",
    "chain_of_thought",
    "cot",
    "internal_reasoning",
    "thought_process",
    "evaluator_prompt",
    "system_prompt",
}

# Regex to find secrets in string values
SECRET_REGEXES = [
    re.compile(r'(?i)bearer\s+[a-zA-Z0-9_\-\.]{15,}'),
    re.compile(r'(?i)sk-[a-zA-Z0-9]{20,}'),
    re.compile(r'(?i)password\s*[:=]\s*[^\s,;&]+'),
    re.compile(r'(?i)secret\s*[:=]\s*[^\s,;&]+'),
    re.compile(r'(?i)api[_\-]?key\s*[:=]\s*[^\s,;&]+'),
]

MAX_STRING_LENGTH = 1000


def _clean_value(val: Any, depth: int = 0) -> Any:
    if depth > 5:
        return "[Max Depth Reached]"

    if isinstance(val, str):
        # Redact known secret regex patterns
        cleaned = val
        for rgx in SECRET_REGEXES:
            cleaned = rgx.sub("[REDACTED_SECRET]", cleaned)
        if len(cleaned) > MAX_STRING_LENGTH:
            cleaned = cleaned[:MAX_STRING_LENGTH] + "... [truncated]"
        return cleaned

    if isinstance(val, dict):
        cleaned_dict = {}
        for k, v in val.items():
            k_lower = str(k).lower()
            if any(sens in k_lower for sens in REDACTED_KEYS):
                cleaned_dict[str(k)] = "[REDACTED]"
            else:
                cleaned_dict[str(k)] = _clean_value(v, depth + 1)
        return cleaned_dict

    if isinstance(val, list):
        return [_clean_value(item, depth + 1) for item in val[:50]]

    if isinstance(val, (int, float, bool)) or val is None:
        return val

    # Fallback to string representation
    str_val = str(val)
    if len(str_val) > MAX_STRING_LENGTH:
        str_val = str_val[:MAX_STRING_LENGTH] + "... [truncated]"
    return str_val


def sanitize_metadata(
    metadata: Optional[Dict[str, Any]],
    max_bytes: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Sanitizes trace and telemetry metadata:
    - Strips API keys, bearer tokens, auth headers, passwords, secrets
    - Strips internal hidden reasoning and chain-of-thought fields
    - Truncates oversized string properties
    - Enforces maximum serialized JSON byte limit (MAX_TRACE_METADATA_BYTES)
    """
    if not metadata:
        return {}

    limit = max_bytes or getattr(settings, "MAX_TRACE_METADATA_BYTES", 10240)
    cleaned = _clean_value(metadata)

    if not isinstance(cleaned, dict):
        return {"value": str(cleaned)[:MAX_STRING_LENGTH]}

    try:
        serialized = json.dumps(cleaned)
        if len(serialized.encode("utf-8")) > limit:
            # Over budget, trim down to key-summary
            trimmed = {
                "summary": "Metadata payload exceeded size limit and was compacted",
                "original_keys": list(cleaned.keys())[:20],
                "item_count": len(cleaned),
            }
            return trimmed
        return cleaned
    except Exception:
        return {"error": "Failed to serialize metadata safely"}
