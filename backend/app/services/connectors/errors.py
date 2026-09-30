"""
Custom exceptions and normalized error codes for the Connector System.
"""
from typing import Any, Dict, Optional


class ConnectorError(Exception):
    """Base exception for all connector operations."""
    def __init__(self, message: str, code: str = "CONNECTOR_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class ConnectorNotFoundError(ConnectorError):
    """Raised when a connector is not registered."""
    def __init__(self, connector_name: str):
        super().__init__(
            message=f"Connector '{connector_name}' is not registered or supported.",
            code="CONNECTOR_NOT_FOUND",
            details={"connector": connector_name},
        )


class ConnectorOperationNotFoundError(ConnectorError):
    """Raised when an operation is not supported by a connector."""
    def __init__(self, connector_name: str, operation: str):
        super().__init__(
            message=f"Operation '{operation}' is not supported by connector '{connector_name}'.",
            code="CONNECTOR_OPERATION_NOT_FOUND",
            details={"connector": connector_name, "operation": operation},
        )


class ConnectorAuthError(ConnectorError):
    """Raised when authentication credentials are missing, invalid, or expired."""
    def __init__(self, message: str = "Connector authentication failed. Check credentials or connection status."):
        super().__init__(message=message, code="CONNECTOR_AUTH_FAILED")


class ConnectorPermissionError(ConnectorError):
    """Raised when an operation is disallowed by workspace or connector permissions."""
    def __init__(self, message: str = "Permission denied for this connector operation."):
        super().__init__(message=message, code="CONNECTOR_PERMISSION_DENIED")


class ConnectorRateLimitError(ConnectorError):
    """Raised when external provider rate limits are exceeded."""
    def __init__(self, message: str = "The connector rate limit was reached."):
        super().__init__(message=message, code="CONNECTOR_RATE_LIMITED")


class ConnectorTimeoutError(ConnectorError):
    """Raised when an external connector API call times out."""
    def __init__(self, message: str = "Connector request timed out."):
        super().__init__(message=message, code="CONNECTOR_TIMEOUT")


class ConnectorUnavailableError(ConnectorError):
    """Raised when the external provider service is unavailable (e.g. 502/503)."""
    def __init__(self, message: str = "The external connector service is currently unavailable."):
        super().__init__(message=message, code="CONNECTOR_UNAVAILABLE")


class ConnectorValidationError(ConnectorError):
    """Raised when operation input arguments fail validation."""
    def __init__(self, message: str):
        super().__init__(message=message, code="CONNECTOR_INVALID_ARGUMENTS")


class ConnectorPayloadTooLargeError(ConnectorError):
    """Raised when connector payload exceeds configured safety byte limit."""
    def __init__(self, message: str = "Connector response exceeds maximum allowed payload size."):
        super().__init__(message=message, code="CONNECTOR_PAYLOAD_TOO_LARGE")
