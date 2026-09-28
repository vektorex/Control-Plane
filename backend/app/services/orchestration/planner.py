import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.db.models.task import Task
from backend.app.db.models.user import User
from backend.app.schemas.task import TaskRunRequest
from backend.app.services.llm.factory import LLMProviderFactory, get_llm_factory
from backend.app.services.orchestration.plan import ExecutionPlan
from backend.app.services.orchestration.planners.base import PlannerContext
from backend.app.services.orchestration.planners.deterministic import DeterministicPlanner
from backend.app.services.orchestration.planners.hybrid import HybridPlanner
from backend.app.services.orchestration.planners.llm import LLMPlanningProvider
from backend.app.services.orchestration.validator import PlanValidator
from backend.app.services.retrieval.router import RetrievalRouter, get_retrieval_router
from backend.app.services.tools.registry import ToolRegistry, get_tool_registry

logger = logging.getLogger("orchestration.planner")


class ExecutionPlanner:
    """
    Unified Execution Planner dispatcher for Step 10 & Step 11.
    Supports deterministic, LLM-assisted, and hybrid planning modes.
    Default mode: hybrid.
    """

    def __init__(
        self,
        retrieval_router: Optional[RetrievalRouter] = None,
        tool_registry: Optional[ToolRegistry] = None,
        llm_factory: Optional[LLMProviderFactory] = None,
        validator: Optional[PlanValidator] = None,
    ) -> None:
        self.retrieval_router = retrieval_router or get_retrieval_router()
        self.tool_registry = tool_registry or get_tool_registry()
        self.llm_factory = llm_factory or get_llm_factory()
        self.validator = validator or PlanValidator(tool_registry=self.tool_registry, llm_factory=self.llm_factory)

        self.deterministic_planner = DeterministicPlanner(
            retrieval_router=self.retrieval_router,
            tool_registry=self.tool_registry,
        )
        self.llm_planner = LLMPlanningProvider(
            llm_factory=self.llm_factory,
            validator=self.validator,
        )
        self.hybrid_planner = HybridPlanner(
            deterministic_planner=self.deterministic_planner,
            llm_planner=self.llm_planner,
            validator=self.validator,
            llm_factory=self.llm_factory,
        )

    async def plan(
        self,
        task: Task,
        request: Optional[TaskRunRequest] = None,
        user: Optional[User] = None,
        session: Optional[AsyncSession] = None,
        context: Optional[PlannerContext] = None,
        **kwargs: Any,
    ) -> ExecutionPlan:
        """
        Synthesizes a structured ExecutionPlan using the configured planning mode.
        """
        req = request or TaskRunRequest()
        mode = (req.planner_mode or settings.PLANNER_DEFAULT_MODE or "hybrid").lower()
        if mode == "auto":
            mode = "hybrid"

        if mode == "deterministic":
            return await self.deterministic_planner.plan(
                task=task,
                request=req,
                user=user,
                session=session,
                context=context,
                **kwargs,
            )

        elif mode == "llm":
            return await self.llm_planner.plan(
                task=task,
                request=req,
                user=user,
                context=context,
                **kwargs,
            )

        # Default: hybrid
        return await self.hybrid_planner.plan(
            task=task,
            request=req,
            user=user,
            session=session,
            context=context,
            **kwargs,
        )


_planner_instance: Optional[ExecutionPlanner] = None


def get_execution_planner() -> ExecutionPlanner:
    global _planner_instance
    if _planner_instance is None:
        _planner_instance = ExecutionPlanner()
    return _planner_instance
