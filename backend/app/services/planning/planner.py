"""
Planning Engines: RuleBasedPlanner, AIPlanningAssistant, and HybridPlanningEngine for Step 44.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from backend.app.services.planning.constraints import ConstraintEngine
from backend.app.services.planning.dependency_graph import PlanningDependencyGraph
from backend.app.services.planning.models import (
    PlanningConstraint,
    PlanningDependency,
    PlanningItem,
    WorkPlan,
    WorkPlanVersion,
    WorkResource,
)
from backend.app.services.planning.optimizer import CandidateComparison
from backend.app.services.planning.policies import PlanningPolicyEngine
from backend.app.services.planning.recommendations import PlanningRecommendationGenerator
from backend.app.services.planning.scheduler import ScheduleGenerator


class RuleBasedPlanner:
    """
    Deterministic baseline planner.
    Evaluates dependencies, capabilities, deadlines, concurrency, and hard constraints.
    """

    @classmethod
    def plan(
        cls,
        items: List[PlanningItem],
        dependencies: List[PlanningDependency],
        resources: List[WorkResource],
        constraints: List[PlanningConstraint],
        horizon_start: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        candidates = ScheduleGenerator.generate_candidates(
            items=items,
            dependencies=dependencies,
            resources=resources,
            constraints=constraints,
            horizon_start=horizon_start,
        )

        comparison = CandidateComparison.compare_candidates(candidates)
        recommendations = PlanningRecommendationGenerator.generate_recommendations(
            items=items,
            blockers=[],
            resources=resources,
        )

        return {
            "mode": "rules_only",
            "candidates": candidates,
            "comparison": comparison,
            "recommendations": recommendations,
        }


class AIPlanningAssistant:
    """
    Optional AI-assisted planning helper.
    Interprets goals and suggests decomposition and assignments.
    AI suggestions must be validated by deterministic rules and cannot override hard constraints.
    """

    @classmethod
    async def suggest_plan_enhancements(
        cls,
        goal_description: str,
        items: List[PlanningItem],
        resources: List[WorkResource],
    ) -> Dict[str, Any]:
        # Structured advice proposal
        suggested_decompositions = []
        for it in items:
            if (it.estimated_duration or 30) > 120:
                suggested_decompositions.append({
                    "parent_item_id": it.id,
                    "suggested_action": "split_task",
                    "reason": f"Item '{it.name}' duration ({it.estimated_duration} mins) exceeds 2 hours; splitting reduces blocker risk.",
                })

        return {
            "ai_suggestions_labeled": True,
            "is_proposal": True,
            "suggested_decompositions": suggested_decompositions,
            "bottleneck_insights": [
                "Ensure required human approvals have assigned reviewers in advance."
            ],
        }


class HybridPlanningEngine:
    """
    Coordinates rule-based analysis, optional AI assistance, and deterministic validation.
    """

    @classmethod
    async def execute_planning_pipeline(
        cls,
        plan: WorkPlan,
        items: List[PlanningItem],
        dependencies: List[PlanningDependency],
        resources: List[WorkResource],
        constraints: List[PlanningConstraint],
        mode: str = "hybrid",
        preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        horizon_start = plan.planning_horizon_start or datetime.now(timezone.utc)

        # 1. Deterministic baseline planning
        rule_results = RuleBasedPlanner.plan(
            items=items,
            dependencies=dependencies,
            resources=resources,
            constraints=constraints,
            horizon_start=horizon_start,
        )

        ai_proposals = {}
        if mode in ("ai_assisted", "hybrid"):
            ai_proposals = await AIPlanningAssistant.suggest_plan_enhancements(
                goal_description=plan.description or plan.name,
                items=items,
                resources=resources,
            )

        return {
            "work_plan_id": plan.id,
            "planning_mode": mode,
            "candidates": rule_results["candidates"],
            "comparison": rule_results["comparison"],
            "recommendations": rule_results["recommendations"],
            "ai_proposals": ai_proposals,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
