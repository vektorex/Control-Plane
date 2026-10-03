"""
PolicyEnforcer: runtime governance enforcement at execution boundaries.
Plugged into: task execution, model execution, tool execution, connector execution,
workflow step execution, external action, prompt release, cache reuse, artifact access,
and job execution. Step 32.
"""
import uuid
from typing import Any, Dict, List, Optional

from backend.app.core.logging import logger
from backend.app.services.governance.constants import (
    ActionCategory,
    GovernanceDecisionType,
    PRIVILEGED_DECISION_TTL_SECONDS,
)
from backend.app.services.governance.errors import (
    GovernanceDeniedError,
    GovernanceStateUnknownError,
)
from backend.app.services.governance.schemas import GovernanceDecision


class PolicyEnforcer:
    """
    Enforces a governance decision at a specific execution boundary.
    Raises GovernanceDeniedError for DENY decisions on privileged operations.
    Raises GovernanceStateUnknownError when governance state is unavailable for
    privileged operations.
    """

    # Operations that are privileged and must fail-closed on unknown governance state
    PRIVILEGED_ENFORCEMENT_POINTS = {
        "connector_execution",
        "external_action",
        "prompt_release",
        "job_execution",
    }

    ALWAYS_SAFE_ENFORCEMENT_POINTS = {
        "request_start",
        "cache_reuse",
        "artifact_access",
    }

    @staticmethod
    def enforce(
        decision: GovernanceDecision,
        enforcement_point: str,
        action_category: Optional[ActionCategory] = None,
    ) -> None:
        """
        Enforces the governance decision at the given enforcement point.
        DENY → raises GovernanceDeniedError.
        ALLOW / ALLOW_WITH_CONSTRAINTS → no exception.
        REQUIRE_APPROVAL / REQUIRE_VERIFICATION → caller is responsible for routing to HITL.
        """
        if decision.decision == GovernanceDecisionType.DENY:
            reason_str = "; ".join(decision.reasons[:3]) if decision.reasons else "operation denied by governance policy"
            raise GovernanceDeniedError(reason_str)

    @staticmethod
    def enforce_fail_safe(
        enforcement_point: str,
        governance_state_available: bool,
        action_category: Optional[ActionCategory] = None,
    ) -> None:
        """
        Called when governance evaluation encountered an error.
        For privileged/destructive operations: fail-closed (block).
        For safe read-only operations: follow configured system fallback.
        """
        if not governance_state_available:
            is_privileged = (
                enforcement_point in PolicyEnforcer.PRIVILEGED_ENFORCEMENT_POINTS
                or action_category in (ActionCategory.DESTRUCTIVE, ActionCategory.FINANCIAL, ActionCategory.WRITE)
            )
            if is_privileged:
                raise GovernanceStateUnknownError(
                    f"Governance state is unavailable; privileged operation at '{enforcement_point}' is blocked"
                )
            # For truly read-only safe operations, log and allow
            logger.warning(
                "Governance: state unavailable for read-only '%s'; allowing with warning",
                enforcement_point,
            )

    @staticmethod
    def extract_cache_constraints(decision: GovernanceDecision) -> Dict[str, Any]:
        """
        Extracts cache-related constraints from a governance decision.
        Returns dict with keys: cache_mode, semantic_cache_enabled, stale_while_revalidate, max_cache_ttl_seconds.
        """
        constraints = decision.constraints
        return {
            "cache_mode": constraints.get("cache_mode"),
            "semantic_cache_enabled": constraints.get("semantic_cache_enabled", True),
            "stale_while_revalidate": constraints.get("stale_while_revalidate", True),
            "max_cache_ttl_seconds": constraints.get("max_cache_ttl_seconds"),
        }

    @staticmethod
    def extract_model_constraints(decision: GovernanceDecision) -> Dict[str, Any]:
        """Extract model/provider constraints from a governance decision."""
        c = decision.constraints
        return {
            "allowed_models": c.get("allowed_models"),
            "blocked_models": c.get("blocked_models", []),
            "allowed_providers": c.get("allowed_providers"),
            "blocked_providers": c.get("blocked_providers", []),
            "max_output_tokens": c.get("max_output_tokens"),
        }
