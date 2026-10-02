"""
Trigger domain exceptions and error definitions.
"""
from typing import Any, Dict, Optional
from backend.app.core.errors import AppError


class TriggerError(AppError):
    """Base exception for trigger domain errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, status_code: int = 400):
        super().__init__(message=message, status_code=status_code)
        self.details = details or {}


class TriggerNotFoundError(TriggerError):
    """Raised when a trigger or trigger run is not found."""
    def __init__(self, message: str = "Trigger not found.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details, status_code=404)


class TriggerValidationError(TriggerError):
    """Raised when trigger configuration or schedule fails validation."""
    def __init__(self, message: str = "Trigger validation failed.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details, status_code=422)


class TriggerDisabledError(TriggerError):
    """Raised when attempting to execute a paused, disabled, or archived trigger."""
    def __init__(self, message: str = "Trigger is not active.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details, status_code=400)


class WebhookSignatureError(TriggerError):
    """Raised when a webhook request signature verification fails."""
    def __init__(self, message: str = "Invalid webhook signature or expired timestamp.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details, status_code=401)


class TriggerRateLimitError(TriggerError):
    """Raised when trigger execution rate limit is exceeded."""
    def __init__(self, message: str = "Trigger rate limit exceeded.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details, status_code=429)


class TriggerConcurrencyError(TriggerError):
    """Raised when max trigger concurrency for workspace is exceeded."""
    def __init__(self, message: str = "Workspace trigger concurrency limit reached.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details, status_code=429)


class TriggerPolicyError(TriggerError):
    """Raised when a trigger violates workflow, connector, or security policies."""
    def __init__(self, message: str = "Trigger policy violation.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details, status_code=403)


class TriggerDeduplicationError(TriggerError):
    """Raised when an event is rejected due to deduplication / idempotency window."""
    def __init__(self, message: str = "Event was already processed (duplicate).", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details, status_code=409)
