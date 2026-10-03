"""
PolicyRegistry: built-in system policies that are always active and cannot be overridden
by organization/workspace/user configurations. Step 32.
"""
from typing import List

from backend.app.services.governance.constants import (
    ActionCategory,
    DataClassification,
    GovernanceDecisionType,
    PolicyAction,
    PolicyRuleType,
)
from backend.app.services.governance.schemas import PolicyRule, RuleCondition
from backend.app.services.governance.constants import RuleConditionOperator


def _build_system_rules() -> List[PolicyRule]:
    """
    Returns the immutable built-in system security policy rules.
    These cannot be overridden by any organization/workspace policy.
    """
    return [
        # Destructive actions always require approval
        PolicyRule(
            id="sys-destructive-approval",
            rule_type=PolicyRuleType.ACTION,
            description="Destructive operations require human approval",
            conditions=[
                RuleCondition(
                    field="action_category",
                    operator=RuleConditionOperator.EQUALS,
                    value=ActionCategory.DESTRUCTIVE.value,
                )
            ],
            action=PolicyAction.REQUIRE_APPROVAL,
            action_params={"scope": "destructive_action"},
            priority=1,
        ),
        # Financial actions require approval
        PolicyRule(
            id="sys-financial-approval",
            rule_type=PolicyRuleType.ACTION,
            description="Financial operations require human approval",
            conditions=[
                RuleCondition(
                    field="action_category",
                    operator=RuleConditionOperator.EQUALS,
                    value=ActionCategory.FINANCIAL.value,
                )
            ],
            action=PolicyAction.REQUIRE_APPROVAL,
            action_params={"scope": "financial_action"},
            priority=1,
        ),
        # Restricted data cannot reach unauthorized providers
        PolicyRule(
            id="sys-restricted-data-require-verification",
            rule_type=PolicyRuleType.DATA,
            description="Restricted data requires verification before model transmission",
            conditions=[
                RuleCondition(
                    field="data_classification",
                    operator=RuleConditionOperator.EQUALS,
                    value=DataClassification.RESTRICTED.value,
                )
            ],
            action=PolicyAction.REQUIRE_VERIFICATION,
            action_params={"verifications": ["grounding_required", "human_review_required"]},
            priority=2,
        ),
        # Authentication operations require verification
        PolicyRule(
            id="sys-auth-verification",
            rule_type=PolicyRuleType.ACTION,
            description="Authentication operations require verification",
            conditions=[
                RuleCondition(
                    field="action_category",
                    operator=RuleConditionOperator.EQUALS,
                    value=ActionCategory.AUTHENTICATION.value,
                )
            ],
            action=PolicyAction.REQUIRE_VERIFICATION,
            action_params={"verifications": ["human_review_required"]},
            priority=2,
        ),
    ]


SYSTEM_POLICY_RULES = _build_system_rules()


class PolicyRegistry:
    """
    Registry of built-in system policies. Always evaluated first, before workspace/org policies.
    Prevents any workspace/org policy from overriding system-level security constraints.
    """

    def __init__(self):
        self._system_rules = SYSTEM_POLICY_RULES

    def get_system_rules(self) -> List[PolicyRule]:
        return list(self._system_rules)

    def is_system_rule(self, rule_id: str) -> bool:
        return any(r.id == rule_id for r in self._system_rules)


# Singleton
policy_registry = PolicyRegistry()
