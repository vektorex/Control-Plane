"""
Agent Execution State Machine for Step 40.
Governs state transitions during agent and multi-agent runs,
validates allowable transitions, and prevents corrupt lifecycle mutations.
"""
from typing import Dict, Set
from backend.app.services.agents.errors import AgentError
from backend.app.services.agents.schemas import AgentExecutionState


# Valid state transitions dictionary
VALID_TRANSITIONS: Dict[AgentExecutionState, Set[AgentExecutionState]] = {
    AgentExecutionState.CREATED: {
        AgentExecutionState.PLANNING,
        AgentExecutionState.EXECUTING,
        AgentExecutionState.CANCELLED,
        AgentExecutionState.FAILED,
    },
    AgentExecutionState.PLANNING: {
        AgentExecutionState.EXECUTING,
        AgentExecutionState.WAITING_FOR_APPROVAL,
        AgentExecutionState.DELEGATING,
        AgentExecutionState.FAILED,
        AgentExecutionState.CANCELLED,
    },
    AgentExecutionState.EXECUTING: {
        AgentExecutionState.WAITING_FOR_APPROVAL,
        AgentExecutionState.DELEGATING,
        AgentExecutionState.EVALUATING,
        AgentExecutionState.PAUSED,
        AgentExecutionState.COMPLETED,
        AgentExecutionState.FAILED,
        AgentExecutionState.CANCELLED,
    },
    AgentExecutionState.WAITING_FOR_APPROVAL: {
        AgentExecutionState.EXECUTING,
        AgentExecutionState.DELEGATING,
        AgentExecutionState.EVALUATING,
        AgentExecutionState.FAILED,
        AgentExecutionState.CANCELLED,
    },
    AgentExecutionState.DELEGATING: {
        AgentExecutionState.EXECUTING,
        AgentExecutionState.WAITING_FOR_APPROVAL,
        AgentExecutionState.EVALUATING,
        AgentExecutionState.FAILED,
        AgentExecutionState.CANCELLED,
    },
    AgentExecutionState.EVALUATING: {
        AgentExecutionState.COMPLETED,
        AgentExecutionState.WAITING_FOR_APPROVAL,  # If evaluation requires review
        AgentExecutionState.FAILED,
        AgentExecutionState.CANCELLED,
    },
    AgentExecutionState.PAUSED: {
        AgentExecutionState.EXECUTING,
        AgentExecutionState.CANCELLED,
        AgentExecutionState.FAILED,
    },
    AgentExecutionState.COMPLETED: set(),  # Terminal
    AgentExecutionState.FAILED: set(),     # Terminal
    AgentExecutionState.CANCELLED: set(),  # Terminal
}


class InvalidStateTransitionError(AgentError):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, from_state: str, to_state: str):
        super().__init__(
            f"Invalid agent execution state transition from '{from_state}' to '{to_state}'.",
            code="INVALID_STATE_TRANSITION",
            details={"from_state": from_state, "to_state": to_state},
        )


def validate_transition(from_state: str, to_state: str) -> bool:
    """
    Validates whether transition from `from_state` to `to_state` is legal.
    Raises InvalidStateTransitionError if illegal.
    """
    try:
        from_enum = AgentExecutionState(from_state)
        to_enum = AgentExecutionState(to_state)
    except ValueError as e:
        raise InvalidStateTransitionError(from_state, to_state) from e

    allowed = VALID_TRANSITIONS.get(from_enum, set())
    if to_enum not in allowed:
        raise InvalidStateTransitionError(from_state, to_state)

    return True


def is_terminal_state(state: str) -> bool:
    """Returns True if the execution state is final."""
    return state in {
        AgentExecutionState.COMPLETED.value,
        AgentExecutionState.FAILED.value,
        AgentExecutionState.CANCELLED.value,
    }
