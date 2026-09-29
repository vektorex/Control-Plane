import re
from typing import Optional


# Patterns to scrub from any error message
SENSITIVE_PATTERNS = [
    re.compile(r'(?i)(bearer\s+)[a-zA-Z0-9_\-\.]{15,}'),
    re.compile(r'(?i)(sk-[a-zA-Z0-9]{20,})'),
    re.compile(r'(?i)(password\s*[:=]\s*)[^\s,;&]+'),
    re.compile(r'(?i)(secret\s*[:=]\s*)[^\s,;&]+'),
    re.compile(r'(?i)(api[_\-]?key\s*[:=]\s*)[^\s,;&]+'),
    re.compile(r'(?i)(token\s*[:=]\s*)[^\s,;&]+'),
]


def sanitize_error_message(msg: Optional[str], max_len: int = 500) -> Optional[str]:
    """
    Sanitizes raw error messages by stripping secrets, keys, and truncating to a safe max length.
    """
    if not msg:
        return None

    cleaned = str(msg)
    for pat in SENSITIVE_PATTERNS:
        cleaned = pat.sub(r'\1[REDACTED]', cleaned)

    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len] + "... [truncated]"

    return cleaned


def extract_error_code(exc: Exception) -> str:
    """
    Extracts a normalized, stable error code from an exception object.
    """
    if hasattr(exc, "code") and exc.code:
        return str(exc.code).upper()
    if hasattr(exc, "status_code") and exc.status_code:
        return f"HTTP_{exc.status_code}"
    
    cls_name = exc.__class__.__name__
    # Convert CamelCase to SNAKE_CASE
    snake = re.sub(r'(?<!^)(?=[A-Z])', '_', cls_name).upper()
    return snake
