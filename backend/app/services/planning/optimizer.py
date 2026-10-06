"""
Multi-Dimensional Schedule Comparison and Factual Trade-Off Optimizer.
Never generates hidden aggregate scores.
"""
from typing import Any, Dict, List
from backend.app.services.planning.policies import PlanningPolicyEngine


class CandidateComparison:
    """
    Compares candidate schedules along explicit, factual dimensions.
    """

    @classmethod
    def compare_candidates(cls, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        comparison_results = []
        for cand in candidates:
            schedule = cand.get("schedule", {})
            duration = float(cand.get("estimated_duration", 0.0))
            cost = float(cand.get("estimated_cost", 0.0))

            human_minutes = 0.0
            agent_minutes = 0.0
            unassigned_items = 0

            for item_id, details in schedule.items():
                dur = float(details.get("duration_minutes", 0.0))
                rtype = details.get("resource_type", "")
                if rtype == "human":
                    human_minutes += dur
                elif rtype in ("agent", "agent_team"):
                    agent_minutes += dur
                elif details.get("resource_id") == "unassigned":
                    unassigned_items += 1

            result = {
                "name": cand.get("name"),
                "duration_minutes": duration,
                "cost_usd": cost,
                "human_workload_minutes": human_minutes,
                "agent_workload_minutes": agent_minutes,
                "unassigned_items_count": unassigned_items,
                "assumptions_count": len(cand.get("assumptions", [])),
                "assumptions": cand.get("assumptions", []),
            }

            # Enforce policy: ensure no hidden aggregate score is placed in metrics
            PlanningPolicyEngine.validate_no_hidden_aggregate_score(result)
            comparison_results.append(result)

        return comparison_results
