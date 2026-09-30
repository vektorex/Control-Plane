"""
Centralized secret detection, input sanitization, and safety normalization for persistent memories.
"""
import json
import re
from typing import Any, Dict, List, Optional, Tuple
from backend.app.services.memory.errors import (
    MemorySecretDetectedError,
    MemoryValidationError,
)

MAX_MEMORY_CONTENT_CHARS = 10000
MAX_MEMORY_METADATA_BYTES = 50000

# High-confidence secret detection regex patterns
SECRET_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----", re.IGNORECASE)),
    ("jwt_token", re.compile(r"\beyJ[a-zA-Z0-9_\-]{10,}\.eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\b")),
    ("bearer_token", re.compile(r"\bBearer\s+[a-zA-Z0-9_\-\.]{16,}\b", re.IGNORECASE)),
    ("openai_api_key", re.compile(r"\bsk-[a-zA-Z0-9]{20,T3BlbkFJ[a-zA-Z0-9]{20,}\b|\bsk-proj-[a-zA-Z0-9_\-]{30,}\b")),
    ("github_token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr|github_pat)_[a-zA-Z0-9_]{16,}\b")),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}\b")),
    ("aws_secret_key", re.compile(r"(?i)\baws_secret_access_key\s*[:=]\s*[a-zA-Z0-9/+=]{40}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[0-9]{10,}-[0-9]{10,}-[a-zA-Z0-9]{24,}\b")),
    ("stripe_secret", re.compile(r"\b(?:sk_live|rk_live)_[0-9a-zA-Z]{24,}\b")),
    ("db_connection_uri", re.compile(r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|mssql):\/\/[^\s:@]+:[^\s:@]+@[^\s/]+\b", re.IGNORECASE)),
    ("generic_secret_assignment", re.compile(r"(?i)\b(?:api[_-]?key|secret[_-]?key|auth[_-]?token|client[_-]?secret|password|passwd|pwd)\s*[:=]\s*['\"]?[a-zA-Z0-9_\-+=/]{16,}['\"]?")),
]


class SecretDetector:
    """
    Centralized scanner for sensitive credentials, authorization tokens, and private secrets.
    """

    @classmethod
    def detect_secrets(cls, text: str) -> List[str]:
        """
        Scans text for credential patterns.
        Returns a list of detected pattern names without echoing matched secret tokens.
        """
        if not text:
            return []
        detected: List[str] = []
        for name, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                detected.append(name)
        return detected

    @classmethod
    def redact_secrets(cls, text: str) -> str:
        """
        Replaces sensitive credential patterns with safe redacted markers.
        """
        if not text:
            return ""
        sanitized = text
        for name, pattern in SECRET_PATTERNS:
            sanitized = pattern.sub(f"[REDACTED_{name.upper()}]", sanitized)
        return sanitized


def normalize_whitespace(text: str) -> str:
    """
    Normalizes consecutive whitespace while preserving intentional paragraph structure.
    """
    if not text:
        return ""
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.strip().splitlines()]
    # Collapse 3+ consecutive newlines to 2
    normalized = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", normalized).strip()


def sanitize_metadata(meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Prunes unsafe authorization keys, bearer headers, and checks byte constraints.
    """
    if not meta:
        return {}
    if not isinstance(meta, dict):
        return {}

    sanitized: Dict[str, Any] = {}
    unsafe_keys = {
        "authorization",
        "cookie",
        "set-cookie",
        "password",
        "token",
        "secret",
        "api_key",
        "access_token",
        "refresh_token",
        "private_key",
    }

    def _clean_val(k: str, v: Any, depth: int = 0) -> Any:
        if depth > 4:
            return str(v)[:200]
        if k.lower() in unsafe_keys:
            return "[REMOVED_SECURITY_FIELD]"
        if isinstance(v, dict):
            return {ck: _clean_val(ck, cv, depth + 1) for ck, cv in v.items() if ck.lower() not in unsafe_keys}
        elif isinstance(v, list):
            return [_clean_val(k, item, depth + 1) for item in v[:50]]
        elif isinstance(v, (str, int, float, bool)) or v is None:
            if isinstance(v, str):
                return SecretDetector.redact_secrets(v[:2000])
            return v
        return str(v)[:500]

    for k, v in meta.items():
        if k.lower() not in unsafe_keys:
            sanitized[k] = _clean_val(k, v, 0)

    try:
        serialized = json.dumps(sanitized)
        if len(serialized.encode("utf-8")) > MAX_MEMORY_METADATA_BYTES:
            raise MemoryValidationError(
                f"Memory metadata exceeds maximum size limit of {MAX_MEMORY_METADATA_BYTES} bytes."
            )
    except MemoryValidationError:
        raise
    except Exception:
        sanitized = {"sanitized": True}

    return sanitized


def sanitize_memory(
    title: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    enforce_no_secrets: bool = True,
) -> Tuple[str, str, str, Dict[str, Any]]:
    """
    Sanitizes title, content, and metadata before persisting into the Memory System.
    
    Returns:
        (sanitized_title, sanitized_content, normalized_content, sanitized_metadata)
    Raises:
        MemorySecretDetectedError if enforce_no_secrets is True and secrets are found.
        MemoryValidationError if length constraints are violated.
    """
    if not title or not title.strip():
        raise MemoryValidationError("Memory title cannot be empty.")
    if not content or not content.strip():
        raise MemoryValidationError("Memory content cannot be empty.")

    clean_title = normalize_whitespace(title)[:255]

    # Secret scanning
    title_secrets = SecretDetector.detect_secrets(clean_title)
    content_secrets = SecretDetector.detect_secrets(content)
    all_secrets = list(set(title_secrets + content_secrets))

    if all_secrets and enforce_no_secrets:
        raise MemorySecretDetectedError(detected_categories=all_secrets)

    # Redact any residual patterns safely
    clean_title = SecretDetector.redact_secrets(clean_title)
    redacted_content = SecretDetector.redact_secrets(content)

    # Truncate content to maximum allowed character budget
    if len(redacted_content) > MAX_MEMORY_CONTENT_CHARS:
        redacted_content = redacted_content[:MAX_MEMORY_CONTENT_CHARS] + " ...[truncated]"

    normalized_content = normalize_whitespace(redacted_content)
    clean_meta = sanitize_metadata(metadata)

    return clean_title, redacted_content, normalized_content, clean_meta
