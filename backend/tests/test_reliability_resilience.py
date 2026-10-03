"""
Comprehensive Unit & Integration Test Suite for Step 35:
AI Reliability, Resilience & Chaos Engineering Layer.
"""
import asyncio
from datetime import datetime, timezone
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.services.reliability.backoff import compute_backoff_delay
from backend.app.services.reliability.bulkhead import BulkheadRegistry, SubsystemBulkhead
from backend.app.services.reliability.chaos import ChaosFailureSimulator
from backend.app.services.reliability.circuit_breaker import CircuitBreaker, CircuitBreakerRegistry
from backend.app.services.reliability.degradation import DegradationPolicy, DegradationResolver
from backend.app.services.reliability.exceptions import (
    BulkheadCapacityExceededError,
    ChaosExperimentAbortedError,
    CheckpointIntegrityError,
    CircuitOpenError,
    InvalidChaosActionError,
    ProductionChaosBlockedError,
    ResumePreconditionFailedError,
    UnauthorizedChaosExecutionError,
)
from backend.app.services.reliability.failure_classifier import FailureClassifier
from backend.app.services.reliability.fallback import FallbackPolicy, FallbackResolver
from backend.app.services.reliability.retry import RetryExecutor, RetryPolicy
from backend.app.services.reliability.validators import (
    compute_state_fingerprint,
    validate_chaos_action_allowlist,
    validate_chaos_experiment_safety,
    validate_checkpoint_integrity,
    validate_resumption_preconditions,
)
from backend.app.services.reliability.schemas import (
    CheckpointResumeRequest,
    ExecutionCheckpointCreate,
)


def _uuid() -> str:
    return str(uuid.uuid4())


# ===========================================================================
# 1. Failure Classifier Tests
# ===========================================================================
def test_failure_classifier_rate_limit():
    res = FailureClassifier.classify(
        error_message="Rate limit exceeded. HTTP 429 Too Many Requests",
        status_code=429,
    )
    assert res.classification == "rate_limited"
    assert res.retryable is True
    assert res.requires_human is False


def test_failure_classifier_authorization_non_retryable():
    res = FailureClassifier.classify(
        error_message="Access denied: Missing tenant boundary permission",
        status_code=403,
    )
    assert res.classification == "authorization"
    assert res.retryable is False
    assert res.requires_human is True


def test_failure_classifier_governance_policy_denied():
    res = FailureClassifier.classify(
        error_message="Blocked by AI Governance policy guardrail",
    )
    assert res.classification == "policy_denied"
    assert res.retryable is False
    assert res.requires_human is True


def test_failure_classifier_timeout():
    res = FailureClassifier.classify(
        error_message="Gateway timeout after 60s",
        status_code=504,
    )
    assert res.classification == "timeout"
    assert res.retryable is True


def test_failure_classifier_provider_unavailable():
    res = FailureClassifier.classify(
        error_message="Provider down. Bad gateway 502",
        status_code=502,
    )
    assert res.classification == "provider_unavailable"
    assert res.retryable is True


# ===========================================================================
# 2. Backoff & Retry Tests
# ===========================================================================
def test_exponential_backoff_calculation():
    d1 = compute_backoff_delay(attempt=1, base_delay=1.0, jitter=False)
    d2 = compute_backoff_delay(attempt=2, base_delay=1.0, jitter=False)
    d3 = compute_backoff_delay(attempt=3, base_delay=1.0, jitter=False)

    assert d1 == 1.0
    assert d2 == 2.0
    assert d3 == 4.0


def test_retry_executor_blocks_authorization_failure():
    policy = RetryPolicy(max_attempts=3)
    decision = RetryExecutor.evaluate_retry(
        attempt=1,
        policy=policy,
        error_message="Unauthorized access to organization workspace",
        status_code=401,
    )
    assert decision.should_retry is False
    assert "strictly forbidden" in decision.reason


def test_retry_executor_blocks_non_idempotent_destructive():
    policy = RetryPolicy(max_attempts=3, is_idempotent=False)
    decision = RetryExecutor.evaluate_retry(
        attempt=1,
        policy=policy,
        error_message="Connection reset",
        is_destructive_operation=True,
    )
    assert decision.should_retry is False
    assert "Destructive operation is not verified idempotent" in decision.reason


def test_retry_executor_allows_transient_error():
    policy = RetryPolicy(max_attempts=3)
    decision = RetryExecutor.evaluate_retry(
        attempt=1,
        policy=policy,
        error_message="Rate limit 429",
        status_code=429,
    )
    assert decision.should_retry is True
    assert decision.delay_seconds > 0


# ===========================================================================
# 3. Circuit Breaker Tests
# ===========================================================================
def test_circuit_breaker_lifecycle():
    breaker = CircuitBreaker("openai_provider", failure_threshold=3, recovery_timeout_seconds=0.2)
    assert breaker.state == "closed"

    # Calls succeed
    breaker.check_call_allowed()
    breaker.record_success()

    # Failures trip to open
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.state == "closed"
    breaker.record_failure()
    assert breaker.state == "open"

    # Call blocked while open
    with pytest.raises(CircuitOpenError):
        breaker.check_call_allowed()

    # Manual reset
    breaker.reset()
    assert breaker.state == "closed"
    breaker.check_call_allowed()


# ===========================================================================
# 4. Bulkhead Concurrency Isolation Tests
# ===========================================================================
@pytest.mark.asyncio
async def test_bulkhead_concurrency_capacity():
    bulkhead = SubsystemBulkhead("test_subsystem", max_concurrent=2)
    assert bulkhead.available_slots == 2

    await bulkhead.acquire(timeout_seconds=0.1)
    assert bulkhead.active_count == 1
    assert bulkhead.available_slots == 1

    await bulkhead.acquire(timeout_seconds=0.1)
    assert bulkhead.active_count == 2
    assert bulkhead.available_slots == 0

    # 3rd acquire exceeds capacity
    with pytest.raises(BulkheadCapacityExceededError):
        await bulkhead.acquire(timeout_seconds=0.01)

    # Release frees slot
    bulkhead.release()
    assert bulkhead.available_slots == 1
    bulkhead.release()
    assert bulkhead.available_slots == 2


# ===========================================================================
# 5. Fallback Resolver Tests
# ===========================================================================
def test_fallback_resolver_alternate_model():
    policy = FallbackPolicy(
        allow_alternate_model=True,
        allowed_model_substitutions=["gpt-4o", "gpt-4o-mini"],
    )
    decision = FallbackResolver.resolve_fallback(
        primary_target="gpt-4o",
        primary_provider="openai",
        failure_reason="Capacity overloaded",
        policy=policy,
    )
    assert decision.fallback_used is True
    assert decision.fallback_target == "openai/gpt-4o-mini"
    assert decision.fallback_tier == "alternate_model"


def test_fallback_resolver_blocked_by_governance():
    policy = FallbackPolicy(governance_allows_fallback=False)
    decision = FallbackResolver.resolve_fallback(
        primary_target="gpt-4o",
        primary_provider="openai",
        failure_reason="Outage",
        policy=policy,
    )
    assert decision.fallback_used is False
    assert decision.fallback_tier == "safe_failure"
    assert "Governance policy explicitly forbids" in decision.reason


# ===========================================================================
# 6. Graceful Degradation Tests
# ===========================================================================
def test_degradation_cache_bypass():
    policy = DegradationPolicy(allow_cache_bypass=True)
    res = DegradationResolver.evaluate_degradation(
        unhealthy_components=["cache"],
        policy=policy,
    )
    assert res.degraded is True
    assert "cache_bypass" in res.mode
    assert res.allowed_by_policy is True


def test_degradation_blocked_when_required():
    policy = DegradationPolicy(allow_retrieval_without_reranker=True)
    res = DegradationResolver.evaluate_degradation(
        unhealthy_components=["reranker"],
        policy=policy,
        task_requires=["reranker"],  # Strict requirement
    )
    assert res.degraded is False
    assert res.mode == "fail_fast"
    assert res.allowed_by_policy is False


# ===========================================================================
# 7. Checkpoint Validation & Resumption Safety Tests
# ===========================================================================
def test_checkpoint_integrity_validation():
    fp = compute_state_fingerprint({"step": 1})
    # Valid
    validate_checkpoint_integrity({"step": 1}, fp, fp)

    # Invalid input hash
    with pytest.raises(CheckpointIntegrityError):
        validate_checkpoint_integrity({"step": 1}, "short_hash", fp)


def test_resume_preconditions_blocked_by_quarantine():
    with pytest.raises(ResumePreconditionFailedError):
        validate_resumption_preconditions(
            target_resource_exists=True,
            is_security_quarantined=True,
        )


def test_resume_preconditions_blocked_by_deleted_data():
    with pytest.raises(ResumePreconditionFailedError):
        validate_resumption_preconditions(
            target_resource_exists=True,
            is_data_deleted_or_redacted=True,
        )


# ===========================================================================
# 8. Chaos Engineering Safety & Validation Tests
# ===========================================================================
def test_chaos_action_allowlist():
    validate_chaos_action_allowlist("simulate_timeout")
    validate_chaos_action_allowlist("simulate_provider_unavailable")

    with pytest.raises(InvalidChaosActionError):
        validate_chaos_action_allowlist("arbitrary_bash_command")

    with pytest.raises(InvalidChaosActionError):
        validate_chaos_action_allowlist("rm_rf_database")


def test_chaos_production_execution_blocked():
    with pytest.raises(ProductionChaosBlockedError):
        validate_chaos_experiment_safety(
            environment="production",
            actor_role="admin",
            has_hitl_approval=False,
            governance_approved=False,
        )


def test_chaos_unauthorized_role_blocked():
    with pytest.raises(UnauthorizedChaosExecutionError):
        validate_chaos_experiment_safety(
            environment="test",
            actor_role="guest",
        )


@pytest.mark.asyncio
async def test_chaos_simulation_sandbox_execution():
    res = await ChaosFailureSimulator.simulate_failure(
        failure_type="simulate_provider_unavailable",
        target_type="ai_gateway",
        target_id="openai_provider",
        duration_seconds=1,
    )
    assert res["failure_type"] == "simulate_provider_unavailable"
    assert len(res["logs"]) >= 2
    assert "completed safely without side effects" in res["logs"][-1]
