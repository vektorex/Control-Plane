from typing import Any, Optional
from fastapi import status
from backend.app.core.errors import AppError


class GatewayError(AppError):
    """Base exception for all AI Gateway runtime errors."""
    code: str = "GATEWAY_ERROR"
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Any] = None,
        status_code: Optional[int] = None,
    ):
        super().__init__(message, details=details, status_code=status_code)
        if code:
            self.code = code

    def to_safe_dict(self) -> dict:
        """Returns safe normalized error dictionary without leaking provider stack traces or keys."""
        return {
            "error": True,
            "code": self.code,
            "message": self.message,
            "details": self.details or {},
        }


class ModelNotFoundError(GatewayError):
    code = "MODEL_NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND


class ModelNotAllowedError(GatewayError):
    code = "MODEL_NOT_ALLOWED"
    status_code = status.HTTP_403_FORBIDDEN


class ProviderUnavailableError(GatewayError):
    code = "PROVIDER_UNAVAILABLE"
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class ProviderTimeoutError(GatewayError):
    code = "PROVIDER_TIMEOUT"
    status_code = status.HTTP_504_GATEWAY_TIMEOUT


class ModelTimeoutError(GatewayError):
    code = "MODEL_TIMEOUT"
    status_code = status.HTTP_504_GATEWAY_TIMEOUT


class RateLimitedError(GatewayError):
    code = "RATE_LIMITED"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS


class CapabilityUnsupportedError(GatewayError):
    code = "CAPABILITY_UNSUPPORTED"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class InvalidRequestError(GatewayError):
    code = "INVALID_REQUEST"
    status_code = status.HTTP_400_BAD_REQUEST


class PolicyDeniedError(GatewayError):
    code = "POLICY_DENIED"
    status_code = status.HTTP_403_FORBIDDEN


class AllFallbacksFailedError(GatewayError):
    code = "ALL_FALLBACKS_FAILED"
    status_code = status.HTTP_502_BAD_GATEWAY


class CircuitOpenError(GatewayError):
    code = "CIRCUIT_OPEN"
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class ConcurrencyLimitError(GatewayError):
    code = "CONCURRENCY_LIMIT"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
