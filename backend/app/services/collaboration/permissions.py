"""
Collaboration Permissions and RBAC Integration for Step 39.
Maps collaboration actions to Step 27 authorization while enforcing tenant/workspace boundaries.
"""
from typing import Optional
from backend.app.services.access_control.permissions import (
    ALL_PERMISSIONS,
)
from backend.app.services.collaboration.exceptions import UnauthorizedSessionAccessError
from backend.app.services.collaboration.models import CollaborationParticipant, CollaborationSession

# Standard Collaboration Permission Identifiers mapped to Step 27
COLLABORATION_PERMISSIONS = {
    "session.read": "collaboration.session_read",
    "session.join": "collaboration.session_join",
    "session.comment": "collaboration.comment",
    "session.annotate": "collaboration.annotate",
    "session.assign": "collaboration.assign",
    "session.edit": "collaboration.edit",
    "session.approve": "collaboration.approve",
    "session.execute": "collaboration.execute",
}

# Role permissions matrix within a session
ROLE_PERMISSIONS = {
    "owner": {
        "session.read", "session.join", "session.comment", "session.annotate",
        "session.assign", "session.edit", "session.approve", "session.execute"
    },
    "editor": {
        "session.read", "session.join", "session.comment", "session.annotate",
        "session.assign", "session.edit", "session.execute"
    },
    "reviewer": {
        "session.read", "session.join", "session.comment", "session.annotate",
        "session.approve"
    },
    "viewer": {
        "session.read", "session.join"
    },
}


class CollaborationPermissionEvaluator:
    """Evaluates session access and actions against participant role and organization boundaries."""

    @classmethod
    def verify_tenant_boundary(
        cls,
        session: CollaborationSession,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
    ) -> None:
        """Enforces that the user belongs to the same organization and workspace as the session."""
        if session.organization_id != user_organization_id:
            raise UnauthorizedSessionAccessError("Cross-organization collaboration session access is strictly prohibited.")

        if user_workspace_id and session.workspace_id != user_workspace_id:
            raise UnauthorizedSessionAccessError("Cross-workspace collaboration session access is strictly prohibited.")

    @classmethod
    def check_action_allowed(
        cls,
        participant: Optional[CollaborationParticipant],
        action: str,
        is_org_admin: bool = False,
    ) -> None:
        """
        Verifies that participant's collaboration role permits the action.
        Organization administrators have implicit authorization for session management.
        """
        if is_org_admin:
            return

        if not participant or participant.status != "active":
            raise UnauthorizedSessionAccessError(f"User is not an active participant in this session to perform '{action}'.")

        allowed_actions = ROLE_PERMISSIONS.get(participant.role, set())
        if action not in allowed_actions:
            raise UnauthorizedSessionAccessError(
                f"Participant role '{participant.role}' does not permit action '{action}'."
            )
