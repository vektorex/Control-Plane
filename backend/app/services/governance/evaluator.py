"""
PolicyEvaluator: deterministic rule evaluation engine.
Evaluates safe conditions against trusted metadata. No LLM, no arbitrary code execution.
Step 32.
"""
from typing import Any, Dict, List, Optional, Tuple

from backend.app.services.governance.constants import (
    GovernanceDecisionType,
    PolicyAction,
    PolicyVersionStatus,
    RuleConditionOperator,
    SYSTEM_SECURITY_CONSTRAINTS,
)
from backend.app.services.governance.errors import GovernancePolicyMalformedError
from backend.app.services.governance.schemas import (
    GovernanceDecision,
    GovernanceEvaluationRequest,
    PolicyRule,
    RuleCondition,
)


def _evaluate_condition(condition: RuleCondition, context: Dict[str, Any]) -> bool:
    """
    Evaluate a single safe condition against trusted context metadata.
    Returns True if the condition is satisfied.
    """
    field_value = context.get(condition.field)
    op = condition.operator
    cond_value = condition.value

    if op == RuleConditionOperator.EXISTS:
        return field_value is not None and field_value != ""

    if field_value is None:
        return False

    try:
        if op == RuleConditionOperator.EQUALS:
            return str(field_value).lower() == str(cond_value).lower()

        elif op == RuleConditionOperator.NOT_EQUALS:
            return str(field_value).lower() != str(cond_value).lower()

        elif op == RuleConditionOperator.IN:
            if not isinstance(cond_value, list):
                return False
            return str(field_value).lower() in [str(v).lower() for v in cond_value]

        elif op == RuleConditionOperator.NOT_IN:
            if not isinstance(cond_value, list):
                return True
            return str(field_value).lower() not in [str(v).lower() for v in cond_value]

        elif op == RuleConditionOperator.GREATER_THAN:
            return float(field_value) > float(cond_value)

        elif op == RuleConditionOperator.LESS_THAN:
            return float(field_value) < float(cond_value)

        elif op == RuleConditionOperator.GREATER_OR_EQUAL:
            return float(field_value) >= float(cond_value)

        elif op == RuleConditionOperator.LESS_OR_EQUAL:
            return float(field_value) <= float(cond_value)

        elif op == RuleConditionOperator.MATCHES_ENUM:
            if not isinstance(cond_value, list):
                return str(field_value).lower() == str(cond_value).lower()
            return str(field_value).lower() in [str(v).lower() for v in cond_value]

    except (TypeError, ValueError):
        return False

    return False


def _rule_matches(rule: PolicyRule, context: Dict[str, Any]) -> bool:
    """Returns True if all conditions in a rule are satisfied."""
    return all(_evaluate_condition(c, context) for c in rule.conditions)


def _action_to_decision(action: PolicyAction) -> GovernanceDecisionType:
    """Maps a policy action to a governance decision type."""
    mapping = {
        PolicyAction.ALLOW: GovernanceDecisionType.ALLOW,
        PolicyAction.DENY: GovernanceDecisionType.DENY,
        PolicyAction.REQUIRE_APPROVAL: GovernanceDecisionType.REQUIRE_APPROVAL,
        PolicyAction.REQUIRE_VERIFICATION: GovernanceDecisionType.REQUIRE_VERIFICATION,
        PolicyAction.SET_LIMIT: GovernanceDecisionType.ALLOW_WITH_CONSTRAINTS,
        PolicyAction.RESTRICT: GovernanceDecisionType.ALLOW_WITH_CONSTRAINTS,
        PolicyAction.FORCE: GovernanceDecisionType.ALLOW_WITH_CONSTRAINTS,
        PolicyAction.DISABLE: GovernanceDecisionType.DENY,
    }
    return mapping.get(action, GovernanceDecisionType.DENY)


def _merge_decisions(
    current: GovernanceDecisionType,
    incoming: GovernanceDecisionType,
) -> GovernanceDecisionType:
    """
    Merges two decisions using a strict precedence:
    DENY > REQUIRE_APPROVAL > REQUIRE_VERIFICATION > ALLOW_WITH_CONSTRAINTS > ALLOW
    """
    precedence = {
        GovernanceDecisionType.DENY: 0,
        GovernanceDecisionType.REQUIRE_APPROVAL: 1,
        GovernanceDecisionType.REQUIRE_VERIFICATION: 2,
        GovernanceDecisionType.ALLOW_WITH_CONSTRAINTS: 3,
        GovernanceDecisionType.ALLOW: 4,
    }
    if precedence.get(incoming, 4) < precedence.get(current, 4):
        return incoming
    return current


class PolicyEvaluator:
    """
    Evaluates a list of policy rules against trusted execution metadata.
    Returns a normalized GovernanceDecision.
    Evaluation is deterministic; no LLM, no arbitrary code.
    """

    @staticmethod
    def build_context(request: GovernanceEvaluationRequest) -> Dict[str, Any]:
        """
        Converts trusted request fields to a flat evaluation context.
        Only pre-defined trusted metadata fields are included.
        """
        ctx: Dict[str, Any] = {
            "enforcement_point": request.enforcement_point.value if request.enforcement_point else None,
            "user_role": request.user_role,
            "task_type": request.task_type,
            "execution_mode": request.execution_mode,
            "action_category": request.action_category.value if request.action_category else None,
            "model_id": request.model_id,
            "provider": request.provider,
            "tool_id": request.tool_id,
            "connector_id": request.connector_id,
            "workflow_id": request.workflow_id,
            "prompt_id": request.prompt_id,
            "prompt_version_id": request.prompt_version_id,
            "artifact_type": request.artifact_type,
            "data_classification": request.data_classification.value if request.data_classification else None,
            "estimated_cost_usd": request.estimated_cost_usd,
            "cache_mode": request.cache_mode,
            "job_type": request.job_type,
        }
        return ctx

    @staticmethod
    def evaluate(
        rules: List[PolicyRule],
        request: GovernanceEvaluationRequest,
        policy_id: str = "",
        policy_version_number: int = 0,
    ) -> Tuple[GovernanceDecisionType, List[str], Dict[str, Any], List[str], List[str]]:
        """
        Evaluates all rules in priority order.
        Returns: (decision, reasons, constraints, required_approvals, required_verifications)
        """
        context = PolicyEvaluator.build_context(request)

        # Sort rules by ascending priority (lower = evaluated first)
        sorted_rules = sorted(rules, key=lambda r: r.priority)

        current_decision = GovernanceDecisionType.ALLOW
        reasons: List[str] = []
        constraints: Dict[str, Any] = {}
        required_approvals: List[str] = []
        required_verifications: List[str] = []

        for rule in sorted_rules:
            if not _rule_matches(rule, context):
                continue

            rule_decision = _action_to_decision(rule.action)
            current_decision = _merge_decisions(current_decision, rule_decision)

            # Collect reason (factual, non-internal)
            if rule.description:
                reasons.append(rule.description)

            # Collect constraints from SET_LIMIT / RESTRICT / FORCE actions
            if rule.action in (PolicyAction.SET_LIMIT, PolicyAction.RESTRICT, PolicyAction.FORCE):
                constraints.update(rule.action_params)

            # Collect approval/verification requirements
            if rule.action == PolicyAction.REQUIRE_APPROVAL:
                approval_scope = rule.action_params.get("scope", "standard")
                required_approvals.append(approval_scope)

            if rule.action == PolicyAction.REQUIRE_VERIFICATION:
                for req in rule.action_params.get("verifications", []):
                    required_verifications.append(req)

        return current_decision, reasons, constraints, required_approvals, required_verifications

    @staticmethod
    def validate_rules(rules: List[PolicyRule]) -> List[str]:
        """
        Validates a list of policy rules for structural correctness.
        Returns a list of error messages (empty = valid).
        Does NOT execute rules.
        """
        errors = []
        if len(rules) > 50:
            errors.append("Policy cannot have more than 50 rules")

        for i, rule in enumerate(rules):
            if len(rule.conditions) > 20:
                errors.append(f"Rule #{i} has more than 20 conditions")
            # Ensure no arbitrary fields slip through
            for j, cond in enumerate(rule.conditions):
                if not isinstance(cond.field, str) or not cond.field.strip():
                    errors.append(f"Rule #{i} condition #{j}: field must be a non-empty string")

        return errors
