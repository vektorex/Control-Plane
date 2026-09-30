"""
Memory creation, trust boundaries, retention, and scoping policies.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Set
from backend.app.services.memory.errors import MemoryPermissionError, MemoryValidationError
from backend.app.services.memory.schemas import (
    MemoryImportance,
    MemoryScope,
    MemorySourceType,
    MemoryType,
)

# Trust hierarchy levels from highest authority to lowest
TRUST_HIERARCHY = [
    "system_policy",
    "application_policy",
    "security_policy",
    "workflow_policy",
    "explicit_user_context",
    "persistent_memory",
    "retrieved_external_data",
]

SOURCE_TRUST_MAP = {
    MemorySourceType.EXPLICIT_USER: "trusted",
    MemorySourceType.SYSTEM: "trusted",
    MemorySourceType.TASK: "candidate",
    MemorySourceType.WORKFLOW: "candidate",
    MemorySourceType.DOCUMENT: "external_untrusted",
    MemorySourceType.CONNECTOR: "external_untrusted",
}

ALLOWED_MEMORY_TYPES: Set[str] = {t.value for t in MemoryType}
ALLOWED_MEMORY_SCOPES: Set[str] = {s.value for s in MemoryScope}


class MemoryPolicy:
    """
    Evaluates permissions, trust levels, confirmation requirements, and expiration dates
    for candidate and explicit memories.
    """

    @classmethod
    def get_source_trust(cls, source_type: str) -> str:
        try:
            st = MemorySourceType(source_type)
            return SOURCE_TRUST_MAP.get(st, "external_untrusted")
        except ValueError:
            return "external_untrusted"

    @classmethod
    def requires_confirmation(cls, source_type: str) -> bool:
        """
        Determines whether memory creation requires explicit user confirmation.
        Explicit user actions are persisted directly. AI suggestions, task extractions,
        workflows, documents, and connectors MUST require confirmation.
        """
        trust = cls.get_source_trust(source_type)
        if source_type == MemorySourceType.EXPLICIT_USER.value:
            return False
        if source_type == MemorySourceType.SYSTEM.value:
            return False
        # External, task, and workflow sources ALWAYS require confirmation before becoming active
        return True

    @classmethod
    def can_automatically_persist(cls, source_type: str) -> bool:
        """
        External connectors and documents must NEVER automatically become persistent memories.
        """
        if source_type in (MemorySourceType.CONNECTOR.value, MemorySourceType.DOCUMENT.value):
            return False
        if source_type in (MemorySourceType.TASK.value, MemorySourceType.WORKFLOW.value):
            return False
        return source_type in (MemorySourceType.EXPLICIT_USER.value, MemorySourceType.SYSTEM.value)

    @classmethod
    def calculate_expiration(cls, expiration_pref: Optional[str], custom_expires_at: Optional[datetime] = None) -> Optional[datetime]:
        """
        Translates expiration preference strings into concrete UTC timestamps.
        """
        if custom_expires_at:
            if custom_expires_at.tzinfo is None:
                return custom_expires_at.replace(tzinfo=timezone.utc)
            return custom_expires_at

        pref = (expiration_pref or "never").lower().strip()
        now = datetime.now(timezone.utc)

        if pref == "7_days":
            return now + timedelta(days=7)
        elif pref == "30_days":
            return now + timedelta(days=30)
        elif pref == "90_days":
            return now + timedelta(days=90)
        elif pref == "never":
            return None
        return None

    @classmethod
    def validate_scope(
        cls,
        scope: str,
        user_id: Optional[str],
        project_id: Optional[str],
    ) -> None:
        """
        Enforces scope integrity:
        - user scope requires an authorized user_id
        - project scope requires an associated project_id
        """
        if scope not in ALLOWED_MEMORY_SCOPES:
            raise MemoryValidationError(f"Invalid scope '{scope}'. Allowed: {ALLOWED_MEMORY_SCOPES}")

        if scope == MemoryScope.USER.value and not user_id:
            raise MemoryValidationError("User-scoped memory requires an authenticated user ID.")

        if scope == MemoryScope.PROJECT.value and not project_id:
            raise MemoryValidationError("Project-scoped memory requires a valid project ID.")
