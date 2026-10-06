"""
Lifecycle Management, State Machine Transitions, and Staleness Detection for Step 44.
"""
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from backend.app.services.planning.errors import (
    ImmutableVersionError,
    PlanStaleError,
    PlanningError,
)
from backend.app.services.planning.models import PlanStalenessRecord, WorkPlan, WorkPlanVersion

VALID_PLAN_TRANSITIONS = {
    "draft": {"proposed", "cancelled", "archived"},
    "proposed": {"approved", "draft", "cancelled"},
    "approved": {"active", "paused", "cancelled"},
    "active": {"paused", "completed", "cancelled"},
    "paused": {"active", "cancelled"},
    "completed": {"archived"},
    "cancelled": {"archived"},
    "archived": set(),
}


class PlanLifecycleManager:
    """
    Controls valid state transitions and enforces staleness guardrails.
    """

    @classmethod
    def validate_transition(cls, current_status: str, target_status: str) -> None:
        curr = (current_status or "draft").lower()
        target = target_status.lower()

        allowed = VALID_PLAN_TRANSITIONS.get(curr, set())
        if target not in allowed:
            raise PlanningError(
                f"Invalid work plan status transition from '{curr}' to '{target}'. Allowed: {sorted(list(allowed))}",
                code="INVALID_PLAN_TRANSITION",
            )

    @classmethod
    def check_staleness(
        cls,
        plan: WorkPlan,
        latest_version: Optional[WorkPlanVersion] = None,
        staleness_records: Optional[List[PlanStalenessRecord]] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Determines whether a plan is stale.
        Returns (is_stale, list_of_reasons).
        """
        reasons: List[str] = []

        if staleness_records:
            active_stale = [r for r in staleness_records if r.is_stale]
            for r in active_stale:
                reasons.append(r.reason)

        is_stale = len(reasons) > 0
        return is_stale, reasons

    @classmethod
    def enforce_version_immutability(cls, version: WorkPlanVersion) -> None:
        """
        Raises ImmutableVersionError if version is published.
        """
        if version.published_at is not None:
            raise ImmutableVersionError(version.version)
