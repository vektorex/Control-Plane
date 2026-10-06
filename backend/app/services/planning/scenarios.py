"""
What-If Planning Scenarios and Isolated Simulations for Step 44.
Never modifies production plans or real allocations.
"""
from typing import Any, Dict, List, Optional
from backend.app.services.planning.scheduler import ScheduleGenerator
from backend.app.services.planning.optimizer import CandidateComparison
from backend.app.services.planning.models import (
    PlanningConstraint,
    PlanningDependency,
    PlanningItem,
    WorkResource,
)


class ScenarioEngine:
    """
    Executes isolated what-if scenario simulations.
    """

    @classmethod
    def run_scenario(
        cls,
        base_items: List[PlanningItem],
        base_dependencies: List[PlanningDependency],
        base_resources: List[WorkResource],
        base_constraints: List[PlanningConstraint],
        modifications: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Clones inputs in memory, applies hypothetical modifications,
        and generates comparative candidates.
        """
        # 1. Apply resource modifications (e.g., removing an agent, adding an agent)
        simulated_resources = list(base_resources)
        disabled_resource_id = modifications.get("disable_resource_id")
        if disabled_resource_id:
            simulated_resources = [r for r in simulated_resources if r.id != disabled_resource_id]

        # 2. Apply duration adjustments
        duration_multiplier = float(modifications.get("duration_multiplier", 1.0))
        simulated_items = []
        for it in base_items:
            # Shallow clone
            sim_it = PlanningItem(
                id=it.id,
                name=it.name,
                resource_type=it.resource_type,
                resource_id=it.resource_id,
                priority=it.priority,
                estimated_duration=int((it.estimated_duration or 30) * duration_multiplier),
                estimated_cost=it.estimated_cost,
                required_capabilities=list(it.required_capabilities or []),
                status=it.status,
            )
            simulated_items.append(sim_it)

        # 3. Generate candidate schedules under simulated conditions
        candidates = ScheduleGenerator.generate_candidates(
            items=simulated_items,
            dependencies=base_dependencies,
            resources=simulated_resources,
            constraints=base_constraints,
        )

        comparison = CandidateComparison.compare_candidates(candidates)

        return {
            "scenario_modifications": modifications,
            "simulated_candidates_count": len(candidates),
            "candidates": candidates,
            "comparison": comparison,
            "is_simulation": True,
        }
