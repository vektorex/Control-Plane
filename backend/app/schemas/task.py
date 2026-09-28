from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from backend.app.db.models.enums import TaskStatus


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(default=None, description="General task summary or description")
    instructions: Optional[str] = Field(default=None, description="Specific prompt/instructions for the LLM")
    context_text: Optional[str] = Field(default=None, description="Optional background context or document snippets")
    status: TaskStatus = Field(default=TaskStatus.DRAFT, description="Task lifecycle status")


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None)
    instructions: Optional[str] = Field(default=None)
    context_text: Optional[str] = Field(default=None)
    status: Optional[TaskStatus] = Field(default=None)


class TaskRunRequest(BaseModel):
    model: Optional[str] = Field(default="gpt-4o-mini", description="Target model identifier (e.g. gpt-4o-mini)")
    temperature: Optional[float] = Field(default=0.2, ge=0.0, le=2.0, description="Sampling temperature")
    max_context_tokens: Optional[int] = Field(default=8000, ge=1, le=128000, description="Max token budget for context assembly")
    retrieval_mode: Optional[str] = Field(default="auto", description="Retrieval mode: auto, always, or never")
    retrieval_strategy: Optional[str] = Field(default=None, description="Optional strategy override: hybrid, vector, keyword, multi_query, none")
    retrieval_scope: Optional[str] = Field(default=None, description="Optional scope override: project or workspace")
    retrieval_top_k: Optional[int] = Field(default=8, ge=1, le=50, description="Top K document chunks to retrieve")
    query: Optional[str] = Field(default=None, description="Optional explicit retrieval query override")
    retrieval_enabled: Optional[bool] = Field(default=None, description="Legacy boolean flag: True=always, False=never")
    retrieval_project_scope: Optional[bool] = Field(default=True, description="Scope retrieval to current project vs entire workspace")

    # Step 9: Tool System & Web Search Configuration
    tool_mode: Optional[str] = Field(default="disabled", description="Tool execution mode: auto, enabled, or disabled")
    tools_enabled: Optional[List[str]] = Field(default=None, description="Allowed tools list (e.g. ['web_search'])")
    enable_web_search: Optional[bool] = Field(default=False, description="Convenience toggle to execute web search tool")
    web_search_query: Optional[str] = Field(default=None, description="Explicit search query override for web search tool")
    web_search_limit: Optional[int] = Field(default=5, ge=1, le=20, description="Max web search result items to retrieve")
    web_search_recency_days: Optional[int] = Field(default=None, ge=1, le=365, description="Optional recency window in days")



class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    context_text: Optional[str] = None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    run_count: Optional[int] = 0
    context_count: Optional[int] = 0


from backend.app.services.retrieval.decision import RetrievalDecision


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int


class RetrievalPreviewResponse(BaseModel):
    task_id: UUID
    decision: RetrievalDecision
