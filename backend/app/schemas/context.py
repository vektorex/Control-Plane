from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class TaskContextBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Context title or identifier")
    content: str = Field(..., min_length=1, max_length=50000, description="Textual context content")
    source_type: str = Field(default="manual", max_length=50, description="Context source type (e.g. manual, system)")
    priority: int = Field(default=1, ge=0, le=100, description="Priority weight (0-100)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom metadata key-values")


class TaskContextCreate(TaskContextBase):
    pass


class TaskContextUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    content: Optional[str] = Field(default=None, min_length=1, max_length=50000)
    source_type: Optional[str] = Field(default=None, max_length=50)
    priority: Optional[int] = Field(default=None, ge=0, le=100)
    metadata: Optional[Dict[str, Any]] = None


class TaskContextResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    task_id: UUID
    source_type: str
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="metadata_json")
    priority: int
    estimated_tokens: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class TaskContextListResponse(BaseModel):
    contexts: List[TaskContextResponse]
    total: int
    total_estimated_tokens: int = 0


class ContextItemDTO(BaseModel):
    id: str
    source_type: str
    title: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    relevance_score: Optional[float] = None
    priority: int
    token_estimate: int
    created_at: datetime


class ContextInspectResponse(BaseModel):
    task_id: UUID
    items: List[ContextItemDTO]
    total_items: int
    estimated_tokens: int
    truncated: bool
    sources: List[str]
    max_context_tokens: int
    dropped_items_count: int = 0
    formatted_prompt_preview: Optional[str] = None
