"""
Error definitions for the Human-in-the-Loop (HITL) system.
"""
from backend.app.core.errors import AppError


class HITLError(AppError):
    """Base error for all HITL operations."""
    status_code = 400
    error_code = "hitl_error"


class HITLNotFoundError(HITLError):
    """Raised when an intervention request or decision cannot be found."""
    status_code = 404
    error_code = "intervention_not_found"

    def __init__(self, request_id: str):
        super().__init__(
            message=f"Human intervention request '{request_id}' not found.",
            details={"request_id": request_id},
        )


class HITLPermissionError(HITLError):
    """Raised when a user is not authorized to review, approve, or resolve an intervention."""
    status_code = 403
    error_code = "hitl_permission_denied"


class HITLStatusError(HITLError):
    """Raised when an operation cannot be performed due to the intervention's current state."""
    status_code = 409
    error_code = "hitl_invalid_state"


class HITLExpiredError(HITLError):
    """Raised when attempting to approve or resolve an expired intervention request."""
    status_code = 410
    error_code = "hitl_request_expired"


class HITLValidationError(HITLError):
    """Raised when intervention payloads or edited inputs fail validation."""
    status_code = 422
    error_code = "hitl_validation_failed"
