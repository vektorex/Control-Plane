"""
Duration, Cost, and Effort Estimators for Planning Items.
Never invents pricing or costs; marks unavailable when missing.
"""
from typing import Any, Dict, Optional
from backend.app.services.planning.models import PlanningItem


class EffortEstimator:
    """
    Factual estimation engine for durations and costs.
    Estimates are explicitly flagged as estimates.
    """

    DEFAULT_DURATIONS = {
        "task": 30,          # minutes
        "workflow": 45,
        "workflow_step": 10,
        "agent_run": 20,
        "agent_team_run": 40,
        "milestone": 0,
        "outcome": 0,
        "approval": 60,
        "evaluation": 15,
        "simulation": 25,
    }

    @classmethod
    def estimate_item_duration(cls, item: PlanningItem) -> int:
        """Returns estimated duration in minutes."""
        if item.estimated_duration is not None and item.estimated_duration > 0:
            return item.estimated_duration
        rtype = (item.resource_type or "task").lower()
        return cls.DEFAULT_DURATIONS.get(rtype, 30)

    @classmethod
    def estimate_item_cost(
        cls,
        item: PlanningItem,
        pricing_catalog: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Estimates execution cost using configured pricing.
        If pricing is unavailable, cost is marked as unavailable.
        """
        if item.estimated_cost is not None:
            return {
                "estimated_cost": item.estimated_cost,
                "cost_status": "configured",
                "is_estimate": True,
            }

        pricing_catalog = pricing_catalog or {}
        rtype = (item.resource_type or "task").lower()

        # Agents and workflows might have model costs
        if rtype in ("agent_run", "agent_team_run", "simulation"):
            unit_price = pricing_catalog.get(rtype)
            if unit_price is not None:
                return {
                    "estimated_cost": float(unit_price),
                    "cost_status": "catalog_estimated",
                    "is_estimate": True,
                }
            return {
                "estimated_cost": None,
                "cost_status": "unavailable",
                "is_estimate": True,
                "explanation": "No pricing configured for model or agent runtime.",
            }

        return {
            "estimated_cost": 0.0,
            "cost_status": "zero_cost_resource",
            "is_estimate": True,
        }
