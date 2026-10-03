"""
Team Planner for Step 40.
Produces structured, deterministic execution plans for multi-agent teams.
Validates dependencies, parallel groups, and output requirements before execution.
"""
from typing import Any, Dict, List, Optional
from backend.app.services.agents.errors import AgentError


class TeamPlanValidationError(AgentError):
    """Raised when a multi-agent team plan fails structural or policy validation."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="TEAM_PLAN_VALIDATION_ERROR", details=details)


class TeamPlanner:
    """Generates and validates structured execution plans for multi-agent team runs."""

    @classmethod
    def generate_plan(
        cls,
        team_run_id: str,
        objective: str,
        members: List[Dict[str, Any]],  # [{agent_id, agent_version_id, role, capabilities, responsibilities}]
        user_input: Dict[str, Any],
        coordination_policy: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Creates a structured plan grouping team members into execution stages / parallel groups.
        """
        coordination_mode = (coordination_policy or {}).get("mode", "sequential_review")

        assignments: List[Dict[str, Any]] = []
        parallel_groups: List[List[str]] = []
        execution_order: List[str] = []

        # Categorize roles
        leads = [m for m in members if m.get("role") == "lead"]
        researchers = [m for m in members if m.get("role") in {"researcher", "specialist"}]
        builders = [m for m in members if m.get("role") in {"builder", "executor", "analyst"}]
        reviewers = [m for m in members if m.get("role") == "reviewer"]

        # If no specific roles, treat all members as standard executors
        all_ordered = leads + researchers + builders + reviewers
        if not all_ordered:
            all_ordered = members

        # Stage 1: Research / Preparation (can run in parallel if multiple)
        stage_1_agents = [m["agent_id"] for m in (leads or researchers)]
        if stage_1_agents:
            parallel_groups.append(stage_1_agents)
            execution_order.extend(stage_1_agents)
            for ag in stage_1_agents:
                assignments.append({
                    "assignment_id": f"assign_{len(assignments) + 1}",
                    "agent_id": ag,
                    "stage": 1,
                    "type": "research_or_lead",
                    "dependencies": [],
                    "description": f"Gather context and formulate approach for: {objective[:80]}",
                })

        # Stage 2: Execution / Analysis (depends on Stage 1)
        stage_2_agents = [m["agent_id"] for m in builders if m["agent_id"] not in execution_order]
        if stage_2_agents:
            parallel_groups.append(stage_2_agents)
            execution_order.extend(stage_2_agents)
            for ag in stage_2_agents:
                assignments.append({
                    "assignment_id": f"assign_{len(assignments) + 1}",
                    "agent_id": ag,
                    "stage": 2,
                    "type": "execute_or_build",
                    "dependencies": stage_1_agents,
                    "description": f"Synthesize primary deliverables for: {objective[:80]}",
                })

        # Stage 3: Review / Verification (depends on Stage 2)
        stage_3_agents = [m["agent_id"] for m in reviewers if m["agent_id"] not in execution_order]
        if stage_3_agents:
            parallel_groups.append(stage_3_agents)
            execution_order.extend(stage_3_agents)
            for ag in stage_3_agents:
                assignments.append({
                    "assignment_id": f"assign_{len(assignments) + 1}",
                    "agent_id": ag,
                    "stage": 3,
                    "type": "review_and_verify",
                    "dependencies": stage_2_agents or stage_1_agents,
                    "description": f"Review and verify findings for: {objective[:80]}",
                })

        # Catch-all: any member not yet assigned
        unassigned = [m["agent_id"] for m in members if m["agent_id"] not in execution_order]
        if unassigned:
            parallel_groups.append(unassigned)
            execution_order.extend(unassigned)
            for ag in unassigned:
                assignments.append({
                    "assignment_id": f"assign_{len(assignments) + 1}",
                    "agent_id": ag,
                    "stage": len(parallel_groups),
                    "type": "general_work",
                    "dependencies": execution_order[: -len(unassigned)],
                    "description": f"Contribute to team objective: {objective[:80]}",
                })

        plan = {
            "team_run_id": team_run_id,
            "objective": objective,
            "agents": [m["agent_id"] for m in members],
            "assignments": assignments,
            "dependencies": {a["assignment_id"]: a["dependencies"] for a in assignments},
            "execution_order": execution_order,
            "parallel_groups": parallel_groups,
            "expected_outputs": ["structured_findings", "review_summary", "final_synthesis"],
            "evaluation_requirements": [
                "output_correctness",
                "evidence_consistency",
                "policy_compliance",
            ],
        }

        cls.validate_plan(plan)
        return plan

    @classmethod
    def validate_plan(cls, plan: Dict[str, Any]) -> None:
        """Validates that plan is non-empty, contains agents and assignments, and has no broken dependencies."""
        if not plan.get("objective"):
            raise TeamPlanValidationError("Team plan must specify an objective.")
        if not plan.get("agents"):
            raise TeamPlanValidationError("Team plan must involve at least one agent.")
        if not plan.get("assignments"):
            raise TeamPlanValidationError("Team plan must have at least one assignment.")

        # Verify dependency integrity
        all_agents = set(plan["agents"])
        for assign in plan["assignments"]:
            if assign["agent_id"] not in all_agents:
                raise TeamPlanValidationError(f"Assignment specifies unknown agent '{assign['agent_id']}'.")
            for dep in assign.get("dependencies", []):
                if dep not in all_agents:
                    raise TeamPlanValidationError(f"Assignment dependency specifies unknown agent '{dep}'.")
