"""
Security sanitizer for Knowledge Graph entities, relationships, properties, and source references.
Prevents credentials, API keys, bearer tokens, and private data from being persisted in the graph.
"""
import re
from typing import Any, Dict, List, Set

SENSITIVE_KEY_PATTERNS = re.compile(
    r"(password|secret|token|api_key|apikey|bearer|auth|credential|private_key|access_key)",
    re.IGNORECASE,
)

CREDENTIAL_VALUE_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9_-]{20,}", re.IGNORECASE),  # OpenAI-style
    re.compile(r"sk-ant-[a-zA-Z0-9_-]{20,}", re.IGNORECASE),  # Anthropic
    re.compile(r"gh[pousr][_-][a-zA-Z0-9_]{10,}", re.IGNORECASE),  # GitHub tokens (ghp_, gho_, ghs_, ghu_, ghr_)
    re.compile(r"AKIA[0-9A-Z]{16}", re.IGNORECASE),  # AWS Access Key
    re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE),  # Bearer
    re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----", re.IGNORECASE),  # Private key
    re.compile(r"(postgres|mysql|mongodb|redis):\/\/[^\s]+:[^\s]+@", re.IGNORECASE),  # URIs with passwords
]


def mask_secrets_in_text(text: str) -> str:
    """
    Replaces detected credential sequences with [REDACTED_CREDENTIAL].
    """
    if not text:
        return ""
    masked = text
    for pattern in CREDENTIAL_VALUE_PATTERNS:
        masked = pattern.sub("[REDACTED_CREDENTIAL]", masked)
    return masked


def sanitize_value(val: Any) -> Any:
    """
    Recursively inspects and sanitizes strings, dicts, and lists.
    """
    if isinstance(val, str):
        return mask_secrets_in_text(val)
    elif isinstance(val, dict):
        return sanitize_properties(val)
    elif isinstance(val, list):
        return [sanitize_value(item) for item in val]
    return val


def sanitize_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitizes entity and relationship properties.
    Removes keys matching sensitive names and masks credential values.
    """
    if not properties:
        return {}

    cleaned: Dict[str, Any] = {}
    for k, v in properties.items():
        if SENSITIVE_KEY_PATTERNS.search(k):
            cleaned[k] = "[REDACTED_CREDENTIAL]"
        else:
            cleaned[k] = sanitize_value(v)
    return cleaned


def sanitize_source_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensures source references and provenance metadata never store credentials or private auth tokens.
    """
    return sanitize_properties(metadata)


# Alias
scrub_secrets_from_text = mask_secrets_in_text
