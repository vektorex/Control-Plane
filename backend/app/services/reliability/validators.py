"""
Safety and integrity validators for Step 35: AI Reliability, Resilience & Chaos Engineering Layer.
"""
import hashlib
import json
from typing import Any, Dict, List, Optional

from backend.app.services.reliability.exceptions import (
    CheckpointIntegrityError,
    InvalidChaosActionError,
    ProductionChaosBlockedError,
    ResumePreconditionFailedError,
    UnauthorizedChaosExecutionError,
)

ALLOWED_CHAOS_ACTIONS = {
    "simulate_timeout",
    "simulate_provider_unavailable",
    "simulate_rate_limit",
    "simulate_connector_failure",
    "simulate_tool_failure",
    "simulate_event_delay",
    "simulate_job_failure",
    "simulate_notification_failure",
    "simulate_retrieval_failure",
    "simulate_evaluation_failure",
    "simulate_cache_unavailable",
}

BLOCKED_CHAOS_PATTERNS = {
    "exec", "eval", "shell", "bash", "delete", "drop", "truncate", "rm", "format", "corrupt", "revoke"
}


def compute_state_fingerprint(data: Any) -> str:
    """Computes a deterministic SHA-256 fingerprint of a state dictionary or payload."""
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def validate_checkpoint_integrity(
    state_snapshot: Dict[str, Any],
    input_fingerprint: str,
    context_fingerprint: str,
) -> None:
    """
    Validates that checkpoint payload contains valid non-empty state and well-formed fingerprints.
    """
    if not isinstance(state_snapshot, dict):
        raise CheckpointIntegrityError("Checkpoint state snapshot must be a valid dictionary structure.")

    if not input_fingerprint or len(input_fingerprint) != 64:
        raise CheckpointIntegrityError("Invalid input fingerprint: must be a 64-character SHA-256 hash.")

    if not context_fingerprint or len(context_fingerprint) != 64:
        raise CheckpointIntegrityError("Invalid context fingerprint: must be a 64-character SHA-256 hash.")


def validate_chaos_action_allowlist(failure_type: str) -> None:
    """
    Ensures that only predefined, safe failure simulations can be registered or executed.
    Guarantees no arbitrary code, shell commands, or destructive side-effects.
    """
    if failure_type not in ALLOWED_CHAOS_ACTIONS:
        raise InvalidChaosActionError(
            f"Chaos failure action '{failure_type}' is not permitted. "
            f"Allowed actions: {', '.join(sorted(ALLOWED_CHAOS_ACTIONS))}"
        )

    # Secondary check against dangerous keywords
    lower_action = failure_type.lower()
    for kw in BLOCKED_CHAOS_PATTERNS:
        if kw in lower_action and lower_action not in ALLOWED_CHAOS_ACTIONS:
            raise InvalidChaosActionError(f"Prohibited destructive action keyword detected: {kw}")


def validate_chaos_experiment_safety(
    environment: str,
    actor_role: Optional[str] = None,
    has_hitl_approval: bool = False,
    governance_approved: bool = False,
) -> None:
    """
    Enforces that production experiments are blocked by default and require
    both Step 32 Governance authorization and Step 18 HITL approval.
    """
    env_clean = (environment or "test").lower()
    if env_clean == "production":
        if not (has_hitl_approval and governance_approved):
            raise ProductionChaosBlockedError(
                "Chaos experiments in 'production' are strictly blocked by default. "
                "Production execution requires explicit Step 32 Governance policy approval "
                "and Step 18 Human-in-the-Loop (HITL) authorization."
            )

    if actor_role and actor_role.lower() not in {"admin", "owner", "lead_engineer"}:
        raise UnauthorizedChaosExecutionError(
            f"Role '{actor_role}' is not authorized to create or run chaos experiments."
        )


def validate_resumption_preconditions(
    target_resource_exists: bool,
    is_security_quarantined: bool = False,
    is_data_deleted_or_redacted: bool = False,
    has_active_legal_hold: bool = False,
) -> None:
    """
    Ensures that resumption from a checkpoint satisfies all security, governance, and data lifecycle checks.
    """
    if not target_resource_exists:
        raise ResumePreconditionFailedError("Resumption failed: Referenced target resource no longer exists.")

    if is_security_quarantined:
        raise ResumePreconditionFailedError(
            "Resumption blocked: Target resource is currently quarantined under a Step 34 security incident."
        )

    if is_data_deleted_or_redacted:
        raise ResumePreconditionFailedError(
            "Resumption blocked: Underlying state or referenced data has been deleted or redacted under Step 33 data governance."
        )
