"""
Schedule Generator and Candidate Schedule Builder for Step 44.
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from backend.app.services.planning.dependency_graph import PlanningDependencyGraph
from backend.app.services.planning.estimators import EffortEstimator
from backend.app.services.planning.models import (
    PlanningConstraint,
    PlanningDependency,
    PlanningItem,
    WorkResource,
)
from backend.app.services.planning.resources import ResourceMatcher


class ScheduleGenerator:
    """
    Generates multiple candidate schedules (e.g. Sequential, Parallel, Automated).
    Does not label one candidate 'best' without factual user-configured criteria.
    """

    @classmethod
    def generate_candidates(
        cls,
        items: List[PlanningItem],
        dependencies: List[PlanningDependency],
        resources: List[WorkResource],
        constraints: List[PlanningConstraint],
        horizon_start: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        if not items:
            return []

        base_time = horizon_start or datetime.now(timezone.utc)
        graph = PlanningDependencyGraph()
        item_map = {item.id: item for item in items}

        for item in items:
            dur = EffortEstimator.estimate_item_duration(item)
            graph.add_node(item.id, float(dur))

        for dep in dependencies:
            graph.add_edge(dep.predecessor_item_id, dep.successor_item_id, dep.dependency_type, dep.lag)

        # Validate cycles - will raise DependencyCycleError if cycle exists
        graph.validate_no_cycles()
        cpm = graph.compute_critical_path()
        order = graph.topological_sort()

        candidates: List[Dict[str, Any]] = []

        # Candidate 1: Standard Topological / Dependency-Driven Schedule
        std_schedule = {}
        resource_allocations = {}
        total_cost = 0.0

        for item_id in order:
            item = item_map[item_id]
            dur = graph.durations.get(item_id, 30.0)
            es_offset = cpm["earliest_start"].get(item_id, 0.0)
            item_start = base_time + timedelta(minutes=es_offset)
            item_end = item_start + timedelta(minutes=dur)

            # Match resource
            matches = ResourceMatcher.find_matching_resources(item.required_capabilities, resources)
            selected_res = next((m for m in matches if m.matched), None)
            res_id = selected_res.resource_id if selected_res else "unassigned"

            cost_info = EffortEstimator.estimate_item_cost(item)
            if cost_info.get("estimated_cost"):
                total_cost += float(cost_info["estimated_cost"])

            std_schedule[item_id] = {
                "name": item.name,
                "start": item_start.isoformat(),
                "end": item_end.isoformat(),
                "duration_minutes": dur,
                "resource_id": res_id,
                "resource_type": selected_res.resource_type if selected_res else "unassigned",
            }
            if res_id not in resource_allocations:
                resource_allocations[res_id] = []
            resource_allocations[res_id].append(item_id)

        project_duration_minutes = cpm["total_duration"]
        project_end = base_time + timedelta(minutes=project_duration_minutes)

        cand1 = {
            "name": "Dependency-Optimized Baseline",
            "schedule": std_schedule,
            "assumptions": [
                "Tasks scheduled at earliest permissible start time per dependency rules.",
                "Resources assumed available in calculated time windows.",
            ],
            "constraint_results": {
                "critical_path_items": cpm["critical_path"],
                "total_duration_minutes": project_duration_minutes,
            },
            "resource_allocations": resource_allocations,
            "estimated_duration": project_duration_minutes,
            "estimated_cost": total_cost,
            "project_end": project_end,
        }
        candidates.append(cand1)

        # Candidate 2: Conservative Sequential Schedule (minimizes concurrency conflicts)
        seq_schedule = {}
        seq_allocations = {}
        curr_time = base_time
        for item_id in order:
            item = item_map[item_id]
            dur = graph.durations.get(item_id, 30.0)
            item_start = curr_time
            item_end = curr_time + timedelta(minutes=dur)
            curr_time = item_end

            matches = ResourceMatcher.find_matching_resources(item.required_capabilities, resources)
            selected_res = next((m for m in matches if m.matched), None)
            res_id = selected_res.resource_id if selected_res else "unassigned"

            seq_schedule[item_id] = {
                "name": item.name,
                "start": item_start.isoformat(),
                "end": item_end.isoformat(),
                "duration_minutes": dur,
                "resource_id": res_id,
            }
            if res_id not in seq_allocations:
                seq_allocations[res_id] = []
            seq_allocations[res_id].append(item_id)

        seq_dur = sum(graph.durations.get(i, 30.0) for i in order)
        cand2 = {
            "name": "Sequential Low-Concurrency Schedule",
            "schedule": seq_schedule,
            "assumptions": [
                "All items executed sequentially to eliminate resource concurrency contention.",
            ],
            "constraint_results": {
                "total_duration_minutes": seq_dur,
            },
            "resource_allocations": seq_allocations,
            "estimated_duration": seq_dur,
            "estimated_cost": total_cost,
            "project_end": base_time + timedelta(minutes=seq_dur),
        }
        candidates.append(cand2)

        return candidates
