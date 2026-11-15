"""
Exceptions and domain error definitions for Step 43:
AI Outcome Intelligence & Work Impact Layer.
"""
from typing import Optional, Dict, Any
from starlette import status
from backend.app.core.errors import AppError


class OutcomeError(AppError):
    """Base exception for all outcome domain errors."""
    code: str = "OUTCOME_ERROR"
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str, code: str = "OUTCOME_ERROR", status_code: int = status.HTTP_400_BAD_REQUEST, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details or {}, status_code=status_code)
        self.code = code


class ObjectiveNotFoundError(OutcomeError):
    def __init__(self, objective_id: str):
        super().__init__(
            message=f"Objective '{objective_id}' not found.",
            code="OBJECTIVE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"objective_id": objective_id},
        )


class OutcomeNotFoundError(OutcomeError):
    def __init__(self, outcome_id: str):
        super().__init__(
            message=f"Outcome '{outcome_id}' not found.",
            code="OUTCOME_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"outcome_id": outcome_id},
        )


class OutcomeTargetNotFoundError(OutcomeError):
    def __init__(self, target_id: str):
        super().__init__(
            message=f"Outcome target '{target_id}' not found.",
            code="TARGET_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"target_id": target_id},
        )


class MilestoneNotFoundError(OutcomeError):
    def __init__(self, milestone_id: str):
        super().__init__(
            message=f"Milestone '{milestone_id}' not found.",
            code="MILESTONE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"milestone_id": milestone_id},
        )


class WorkDecisionNotFoundError(OutcomeError):
    def __init__(self, decision_id: str):
        super().__init__(
            message=f"Work decision '{decision_id}' not found.",
            code="DECISION_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"decision_id": decision_id},
        )

DecisionNotFoundError = WorkDecisionNotFoundError


class HumanImpersonationError(OutcomeError):
    def __init__(self, message: str = "AI-assisted or agent decisions cannot be disguised or represented as human decisions."):
        super().__init__(
            message=message,
            code="HUMAN_IMPERSONATION_FORBIDDEN",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )


class FabricatedMetricError(OutcomeError):
    def __init__(self, message: str = "Metrics cannot be fabricated or synthesized without empirical measurement."):
        super().__init__(
            message=message,
            code="FABRICATED_METRIC_FORBIDDEN",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )


class EvidenceNotFoundError(OutcomeError):
    def __init__(self, evidence_id: str):
        super().__init__(
            message=f"Outcome evidence '{evidence_id}' not found.",
            code="EVIDENCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"evidence_id": evidence_id},
        )


class MeasurementNotFoundError(OutcomeError):
    def __init__(self, measurement_id: str):
        super().__init__(
            message=f"Outcome measurement '{measurement_id}' not found.",
            code="MEASUREMENT_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"measurement_id": measurement_id},
        )


class RequirementNotMetError(OutcomeError):
    def __init__(self, message: str, missing_requirements: Optional[list] = None):
        super().__init__(
            message=message,
            code="REQUIREMENT_NOT_MET",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            details={"missing_requirements": missing_requirements or []},
        )


class UnauthorizedVerificationError(OutcomeError):
    def __init__(self, message: str = "Unauthorized to verify outcome."):
        super().__init__(
            message=message,
            code="UNAUTHORIZED_VERIFICATION",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class InvalidOutcomeStateTransitionError(OutcomeError):
    def __init__(self, from_state: str, to_state: str, reason: str):
        super().__init__(
            message=f"Invalid transition from '{from_state}' to '{to_state}': {reason}",
            code="INVALID_STATE_TRANSITION",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"from_state": from_state, "to_state": to_state, "reason": reason},
        )


class CausalityClaimForbiddenError(OutcomeError):
    def __init__(self, message: str = "Direct causality claim requires explicit causal evidence. Use 'contributed_to' instead."):
        super().__init__(
            message=message,
            code="CAUSALITY_CLAIM_FORBIDDEN",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )


class SubjectiveScoreForbiddenError(OutcomeError):
    def __init__(self, message: str = "Subjective AI quality or intelligence scores without evidence-backed evaluations are forbidden."):
        super().__init__(
            message=message,
            code="SUBJECTIVE_SCORE_FORBIDDEN",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )


class EvidenceTamperingDetectedError(OutcomeError):
    def __init__(self, message: str = "Evidence integrity verification failed or tampering detected."):
        super().__init__(
            message=message,
            code="EVIDENCE_TAMPERING_DETECTED",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class OutcomeTenantViolationError(OutcomeError):
    def __init__(self, message: str = "Cross-tenant access to outcome, objective, evidence or decision is denied."):
        super().__init__(
            message=message,
            code="TENANT_VIOLATION",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class MissingBaselineError(OutcomeError):
    def __init__(self, metric_name: str):
        super().__init__(
            message=f"Baseline measurement for '{metric_name}' is not established. Cannot fabricate savings or impact without baseline.",
            code="MISSING_BASELINE",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            details={"metric_name": metric_name},
        )
