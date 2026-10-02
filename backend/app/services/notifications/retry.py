"""
DeliveryRetryPolicy: Classification of transient vs permanent errors and jittered backoff.
"""
import random
from typing import Optional
import httpx

from backend.app.services.notifications.errors import (
    DeliveryPermanentError,
    DeliveryTransientError,
    SSRFSecurityError,
)


class DeliveryRetryPolicy:
    """
    Evaluates delivery failures, determines whether a retry is permitted,
    and calculates jittered exponential backoff intervals.
    """

    DEFAULT_BASE_DELAY_SECONDS = 5.0
    DEFAULT_MAX_DELAY_SECONDS = 300.0
    DEFAULT_MAX_ATTEMPTS = 3

    @classmethod
    def is_transient_error(cls, exc: Exception) -> bool:
        """
        Determines if an exception or HTTP status code is transient and eligible for retry.
        """
        if isinstance(exc, DeliveryTransientError):
            return True

        if isinstance(exc, (DeliveryPermanentError, SSRFSecurityError, ValueError)):
            return False

        # HTTPX client exceptions
        if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError, httpx.ConnectError, httpx.ReadTimeout)):
            return True

        # Standard OS / network socket exceptions
        if isinstance(exc, (TimeoutError, ConnectionResetError, ConnectionError)):
            return True

        if isinstance(exc, httpx.HTTPStatusError):
            status_code = exc.response.status_code
            if status_code == 429 or status_code >= 500:
                return True
            return False

        return False

    @classmethod
    def calculate_backoff(
        cls,
        attempt: int,
        base_delay: float = DEFAULT_BASE_DELAY_SECONDS,
        max_delay: float = DEFAULT_MAX_DELAY_SECONDS,
    ) -> float:
        """
        Computes bounded exponential backoff with uniform random jitter.
        delay = min(base * (2 ** (attempt - 1)) + jitter, max_delay)
        """
        if attempt <= 0:
            attempt = 1
        exp_factor = 2 ** (attempt - 1)
        raw_delay = base_delay * exp_factor
        jitter = random.uniform(0.1, 1.5)
        return min(raw_delay + jitter, max_delay)
