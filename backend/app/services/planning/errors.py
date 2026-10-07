"""
Error classes for Step 44: AI Work Planning, Capacity & Resource Optimization Layer.
"""
from typing import Any, Optional
from starlette import status
from backend.app.core.errors import AppError


class PlanningError(AppError):
    """Base error for all planning operations."""
    code: str = "PLANNING_ERROR"
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(
        self,
        message: str,
        code: str = "PLANNING_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, details=details, status_code=status_code)
        self.code = code


class PlanNotFoundError(PlanningError):
    def __init__(self, plan_id: str):
        super().__init__(
            message=f"Work plan '{plan_id}' not found.",
            code="PLAN_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class PlanVersionNotFoundError(PlanningError):
    def __init__(self, version_id: str):
        super().__init__(
            message=f"Work plan version '{version_id}' not found.",
            code="PLAN_VERSION_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ResourceNotFoundError(PlanningError):
    def __init__(self, resource_id: str):
        super().__init__(
            message=f"Work resource '{resource_id}' not found.",
            code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class PlanStaleError(PlanningError):
    def __init__(self, reason: str):
        super().__init__(
            message=f"Cannot activate plan because it is stale: {reason}",
            code="PLAN_STALE",
            status_code=status.HTTP_409_CONFLICT,
            details={"reason": reason},
        )


class DependencyCycleError(PlanningError):
    def __init__(self, cycle_path: list):
        super().__init__(
            message=f"Dependency cycle detected in plan: {' -> '.join(str(x) for x in cycle_path)}. Cycles are forbidden.",
            code="DEPENDENCY_CYCLE_DETECTED",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"cycle": cycle_path},
        )


class HardConstraintViolationError(PlanningError):
    def __init__(self, constraint_type: str, reason: str):
        super().__init__(
            message=f"Hard constraint '{constraint_type}' violated: {reason}. Optimization cannot override hard constraints.",
            code="HARD_CONSTRAINT_VIOLATION",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"constraint_type": constraint_type, "reason": reason},
        )


class CapacityExceededError(PlanningError):
    def __init__(self, resource_id: str, requested: float, available: float):
        super().__init__(
            message=f"Resource '{resource_id}' capacity exceeded. Requested {requested}, available {available}.",
            code="CAPACITY_EXCEEDED",
            status_code=status.HTTP_409_CONFLICT,
            details={"resource_id": resource_id, "requested": requested, "available": available},
        )


class UnauthorizedCapacityReservationError(PlanningError):
    def __init__(self, message: str = "Capacity reservation requires explicit authorization."):
        super().__init__(
            message=message,
            code="UNAUTHORIZED_RESERVATION",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class PrivacyViolationError(PlanningError):
    def __init__(self, message: str = "Attempted access to private human availability data."):
        super().__init__(
            message=message,
            code="PRIVACY_VIOLATION",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class FabricatedCapacityError(PlanningError):
    def __init__(self, message: str = "Capacity or availability cannot be fabricated without verifiable data."):
        super().__init__(
            message=message,
            code="FABRICATED_CAPACITY_FORBIDDEN",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class SubjectiveRankingForbiddenError(PlanningError):
    def __init__(self, message: str = "Subjective productivity rankings of employees or resources are strictly forbidden."):
        super().__init__(
            message=message,
            code="SUBJECTIVE_RANKING_FORBIDDEN",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class HiddenAggregateScoreForbiddenError(PlanningError):
    def __init__(self, message: str = "Hidden aggregate optimization scores are forbidden. Comparison must be multi-dimensional and factual."):
        super().__init__(
            message=message,
            code="HIDDEN_AGGREGATE_SCORE_FORBIDDEN",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class PlanningTenantViolationError(PlanningError):
    def __init__(self, message: str = "Cross-tenant access in planning is strictly forbidden."):
        super().__init__(
            message=message,
            code="PLANNING_TENANT_VIOLATION",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ImmutableVersionError(PlanningError):
    def __init__(self, version: int):
        super().__init__(
            message=f"Published plan version {version} is immutable and cannot be modified. Create a new version.",
            code="VERSION_IMMUTABLE",
            status_code=status.HTTP_409_CONFLICT,
        )


class DirectExecutionForbiddenError(PlanningError):
    def __init__(self, message: str = "Planning layer cannot execute work directly; execution must be delegated to existing TaskExecution, WorkflowExecutor, or AgentRuntime."):
        super().__init__(
            message=message,
            code="DIRECT_EXECUTION_FORBIDDEN",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class PermissionGrantForbiddenError(PlanningError):
    def __init__(self, message: str = "Capability declarations describe suitability only and cannot grant authorization or permissions."):
        super().__init__(
            message=message,
            code="PERMISSION_GRANT_FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class GovernanceBypassForbiddenError(PlanningError):
    def __init__(self, message: str = "Planning cannot override or bypass Governance policies or disablement."):
        super().__init__(
            message=message,
            code="GOVERNANCE_BYPASS_FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class HITLBypassForbiddenError(PlanningError):
    def __init__(self, message: str = "External actions and sensitive operations require Human-in-the-Loop review and cannot be auto-executed."):
        super().__init__(
            message=message,
            code="HITL_BYPASS_FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class AutoApprovalForbiddenError(PlanningError):
    def __init__(self, message: str = "AI-generated planning suggestions cannot become approved plans automatically without human authorization."):
        super().__init__(
            message=message,
            code="AUTO_APPROVAL_FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class CrossProjectPolicyViolationError(PlanningError):
    def __init__(self, message: str = "Cross-project planning is blocked when project policy denies cross-project access."):
        super().__init__(
            message=message,
            code="CROSS_PROJECT_POLICY_VIOLATION",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class CompletionFalsificationForbiddenError(PlanningError):
    def __init__(self, message: str = "Planned completion dates cannot be represented as actual completion dates."):
        super().__init__(
            message=message,
            code="COMPLETION_FALSIFICATION_FORBIDDEN",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
