"""
High-level Recovery Orchestrator for Step 35: AI Reliability, Resilience & Chaos Engineering Layer.
Coordinates retry, checkpoint resumption, fallback routing, and graceful degradation.
Never blindly replays side-effecting external steps.
"""
from typing import Any, Callable, Coroutine, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.reliability.circuit_breaker import CircuitBreakerRegistry
from backend.app.services.reliability.degradation import DegradationPolicy, DegradationResolver
from backend.app.services.reliability.failure_classifier import FailureClassifier
from backend.app.services.reliability.fallback import FallbackPolicy, FallbackResolver
from backend.app.services.reliability.resume import ResumeService
from backend.app.services.reliability.retry import RetryExecutor, RetryPolicy
from backend.app.services.reliability.schemas import (
    DegradationDecisionResult,
    FailureClassificationResult,
    FallbackDecisionResult,
    RetryDecisionResult,
)


class RecoveryOrchestrator:
    """Central recovery controller integrating failure classification, retry, fallback, and resume."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.resume_service = ResumeService(session)

    async def handle_execution_failure(
        self,
        component_name: str,
        attempt: int,
        error: Exception,
        retry_policy: Optional[RetryPolicy] = None,
        fallback_policy: Optional[FallbackPolicy] = None,
        is_destructive: bool = False,
    ) -> Dict[str, Any]:
        """
        Coordinates full failure resolution chain:
        1. Classify failure deterministically
        2. Evaluate retry decision
        3. Check/update circuit breaker
        4. If retry blocked or exhausted, evaluate fallback
        5. If fallback unavailable, evaluate degraded mode or safe fail
        """
        # 1. Classify
        classification = FailureClassifier.classify(error=error)

        # 2. Update circuit breaker if applicable
        breaker = CircuitBreakerRegistry.get_breaker(component_name)
        if classification.classification in {"timeout", "network", "provider_unavailable", "capacity"}:
            breaker.record_failure()
        elif classification.classification in {"authorization", "policy_denied", "validation"}:
            # Do not trip circuit breakers on client errors or policy denials
            pass

        # 3. Check Retry
        r_policy = retry_policy or RetryPolicy()
        retry_decision = RetryExecutor.evaluate_retry(
            attempt=attempt,
            policy=r_policy,
            error=error,
            is_destructive_operation=is_destructive,
        )

        if retry_decision.should_retry:
            return {
                "action": "retry",
                "classification": classification.model_dump(),
                "retry_decision": retry_decision.model_dump(),
                "circuit_state": breaker.get_status(),
            }

        # 4. Fallback Evaluation
        f_policy = fallback_policy or FallbackPolicy()
        fallback_decision = FallbackResolver.resolve_fallback(
            primary_target=component_name,
            primary_provider="primary",
            failure_reason=classification.rationale,
            policy=f_policy,
        )

        if fallback_decision.fallback_used:
            return {
                "action": "fallback",
                "classification": classification.model_dump(),
                "fallback_decision": fallback_decision.model_dump(),
                "circuit_state": breaker.get_status(),
            }

        # 5. Safe Failure
        return {
            "action": "fail_safely",
            "classification": classification.model_dump(),
            "fallback_decision": fallback_decision.model_dump(),
            "circuit_state": breaker.get_status(),
            "reason": f"Operation cannot proceed: {classification.rationale}",
        }
