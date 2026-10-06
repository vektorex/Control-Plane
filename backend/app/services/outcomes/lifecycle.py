"""
Lifecycle state transitions for Step 43:
AI Outcome Intelligence & Work Impact Layer.
"""
from typing import Any, Dict, Set
from backend.app.services.outcomes.errors import InvalidOutcomeStateTransitionError
from backend.app.services.outcomes.registry import (
    ObjectiveStatus,
    OutcomeStatus,
    MilestoneStatus,
    WorkDecisionStatus,
)


class OutcomeLifecycle:
    """Validates finite state transitions for outcome entities."""

    OBJECTIVE_TRANSITIONS: Dict[str, Set[str]] = {
        ObjectiveStatus.DRAFT.value: {
            ObjectiveStatus.ACTIVE.value,
            ObjectiveStatus.CANCELLED.value,
            ObjectiveStatus.ARCHIVED.value,
        },
        ObjectiveStatus.ACTIVE.value: {
            ObjectiveStatus.AT_RISK.value,
            ObjectiveStatus.COMPLETED.value,
            ObjectiveStatus.CANCELLED.value,
            ObjectiveStatus.ARCHIVED.value,
        },
        ObjectiveStatus.AT_RISK.value: {
            ObjectiveStatus.ACTIVE.value,
            ObjectiveStatus.COMPLETED.value,
            ObjectiveStatus.CANCELLED.value,
            ObjectiveStatus.ARCHIVED.value,
        },
        ObjectiveStatus.COMPLETED.value: {
            ObjectiveStatus.ARCHIVED.value,
            ObjectiveStatus.ACTIVE.value,  # reopen
        },
        ObjectiveStatus.CANCELLED.value: {
            ObjectiveStatus.ARCHIVED.value,
            ObjectiveStatus.ACTIVE.value,  # reopen
        },
        ObjectiveStatus.ARCHIVED.value: {
            ObjectiveStatus.DRAFT.value,
            ObjectiveStatus.ACTIVE.value,
        },
    }

    OUTCOME_TRANSITIONS: Dict[str, Set[str]] = {
        OutcomeStatus.PLANNED.value: {
            OutcomeStatus.IN_PROGRESS.value,
            OutcomeStatus.OBSERVED.value,
            OutcomeStatus.FAILED.value,
            OutcomeStatus.CANCELLED.value,
        },
        OutcomeStatus.IN_PROGRESS.value: {
            OutcomeStatus.OBSERVED.value,
            OutcomeStatus.FAILED.value,
            OutcomeStatus.CANCELLED.value,
        },
        OutcomeStatus.OBSERVED.value: {
            OutcomeStatus.VERIFIED.value,
            OutcomeStatus.DISPUTED.value,
            OutcomeStatus.FAILED.value,
            OutcomeStatus.IN_PROGRESS.value,
        },
        OutcomeStatus.VERIFIED.value: {
            OutcomeStatus.DISPUTED.value,  # dispute can overturn verified
        },
        OutcomeStatus.DISPUTED.value: {
            OutcomeStatus.OBSERVED.value,
            OutcomeStatus.VERIFIED.value,
            OutcomeStatus.FAILED.value,
            OutcomeStatus.IN_PROGRESS.value,
        },
        OutcomeStatus.FAILED.value: {
            OutcomeStatus.IN_PROGRESS.value,  # retry
            OutcomeStatus.CANCELLED.value,
        },
        OutcomeStatus.CANCELLED.value: {
            OutcomeStatus.PLANNED.value,
        },
    }

    MILESTONE_TRANSITIONS: Dict[str, Set[str]] = {
        MilestoneStatus.PLANNED.value: {
            MilestoneStatus.IN_PROGRESS.value,
            MilestoneStatus.BLOCKED.value,
            MilestoneStatus.COMPLETED.value,
            MilestoneStatus.CANCELLED.value,
        },
        MilestoneStatus.IN_PROGRESS.value: {
            MilestoneStatus.BLOCKED.value,
            MilestoneStatus.COMPLETED.value,
            MilestoneStatus.MISSED.value,
            MilestoneStatus.CANCELLED.value,
        },
        MilestoneStatus.BLOCKED.value: {
            MilestoneStatus.IN_PROGRESS.value,
            MilestoneStatus.MISSED.value,
            MilestoneStatus.CANCELLED.value,
        },
        MilestoneStatus.MISSED.value: {
            MilestoneStatus.IN_PROGRESS.value,
            MilestoneStatus.COMPLETED.value,
            MilestoneStatus.CANCELLED.value,
        },
        MilestoneStatus.COMPLETED.value: set(),
        MilestoneStatus.CANCELLED.value: {MilestoneStatus.PLANNED.value},
    }

    DECISION_TRANSITIONS: Dict[str, Set[str]] = {
        WorkDecisionStatus.PROPOSED.value: {
            WorkDecisionStatus.UNDER_REVIEW.value,
            WorkDecisionStatus.APPROVED.value,
            WorkDecisionStatus.REJECTED.value,
        },
        WorkDecisionStatus.UNDER_REVIEW.value: {
            WorkDecisionStatus.APPROVED.value,
            WorkDecisionStatus.REJECTED.value,
            WorkDecisionStatus.SUPERSEDED.value,
        },
        WorkDecisionStatus.APPROVED.value: {
            WorkDecisionStatus.SUPERSEDED.value,
        },
        WorkDecisionStatus.REJECTED.value: {
            WorkDecisionStatus.PROPOSED.value,  # reconsider
            WorkDecisionStatus.SUPERSEDED.value,
        },
        WorkDecisionStatus.SUPERSEDED.value: set(),
    }

    @classmethod
    def validate_objective_transition(cls, current: str, target: str) -> None:
        if current == target:
            return
        allowed = cls.OBJECTIVE_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidOutcomeStateTransitionError(current, target, f"Allowed targets: {sorted(allowed)}")

    @classmethod
    def validate_outcome_transition(cls, current: str, target: str) -> None:
        if current == target:
            return
        allowed = cls.OUTCOME_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidOutcomeStateTransitionError(current, target, f"Allowed targets: {sorted(allowed)}")

    @classmethod
    def validate_milestone_transition(cls, current: str, target: str) -> None:
        if current == target:
            return
        allowed = cls.MILESTONE_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidOutcomeStateTransitionError(current, target, f"Allowed targets: {sorted(allowed)}")

    @classmethod
    def validate_decision_transition(cls, current: str, target: str) -> None:
        if current == target:
            return
        allowed = cls.DECISION_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidOutcomeStateTransitionError(current, target, f"Allowed targets: {sorted(allowed)}")


class OutcomeStateMachine:
    """State machine controller for Outcome deliverables."""

    @classmethod
    def transition_on_agent_complete(cls, outcome: Any) -> OutcomeStatus:
        """Agent completion transitions outcome to OBSERVED, never directly to VERIFIED."""
        return OutcomeStatus.OBSERVED


class ObjectiveStateMachine:
    """State machine controller for Objectives."""
    pass


class DecisionStateMachine:
    """State machine controller for Work Decisions."""
    pass
