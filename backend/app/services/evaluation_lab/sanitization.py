import json
import re
from typing import Any, Dict, List, Set, Union

from backend.app.config import settings
from backend.app.services.evaluation_lab.errors import DatasetImportError, DatasetValidationError

# Sensitive keys to redact
SENSITIVE_KEY_PATTERNS = {
    "api_key", "apikey", "secret", "password", "token", "auth", "authorization",
    "cookie", "private_key", "access_token", "refresh_token", "jwt", "credential"
}

# Regex for detecting common secrets in string values
SECRET_REGEXES = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE),
    re.compile(r"Bearer\s+[a-zA-Z0-9\-._~+/]+=*", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"(postgres|mysql|mongodb):\/\/[^\s]+", re.IGNORECASE),
    re.compile(r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}", re.IGNORECASE),
]


def sanitize_value(val: Any, max_string_len: int = 50000) -> Any:
    """
    Recursively sanitize dictionaries, lists, and primitives:
    - Redacts sensitive keys and secret patterns with [REDACTED].
    - Truncates oversized strings.
    """
    if isinstance(val, dict):
        sanitized_dict = {}
        for k, v in val.items():
            k_lower = str(k).lower().strip()
            if any(pattern in k_lower for pattern in SENSITIVE_KEY_PATTERNS):
                sanitized_dict[k] = "[REDACTED]"
            else:
                sanitized_dict[k] = sanitize_value(v, max_string_len=max_string_len)
        return sanitized_dict

    if isinstance(val, list):
        return [sanitize_value(item, max_string_len=max_string_len) for item in val]

    if isinstance(val, str):
        cleaned = val
        for rgx in SECRET_REGEXES:
            cleaned = rgx.sub("[REDACTED]", cleaned)
        if len(cleaned) > max_string_len:
            cleaned = cleaned[:max_string_len] + f"... [TRUNCATED: {len(cleaned)} chars]"
        return cleaned

    return val


def validate_and_sanitize_case_payload(
    input_data: Dict[str, Any],
    expected_output: Any = None,
    expected_context: Any = None,
    expected_sources: Any = None,
    assertions: Any = None,
    metadata: Any = None,
) -> Dict[str, Any]:
    """
    Validates byte limits on a single evaluation case and returns a sanitized dictionary.
    """
    # Check input_data size
    input_bytes = len(json.dumps(input_data or {}).encode("utf-8"))
    if input_bytes > settings.MAX_CASE_INPUT_BYTES:
        raise DatasetValidationError(
            f"Case input exceeds MAX_CASE_INPUT_BYTES ({input_bytes} > {settings.MAX_CASE_INPUT_BYTES})"
        )

    sanitized_input = sanitize_value(input_data or {})
    sanitized_output = sanitize_value(expected_output) if expected_output is not None else None
    sanitized_context = sanitize_value(expected_context) if expected_context is not None else None
    sanitized_sources = sanitize_value(expected_sources) if expected_sources is not None else None
    sanitized_assertions = sanitize_value(assertions or [])
    sanitized_metadata = sanitize_value(metadata or {})

    return {
        "input_data": sanitized_input,
        "expected_output": sanitized_output,
        "expected_context": sanitized_context,
        "expected_sources": sanitized_sources,
        "assertions": sanitized_assertions,
        "metadata": sanitized_metadata,
    }


def validate_dataset_import_payload(raw_content_bytes: bytes, max_bytes: int = None) -> None:
    """
    Validates total dataset payload size before parsing.
    """
    limit = max_bytes or settings.MAX_DATASET_BYTES
    if len(raw_content_bytes) > limit:
        raise DatasetImportError(
            f"Dataset import payload exceeds maximum size limit ({len(raw_content_bytes)} > {limit} bytes)"
        )
