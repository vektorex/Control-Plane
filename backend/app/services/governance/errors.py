"""
Custom exception hierarchy for Step 32: AI Governance, Policy Control Plane, and Safety Guardrails.
"""
from fastapi import status


class GovernanceError(Exception):
    """Base class for all governance errors."""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "Governance error"

    def __init__(self, message: str = ""):
        self.detail = message or self.__class__.detail
        super().__init__(self.detail)


class GovernanceDeniedError(GovernanceError):
    """Raised when a governance decision is DENY."""
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Operation denied by governance policy"


class GovernancePolicyNotFoundError(GovernanceError):
    """Raised when a referenced policy does not exist."""
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Governance policy not found"


class GovernancePolicyVersionError(GovernanceError):
    """Raised when a policy version operation fails."""
    status_code = status.HTTP_409_CONFLICT
    detail = "Policy version conflict"


class GovernancePolicyMalformedError(GovernanceError):
    """Raised when a policy rule set is invalid or cannot be activated."""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "Governance policy is malformed and cannot be activated"


class GovernanceBudgetExceededError(GovernanceError):
    """Raised when a hard budget limit is exceeded."""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    detail = "Budget limit exceeded"


class GovernanceRateLimitError(GovernanceError):
    """Raised when a rate limit is exceeded."""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    detail = "Rate limit exceeded by governance policy"


class GovernanceSecurityViolationError(GovernanceError):
    """Raised when an operation attempts to violate a system-level security constraint."""
    status_code = status.HTTP_403_FORBIDDEN
    detail = "System security constraint violation"


class GovernanceStateUnknownError(GovernanceError):
    """Raised when governance state cannot be determined for a privileged operation."""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    detail = "Governance state is unknown; privileged operation blocked"


class GovernanceConflictError(GovernanceError):
    """Raised on concurrent policy activation race conditions."""
    status_code = status.HTTP_409_CONFLICT
    detail = "Policy activation conflict detected"


class GovernanceReservationError(GovernanceError):
    """Raised when budget reservation cannot be created."""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "Budget reservation failed"
