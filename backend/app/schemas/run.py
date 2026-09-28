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
    context_item_count: Optional[int] = Field(default=None, ge=0, description="Total context items included in this execution")
    estimated_context_tokens: Optional[int] = Field(default=None, ge=0, description="Estimated token count of assembled context")
    context_truncated: Optional[bool] = Field(default=False, description="Whether context budget truncation occurred")
    context_sources: Optional[List[str]] = Field(default=None, description="List of unique context sources used")
    retrieval_enabled: Optional[bool] = Field(default=False, description="Whether hybrid document retrieval was executed")
    retrieved_chunk_count: Optional[int] = Field(default=None, ge=0, description="Count of retrieved chunks from knowledge base")
    retrieval_latency_ms: Optional[int] = Field(default=None, ge=0, description="Latency spent executing hybrid retrieval and reranking")
    retrieval_sources: Optional[List[Dict[str, Any]]] = Field(default=None, description="Retrieved source document references and scores")
    retrieval_mode: Optional[str] = Field(default=None, description="Retrieval routing mode used (auto, always, never)")
    retrieval_required: Optional[bool] = Field(default=None, description="Whether retrieval was deemed necessary by router")
    retrieval_strategy: Optional[str] = Field(default=None, description="Strategy selected by router (hybrid, vector, keyword, multi_query, none)")
    retrieval_scope: Optional[str] = Field(default=None, description="Scope selected by router (project, workspace)")
    retrieval_top_k: Optional[int] = Field(default=None, description="Top-K limit determined by router")
    retrieval_reason: Optional[str] = Field(default=None, description="Explanation for routing decision")
    retrieval_confidence: Optional[float] = Field(default=None, description="Confidence score of the routing decision (0.0 - 1.0)")
    tools_used: Optional[List[str]] = Field(default=None, description="List of external tools executed during run")
    tool_call_count: Optional[int] = Field(default=0, ge=0, description="Total count of tool executions")
    tool_latency_ms: Optional[int] = Field(default=0, ge=0, description="Total time spent in tool execution")
    tool_errors: Optional[List[Dict[str, Any]]] = Field(default=None, description="Errors encountered during tool calls")
    tool_executions: Optional[List[Dict[str, Any]]] = Field(default=None, description="Detailed records of tool executions")
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
    context_item_count: Optional[int] = None
    estimated_context_tokens: Optional[int] = None
    context_truncated: Optional[bool] = False
    context_sources: Optional[List[str]] = None
    retrieval_enabled: Optional[bool] = False
    retrieved_chunk_count: Optional[int] = None
    retrieval_latency_ms: Optional[int] = None
    retrieval_sources: Optional[List[Dict[str, Any]]] = None
    retrieval_mode: Optional[str] = None
    retrieval_required: Optional[bool] = None
    retrieval_strategy: Optional[str] = None
    retrieval_scope: Optional[str] = None
    retrieval_top_k: Optional[int] = None
    retrieval_reason: Optional[str] = None
    retrieval_confidence: Optional[float] = None
    tools_used: Optional[List[str]] = None
    tool_call_count: Optional[int] = 0
    tool_latency_ms: Optional[int] = 0
    tool_errors: Optional[List[Dict[str, Any]]] = None
    tool_executions: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class RunListResponse(BaseModel):
    runs: List[RunResponse]
    total: int

