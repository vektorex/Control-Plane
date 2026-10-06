"""
Simulation and Scenario Validators for Step 41.
Validates configurations, assertions, fault profiles, and security overrides prior to execution.
"""
from typing import Any, Dict, List, Optional
from backend.app.services.simulation.errors import SimulationValidationError
from backend.app.services.simulation.faults import SUPPORTED_FAULTS


VALID_ASSERTION_TYPES = {
    "must_complete",
    "must_not_complete",
    "output_contains",
    "output_not_contains",
    "required_tool_call",
    "forbidden_tool_call",
    "required_connector_call",
    "forbidden_connector_call",
    "required_approval",
    "forbidden_approval",
    "max_steps",
    "max_iterations",
    "max_cost",
    "max_latency",
    "max_delegations",
    "required_agent",
    "forbidden_agent",
    "required_capability",
    "forbidden_capability",
    "policy_must_allow",
    "policy_must_deny",
    "must_ground_output",
    "must_include_citation",
    "must_not_cross_scope",
    "must_not_modify_external_state",
    # Security assertions
    "no_privilege_escalation",
    "no_cross_tenant_access",
    "no_secret_exposure",
    "no_policy_bypass",
    "no_self_authorization",
    "no_external_side_effect",
    "no_capability_escalation",
    "no_forbidden_connector_access",
    "no_forbidden_memory_access",
    "no_forbidden_knowledge_access",
}


class SimulationValidator:
    """
    Validates simulation settings before launching runs.
    """

    @classmethod
    def validate_simulation_config(
        cls,
        target_type: str,
        target_id: str,
        assertions: Optional[List[Dict[str, Any]]] = None,
        fault_config: Optional[Dict[str, Any]] = None,
        policy_overrides: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not target_id:
            raise SimulationValidationError("Target ID is required.")

        if target_type not in ["agent", "agent_team", "workflow", "task", "replay"]:
            raise SimulationValidationError(f"Invalid target_type '{target_type}'.")

        # Validate assertions
        if assertions:
            for i, a in enumerate(assertions):
                a_type = a.get("type", "").lower()
                if not a_type:
                    raise SimulationValidationError(f"Assertion at index {i} is missing 'type'.")
                if a_type not in VALID_ASSERTION_TYPES:
                    raise SimulationValidationError(f"Unsupported assertion type '{a_type}' at index {i}.")

        # Validate faults
        if fault_config:
            for fault_key in fault_config.keys():
                fault_base = fault_key.split(":")[0]
                if fault_base not in SUPPORTED_FAULTS:
                    raise SimulationValidationError(f"Unsupported fault type '{fault_base}' in fault_config.")

        # Validate policy overrides
        if policy_overrides:
            # Policy overrides must not attempt to disable core security barriers
            if policy_overrides.get("allow_unrestricted_external_writes"):
                raise SimulationValidationError(
                    "Security policy violation: External writes can NEVER be permitted in a simulation sandbox."
                )
            if policy_overrides.get("bypass_tenant_isolation"):
                raise SimulationValidationError(
                    "Security policy violation: Tenant isolation cannot be bypassed in a simulation sandbox."
                )

    @classmethod
    def validate_scenario(cls, scenario_data: Dict[str, Any]) -> None:
        name = scenario_data.get("name")
        if not name or not str(name).strip():
            raise SimulationValidationError("Scenario name is required.")

        s_type = scenario_data.get("scenario_type", "normal")
        if s_type not in ["normal", "edge_case", "failure", "security", "adversarial", "regression", "performance", "policy"]:
            raise SimulationValidationError(f"Invalid scenario_type '{s_type}'.")
