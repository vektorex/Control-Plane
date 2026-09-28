from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.db.models.task import Task
from backend.app.db.models.user import User
from backend.app.schemas.task import TaskRunRequest
from backend.app.services.orchestration.plan import ExecutionPlan


class AvailableCapabilities(BaseModel):
    """
    Representation of application capabilities available for planning.
    The planner is restricted to only propose capabilities in this set.
    """
    retrieval: List[str] = Field(default_factory=lambda: ["hybrid", "vector", "keyword", "multi_query"])
    tools: List[str] = Field(default_factory=list)
    generation: bool = Field(default=True)
    max_steps: int = Field(default=10)

    @classmethod
    def from_request_and_environment(cls, req: TaskRunRequest) -> "AvailableCapabilities":
        ret_list = ["hybrid", "vector", "keyword", "multi_query"] if req.retrieval_mode != "never" else []
        tools_list: List[str] = []
        if req.tool_mode in ("enabled", "auto") or req.enable_web_search or bool(req.tools_enabled):
            if req.tools_enabled:
                tools_list = list(req.tools_enabled)
            elif req.enable_web_search or req.tool_mode in ("enabled", "auto"):
                tools_list = ["web_search"]
        return cls(retrieval=ret_list, tools=tools_list, generation=True)


class PlannerContext(BaseModel):
    """
    Structured context provided to the planner.
    Does NOT contain raw documents or unbounded external content.
    """
    task_id: str
    task_title: str
    task_instructions: str
    context_text: Optional[str] = None
    has_manual_context: bool = False
    manual_context_count: int = 0
    retrieval_mode: str = "auto"
    tool_mode: str = "disabled"
    tools_enabled: List[str] = Field(default_factory=list)
    available_capabilities: AvailableCapabilities = Field(default_factory=AvailableCapabilities)
    target_model: str = "gpt-4o-mini"
    temperature: float = 0.2
    max_context_tokens: int = 8000
    missing_information: Optional[List[str]] = None
    iteration: int = 1

    @classmethod
    def from_task_and_request(
        cls,
        task: Task,
        req: TaskRunRequest,
        capabilities: Optional[AvailableCapabilities] = None,
        missing_information: Optional[List[str]] = None,
        iteration: int = 1,
    ) -> "PlannerContext":
        caps = capabilities or AvailableCapabilities.from_request_and_environment(req)
        return cls(
            task_id=str(task.id),
            task_title=task.title or "",
            task_instructions=task.instructions or task.description or "",
            context_text=task.context_text,
            retrieval_mode=req.retrieval_mode or "auto",
            tool_mode=req.tool_mode or ("enabled" if req.enable_web_search or req.tools_enabled else "disabled"),
            tools_enabled=req.tools_enabled or (["web_search"] if req.enable_web_search else []),
            available_capabilities=caps,
            target_model=req.model or "gpt-4o-mini",
            temperature=req.temperature if req.temperature is not None else 0.2,
            max_context_tokens=req.max_context_tokens or 8000,
            missing_information=missing_information,
            iteration=iteration,
        )


class BasePlanner(ABC):
    """
    Abstract interface for planning providers (deterministic, LLM-assisted, hybrid).
    """

    @abstractmethod
    async def plan(
        self,
        task: Task,
        request: Optional[TaskRunRequest] = None,
        user: Optional[User] = None,
        context: Optional[PlannerContext] = None,
        **kwargs: Any,
    ) -> ExecutionPlan:
        """
        Synthesizes a structured ExecutionPlan for the specified task and capabilities.
        """
        pass
