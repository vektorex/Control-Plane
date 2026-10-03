"""
Governance policy bridge for Step 35: AI Reliability, Resilience & Chaos Engineering Layer.
Connects with Step 32 AI Governance to retrieve authoritative timeout, retry, and fallback limits.
"""
from typing import Any, Dict, Optional

# Default bounded timeouts (seconds) per operation category
DEFAULT_TIMEOUT_BOUNDS: Dict[str, float] = {
    "request": 30.0,
    "ai_generation": 60.0,
    "streaming": 120.0,
    "retrieval": 15.0,
    "embedding": 20.0,
    "reranking": 15.0,
    "tool": 30.0,
    "connector": 45.0,
    "workflow_step": 90.0,
    "job": 300.0,
    "notification": 15.0,
    "export": 180.0,
    "artifact_processing": 60.0,
}


class ReliabilityPolicyManager:
    """Retrieves authoritative timeouts, retry policies, and fallback authorizations."""

    @classmethod
    def get_timeout_seconds(
        cls,
        category: str,
        governance_override: Optional[float] = None,
    ) -> float:
        """
        Returns bounded timeout for a category. Never permits infinite waits.
        """
        if governance_override and 0.5 <= governance_override <= 600.0:
            return float(governance_override)
        return DEFAULT_TIMEOUT_BOUNDS.get(category, 30.0)

    @classmethod
    def is_fallback_permitted_by_governance(
        cls,
        task_governance_rules: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Checks whether Step 32 AI Governance permits dynamic model/provider substitution.
        """
        if not task_governance_rules:
            return True
        return task_governance_rules.get("allow_model_fallback", True)
