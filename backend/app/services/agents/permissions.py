"""
Governed Agent Permission Evaluation Chain for Step 40.
Combines RBAC, Tenant/Resource Scoping, Agent Capability Policy, Governance, and HITL Policy.
Strictly enforces that the most restrictive outcome wins.
Guarantees agents cannot modify their own permissions or approve their own actions.
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from backend.app.services.agents.errors import (
    AgentSelfApprovalBlockedError,
    CapabilityNotGrantedError,
)
from backend.app.services.agents.identity import AgentIdentity


class PermissionDecision(str, Enum):
    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"
    DENY = "deny"


class AgentPermissionEvaluator:
    """Evaluates whether an action requested by or on behalf of an agent is permitted."""

    @classmethod
    def evaluate_action(
        cls,
        identity: AgentIdentity,
        action: str,
        required_capability: Optional[str],
        granted_capabilities: List[str],
        resource_workspace_id: str,
        resource_project_id: Optional[str] = None,
        approval_policy: Optional[Dict[str, Any]] = None,
        governance_verdict: Optional[str] = None,  # "ALLOW", "DENY", "REQUIRE_APPROVAL"
    ) -> PermissionDecision:
        """
        Evaluates the full permission chain:
        1. Tenant isolation (workspace boundary): if mismatched => DENY
        2. Project boundary: if agent has specific project and target does not match => DENY
        3. Self-modification / Self-approval prevention: if agent attempts to edit agent/version/permissions => DENY
        4. Capability check: if required_capability not in granted_capabilities => DENY
        5. Governance check: if governance is DENY => DENY; if governance is REQUIRE_APPROVAL => REQUIRE_APPROVAL
        6. HITL check: if approval policy requires human sign-off => REQUIRE_APPROVAL
        7. Otherwise ALLOW
        """
        # 1. Tenant boundary check
        if identity.workspace_id != resource_workspace_id:
            return PermissionDecision.DENY

        # 2. Project boundary check
        if identity.project_id and resource_project_id and identity.project_id != resource_project_id:
            return PermissionDecision.DENY

        # 3. Prevent agent self-approval or self-permission modification
        forbidden_self_actions = {
            "agent_permission_modify",
            "agent_policy_modify",
            "agent_budget_modify",
            "agent_self_approve",
            "approve_hitl",
        }
        if action in forbidden_self_actions:
            raise AgentSelfApprovalBlockedError(identity.agent_id, action)

        # 4. Agent declarative capability check
        if required_capability:
            if required_capability not in granted_capabilities:
                return PermissionDecision.DENY

        # 5. Governance check (from Step 32 Governance Engine)
        if governance_verdict == "DENY":
            return PermissionDecision.DENY
        if governance_verdict == "REQUIRE_APPROVAL":
            return PermissionDecision.REQUIRE_APPROVAL

        # 6. HITL approval policy check
        if approval_policy:
            # Check external actions
            if action.startswith("external_") and approval_policy.get("requires_approval_for_external_actions", True):
                return PermissionDecision.REQUIRE_APPROVAL

            # Check delegation approval
            if action == "delegate" and approval_policy.get("requires_approval_for_delegation", False):
                return PermissionDecision.REQUIRE_APPROVAL

            # Check memory write approval
            if action == "memory_write" and approval_policy.get("requires_approval_for_memory_write", False):
                return PermissionDecision.REQUIRE_APPROVAL

            # Check specific tool approvals
            req_tools = approval_policy.get("requires_approval_for_tools", [])
            if action.startswith("tool:") and action.split(":", 1)[1] in req_tools:
                return PermissionDecision.REQUIRE_APPROVAL

            # Check specific connector approvals
            req_connectors = approval_policy.get("requires_approval_for_connectors", [])
            if action.startswith("connector:") and action.split(":", 1)[1] in req_connectors:
                return PermissionDecision.REQUIRE_APPROVAL

        return PermissionDecision.ALLOW

    @classmethod
    def assert_capability(cls, identity: AgentIdentity, required_capability: str, granted_capabilities: List[str]) -> None:
        """Helper to assert that a capability is present; raises CapabilityNotGrantedError otherwise."""
        if required_capability not in granted_capabilities:
            raise CapabilityNotGrantedError(required_capability, identity.agent_id)
