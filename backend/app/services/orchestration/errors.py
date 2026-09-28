from typing import Any, Optional
from backend.app.core.errors import AppError


class OrchestrationError(AppError):
    """Base exception for all orchestration engine errors."""
    code: str = "ORCHESTRATION_ERROR"
    status_code: int = 500

    def __init__(
        self,
        message: str,
        details: Optional[Any] = None,
        status_code: Optional[int] = None,
        code: Optional[str] = None,
    ):
        super().__init__(message=message, details=details, status_code=status_code)
        if code is not None:
            self.code = code


class PlanValidationError(OrchestrationError):
    """Raised when an ExecutionPlan fails schema, limit, or permission validation."""
    code: str = "PLAN_VALIDATION_ERROR"
    status_code: int = 422

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            details=details,
            status_code=422,
            code="PLAN_VALIDATION_ERROR",
        )


class ExecutionLimitExceededError(PlanValidationError):
    """Raised when an ExecutionPlan exceeds configured server-side limits."""
    code: str = "EXECUTION_LIMIT_EXCEEDED"
    status_code: int = 400

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            details=details,
        )
        self.code = "EXECUTION_LIMIT_EXCEEDED"
        self.status_code = 400


class StepExecutionError(OrchestrationError):
    """Raised when an individual plan step fails under a strict failure policy."""
    code: str = "STEP_EXECUTION_ERROR"
    status_code: int = 500

    def __init__(self, message: str, step_id: Optional[str] = None, details: Optional[Any] = None):
        error_details = {"step_id": step_id}
        if details:
            if isinstance(details, dict):
                error_details.update(details)
            else:
                error_details["details"] = details
        super().__init__(
            message=message,
            details=error_details,
            status_code=500,
            code="STEP_EXECUTION_ERROR",
        )


class OrchestrationTimeoutError(OrchestrationError):
    """Raised when total orchestration execution duration exceeds configured limits."""
    code: str = "ORCHESTRATION_TIMEOUT"
    status_code: int = 504

    def __init__(self, message: str = "Orchestration execution timed out."):
        super().__init__(
            message=message,
            status_code=504,
            code="ORCHESTRATION_TIMEOUT",
        )


class PlanExecutionAbortedError(OrchestrationError):
    """Raised when orchestration execution is aborted due to required step failure."""
    code: str = "PLAN_EXECUTION_ABORTED"
    status_code: int = 400

    def __init__(self, message: str, failed_step_id: Optional[str] = None):
        super().__init__(
            message=message,
            details={"failed_step_id": failed_step_id} if failed_step_id else None,
            status_code=400,
            code="PLAN_EXECUTION_ABORTED",
        )
