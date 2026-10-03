"""
Developer Platform & Public API Domain Exceptions and Error Enums.
Step 37: Public API, Developer Platform & SDK Layer.
"""
from enum import Enum
from typing import Any, Dict, Optional


class PublicAPIErrorType(str, Enum):
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RATE_LIMIT_ERROR = "rate_limit_error"
    POLICY_ERROR = "policy_error"
    GOVERNANCE_ERROR = "governance_error"
    EXECUTION_ERROR = "execution_error"
    DEPENDENCY_ERROR = "dependency_error"
    TEMPORARILY_UNAVAILABLE = "temporarily_unavailable"
    INTERNAL_ERROR = "internal_error"


class PublicAPIException(Exception):
    """Base exception for all public API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_type: PublicAPIErrorType = PublicAPIErrorType.VALIDATION_ERROR,
        code: str = "bad_request",
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.code = code
        self.details = details or {}
        self.headers = headers or {}


class AuthenticationFailedError(PublicAPIException):
    def __init__(self, message: str = "Invalid or missing API key."):
        super().__init__(
            message=message,
            status_code=401,
            error_type=PublicAPIErrorType.AUTHENTICATION_ERROR,
            code="authentication_failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


class CredentialExpiredError(PublicAPIException):
    def __init__(self, message: str = "API credential has expired."):
        super().__init__(
            message=message,
            status_code=401,
            error_type=PublicAPIErrorType.AUTHENTICATION_ERROR,
            code="credential_expired",
        )


class CredentialRevokedError(PublicAPIException):
    def __init__(self, message: str = "API credential has been revoked."):
        super().__init__(
            message=message,
            status_code=401,
            error_type=PublicAPIErrorType.AUTHENTICATION_ERROR,
            code="credential_revoked",
        )


class ApplicationSuspendedError(PublicAPIException):
    def __init__(self, message: str = "Developer application is suspended."):
        super().__init__(
            message=message,
            status_code=403,
            error_type=PublicAPIErrorType.AUTHORIZATION_ERROR,
            code="application_suspended",
        )


class ScopeDeniedError(PublicAPIException):
    def __init__(self, required_scope: str, message: Optional[str] = None):
        msg = message or f"API credential lacks required scope '{required_scope}'."
        super().__init__(
            message=msg,
            status_code=403,
            error_type=PublicAPIErrorType.AUTHORIZATION_ERROR,
            code="insufficient_scope",
            details={"required_scope": required_scope},
        )


class ResourceScopeViolationError(PublicAPIException):
    def __init__(self, message: str = "Resource is outside the credential's authorized scope."):
        super().__init__(
            message=message,
            status_code=403,
            error_type=PublicAPIErrorType.AUTHORIZATION_ERROR,
            code="resource_scope_violation",
        )


class EnvironmentMismatchError(PublicAPIException):
    def __init__(self, key_env: str, target_env: str):
        super().__init__(
            message=f"Environment mismatch: key for '{key_env}' cannot access '{target_env}' resources.",
            status_code=403,
            error_type=PublicAPIErrorType.AUTHORIZATION_ERROR,
            code="environment_mismatch",
            details={"key_environment": key_env, "target_environment": target_env},
        )


class RateLimitExceededError(PublicAPIException):
    def __init__(self, retry_after: int = 60, message: str = "Too many requests."):
        super().__init__(
            message=message,
            status_code=429,
            error_type=PublicAPIErrorType.RATE_LIMIT_ERROR,
            code="rate_limit_exceeded",
            headers={"Retry-After": str(retry_after)},
            details={"retry_after_seconds": retry_after},
        )


class QuotaExceededError(PublicAPIException):
    def __init__(self, resource_type: str, limit: int, period: str):
        super().__init__(
            message=f"Quota exceeded for '{resource_type}': limit of {limit} per {period} reached.",
            status_code=429,
            error_type=PublicAPIErrorType.RATE_LIMIT_ERROR,
            code="quota_exceeded",
            details={"resource_type": resource_type, "limit": limit, "period": period},
        )


class IdempotencyConflictError(PublicAPIException):
    def __init__(self, message: str = "Idempotency key reused with different request payload."):
        super().__init__(
            message=message,
            status_code=409,
            error_type=PublicAPIErrorType.CONFLICT,
            code="idempotency_conflict",
        )


class SSRFBlockedError(PublicAPIException):
    def __init__(self, message: str = "Webhook URL points to a restricted or private network destination."):
        super().__init__(
            message=message,
            status_code=400,
            error_type=PublicAPIErrorType.VALIDATION_ERROR,
            code="ssrf_destination_blocked",
        )


class ResourceNotFoundError(PublicAPIException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} '{resource_id}' not found.",
            status_code=404,
            error_type=PublicAPIErrorType.NOT_FOUND,
            code="resource_not_found",
            details={"resource": resource, "id": resource_id},
        )


class PublicAPIGovernanceDeniedError(PublicAPIException):
    def __init__(self, reasons: list):
        super().__init__(
            message=f"Request denied by Governance Policy: {'; '.join(reasons)}",
            status_code=403,
            error_type=PublicAPIErrorType.GOVERNANCE_ERROR,
            code="governance_policy_denied",
            details={"reasons": reasons},
        )
