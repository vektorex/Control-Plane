"""
Bounded retry evaluation with transient failure classification and exponential backoff.
"""
from typing import Optional


class TriggerRetryManager:
    """
    Evaluates whether trigger execution failures are transient and retryable.
    """

    TRANSIENT_PATTERNS = [
        "provider_unavailable",
        "timeout",
        "temporary_network_failure",
        "temporary_connector_failure",
        "gateway_timeout",
        "connection_error",
        "timed out",
        "service unavailable",
        "502",
        "503",
        "504",
        "rate_limited",
    ]

    NON_RETRYABLE_PATTERNS = [
        "invalid_workflow",
        "authorization_failure",
        "invalid_input",
        "policy_denial",
        "hitl_rejection",
        "permission_denied",
        "not_found",
        "validation_error",
        "unauthorized",
        "forbidden",
        "401",
        "403",
        "422",
    ]

    @classmethod
    def is_transient_failure(
        cls,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Determines if failure is transient.
        Never retries authorization, validation, or policy rejection.
        """
        combined = f"{error_code or ''} {error_message or ''}".lower()

        # Check explicit non-retryable first
        for non_ret in cls.NON_RETRYABLE_PATTERNS:
            if non_ret in combined:
                return False

        # Check transient indicators
        for trans in cls.TRANSIENT_PATTERNS:
            if trans in combined:
                return True

        return False

    @classmethod
    def should_retry(
        cls,
        error_code: Optional[str],
        error_message: Optional[str],
        current_retry_count: int,
        max_retries: int = 2,
    ) -> bool:
        """
        Checks if a retry should be scheduled given retry limits and failure type.
        """
        if current_retry_count >= max_retries:
            return False

        return cls.is_transient_failure(error_code=error_code, error_message=error_message)

    @classmethod
    def calculate_backoff_delay(
        cls,
        retry_count: int,
        backoff_factor: float = 2.0,
        base_seconds: float = 2.0,
        max_seconds: float = 60.0,
    ) -> float:
        """
        Calculates exponential backoff delay: min(base * (factor ** retry_count), max_seconds).
        """
        delay = base_seconds * (backoff_factor ** max(0, retry_count))
        return min(delay, max_seconds)
