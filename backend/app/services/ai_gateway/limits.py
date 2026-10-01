import asyncio
from typing import Any, Callable, Dict, Optional
from backend.app.core.logging import logger
from backend.app.services.ai_gateway.errors import (
    ConcurrencyLimitError,
    GatewayError,
    ModelNotAllowedError,
    ModelTimeoutError,
    PolicyDeniedError,
    CapabilityUnsupportedError,
    InvalidRequestError,
    RateLimitedError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)

MAX_MODEL_RETRIES = 2
MAX_CONCURRENT_MODEL_REQUESTS = 10
MODEL_REQUEST_TIMEOUT_SECONDS = 120


class ConcurrencyLimiter:
    """
    Manages bounded concurrency across model executions to protect providers
    and prevent runaway concurrent workflow calls from overwhelming the system.
    """

    def __init__(self, max_concurrent: int = MAX_CONCURRENT_MODEL_REQUESTS):
        self._max_concurrent = max_concurrent
        self._semaphores: Dict[str, asyncio.Semaphore] = {}
        self._global_semaphore = asyncio.Semaphore(max_concurrent)

    def _get_workspace_semaphore(self, workspace_id: Optional[str], limit: Optional[int] = None) -> asyncio.Semaphore:
        ws_key = str(workspace_id or "global")
        if ws_key not in self._semaphores:
            effective_limit = limit or self._max_concurrent
            self._semaphores[ws_key] = asyncio.Semaphore(effective_limit)
        return self._semaphores[ws_key]

    async def acquire(self, workspace_id: Optional[str] = None, limit: Optional[int] = None) -> None:
        """Acquire concurrency slot, rejecting if capacity is exhausted."""
        sem = self._get_workspace_semaphore(workspace_id, limit)
        try:
            # Non-blocking acquisition attempt or rapid acquisition
            acquired = await asyncio.wait_for(sem.acquire(), timeout=0.1)
            if not acquired:
                raise ConcurrencyLimitError(
                    f"Concurrency limit ({limit or self._max_concurrent}) exceeded for workspace."
                )
        except asyncio.TimeoutError:
            raise ConcurrencyLimitError(
                f"Concurrency limit ({limit or self._max_concurrent}) reached. Please retry shortly."
            )

    def release(self, workspace_id: Optional[str] = None) -> None:
        """Release concurrency slot."""
        ws_key = str(workspace_id or "global")
        if ws_key in self._semaphores:
            try:
                self._semaphores[ws_key].release()
            except ValueError:
                pass


class RetryPolicy:
    """
    Bounded exponential backoff retry manager for transient operational failures.
    Strictly forbids retrying validation, permission, or policy violations.
    """

    NON_RETRYABLE_ERRORS = (
        ModelNotAllowedError,
        PolicyDeniedError,
        CapabilityUnsupportedError,
        InvalidRequestError,
    )

    RETRYABLE_ERRORS = (
        RateLimitedError,
        ProviderTimeoutError,
        ModelTimeoutError,
        ProviderUnavailableError,
    )

    @classmethod
    def is_retryable(cls, exc: Exception) -> bool:
        from backend.app.core.errors import ProviderAuthError
        if isinstance(exc, (cls.NON_RETRYABLE_ERRORS, ProviderAuthError)):
            return False
        err_msg = str(exc).lower()
        if any(k in err_msg for k in ["auth", "unauthorized", "forbidden", "permission", "invalid", "validation"]):
            return False
        if isinstance(exc, cls.RETRYABLE_ERRORS):
            return True
        return any(k in err_msg for k in ["rate limit", "429", "timeout", "connection reset", "econnreset", "503"])

    @classmethod
    def get_backoff(cls, attempt: int, initial_delay: float = 0.25) -> float:
        """Compute exponential backoff delay in seconds."""
        return initial_delay * (2 ** (attempt - 1))


default_concurrency_limiter = ConcurrencyLimiter()
