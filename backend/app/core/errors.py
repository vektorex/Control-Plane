from typing import Any, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


class AppError(Exception):
    """Base application exception."""
    code: str = "APP_ERROR"
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, message: str, details: Optional[Any] = None, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.details = details
        if status_code is not None:
            self.status_code = status_code


class NotFoundError(AppError):
    """Raised when a requested resource is not found."""
    code = "NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND


class AuthenticationError(AppError):
    """Raised when authentication fails (missing, invalid, or expired token)."""
    code = "AUTHENTICATION_REQUIRED"
    status_code = status.HTTP_401_UNAUTHORIZED


class AuthorizationError(AppError):
    """Raised when user lacks permission to access or perform an action on a resource."""
    code = "FORBIDDEN"
    status_code = status.HTTP_403_FORBIDDEN



class ConflictError(AppError):
    """Raised when a uniqueness or integrity conflict occurs (e.g. duplicate slug)."""
    code = "CONFLICT"
    status_code = status.HTTP_409_CONFLICT


class InvalidStateError(AppError):
    """Raised when an invalid state transition or operation is requested."""
    code = "INVALID_STATE"
    status_code = status.HTTP_400_BAD_REQUEST


class DatabaseError(AppError):
    """Raised when an unexpected database execution error occurs."""
    code = "DATABASE_ERROR"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class LLMError(AppError):
    """Base exception for all LLM abstraction errors."""
    code = "LLM_ERROR"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class ProviderNotConfiguredError(LLMError):
    """Raised when an LLM provider lacks required configuration (e.g. API keys)."""
    code = "PROVIDER_NOT_CONFIGURED"
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class ModelNotFoundError(LLMError):
    """Raised when a requested model is not supported or recognized by registered providers."""
    code = "MODEL_NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND


class ProviderAuthenticationError(LLMError):
    """Raised when provider rejects credentials."""
    code = "PROVIDER_AUTHENTICATION_ERROR"
    status_code = status.HTTP_401_UNAUTHORIZED


class ProviderRateLimitError(LLMError):
    """Raised when provider throttles or rate limits requests."""
    code = "PROVIDER_RATE_LIMIT_ERROR"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS


class ProviderTimeoutError(LLMError):
    """Raised when provider call times out."""
    code = "PROVIDER_TIMEOUT_ERROR"
    status_code = status.HTTP_504_GATEWAY_TIMEOUT


class ProviderAPIError(LLMError):
    """Raised when provider returns an unhandled API error."""
    code = "PROVIDER_API_ERROR"
    status_code = status.HTTP_502_BAD_GATEWAY


def format_error_response(code: str, message: str, details: Optional[Any] = None) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
        }
    }


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(exc.code, exc.message, exc.details),
    )


# Backward compatibility alias
llm_error_handler = app_error_handler


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    status_code = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", status.HTTP_422_UNPROCESSABLE_ENTITY)
    return JSONResponse(
        status_code=status_code,
        content=format_error_response(
            "VALIDATION_ERROR",
            "Invalid request parameters",
            exc.errors(),
        ),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=format_error_response(
            "INTERNAL_SERVER_ERROR",
            "An unexpected error occurred processing your request." if not isinstance(exc, AppError) else str(exc),
        ),
    )
