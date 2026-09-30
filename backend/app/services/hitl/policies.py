"""
Deterministic Approval Policy Engine and Risk Classification for HITL (Step 18).
"""
import re
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from backend.app.db.models.hitl import WorkspaceApprovalPolicy
from backend.app.services.hitl.schemas import RiskAssessment, RiskLevel, StepApprovalConfig


class ApprovalPolicyEngine:
    """
    Evaluates whether an action, step, tool execution, or connector operation
    requires human authorization according to deterministic policies and risk tiers.
    """

    DESTRUCTIVE_KEYWORDS = {
        "delete",
        "drop",
        "destroy",
        "purge",
        "remove",
        "terminate",
        "revoke",
        "truncate",
        "wipe",
        "uninstall",
    }

    WRITE_KEYWORDS = {
        "create",
        "insert",
        "update",
        "modify",
        "edit",
        "patch",
        "post",
        "write",
        "push",
        "publish",
        "commit",
        "assign",
    }

    @classmethod
    def classify_risk(
        cls,
        target_type: str,
        operation: str,
        capability: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> RiskAssessment:
        """
        Deterministically classifies the risk level of an operation without LLM speculation.
        """
        op_lower = (operation or "").lower().strip()
        reasons = []

        # 1. Check for destructive signals
        is_destructive = (
            capability == "destructive"
            or any(k in op_lower for k in cls.DESTRUCTIVE_KEYWORDS)
        )
        if is_destructive:
            reasons.append(f"Operation '{operation}' is classified as DESTRUCTIVE.")
            return RiskAssessment(
                level=RiskLevel.CRITICAL,
                reasons=reasons,
                requires_approval=True,
                is_destructive=True,
            )

        # 2. Check for high-impact write signals
        is_write = (
            capability == "write"
            or any(k in op_lower for k in cls.WRITE_KEYWORDS)
        )
        if is_write:
            # Check if affecting repository, security, or permissions
            if any(term in op_lower for term in ["repo", "branch", "access", "member", "collaborator", "permission"]):
                reasons.append(f"Operation '{operation}' modifies high-impact resources or security settings.")
                return RiskAssessment(
                    level=RiskLevel.HIGH,
                    reasons=reasons,
                    requires_approval=True,
                    is_destructive=False,
                )
            reasons.append(f"Operation '{operation}' performs external state modification (write).")
            return RiskAssessment(
                level=RiskLevel.MEDIUM,
                reasons=reasons,
                requires_approval=True,
                is_destructive=False,
            )

        # 3. Read-only operation
        reasons.append(f"Operation '{operation}' is read-only inspection.")
        return RiskAssessment(
            level=RiskLevel.LOW,
            reasons=reasons,
            requires_approval=False,
            is_destructive=False,
        )

    @classmethod
    def evaluate_requirement(
        cls,
        workspace_policy: Optional[WorkspaceApprovalPolicy],
        step_approval_config: Optional[StepApprovalConfig] = None,
        target_type: str = "workflow_step",
        operation: str = "execute",
        capability: Optional[str] = None,
        cost_estimate: Optional[float] = None,
        evaluation_status: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str, RiskAssessment]:
        """
        Evaluates whether an action requires human intervention.
        Returns: (requires_approval, reason, risk_assessment)
        """
        risk = cls.classify_risk(
            target_type=target_type,
            operation=operation,
            capability=capability,
            arguments=arguments,
        )

        # Mandatory Rule: Destructive operations must ALWAYS require explicit human authorization
        if risk.is_destructive:
            return True, "Destructive operations strictly require mandatory human authorization.", risk

        # Explicit step-level requirement
        if step_approval_config and step_approval_config.required:
            return True, f"Workflow step policy '{step_approval_config.policy or 'required'}' mandates human approval.", risk

        # Workspace policy evaluations
        if workspace_policy:
            # Connector writes
            if target_type == "connector" and risk.level in [RiskLevel.MEDIUM, RiskLevel.HIGH]:
                if workspace_policy.require_connector_write_approval:
                    return True, "Workspace policy requires approval for all connector write actions.", risk

            # Tools
            if target_type == "tool" and workspace_policy.require_tool_approval:
                return True, "Workspace policy requires approval for tool executions.", risk

            # External actions
            if target_type in ["connector", "external_api"] and workspace_policy.require_external_action_approval:
                if risk.level != RiskLevel.LOW:
                    return True, "Workspace policy requires approval before invoking external services.", risk

            # Evaluation review
            if evaluation_status in ["failed", "warning"] and workspace_policy.require_evaluation_failure_review:
                return True, f"Evaluation resulted in '{evaluation_status}'; human review is required before proceeding.", risk

            # Cost threshold
            if workspace_policy.max_auto_cost is not None and cost_estimate is not None:
                if cost_estimate > workspace_policy.max_auto_cost:
                    return (
                        True,
                        f"Estimated action cost (${cost_estimate:.4f}) exceeds workspace auto-approval limit (${workspace_policy.max_auto_cost:.4f}).",
                        risk,
                    )

        # By default, low risk read operations do not require approval
        if risk.level == RiskLevel.LOW:
            return False, "Read-only operation with low risk does not require approval.", risk

        return False, "No approval policy triggered.", risk
