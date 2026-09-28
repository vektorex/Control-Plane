import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class StepType(str, Enum):
    """Supported step types for the orchestration plan."""
    CONTEXT = "context"
    RETRIEVE = "retrieve"
    TOOL = "tool"
    GENERATE = "generate"
    # Extensible future step types
    TRANSFORM = "transform"
    EVALUATE = "evaluate"
    RETRY = "retry"
    HUMAN_APPROVAL = "human_approval"


class StepStatus(str, Enum):
    """Lifecycle status of an individual execution step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionStepPlan(BaseModel):
    """
    Specification of an individual planned step in an ExecutionPlan.
    """
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(..., description="Unique step identifier, e.g. step_1, step_2")
    type: StepType = Field(..., description="Type of step to execute")
    description: Optional[str] = Field(default=None, description="Human-readable step intent")

    # Retrieval step parameters
    strategy: Optional[str] = Field(default=None, description="Retrieval strategy (hybrid, vector, keyword, multi_query)")
    scope: Optional[str] = Field(default=None, description="Retrieval scope (project, workspace)")
    top_k: Optional[int] = Field(default=None, ge=1, le=50, description="Max candidate chunks to retrieve")
    query: Optional[str] = Field(default=None, description="Specific query string for retrieval")

    # Tool step parameters
    tool: Optional[str] = Field(default=None, description="Registered tool name, e.g. web_search")
    tool_input: Optional[Dict[str, Any]] = Field(default=None, description="Input parameters passed to the tool")

    # Generation step parameters
    model: Optional[str] = Field(default=None, description="Target LLM model, e.g. gpt-4o-mini")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="Model generation temperature")
    max_tokens: Optional[int] = Field(default=None, ge=1, description="Maximum response tokens")

    # Failure policy
    required: bool = Field(default=True, description="Whether step failure should abort entire execution")

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary step metadata")


class ExecutionPlan(BaseModel):
    """
    Complete, validated sequential execution plan for a Task.
    """
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(default_factory=lambda: f"plan-{uuid.uuid4().hex[:8]}", description="Unique execution plan ID")
    task_id: Optional[str] = Field(default=None, description="Associated task ID")
    steps: List[ExecutionStepPlan] = Field(default_factory=list, description="Ordered list of execution steps")
    plan_reason: Optional[str] = Field(default=None, description="Planner rationale for the selected workflow")
    estimated_steps: int = Field(default=0, description="Total step count")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if not self.estimated_steps:
            self.estimated_steps = len(self.steps)
