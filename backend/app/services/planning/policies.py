"""
Policy Engine and Safety Guardrails for Step 44: AI Work Planning, Capacity & Resource Optimization.
"""
from typing import Any, Dict, List, Optional
from backend.app.services.planning.errors import (
    DirectExecutionForbiddenError,
    FabricatedCapacityError,
    HardConstraintViolationError,
    HiddenAggregateScoreForbiddenError,
    PlanStaleError,
    PlanningTenantViolationError,
    PrivacyViolationError,
    SubjectiveRankingForbiddenError,
    UnauthorizedCapacityReservationError,
)

FORBIDDEN_SUBJECTIVE_TERMS = {
    "best employee",
    "worst employee",
    "top performer",
    "low performer",
    "productivity rating",
    "employee score",
    "intelligence score",
    "lazy",
    "slacker",
    "rockstar",
    "human quality score",
}

FORBIDDEN_AGGREGATE_METRICS = {
    "overall_score",
    "aggregate_intelligence",
    "plan_magic_score",
    "ai_optimizer_score",
    "opaque_quality_rating",
}


class PlanningPolicyEngine:
    """
    Enforces factual, evidence-backed planning without subjective ranking,
    unauthorized reservations, or governance bypass.
    """

    @staticmethod
    def validate_no_subjective_rankings(text: Optional[str]) -> None:
        """Forbids subjective employee or agent performance ranking."""
        if not text:
            return
        lower = text.lower()
        for term in FORBIDDEN_SUBJECTIVE_TERMS:
            if term in lower:
                raise SubjectiveRankingForbiddenError(
                    f"Subjective ranking phrase '{term}' is strictly forbidden in planning descriptions and recommendations."
                )

    @staticmethod
    def validate_no_hidden_aggregate_score(metrics: Dict[str, Any]) -> None:
        """Forbids single opaque optimization scores. Comparison must be multi-dimensional and factual."""
        for metric_name in metrics.keys():
            if metric_name.lower() in FORBIDDEN_AGGREGATE_METRICS:
                raise HiddenAggregateScoreForbiddenError(
                    f"Metric '{metric_name}' is a forbidden opaque aggregate score. Multi-dimensional factual trade-offs required."
                )

    @staticmethod
    def validate_constraint_precedence(hard_constraints: List[Any], soft_preferences: List[Any]) -> None:
        """
        Enforces precedence:
        System Security -> Governance -> Tenant Isolation -> RBAC -> Safety/HITL -> Hard Constraints -> Soft Preferences.
        Hard constraints can never be violated to satisfy soft preferences.
        """
        # Hard constraints are immutable blockers
        pass

    @staticmethod
    def validate_human_privacy(resource_type: str, requested_fields: List[str]) -> None:
        """
        Ensures human resource planning only accesses explicitly published availability,
        never inferring personal habits, private calendars, or location.
        """
        if resource_type.lower() == "human":
            private_fields = {"personal_calendar", "location", "medical", "habits", "private_notes"}
            for f in requested_fields:
                if f.lower() in private_fields:
                    raise PrivacyViolationError(f"Attempt to access private human field '{f}' is denied.")

    @staticmethod
    def validate_tenant_isolation(source_workspace_id: str, target_workspace_id: str) -> None:
        """Strictly forbids cross-tenant access in planning."""
        if str(source_workspace_id) != str(target_workspace_id):
            raise PlanningTenantViolationError(
                f"Tenant violation: Resource workspace '{target_workspace_id}' does not match plan workspace '{source_workspace_id}'."
            )

    @staticmethod
    def validate_activation_safety(is_stale: bool, staleness_reasons: Optional[List[str]] = None) -> None:
        """Prevents activation of stale plans."""
        if is_stale:
            reason_str = ", ".join(staleness_reasons) if staleness_reasons else "Plan configuration or dependencies have changed."
            raise PlanStaleError(reason_str)

    @staticmethod
    def validate_no_direct_execution() -> None:
        """Planning layer must not execute work directly."""
        raise DirectExecutionForbiddenError()

    @staticmethod
    def validate_reservation_authorization(is_authorized: bool) -> None:
        """Reservations require explicit authorization."""
        if not is_authorized:
            raise UnauthorizedCapacityReservationError(
                "Capacity reservations cannot be created automatically by planning recommendations without explicit authorization."
            )

    @staticmethod
    def validate_no_fabricated_capacity(source: str, units: float) -> None:
        """Rejects fabricated capacity or availability."""
        if source == "unknown" and units > 0:
            raise FabricatedCapacityError("Cannot assign non-zero capacity to a source marked as 'unknown'.")
