"""
Policy engine and authorization guard for Step 26: Unified Event Bus.
"""
from typing import Any, List, Optional
from uuid import UUID
from backend.app.services.events.constants import (
    ActorType,
    EventVisibility,
    SystemEventType,
)
from backend.app.services.events.errors import (
    EventAuthorizationError,
    EventValidationError,
)


class EventPolicyEngine:
    """
    Enforces authorization, valid actor constraints, visibility boundaries,
    and retention policies.
    """

    ALLOWED_ACTORS = {a.value for a in ActorType}

    SYSTEM_INTERNAL_EVENTS = {
        SystemEventType.JOB_QUEUED.value,
        SystemEventType.JOB_CANCEL_REQUESTED.value,
        SystemEventType.JOB_RECOVERED.value,
        SystemEventType.NOTIFICATION_DELIVERY_STARTED.value,
    }

    @classmethod
    def validate_actor_type(cls, actor_type: str) -> str:
        if not actor_type or actor_type.lower() not in cls.ALLOWED_ACTORS:
            raise EventValidationError(
                f"Actor type '{actor_type}' is not recognized. Must be one of: {', '.join(sorted(cls.ALLOWED_ACTORS))}."
            )
        return actor_type.lower()

    @classmethod
    def determine_visibility(cls, event_type: str) -> EventVisibility:
        if event_type in cls.SYSTEM_INTERNAL_EVENTS:
            return EventVisibility.SYSTEM
        return EventVisibility.WORKSPACE

    @classmethod
    def authorize_read(
        cls,
        event_workspace_id: UUID,
        user_workspace_ids: List[UUID],
        event_project_id: Optional[UUID] = None,
        user_project_ids: Optional[List[UUID]] = None,
        is_admin: bool = False,
    ) -> None:
        """
        Validates that the authenticated user possesses authorization to inspect the event.
        """
        if is_admin:
            return

        if event_workspace_id not in user_workspace_ids:
            raise EventAuthorizationError("Access denied: Event belongs to another workspace.")

        if event_project_id and user_project_ids is not None:
            if event_project_id not in user_project_ids:
                raise EventAuthorizationError("Access denied: Event belongs to an unauthorized project.")

    @classmethod
    def is_visible_to_client(cls, event_type: str, is_admin: bool = False) -> bool:
        """
        Filters out sensitive internal system events for standard client subscriptions.
        """
        if is_admin:
            return True
        return event_type not in cls.SYSTEM_INTERNAL_EVENTS
