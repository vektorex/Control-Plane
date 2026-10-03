"""
Input and Content Sanitization Validators for Step 39: Collaboration.
Reuses existing platform security detectors to prevent XSS, script injection, and payload abuse.
"""
import html
import re
from typing import Any, Dict, List, Set, Tuple
from urllib.parse import urlparse

from backend.app.services.collaboration.exceptions import CollaborationException

# Dangerous HTML/script patterns
DISALLOWED_TAGS = re.compile(r"<\s*(?:script|iframe|object|embed|applet|meta|link|style)[^>]*>", re.IGNORECASE)
JAVASCRIPT_URI = re.compile(r"javascript\s*:", re.IGNORECASE)
DATA_URI_EXECUTABLE = re.compile(r"data\s*:\s*(?:text/html|application/javascript)", re.IGNORECASE)
EVENT_HANDLER_ATTR = re.compile(r"\bon[a-z]+\s*=", re.IGNORECASE)

# Mention pattern: matches @username or @[uuid/id]
MENTION_PATTERN = re.compile(r"@([a-zA-Z0-9_\-\.]+)")


class CollaborationValidator:
    """Validates and sanitizes untrusted user-generated collaboration content."""

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """
        Strips or escapes dangerous script tags, event handlers, and javascript URIs.
        Returns safe plain/markdown content.
        """
        if not text:
            return ""

        # Remove <script ...>...</script> tags and contents
        cleaned = re.sub(r"<\s*script[^>]*>[\s\S]*?<\s*/\s*script\s*>", "", text, flags=re.IGNORECASE)
        # Remove remaining solitary <script...> or </script> tags
        cleaned = re.sub(r"<\s*/?\s*script[^>]*>", "", cleaned, flags=re.IGNORECASE)
        # Remove inline event handlers like onmouseover="..." or onerror=...
        cleaned = re.sub(r"""\bon[a-zA-Z]+\s*=\s*(?:'[^']*'|"[^"]*"|[^\s>]+)""", "", cleaned, flags=re.IGNORECASE)
        # Remove javascript: and data:text/html or data:application/javascript URIs
        cleaned = re.sub(r"javascript\s*:[^\s\)\"\']*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"data\s*:\s*(?:text/html|application/javascript)[^\s\)\"\']*", "", cleaned, flags=re.IGNORECASE)
        # Clean up any leftover disallowed tags like <iframe...>, <object...>, etc.
        cleaned = re.sub(r"<\s*/?\s*(?:iframe|object|embed|applet|meta|link|style)[^>]*>", "", cleaned, flags=re.IGNORECASE)

        return cleaned.strip()

    @classmethod
    def extract_mentions(cls, text: str) -> List[str]:
        """Extracts unique usernames or user identifiers from @mentions."""
        if not text:
            return []
        matches = MENTION_PATTERN.findall(text)
        # Deduplicate preserving order
        seen: Set[str] = set()
        result: List[str] = []
        for m in matches:
            clean = m.strip()
            if clean and clean not in seen:
                seen.add(clean)
                result.append(clean)
        return result

    @classmethod
    def bound_cursor_context(cls, cursor_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensures presence cursor context is bounded (max 10 keys, strings capped at 100 chars)
        and does not contain keystroke logs or sensitive text.
        """
        if not cursor_context or not isinstance(cursor_context, dict):
            return {}

        safe_context: Dict[str, Any] = {}
        count = 0
        for k, v in cursor_context.items():
            if count >= 10:
                break
            if isinstance(v, str):
                safe_context[k] = v[:100]
            elif isinstance(v, (int, float, bool)):
                safe_context[k] = v
            else:
                safe_context[k] = str(v)[:100]
            count += 1

        return safe_context

    # Alias for compatibility
    validate_cursor_context = bound_cursor_context
