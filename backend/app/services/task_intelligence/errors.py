from typing import Any, Optional
from fastapi import status
from backend.app.core.errors import AppError


class TaskIntelligenceError(AppError):
    """Base exception for all Task Intelligence errors."""
    code: str = "TASK_INTELLIGENCE_ERROR"
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR


class AnalyzerError(TaskIntelligenceError):
    """Raised when an analyzer fails to parse or analyze a task."""
    code: str = "ANALYZER_ERROR"
    status_code: int = status.HTTP_502_BAD_GATEWAY


class AnalyzerTimeoutError(AnalyzerError):
    """Raised when analyzer model execution times out."""
    code: str = "ANALYZER_TIMEOUT"
    status_code: int = status.HTTP_504_GATEWAY_TIMEOUT


class RequirementValidationError(TaskIntelligenceError):
    """Raised when execution requirements violate policy, limits, or invariants."""
    code: str = "REQUIREMENT_VALIDATION_ERROR"
    status_code: int = status.HTTP_422_UNPROCESSABLE_CONTENT


class PolicyViolationError(TaskIntelligenceError):
    """Raised when a task request attempts to violate workspace or server policy."""
    code: str = "POLICY_VIOLATION"
    status_code: int = status.HTTP_403_FORBIDDEN
