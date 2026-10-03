"""
Deterministic Fallback Engine for Step 35: AI Reliability, Resilience & Chaos Engineering Layer.
Coordinates fallback hierarchies across models, providers, and deterministic handlers.
Integrates with Step 12 ModelRouter, Step 19 AI Gateway, and Step 32 Governance.
Never silently switches providers if governance forbids model substitutions.
"""
from typing import Any, Dict, List, Optional
from backend.app.services.reliability.schemas import FallbackDecisionResult


class FallbackPolicy:
    """Configures fallback options for a task or execution step."""
    def __init__(
        self,
        allow_alternate_model: bool = True,
        allow_alternate_provider: bool = True,
        allow_deterministic_fallback: bool = True,
        allowed_model_substitutions: Optional[List[str]] = None,
        governance_allows_fallback: bool = True,
    ):
        self.allow_alternate_model = allow_alternate_model
        self.allow_alternate_provider = allow_alternate_provider
        self.allow_deterministic_fallback = allow_deterministic_fallback
        self.allowed_model_substitutions = allowed_model_substitutions or [
            "gpt-4o-mini",
            "claude-3-5-sonnet",
            "gemini-1.5-flash",
        ]
        self.governance_allows_fallback = governance_allows_fallback


class FallbackResolver:
    """Resolves next viable target according to deterministic fallback hierarchy."""

    @classmethod
    def resolve_fallback(
        cls,
        primary_target: str,
        primary_provider: str,
        failure_reason: str,
        policy: FallbackPolicy,
        governance_override: bool = False,
    ) -> FallbackDecisionResult:
        """
        Calculates fallback target respecting governance constraints.
        Hierarchy:
          1. alternate compatible model on same provider
          2. alternate provider
          3. deterministic fallback
          4. safe failure
        """
        # Rule 1: Step 32 Governance veto
        if not policy.governance_allows_fallback and not governance_override:
            return FallbackDecisionResult(
                fallback_used=False,
                original_target=primary_target,
                fallback_target=None,
                fallback_tier="safe_failure",
                reason=f"Step 32 Governance policy explicitly forbids model/provider fallback: {failure_reason}",
                governance_verified=True,
            )

        # Tier 1: Alternate compatible model
        if policy.allow_alternate_model:
            candidates = [m for m in policy.allowed_model_substitutions if m != primary_target]
            if candidates:
                fallback_model = candidates[0]
                return FallbackDecisionResult(
                    fallback_used=True,
                    original_target=f"{primary_provider}/{primary_target}",
                    fallback_target=f"{primary_provider}/{fallback_model}",
                    fallback_tier="alternate_model",
                    reason=f"Primary model {primary_target} failed ({failure_reason}); routed to compatible model {fallback_model}",
                    governance_verified=True,
                )

        # Tier 2: Alternate provider
        if policy.allow_alternate_provider:
            alt_provider = "anthropic" if primary_provider == "openai" else "openai"
            alt_model = "claude-3-5-sonnet" if alt_provider == "anthropic" else "gpt-4o-mini"
            return FallbackDecisionResult(
                fallback_used=True,
                original_target=f"{primary_provider}/{primary_target}",
                fallback_target=f"{alt_provider}/{alt_model}",
                fallback_tier="alternate_provider",
                reason=f"Provider {primary_provider} unavailable ({failure_reason}); cross-provider fallback activated",
                governance_verified=True,
            )

        # Tier 3: Deterministic fallback
        if policy.allow_deterministic_fallback:
            return FallbackDecisionResult(
                fallback_used=True,
                original_target=primary_target,
                fallback_target="deterministic_handler",
                fallback_tier="deterministic",
                reason=f"AI generation unavailable; falling back to deterministic template/rules",
                governance_verified=True,
            )

        # Tier 4: Safe failure
        return FallbackDecisionResult(
            fallback_used=False,
            original_target=primary_target,
            fallback_target=None,
            fallback_tier="safe_failure",
            reason=f"No viable fallback options permitted by policy. Failing safely: {failure_reason}",
            governance_verified=True,
        )
