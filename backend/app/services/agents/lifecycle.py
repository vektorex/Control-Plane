"""
Agent and Agent Team Lifecycle Management for Step 40.
Governs agent operational lifecycle states: draft, active, paused, disabled, archived.
"""
from typing import Dict, Set
from backend.app.services.agents.errors import AgentLifecycleError
from backend.app.services.agents.schemas import AgentStatus, AgentTeamStatus


# Valid status transitions for Agent and AgentTeam
VALID_LIFECYCLE_TRANSITIONS: Dict[str, Set[str]] = {
    AgentStatus.DRAFT.value: {
        AgentStatus.ACTIVE.value,
        AgentStatus.ARCHIVED.value,
    },
    AgentStatus.ACTIVE.value: {
        AgentStatus.PAUSED.value,
        AgentStatus.DISABLED.value,
        AgentStatus.ARCHIVED.value,
    },
    AgentStatus.PAUSED.value: {
        AgentStatus.ACTIVE.value,
        AgentStatus.DISABLED.value,
        AgentStatus.ARCHIVED.value,
    },
    AgentStatus.DISABLED.value: {
        AgentStatus.ACTIVE.value,
        AgentStatus.ARCHIVED.value,
    },
    AgentStatus.ARCHIVED.value: set(),  # Terminal state
}


def validate_lifecycle_transition(current_status: str, target_status: str, has_published_version: bool = True) -> None:
    """
    Validates lifecycle transition.
    Enforces that activating an agent requires at least one published version.
    """
    allowed = VALID_LIFECYCLE_TRANSITIONS.get(current_status, set())
    if target_status not in allowed:
        raise AgentLifecycleError(
            current_status=current_status,
            target_status=target_status,
            reason=f"Transition not permitted from '{current_status}' to '{target_status}'.",
        )

    if target_status == AgentStatus.ACTIVE.value and not has_published_version:
        raise AgentLifecycleError(
            current_status=current_status,
            target_status=target_status,
            reason="Cannot activate an agent or team without a published version.",
        )


def is_executable_status(status: str) -> bool:
    """Only active agents/teams can be invoked for execution."""
    return status == AgentStatus.ACTIVE.value
