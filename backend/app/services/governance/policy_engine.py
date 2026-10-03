"""
GovernancePolicyEngine: primary evaluation facade.
Applies system rules → org rules → workspace rules → project rules in precedence order.
Returns a normalized GovernanceDecision with bounded TTL. Step 32.
"""
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.governance.constants import (
    ActionCategory,
    GovernanceDecisionType,
    GOVERNANCE_DECISION_TTL_SECONDS,
    PRIVILEGED_DECISION_TTL_SECONDS,
)
from backend.app.services.governance.errors import GovernanceStateUnknownError
from backend.app.services.governance.evaluator import PolicyEvaluator
from backend.app.services.governance.policy_registry import policy_registry
from backend.app.services.governance.repository import GovernancePolicyRepository
from backend.app.services.governance.resolver import PolicyResolver
from backend.app.services.governance.schemas import (
    GovernanceDecision,
    GovernanceEvaluationRequest,
)


class GovernancePolicyEngine:
    """
    Core policy evaluation engine.
    Combines system rules + database-backed org/workspace/project rules.
    Produces bounded GovernanceDecision with TTL.
    """

    def __init__(self, repo: GovernancePolicyRepository):
        self.repo = repo
        self.resolver = PolicyResolver(repo=repo, registry=policy_registry)

    async def evaluate(
        self, request: GovernanceEvaluationRequest
    ) -> GovernanceDecision:
        """
        Evaluates all applicable policies for the given request context.
        On unexpected failure for privileged operations: returns DENY (fail-closed).
        On unexpected failure for read-only operations: returns ALLOW (fail-open only for reads).
        """
        start_ms = time.monotonic()
        governance_state_available = True

        try:
            all_rules, policy_ids = await self.resolver.resolve_rules(request)
        except Exception as exc:
            logger.error("Governance: failed to resolve rules: %s", exc)
            governance_state_available = False
            all_rules, policy_ids = [], []

        if not governance_state_available:
            # Fail-closed for privileged; fail-open for reads
            is_privileged = request.action_category in (
                ActionCategory.DESTRUCTIVE, ActionCategory.FINANCIAL, ActionCategory.WRITE
            ) or request.enforcement_point.value in (
                "connector_execution", "external_action", "prompt_release", "job_execution"
            )
            decision_type = (
                GovernanceDecisionType.DENY if is_privileged else GovernanceDecisionType.ALLOW
            )
            return GovernanceDecision(
                decision=decision_type,
                reasons=["Governance state is temporarily unavailable"] if is_privileged else [],
                matched_policies=[],
            )

        # Evaluate all rules
        try:
            decision_type, reasons, constraints, approvals, verifications = PolicyEvaluator.evaluate(
                rules=all_rules,
                request=request,
            )
        except Exception as exc:
            logger.error("Governance: evaluation error: %s", exc)
            return GovernanceDecision(
                decision=GovernanceDecisionType.DENY,
                reasons=["Governance evaluation error"],
                matched_policies=policy_ids,
            )

        # Compute TTL based on decision type and operation risk
        is_privileged = request.action_category in (
            ActionCategory.DESTRUCTIVE, ActionCategory.FINANCIAL
        )
        ttl = PRIVILEGED_DECISION_TTL_SECONDS if is_privileged else GOVERNANCE_DECISION_TTL_SECONDS
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)

        latency_ms = int((time.monotonic() - start_ms) * 1000)

        # Build active policy version string
        policy_version = f"{len(policy_ids)}_policies_v{len(all_rules)}_rules"

        return GovernanceDecision(
            decision=decision_type,
            reasons=reasons,
            constraints=constraints,
            required_approvals=approvals,
            required_verifications=verifications,
            matched_policies=policy_ids,
            policy_version=policy_version,
            expires_at=expires_at,
            evaluation_latency_ms=latency_ms,
        )

    async def evaluate_and_log(
        self,
        request: GovernanceEvaluationRequest,
        user_id: Optional[uuid.UUID] = None,
    ) -> GovernanceDecision:
        """Evaluate and persist decision to audit log."""
        decision = await self.evaluate(request)
        try:
            await self.repo.log_decision(
                decision=decision,
                organization_id=request.organization_id,
                workspace_id=request.workspace_id,
                project_id=request.project_id,
                user_id=user_id or request.user_id,
                enforcement_point=request.enforcement_point.value,
                latency_ms=decision.evaluation_latency_ms,
            )
        except Exception as exc:
            logger.warning("Governance: failed to log decision: %s", exc)
        return decision
