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


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int
