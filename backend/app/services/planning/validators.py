"""
Plan Validators, Cycle Detection, and Conflict Checks for Step 44.
"""
from typing import Any, Dict, List, Optional
from backend.app.services.planning.constraints import ConstraintEngine
from backend.app.services.planning.dependency_graph import PlanningDependencyGraph
from backend.app.services.planning.models import (
    PlanningBlocker,
    PlanningConstraint,
    PlanningDependency,
    PlanningItem,
    WorkPlan,
    WorkResource,
)
from backend.app.services.planning.resources import ResourceMatcher


class PlanValidator:
    """
    Performs comprehensive deterministic validation of a work plan version.
    """

    @classmethod
    def validate_plan_version(
        cls,
        items: List[PlanningItem],
        dependencies: List[PlanningDependency],
        resources: List[WorkResource],
        constraints: List[PlanningConstraint],
        schedule_candidate: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        hard_violations: List[str] = []
        soft_violations: List[str] = []
        conflicts: List[Dict[str, Any]] = []
        blockers: List[Dict[str, Any]] = []

        # 1. Dependency Cycle Validation
        graph = PlanningDependencyGraph()
        for it in items:
            graph.add_node(it.id, float(it.estimated_duration or 30))
        for dep in dependencies:
            graph.add_edge(dep.predecessor_item_id, dep.successor_item_id, dep.dependency_type, dep.lag)

        cycle = graph.detect_cycles()
        cycle_detected = cycle is not None
        if cycle_detected:
            msg = f"Dependency cycle detected: {' -> '.join(cycle)}"
            hard_violations.append(msg)
            blockers.append({
                "type": "dependency",
                "description": msg,
                "severity": "critical",
                "status": "open",
            })

        # 2. Capability Matching & Missing Resource Checks
        for it in items:
            req_caps = it.required_capabilities or []
            if req_caps:
                matches = ResourceMatcher.find_matching_resources(req_caps, resources)
                has_valid_resource = any(m.matched for m in matches)
                if not has_valid_resource:
                    msg = f"Item '{it.name}' requires capabilities {req_caps}, but no active resource matches."
                    soft_violations.append(msg)
                    blockers.append({
                        "type": "resource",
                        "description": msg,
                        "severity": "high",
                        "planning_item_id": it.id,
                        "status": "open",
                    })

        # 3. Constraint checks against schedule candidate if present
        if schedule_candidate:
            c_results = ConstraintEngine.evaluate_all(constraints, schedule_candidate)
            for cr in c_results:
                if not cr.satisfied:
                    if cr.hard_constraint:
                        hard_violations.append(f"Hard constraint '{cr.constraint_type}' failed: {cr.message}")
                    else:
                        soft_violations.append(f"Soft constraint '{cr.constraint_type}' missed: {cr.message}")

        is_valid = len(hard_violations) == 0 and not cycle_detected

        return {
            "is_valid": is_valid,
            "cycle_detected": cycle_detected,
            "hard_violations": hard_violations,
            "soft_violations": soft_violations,
            "conflicts": conflicts,
            "blockers": blockers,
        }
