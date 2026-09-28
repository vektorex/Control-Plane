import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.task import Task
from backend.app.db.models.user import User
from backend.app.schemas.task import TaskRunRequest
from backend.app.services.orchestration.plan import ExecutionPlan
from backend.app.services.orchestration.planners.base import BasePlanner, PlannerContext
from backend.app.services.orchestration.planners.deterministic import DeterministicPlanner
from backend.app.services.orchestration.planners.llm import LLMPlanningProvider
from backend.app.services.orchestration.validator import PlanValidator

logger = logging.getLogger("orchestration.planner.hybrid")


class HybridPlanner(BasePlanner):
    """
    Hybrid Planner that combines deterministic safety baselines with LLM-assisted reasoning.
    1. Deterministic planner establishes safe baseline plan.
    2. LLM planner proposes an execution plan.
    3. Validator checks the proposed plan.
    4. If LLM planning fails, the deterministic baseline plan is safely used.
    """

    def __init__(
        self,
        deterministic_planner: Optional[DeterministicPlanner] = None,
        llm_planner: Optional[LLMPlanningProvider] = None,
        validator: Optional[PlanValidator] = None,
        llm_factory: Optional[Any] = None,
    ) -> None:
        self.llm_factory = llm_factory
        self.deterministic_planner = deterministic_planner or DeterministicPlanner()
        self.llm_planner = llm_planner or LLMPlanningProvider(llm_factory=self.llm_factory)
        self.validator = validator or PlanValidator(llm_factory=self.llm_factory)

    async def plan(
        self,
        task: Task,
        request: Optional[TaskRunRequest] = None,
        user: Optional[User] = None,
        context: Optional[PlannerContext] = None,
        session: Optional[AsyncSession] = None,
        **kwargs: Any,
    ) -> ExecutionPlan:
        """
        Executes hybrid planning workflow.
        """
        req = request or TaskRunRequest()

        # 1. Establish deterministic baseline plan
        baseline_plan = await self.deterministic_planner.plan(
            task=task,
            request=req,
            user=user,
            context=context,
            session=session,
            **kwargs,
        )

        # 2. Attempt LLM-assisted planning
        try:
            llm_plan = await self.llm_planner.plan(
                task=task,
                request=req,
                user=user,
                context=context,
                **kwargs,
            )
            # Ensure validated
            self.validator.validate(llm_plan, user=user)
            llm_plan.metadata["planner"] = "hybrid"
            llm_plan.metadata["planner_mode"] = "hybrid"
            llm_plan.metadata["baseline_plan_id"] = baseline_plan.id
            return llm_plan

        except Exception as err:
            logger.warning(
                f"LLM planning in HybridPlanner failed ({err}). Safely falling back to deterministic baseline."
            )
            baseline_plan.metadata["planner"] = "hybrid_fallback"
            baseline_plan.metadata["planner_mode"] = "deterministic_fallback"
            baseline_plan.metadata["fallback_reason"] = str(err)
            return baseline_plan
