"""
Structured Python SDK Exceptions.
Preserves request_id, error code, and HTTP status.
"""
from typing import Any, Dict, Optional


class APIError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        code: str = "api_error",
        request_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.request_id = request_id
        self.details = details or {}


class AuthenticationError(APIError):
    def __init__(self, message: str = "Authentication failed", request_id: Optional[str] = None):
        super().__init__(message, status_code=401, code="authentication_failed", request_id=request_id)


class AuthorizationError(APIError):
    def __init__(self, message: str = "Permission denied", request_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, code="permission_denied", request_id=request_id, details=details)


class ValidationError(APIError):
    def __init__(self, message: str = "Invalid request payload", request_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, code="validation_error", request_id=request_id, details=details)


class NotFoundError(APIError):
    def __init__(self, message: str = "Resource not found", request_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, code="not_found", request_id=request_id, details=details)


class ConflictError(APIError):
    def __init__(self, message: str = "Conflict", request_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=409, code="conflict", request_id=request_id, details=details)


class RateLimitError(APIError):
    def __init__(self, message: str = "Rate limit exceeded", request_id: Optional[str] = None, retry_after: int = 60):
        super().__init__(message, status_code=429, code="rate_limit_exceeded", request_id=request_id)
        self.retry_after = retry_after


class PolicyError(APIError):
    def __init__(self, message: str = "Policy denied", request_id: Optional[str] = None):
        super().__init__(message, status_code=403, code="policy_error", request_id=request_id)


class GovernanceError(APIError):
    def __init__(self, message: str = "Governance denied", request_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, code="governance_denied", request_id=request_id, details=details)


class ExecutionError(APIError):
    def __init__(self, message: str = "Execution error", request_id: Optional[str] = None):
        super().__init__(message, status_code=500, code="execution_error", request_id=request_id)


class DependencyError(APIError):
    def __init__(self, message: str = "Dependency unavailable", request_id: Optional[str] = None):
        super().__init__(message, status_code=502, code="dependency_error", request_id=request_id)
