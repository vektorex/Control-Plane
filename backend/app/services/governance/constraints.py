"""
GovernanceConstraints: standardized constraint builders for policy actions.
Step 32.
"""
from typing import Any, Dict, List, Optional


class ConstraintBuilder:
    """Builds normalized constraint dictionaries from policy action parameters."""

    @staticmethod
    def allowed_models(model_ids: List[str]) -> Dict[str, Any]:
        return {"allowed_models": model_ids}

    @staticmethod
    def blocked_models(model_ids: List[str]) -> Dict[str, Any]:
        return {"blocked_models": model_ids}

    @staticmethod
    def allowed_providers(providers: List[str]) -> Dict[str, Any]:
        return {"allowed_providers": providers}

    @staticmethod
    def blocked_providers(providers: List[str]) -> Dict[str, Any]:
        return {"blocked_providers": providers}

    @staticmethod
    def max_output_tokens(tokens: int) -> Dict[str, Any]:
        return {"max_output_tokens": tokens}

    @staticmethod
    def max_context_window(tokens: int) -> Dict[str, Any]:
        return {"max_context_window": tokens}

    @staticmethod
    def max_cost_per_run(usd: float) -> Dict[str, Any]:
        return {"max_cost_per_run_usd": usd}

    @staticmethod
    def allowed_tools(tool_ids: List[str]) -> Dict[str, Any]:
        return {"allowed_tools": tool_ids}

    @staticmethod
    def blocked_tools(tool_ids: List[str]) -> Dict[str, Any]:
        return {"blocked_tools": tool_ids}

    @staticmethod
    def allowed_connectors(connector_ids: List[str]) -> Dict[str, Any]:
        return {"allowed_connectors": connector_ids}

    @staticmethod
    def blocked_connectors(connector_ids: List[str]) -> Dict[str, Any]:
        return {"blocked_connectors": connector_ids}

    @staticmethod
    def cache_disabled() -> Dict[str, Any]:
        return {"cache_mode": "disabled"}

    @staticmethod
    def cache_exact_only() -> Dict[str, Any]:
        return {"cache_mode": "exact_only"}

    @staticmethod
    def semantic_cache_disabled() -> Dict[str, Any]:
        return {"semantic_cache_enabled": False}

    @staticmethod
    def stale_while_revalidate_disabled() -> Dict[str, Any]:
        return {"stale_while_revalidate": False}

    @staticmethod
    def max_cache_ttl(seconds: int) -> Dict[str, Any]:
        return {"max_cache_ttl_seconds": seconds}

    @staticmethod
    def evaluation_required(scope: str = "standard") -> Dict[str, Any]:
        return {"evaluation_required": True, "evaluation_scope": scope}

    @staticmethod
    def allowed_artifact_types(types: List[str]) -> Dict[str, Any]:
        return {"allowed_artifact_types": types}

    @staticmethod
    def max_artifact_size_bytes(size: int) -> Dict[str, Any]:
        return {"max_artifact_size_bytes": size}

    @staticmethod
    def max_workflow_steps(steps: int) -> Dict[str, Any]:
        return {"max_workflow_steps": steps}

    @staticmethod
    def max_workflow_cost(usd: float) -> Dict[str, Any]:
        return {"max_workflow_cost_usd": usd}

    @staticmethod
    def merge(*constraint_dicts: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple constraint dicts. Later dicts take precedence."""
        merged: Dict[str, Any] = {}
        for d in constraint_dicts:
            merged.update(d)
        return merged


def apply_model_constraint(constraints: Dict[str, Any], model_id: Optional[str]) -> bool:
    """Returns True if the model is allowed given current constraints."""
    if "blocked_models" in constraints and model_id in constraints["blocked_models"]:
        return False
    if "allowed_models" in constraints and model_id not in constraints["allowed_models"]:
        return False
    return True


def apply_provider_constraint(constraints: Dict[str, Any], provider: Optional[str]) -> bool:
    """Returns True if the provider is allowed given current constraints."""
    if not provider:
        return True
    if "blocked_providers" in constraints and provider.lower() in [p.lower() for p in constraints["blocked_providers"]]:
        return False
    if "allowed_providers" in constraints and provider.lower() not in [p.lower() for p in constraints["allowed_providers"]]:
        return False
    return True


def apply_tool_constraint(constraints: Dict[str, Any], tool_id: Optional[str]) -> bool:
    """Returns True if the tool is allowed given current constraints."""
    if not tool_id:
        return True
    if "blocked_tools" in constraints and tool_id in constraints["blocked_tools"]:
        return False
    if "allowed_tools" in constraints and tool_id not in constraints["allowed_tools"]:
        return False
    return True


def apply_connector_constraint(constraints: Dict[str, Any], connector_id: Optional[str]) -> bool:
    """Returns True if the connector is allowed given current constraints."""
    if not connector_id:
        return True
    if "blocked_connectors" in constraints and connector_id in constraints["blocked_connectors"]:
        return False
    if "allowed_connectors" in constraints and connector_id not in constraints["allowed_connectors"]:
        return False
    return True
