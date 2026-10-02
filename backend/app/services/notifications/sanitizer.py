"""
NotificationSanitizer: Deep secret removal, payload truncation, and HTML safety.
"""
import copy
import re
from typing import Any, Dict, List, Union


class NotificationSanitizer:
    """
    Sanitizes notification bodies, metadata, webhook payloads, and HTML email templates
    to prevent leaking credentials, internal secrets, or malicious scripts.
    """

    SECRET_KEY_PATTERNS = [
        r"api[-_]?key",
        r"secret[-_]?key",
        r"client[-_]?secret",
        r"private[-_]?key",
        r"password",
        r"access[-_]?token",
        r"refresh[-_]?token",
        r"auth[-_]?token",
        r"credentials",
        r"bearer",
    ]

    SECRET_VALUE_PREFIXES = (
        "sk-",
        "ghp_",
        "gho_",
        "github_pat_",
        "xoxb-",
        "xoxp-",
        "bearer ey",
    )

    MAX_PAYLOAD_BYTES = 64 * 1024  # 64 KB

    @classmethod
    def sanitize_payload(cls, data: Any) -> Any:
        """
        Creates a deep sanitized copy of any dictionary/list structure,
        replacing detected credential keys or values with '[REDACTED]'.
        """
        data_copy = copy.deepcopy(data)
        return cls._sanitize_node(data_copy)

    @classmethod
    def _sanitize_node(cls, node: Any) -> Any:
        if isinstance(node, dict):
            sanitized_dict = {}
            for k, v in node.items():
                k_str = str(k).lower()
                is_secret_key = any(re.search(pat, k_str) for pat in cls.SECRET_KEY_PATTERNS)
                if is_secret_key:
                    sanitized_dict[k] = "[REDACTED]"
                else:
                    sanitized_dict[k] = cls._sanitize_node(v)
            return sanitized_dict
        elif isinstance(node, list):
            return [cls._sanitize_node(item) for item in node]
        elif isinstance(node, str):
            val_strip = node.strip().lower()
            if any(val_strip.startswith(p) for p in cls.SECRET_VALUE_PREFIXES):
                return "[REDACTED]"
            if "bearer ey" in val_strip:
                return "[REDACTED]"
            # Truncate strings larger than 16KB individually
            if len(node) > 16384:
                return node[:16384] + "... [TRUNCATED]"
            return node
        return node

    @classmethod
    def sanitize_html(cls, html_content: str) -> str:
        """
        Strips executable script tags, iframes, and javascript: links for safe email rendering.
        """
        if not html_content:
            return ""
        # Remove script and iframe elements
        clean = re.sub(r"<\s*script[^>]*>[\s\S]*?<\s*/\s*script\s*>", "", html_content, flags=re.IGNORECASE)
        clean = re.sub(r"<\s*iframe[^>]*>[\s\S]*?<\s*/\s*iframe\s*>", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"<\s*style[^>]*>[\s\S]*?<\s*/\s*style\s*>", "", clean, flags=re.IGNORECASE)
        # Remove event handlers (e.g. onload, onerror, onclick)
        clean = re.sub(r"\bon\w+\s*=\s*['\"][^'\"]*['\"]", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\bon\w+\s*=\s*[^ >]+", "", clean, flags=re.IGNORECASE)
        # Remove javascript: uris
        clean = re.sub(r"href\s*=\s*['\"]javascript:[^'\"]*['\"]", "href=\"#\"", clean, flags=re.IGNORECASE)
        return clean

    @classmethod
    def build_webhook_payload(
        cls,
        event_id: str,
        event_type: str,
        timestamp: str,
        workspace_id: str,
        source_type: str,
        source_id: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Constructs the normalized, sanitized webhook event payload conforming to spec.
        """
        clean_data = cls.sanitize_payload(data)
        return {
            "id": event_id,
            "type": event_type,
            "timestamp": timestamp,
            "workspace_id": workspace_id,
            "source": {
                "type": source_type,
                "id": source_id,
            },
            "data": clean_data,
        }
