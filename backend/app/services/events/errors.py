"""
Domain exception hierarchy for Step 26: Unified Event Bus and Real-Time Execution Updates.
"""
from backend.app.core.errors import (
    AppError,
    NotFoundError,
    ValidationError,
    AuthorizationError,
)


class EventError(AppError):
    """Base exception for event domain errors."""
    def __init__(self, message: str, status_code: int = 400, details: dict = None):
        super().__init__(message=message, status_code=status_code, details=details or {})


class EventNotFoundError(NotFoundError):
    """Event entity not found."""
    def __init__(self, event_id: str):
        super().__init__(f"Event '{event_id}' not found.")


class EventValidationError(ValidationError):
    """Event validation failed."""
    def __init__(self, message: str):
        super().__init__(message)


class EventAuthorizationError(AuthorizationError):
    """Unauthorized attempt to access or publish an event."""
    def __init__(self, message: str = "Unauthorized event access."):
        super().__init__(message)


class EventPayloadTooLargeError(ValidationError):
    """Event payload exceeds maximum configured byte budget."""
    def __init__(self, size_bytes: int, max_bytes: int):
        super().__init__(f"Event payload of {size_bytes} bytes exceeds maximum limit of {max_bytes} bytes.")


class InvalidFilterError(ValidationError):
    """Stream or history filter expression is invalid or dangerous."""
    def __init__(self, message: str):
        super().__init__(f"Invalid filter: {message}")


class SlowClientError(EventError):
    """Real-time SSE client buffer overflowed due to slow reading."""
    def __init__(self, client_id: str):
        super().__init__(f"Client '{client_id}' fell behind real-time stream; connection terminated.", status_code=429)


class ConsumerExecutionError(EventError):
    """Event consumer execution encountered a failure."""
    def __init__(self, consumer_name: str, event_id: str, reason: str):
        super().__init__(
            message=f"Consumer '{consumer_name}' failed processing event '{event_id}': {reason}",
            status_code=500,
        )


class EventDuplicateError(EventError):
    """Event publication duplicate detected via idempotency key."""
    def __init__(self, idempotency_key: str):
        super().__init__(f"Duplicate event publication for key '{idempotency_key}'.", status_code=409)
