"""
CacheSanitizer equivalent for Governance: strips secrets and sensitive metadata
from governance audit payloads before persisting. Step 32.
"""
import re
from typing import Any, Dict


# Patterns for secrets/credentials – never store these in audit logs
_SECRET_PATTERNS = [
    re.compile(r"(api[-_]?key|apikey|secret[-_]?key|access[-_]?token|refresh[-_]?token|"
               r"password|passwd|bearer|authorization|private[-_]?key|"
               r"connection[-_]?string|database[-_]?url|webhook[-_]?secret)\s*[:=]\s*\S+",
               re.IGNORECASE),
]

_SENSITIVE_KEYS = {
    "api_key", "apikey", "secret", "secret_key", "password", "passwd",
    "token", "access_token", "refresh_token", "authorization", "auth",
    "private_key", "credential", "credentials", "database_url",
    "connection_string", "webhook_secret", "bearer",
    "system_prompt", "hidden_prompt", "chain_of_thought",
}


class GovernanceSanitizer:
    """
    Strips secrets, credentials, and hidden prompts from governance audit metadata.
    Never mutates the original object; always returns a clean copy.
    """

    @staticmethod
    def sanitize_dict(data: Dict[str, Any], depth: int = 0) -> Dict[str, Any]:
        """Return a sanitized copy of the dict, recursively scrubbing sensitive keys."""
        if depth > 8:
            return {}
        cleaned: Dict[str, Any] = {}
        for key, value in data.items():
            if key.lower() in _SENSITIVE_KEYS:
                cleaned[key] = "[REDACTED]"
            elif isinstance(value, dict):
                cleaned[key] = GovernanceSanitizer.sanitize_dict(value, depth + 1)
            elif isinstance(value, list):
                cleaned[key] = GovernanceSanitizer.sanitize_list(value, depth + 1)
            elif isinstance(value, str):
                cleaned[key] = GovernanceSanitizer.sanitize_string(value)
            else:
                cleaned[key] = value
        return cleaned

    @staticmethod
    def sanitize_list(data: list, depth: int = 0) -> list:
        if depth > 8:
            return []
        result = []
        for item in data:
            if isinstance(item, dict):
                result.append(GovernanceSanitizer.sanitize_dict(item, depth + 1))
            elif isinstance(item, str):
                result.append(GovernanceSanitizer.sanitize_string(item))
            else:
                result.append(item)
        return result

    @staticmethod
    def sanitize_string(value: str) -> str:
        for pattern in _SECRET_PATTERNS:
            value = pattern.sub("[REDACTED]", value)
        return value

    @staticmethod
    def sanitize_reasons(reasons: list[str]) -> list[str]:
        """Ensure reason strings are factual and free of internal security logic."""
        return [GovernanceSanitizer.sanitize_string(r) for r in reasons[:20]]
