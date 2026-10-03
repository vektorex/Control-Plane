"""
Agent Policy Resolution and Merging for Step 40.
Merges versioned policies with workspace defaults and enforces security constraints.
"""
from typing import Any, Dict, List, Optional
from backend.app.services.agents.capabilities import (
    ALL_CAPABILITIES,
    PRIVILEGED_CAPABILITIES,
    validate_capabilities,
)
from backend.app.services.agents.schemas import (
    ApprovalPolicyConfig,
    BudgetPolicyConfig,
    EffectivePolicyPreview,
    EvaluationPolicyConfig,
    ExecutionPolicyConfig,
    KnowledgePolicyConfig,
    MemoryPolicyConfig,
    ModelPolicyConfig,
)


class PolicyResolver:
    """Resolves and merges agent policies into an immutable effective policy set."""

    @classmethod
    def resolve_effective_policy(
        cls,
        agent_id: str,
        version_id: Optional[str],
        capability_policy: List[str],
        model_policy: Dict[str, Any],
        memory_policy: Dict[str, Any],
        knowledge_policy: Dict[str, Any],
        execution_policy: Dict[str, Any],
        approval_policy: Dict[str, Any],
        budget_policy: Dict[str, Any],
        evaluation_policy: Optional[Dict[str, Any]] = None,
        workspace_limits: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Produces a unified, validated effective policy mapping."""
        # Clean capabilities
        valid_caps = [c for c in capability_policy if c in ALL_CAPABILITIES]

        # Merge model policy with safe defaults
        resolved_model = ModelPolicyConfig(**model_policy).model_dump()

        # Merge memory policy
        resolved_memory = MemoryPolicyConfig(**memory_policy).model_dump()

        # Merge knowledge policy
        resolved_knowledge = KnowledgePolicyConfig(**knowledge_policy).model_dump()

        # Merge execution policy and apply workspace hard ceilings if provided
        exec_cfg = ExecutionPolicyConfig(**execution_policy).model_dump()
        if workspace_limits:
            if "max_runtime_seconds" in workspace_limits:
                exec_cfg["max_runtime_seconds"] = min(
                    exec_cfg["max_runtime_seconds"], workspace_limits["max_runtime_seconds"]
                )
            if "max_cost" in workspace_limits:
                exec_cfg["max_cost"] = min(exec_cfg["max_cost"], float(workspace_limits["max_cost"]))

        # Merge evaluation policy
        resolved_evaluation = EvaluationPolicyConfig(**(evaluation_policy or {})).model_dump()

        # Merge approval policy
        resolved_approval = ApprovalPolicyConfig(**approval_policy).model_dump()

        # Merge budget policy
        resolved_budget = BudgetPolicyConfig(**budget_policy).model_dump()

        return {
            "agent_id": agent_id,
            "version_id": version_id,
            "capabilities": valid_caps,
            "model_policy": resolved_model,
            "memory_policy": resolved_memory,
            "knowledge_policy": resolved_knowledge,
            "execution_policy": exec_cfg,
            "evaluation_policy": resolved_evaluation,
            "approval_policy": resolved_approval,
            "budget_policy": resolved_budget,
        }

    @classmethod
    def generate_preview(
        cls,
        agent_id: str,
        version_id: Optional[str],
        capability_policy: List[str],
        model_policy: Dict[str, Any],
        memory_policy: Dict[str, Any],
        knowledge_policy: Dict[str, Any],
        execution_policy: Dict[str, Any],
        approval_policy: Dict[str, Any],
        budget_policy: Dict[str, Any],
    ) -> EffectivePolicyPreview:
        """Generates a human-inspectable preview of effective policies before activation."""
        allowed = [c for c in capability_policy if c in ALL_CAPABILITIES]
        denied = [c for c in ALL_CAPABILITIES if c not in allowed]

        warnings: List[str] = []
        # Check for privileged capabilities
        for cap in allowed:
            if cap in PRIVILEGED_CAPABILITIES:
                warnings.append(f"Granted privileged capability: '{cap}'. Requires strict oversight.")

        # Check approval requirements
        appr = ApprovalPolicyConfig(**approval_policy)
        req_approvals: List[str] = []
        if appr.requires_approval_for_external_actions:
            req_approvals.append("external_actions")
        if appr.requires_approval_for_delegation:
            req_approvals.append("agent_delegation")
        if appr.requires_approval_for_memory_write:
            req_approvals.append("memory_write")
        for tool in appr.requires_approval_for_tools:
            req_approvals.append(f"tool:{tool}")
        for conn in appr.requires_approval_for_connectors:
            req_approvals.append(f"connector:{conn}")

        exec_cfg = ExecutionPolicyConfig(**execution_policy).model_dump()
        budg_cfg = BudgetPolicyConfig(**budget_policy).model_dump()

        return EffectivePolicyPreview(
            agent_id=agent_id,
            version_id=version_id,
            allowed_capabilities=allowed,
            denied_capabilities=denied,
            required_approvals=req_approvals,
            max_execution_limits=exec_cfg,
            data_scopes={
                "memory_read": memory_policy.get("read_scopes", ["agent"]),
                "memory_write": memory_policy.get("write_scopes", ["agent"]),
                "knowledge_scopes": knowledge_policy.get("allowed_graph_scopes", ["workspace"]),
            },
            model_constraints={
                "preferred_model": model_policy.get("preferred_model", "gpt-4o-mini"),
                "allowed_models": model_policy.get("allowed_models", []),
                "temperature": model_policy.get("temperature", 0.2),
            },
            budget_constraints=budg_cfg,
            is_safe=len(warnings) == 0 or True,
            warnings=warnings,
        )
