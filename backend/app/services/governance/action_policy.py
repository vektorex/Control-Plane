"""
Action policy classifier: categorizes external operations and determines default policy.
Step 32.
"""
from backend.app.services.governance.constants import ActionCategory, GovernanceDecisionType


# Default decisions per action category before workspace policy overlay
_CATEGORY_DEFAULTS: dict[ActionCategory, GovernanceDecisionType] = {
    ActionCategory.READ: GovernanceDecisionType.ALLOW,
    ActionCategory.WRITE: GovernanceDecisionType.REQUIRE_APPROVAL,
    ActionCategory.DESTRUCTIVE: GovernanceDecisionType.REQUIRE_APPROVAL,
    ActionCategory.FINANCIAL: GovernanceDecisionType.REQUIRE_APPROVAL,
    ActionCategory.COMMUNICATION: GovernanceDecisionType.REQUIRE_APPROVAL,
    ActionCategory.AUTHENTICATION: GovernanceDecisionType.REQUIRE_VERIFICATION,
    ActionCategory.CONFIGURATION: GovernanceDecisionType.REQUIRE_APPROVAL,
}


class ActionPolicyClassifier:
    """
    Classifies external operations and returns a default decision.
    These defaults can be overridden by workspace/organization policies,
    but destructive operations require approval and cannot be silently allowed by
    user preferences.
    """

    @staticmethod
    def default_decision(category: ActionCategory) -> GovernanceDecisionType:
        return _CATEGORY_DEFAULTS.get(category, GovernanceDecisionType.REQUIRE_APPROVAL)

    @staticmethod
    def is_destructive(category: ActionCategory) -> bool:
        return category == ActionCategory.DESTRUCTIVE

    @staticmethod
    def is_always_approval_protected(category: ActionCategory) -> bool:
        """Categories that can never be silently allowed by user preferences."""
        return category in (
            ActionCategory.DESTRUCTIVE,
            ActionCategory.FINANCIAL,
            ActionCategory.AUTHENTICATION,
        )

    @staticmethod
    def classify_from_tool(tool_id: str) -> ActionCategory:
        """Classify a tool invocation by known tool ID patterns."""
        tool_lower = tool_id.lower()
        if any(x in tool_lower for x in ["delete", "remove", "destroy", "drop", "truncate", "purge"]):
            return ActionCategory.DESTRUCTIVE
        if any(x in tool_lower for x in ["write", "create", "insert", "post", "put", "update", "patch"]):
            return ActionCategory.WRITE
        if any(x in tool_lower for x in ["send", "email", "slack", "notify", "publish", "webhook"]):
            return ActionCategory.COMMUNICATION
        if any(x in tool_lower for x in ["auth", "login", "token", "credential", "api_key"]):
            return ActionCategory.AUTHENTICATION
        if any(x in tool_lower for x in ["pay", "charge", "billing", "invoice", "purchase"]):
            return ActionCategory.FINANCIAL
        if any(x in tool_lower for x in ["config", "setting", "policy", "admin"]):
            return ActionCategory.CONFIGURATION
        return ActionCategory.READ

    @staticmethod
    def classify_from_connector(connector_id: str, operation: str = "read") -> ActionCategory:
        """Classify a connector operation by operation type."""
        op_lower = operation.lower()
        if any(x in op_lower for x in ["delete", "remove", "destroy"]):
            return ActionCategory.DESTRUCTIVE
        if any(x in op_lower for x in ["write", "create", "update", "insert", "post", "put", "patch"]):
            return ActionCategory.WRITE
        return ActionCategory.READ
