"""
Deterministic retry engine for Step 35: AI Reliability, Resilience & Chaos Engineering Layer.
Integrates with FailureClassifier to ensure non-retryable failures are never retried.
"""
import asyncio
import logging
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set

from backend.app.services.reliability.backoff import compute_backoff_delay
from backend.app.services.reliability.failure_classifier import FailureClassifier
from backend.app.services.reliability.schemas import RetryDecisionResult

logger = logging.getLogger("reliability.retry")

NON_RETRYABLE_CLASSIFICATIONS: Set[str] = {
    "authorization",
    "policy_denied",
    "validation",
    "human_required",
}


class RetryPolicy:
    """Configuration for retry execution."""
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        factor: float = 2.0,
        jitter: bool = True,
        retryable_classifications: Optional[Set[str]] = None,
        is_idempotent: bool = True,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.factor = factor
        self.jitter = jitter
        self.retryable_classifications = retryable_classifications or {
            "transient",
            "rate_limited",
            "capacity",
            "timeout",
            "network",
            "provider_unavailable",
            "database_failure",
            "connector_failure",
        }
        self.is_idempotent = is_idempotent


class RetryExecutor:
    """Evaluates and executes retry attempts safely."""

    @classmethod
    def evaluate_retry(
        cls,
        attempt: int,
        policy: RetryPolicy,
        error: Optional[Exception] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        status_code: Optional[int] = None,
        is_destructive_operation: bool = False,
    ) -> RetryDecisionResult:
        """
        Determines whether an operation can be retried and computes delay.
        """
        # Rule 1: Non-idempotent destructive operations cannot be retried automatically
        if is_destructive_operation and not policy.is_idempotent:
            return RetryDecisionResult(
                should_retry=False,
                attempt_number=attempt,
                max_attempts=policy.max_attempts,
                delay_seconds=0.0,
                reason="Destructive operation is not verified idempotent; retry blocked.",
            )

        # Rule 2: Attempt threshold reached
        if attempt >= policy.max_attempts:
            return RetryDecisionResult(
                should_retry=False,
                attempt_number=attempt,
                max_attempts=policy.max_attempts,
                delay_seconds=0.0,
                reason=f"Maximum retry attempts reached ({attempt}/{policy.max_attempts}).",
            )

        # Rule 3: Classify failure deterministically
        classified = FailureClassifier.classify(
            error=error,
            error_type=error_type,
            error_message=error_message,
            status_code=status_code,
        )

        # Rule 4: Explicit non-retryable categories
        if classified.classification in NON_RETRYABLE_CLASSIFICATIONS or not classified.retryable:
            return RetryDecisionResult(
                should_retry=False,
                attempt_number=attempt,
                max_attempts=policy.max_attempts,
                delay_seconds=0.0,
                reason=f"Failure classified as '{classified.classification}'; retry is strictly forbidden ({classified.rationale}).",
            )

        # Rule 5: Check policy allowlist
        if classified.classification not in policy.retryable_classifications:
            return RetryDecisionResult(
                should_retry=False,
                attempt_number=attempt,
                max_attempts=policy.max_attempts,
                delay_seconds=0.0,
                reason=f"Classification '{classified.classification}' is not in policy retryable set.",
            )

        # Calculate backoff delay
        delay = compute_backoff_delay(
            attempt=attempt,
            base_delay=policy.base_delay,
            max_delay=policy.max_delay,
            factor=policy.factor,
            jitter=policy.jitter,
        )

        return RetryDecisionResult(
            should_retry=True,
            attempt_number=attempt,
            max_attempts=policy.max_attempts,
            delay_seconds=round(delay, 3),
            reason=f"Retrying after {classified.classification} with {delay:.2f}s backoff.",
        )

    @classmethod
    async def execute_with_retry(
        cls,
        operation: Callable[[], Coroutine[Any, Any, Any]],
        policy: RetryPolicy,
        operation_name: str = "operation",
        is_destructive: bool = False,
    ) -> Any:
        """Executes an async callable with bound retries and backoff."""
        attempt = 1
        while True:
            try:
                return await operation()
            except Exception as exc:
                decision = cls.evaluate_retry(
                    attempt=attempt,
                    policy=policy,
                    error=exc,
                    is_destructive_operation=is_destructive,
                )
                if not decision.should_retry:
                    logger.warning(
                        "Retry declined for %s on attempt %d: %s",
                        operation_name, attempt, decision.reason
                    )
                    raise exc

                logger.info(
                    "Retrying %s (attempt %d/%d) after %.2fs delay: %s",
                    operation_name, attempt, policy.max_attempts, decision.delay_seconds, decision.reason
                )
                await asyncio.sleep(decision.delay_seconds)
                attempt += 1
