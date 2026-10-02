"""
Safe filter validation and matcher for Step 26: Unified Event Bus.
"""
import re
from typing import List, Optional
from backend.app.services.events.errors import InvalidFilterError

# Allowed event categories for wildcard subscription (e.g. 'job.*')
ALLOWED_WILDCARD_CATEGORIES = {
    "job",
    "workflow",
    "trigger",
    "document",
    "evaluation",
    "replay",
    "connector",
    "approval",
    "notification",
    "system",
}

# Strict pattern regex: exactly category.* or category.action_name
PATTERN_REGEX = re.compile(r"^[a-z0-9_]+(\.\*|\.[a-z0-9_]+)?$")


class EventFilterValidator:
    """
    Validates event type patterns and filters to prevent SQL injection or regex DoS.
    """

    @classmethod
    def validate_event_type_pattern(cls, pattern: Optional[str]) -> Optional[str]:
        if not pattern:
            return None

        cleaned = pattern.strip().lower()
        if not PATTERN_REGEX.match(cleaned):
            raise InvalidFilterError(
                f"Pattern '{pattern}' is not a valid event filter. Use exact names or category wildcards (e.g. 'workflow.*')."
            )

        if cleaned.endswith(".*"):
            cat = cleaned[:-2]
            if cat not in ALLOWED_WILDCARD_CATEGORIES and cat != "*":
                raise InvalidFilterError(
                    f"Category '{cat}' is not a permitted wildcard prefix. Supported: {', '.join(sorted(ALLOWED_WILDCARD_CATEGORIES))}."
                )

        return cleaned

    @classmethod
    def matches(cls, event_type: str, pattern: Optional[str]) -> bool:
        """
        Determines whether a concrete event_type satisfies the filter pattern.
        """
        if not pattern or pattern == "*":
            return True

        if pattern.endswith(".*"):
            prefix = pattern[:-1]  # 'job.'
            return event_type.startswith(prefix)

        return event_type == pattern
