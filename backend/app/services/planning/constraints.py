"""
Planning Constraint Model and Evaluation Engine for Step 44.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from backend.app.services.planning.errors import HardConstraintViolationError
from backend.app.services.planning.models import PlanningConstraint


class ConstraintCheckResult:
    def __init__(
        self,
        constraint_id: str,
        constraint_type: str,
        hard_constraint: bool,
        satisfied: bool,
        message: str,
    ):
        self.constraint_id = constraint_id
        self.constraint_type = constraint_type
        self.hard_constraint = hard_constraint
        self.satisfied = satisfied
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "constraint_id": self.constraint_id,
            "constraint_type": self.constraint_type,
            "hard_constraint": self.hard_constraint,
            "satisfied": self.satisfied,
            "message": self.message,
        }


class ConstraintEngine:
    """
    Evaluates hard and soft constraints against candidate schedules and assignments.
    Hard constraints cannot be bypassed or traded off.
    """

    @classmethod
    def evaluate_constraint(
        cls,
        constraint: PlanningConstraint,
        candidate_schedule: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> ConstraintCheckResult:
        ctype = constraint.constraint_type.lower()
        config = constraint.configuration or {}
        context = context or {}

        satisfied = True
        message = "Constraint satisfied."

        if ctype == "deadline":
            deadline_str = config.get("deadline")
            if deadline_str:
                if isinstance(deadline_str, str):
                    try:
                        deadline_dt = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
                    except Exception:
                        deadline_dt = None
                else:
                    deadline_dt = deadline_str

                project_end = candidate_schedule.get("project_end")
                if deadline_dt and project_end:
                    if isinstance(project_end, str):
                        project_end_dt = datetime.fromisoformat(project_end.replace("Z", "+00:00"))
                    else:
                        project_end_dt = project_end

                    if project_end_dt > deadline_dt:
                        satisfied = False
                        message = f"Planned completion {project_end_dt.isoformat()} exceeds deadline {deadline_dt.isoformat()}."

        elif ctype == "budget":
            max_budget = config.get("max_cost")
            estimated_cost = candidate_schedule.get("estimated_cost", 0.0)
            if max_budget is not None and estimated_cost > float(max_budget):
                satisfied = False
                message = f"Estimated cost ${estimated_cost:.2f} exceeds configured budget limit of ${max_budget:.2f}."

        elif ctype == "approval":
            # Requires human approval step for sensitive operations
            requires_approval = config.get("requires_approval", True)
            has_approval_gate = candidate_schedule.get("has_approval_gate", False)
            if requires_approval and not has_approval_gate:
                satisfied = False
                message = "Plan involves sensitive actions requiring an explicit human approval gate, but none was defined."

        elif ctype == "concurrency":
            max_conc = config.get("max_concurrency", 5)
            peak_conc = candidate_schedule.get("peak_concurrency", 1)
            if peak_conc > max_conc:
                satisfied = False
                message = f"Peak concurrency {peak_conc} exceeds limit of {max_conc}."

        elif ctype == "security" or ctype == "policy":
            policy_denied = config.get("policy_denied", False)
            if policy_denied:
                satisfied = False
                message = f"Governance policy '{config.get('policy_name', 'default')}' blocked the proposed plan."

        return ConstraintCheckResult(
            constraint_id=constraint.id,
            constraint_type=constraint.constraint_type,
            hard_constraint=constraint.hard_constraint,
            satisfied=satisfied,
            message=message,
        )

    @classmethod
    def evaluate_all(
        cls,
        constraints: List[PlanningConstraint],
        candidate_schedule: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        raise_on_hard_violation: bool = False,
    ) -> List[ConstraintCheckResult]:
        results: List[ConstraintCheckResult] = []
        for c in constraints:
            res = cls.evaluate_constraint(c, candidate_schedule, context)
            results.append(res)
            if not res.satisfied and res.hard_constraint and raise_on_hard_violation:
                raise HardConstraintViolationError(
                    constraint_type=res.constraint_type,
                    reason=res.message,
                )
        return results
