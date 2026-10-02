"""
Domain exception hierarchy for Step 25: Notifications & External Delivery Layer.
"""
from backend.app.core.errors import (
    AppError,
    NotFoundError,
    ValidationError,
    AuthorizationError,
)


class NotificationError(AppError):
    """Base exception for notification domain errors."""
    def __init__(self, message: str, status_code: int = 400, details: dict = None):
        super().__init__(message=message, status_code=status_code, details=details or {})


class NotificationNotFoundError(NotFoundError):
    """Notification entity not found."""
    def __init__(self, notification_id: str):
        super().__init__(f"Notification '{notification_id}' not found.")


class WebhookEndpointNotFoundError(NotFoundError):
    """Webhook destination endpoint not found."""
    def __init__(self, endpoint_id: str):
        super().__init__(f"Webhook endpoint '{endpoint_id}' not found.")


class NotificationValidationError(ValidationError):
    """Validation failed for notification, preference, or endpoint."""
    def __init__(self, message: str):
        super().__init__(message)


class SSRFSecurityError(AuthorizationError):
    """Outbound URL violates SSRF security boundaries."""
    def __init__(self, reason: str):
        super().__init__(f"SSRF Protection blocked destination URL: {reason}")


class RateLimitExceededError(NotificationError):
    """Workspace exceeded outbound notification quota."""
    def __init__(self, message: str):
        super().__init__(message=message, status_code=429)


NotificationRateLimitError = RateLimitExceededError


class ChannelNotConfiguredError(NotificationError):
    """Delivery channel is unconfigured or unavailable."""
    def __init__(self, channel: str, reason: str = ""):
        super().__init__(
            message=f"Delivery channel '{channel}' is not configured: {reason}".strip(),
            status_code=503,
        )


class DeliveryError(NotificationError):
    """Base delivery exception."""
    def __init__(self, message: str, error_code: str = "DELIVERY_ERROR", is_transient: bool = False):
        super().__init__(message=message, status_code=500, details={"error_code": error_code, "transient": is_transient})
        self.error_code = error_code
        self.is_transient = is_transient


class DeliveryTransientError(DeliveryError):
    """Transient delivery failure eligible for retry with backoff."""
    def __init__(self, message: str, error_code: str = "TRANSIENT_DELIVERY_FAILURE"):
        super().__init__(message=message, error_code=error_code, is_transient=True)


class DeliveryPermanentError(DeliveryError):
    """Permanent delivery failure (4xx, invalid destination, rejected by remote)."""
    def __init__(self, message: str, error_code: str = "PERMANENT_DELIVERY_FAILURE"):
        super().__init__(message=message, error_code=error_code, is_transient=False)


class InvalidDestinationError(DeliveryPermanentError):
    """Destination is malformed, unreachable, or violates protocol rules."""
    def __init__(self, message: str):
        super().__init__(message=message, error_code="INVALID_DESTINATION")
