from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from backend.app.db.models.enums import RunStatus


class RunBase(BaseModel):
    status: RunStatus = Field(default=RunStatus.QUEUED, description="Execution status")
    model_provider: Optional[str] = Field(default=None, description="Provider used, e.g. openai")
    model_name: Optional[str] = Field(default=None, description="Model identifier, e.g. gpt-4o-mini")
    input_tokens: Optional[int] = Field(default=None, ge=0)
    output_tokens: Optional[int] = Field(default=None, ge=0)
    total_tokens: Optional[int] = Field(default=None, ge=0)
    latency_ms: Optional[int] = Field(default=None, ge=0)
    error_message: Optional[str] = Field(default=None)
    input_snapshot: Optional[Dict[str, Any]] = Field(default=None, description="Snapshot of prompt & parameters sent to model")
    output_content: Optional[str] = Field(default=None, description="Full text output returned by LLM")
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)


class RunCreate(RunBase):
    pass


class RunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    task_id: UUID
    status: RunStatus
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    error_message: Optional[str] = None
    input_snapshot: Optional[Dict[str, Any]] = None
    output_content: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class RunListResponse(BaseModel):
    runs: List[RunResponse]
    total: int
