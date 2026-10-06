"""
Policy Simulation Engine for Step 41: AI Agent Simulation.
Evaluates governance impact with temporary simulation-only overrides without modifying production policies.
"""
from typing import Any, Dict, List, Optional
from backend.app.core.logging import logger


class PolicySimulator:
    """
    Evaluates policy decisions under simulated policy overrides.
    Never alters production governance rules.
    """

    @classmethod
    def evaluate_effective_policy(
        cls,
        base_policy: Dict[str, Any],
        overrides: Optional[Dict[str, Any]] = None,
        action: str = "execute",
        resource_type: str = "agent",
    ) -> Dict[str, Any]:
        """
        Calculates the effective governance decision under hypothetical overrides.
        """
        overrides = overrides or {}
        merged_policy = dict(base_policy)
        merged_policy.update(overrides)

        matched_rules = []
        constraints = []
        denied_capabilities = []
        requires_approval = False
        decision = "ALLOW"

        # Check budget override constraint
        if "max_budget_per_run" in overrides:
            constraints.append(f"Simulated budget limit capped at ${overrides['max_budget_per_run']}")
            matched_rules.append("rule_sim_budget_override")

        # Check disabled connectors
        if "disabled_connectors" in overrides:
            disabled = overrides["disabled_connectors"]
            constraints.append(f"Connectors disabled in simulation: {disabled}")
            matched_rules.append("rule_sim_disable_connectors")
            if resource_type == "connector" and action in disabled:
                decision = "DENY"

        # Check required approvals
        if overrides.get("require_approval_all") or overrides.get("require_tool_approval"):
            requires_approval = True
            constraints.append("Mandatory HITL approval required per simulation policy override.")
            matched_rules.append("rule_sim_require_approval")

        # Check denied capabilities
        if "denied_capabilities" in overrides:
            denied_capabilities.extend(overrides["denied_capabilities"])
            constraints.append(f"Capabilities explicitly denied: {denied_capabilities}")
            matched_rules.append("rule_sim_deny_capabilities")

        # Check model restrictions
        if "denied_models" in overrides:
            constraints.append(f"Models prohibited: {overrides['denied_models']}")
            matched_rules.append("rule_sim_deny_models")

        # Check memory restrictions
        if overrides.get("restrict_memory_write"):
            constraints.append("Memory write operations strictly prohibited.")
            matched_rules.append("rule_sim_restrict_memory_write")

        return {
            "effective_decision": decision,
            "matched_rules": matched_rules,
            "constraints": constraints,
            "approval_requirements": {
                "requires_approval": requires_approval,
                "approval_type": "SIMULATED_HITL" if requires_approval else "NONE",
            },
            "denied_capabilities": denied_capabilities,
            "simulation_only": True,
        }


class SimulationPolicyOverride:
    """Represents a discrete hypothetical policy override for testing."""

    def __init__(
        self,
        rule_type: str,
        target: Optional[str] = None,
        value: Optional[Any] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        self.rule_type = rule_type
        self.target = target
        self.value = value
        self.parameters = parameters or {}


class SimulationPolicyEngine:
    """
    Evaluator engine for testing governance policy hypotheses.
    """

    def __init__(self, overrides: Optional[List[SimulationPolicyOverride]] = None):
        self.overrides = overrides or []

    def evaluate_connector_access(self, connector_name: str) -> Dict[str, Any]:
        for o in self.overrides:
            if o.rule_type == "disable_connector" and (o.target == connector_name or o.target == "*"):
                return {
                    "allowed": False,
                    "matched_override": f"disable_connector:{connector_name}",
                    "reason": f"Connector '{connector_name}' disabled by simulation policy override.",
                }
        return {"allowed": True, "matched_override": None}

    def evaluate_tool_execution(self, tool_name: str) -> Dict[str, Any]:
        for o in self.overrides:
            if o.rule_type == "require_approval":
                if o.target in [tool_name, f"tool:{tool_name}", "*"]:
                    return {
                        "allowed": True,
                        "requires_approval": True,
                        "matched_override": f"require_approval:{tool_name}",
                    }
        return {"allowed": True, "requires_approval": False, "matched_override": None}

    def evaluate_budget_limit(self, current_cost: float) -> Dict[str, Any]:
        for o in self.overrides:
            if o.rule_type == "reduce_cost_limit":
                limit = float(o.value if o.value is not None else 1.0)
                return {
                    "limit": limit,
                    "current_cost": current_cost,
                    "exceeded": current_cost > limit,
                    "matched_override": "reduce_cost_limit",
                }
        return {"limit": 100.0, "current_cost": current_cost, "exceeded": False, "matched_override": None}

    def simulate_hitl_approval(
        self,
        action: str,
        target: str,
        actor: str,
        decision: str = "approve",
        reviewer: str = "simulated_human@sandbox.local",
    ) -> Dict[str, Any]:
        """
        Simulates human-in-the-loop approval decision.
        Strict Guarantee: NEVER authorizes real production operations!
        """
        return {
            "is_simulated": True,
            "authorizes_production": False,
            "action": action,
            "target": target,
            "actor": actor,
            "decision": decision,
            "reviewer": reviewer,
            "classification": "SIMULATED APPROVAL",
            "warning": "SIMULATED APPROVAL: This approval is for dry-run simulation testing only and does NOT authorize any production action.",
        }

