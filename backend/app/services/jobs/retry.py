"""
Retry policy and backoff calculation for Step 24: Durable Background Job System.
"""
import random
from typing import Optional, Tuple


class JobRetryPolicy:
    """
    Classifies job execution errors as transient or permanent,
    and calculates exponential backoff with jitter.
    """

    TRANSIENT_PATTERNS = [
        "timeout",
        "timed out",
        "connection_error",
        "connection refused",
        "connection reset",
        "provider_unavailable",
        "temporary_network_failure",
        "temporary_connector_failure",
        "rate_limited",
        "429",
        "502",
        "503",
        "504",
        "service unavailable",
        "bad gateway",
        "gateway timeout",
        "lease_expired",
        "worker_crashed",
    ]

    PERMANENT_PATTERNS = [
        "invalid_credentials",
        "authorization_failure",
        "unauthorized",
        "forbidden",
        "permission_denied",
        "401",
        "403",
        "422",
        "destructive_policy_violation",
        "policy_blocked",
        "policy_denial",
        "hitl_rejection",
        "malformed_workflow",
        "invalid_input",
        "validation_error",
        "not_found",
        "notfound",
        "schema_validation_error",
        "invalid_target",
        "unsupported",
    ]

    @classmethod
    def is_transient_error(
        cls,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Returns True if the failure is transient and eligible for retry.
        Permanent errors (authorization, validation, HITL, security) are NEVER retried.
        """
        combined = f"{error_code or ''} {error_message or ''}".lower()

        # Check explicit permanent first
        for perm in cls.PERMANENT_PATTERNS:
            if perm in combined:
                return False

        # Check transient indicators
        for trans in cls.TRANSIENT_PATTERNS:
            if trans in combined:
                return True

        # Default: if error_code matches generic transient errors
        return False

    @classmethod
    def should_retry(
        cls,
        attempts: int,
        max_attempts: int,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Determines whether a job should be scheduled for a retry attempt.
        """
        if attempts >= max_attempts:
            return False

        return cls.is_transient_error(error_code=error_code, error_message=error_message)

    @classmethod
    def calculate_backoff_delay(
        cls,
        attempts: int,
        base_seconds: float = 2.0,
        factor: float = 2.0,
        max_seconds: float = 300.0,
        jitter_pct: float = 0.2,
    ) -> float:
        """
        Calculates bounded exponential backoff delay with random jitter:
        delay = min(base * (factor ** attempts) + jitter, max_seconds).
        """
        exp_delay = base_seconds * (factor ** max(0, attempts - 1))
        capped = min(exp_delay, max_seconds)
        
        # Add random jitter up to +/- jitter_pct
        jitter = capped * random.uniform(0.0, jitter_pct)
        return round(min(capped + jitter, max_seconds), 2)
