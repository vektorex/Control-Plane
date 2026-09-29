"""
Workflow domain exceptions and error definitions.
"""
from typing import Any, Dict, Optional
from backend.app.core.errors import AppError


class WorkflowError(AppError):
    """Base exception for workflow domain errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, status_code: int = 400):
        super().__init__(message=message, status_code=status_code)
        self.details = details or {}


class WorkflowNotFoundError(WorkflowError):
    """Raised when a workflow or workflow run is not found."""
    def __init__(self, message: str = "Workflow not found.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details, status_code=404)


class WorkflowValidationError(WorkflowError):
    """Raised when a workflow definition fails structural or semantic validation."""
    def __init__(self, message: str = "Workflow validation failed.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details, status_code=422)


class WorkflowInputValidationError(WorkflowError):
    """Raised when runtime inputs do not conform to workflow input_schema."""
    def __init__(self, message: str = "Workflow input validation failed.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details, status_code=422)


class WorkflowExecutionError(WorkflowError):
    """Raised when workflow execution encounters a non-recoverable error."""
    def __init__(self, message: str = "Workflow execution failed.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details, status_code=500)


class WorkflowStepExecutionError(WorkflowError):
    """Raised when a specific step execution fails."""
    def __init__(self, step_id: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=f"Step '{step_id}' execution failed: {message}", details=details, status_code=500)
        self.step_id = step_id


class WorkflowVersionError(WorkflowError):
    """Raised when attempting to modify an immutable published workflow version."""
    def __init__(self, message: str = "Published workflow versions are immutable.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details, status_code=409)
