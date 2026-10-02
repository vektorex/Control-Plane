"""
Pydantic schemas for Step 24: Durable Background Job System.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.services.jobs.constants import JobEventType, JobPriority, JobStatus, JobType


class JobProgressUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    percentage: Optional[int] = Field(default=None, ge=0, le=100)
    current_step: Optional[str] = None
    completed_steps: Optional[int] = Field(default=None, ge=0)
    total_steps: Optional[int] = Field(default=None, ge=0)
    message: Optional[str] = None


class JobCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    job_type: JobType
    priority: JobPriority = Field(default=JobPriority.NORMAL)
    payload: Dict[str, Any] = Field(default_factory=dict)
    project_id: Optional[uuid.UUID] = None
    idempotency_key: Optional[str] = Field(default=None, max_length=255)
    parent_job_id: Optional[uuid.UUID] = None
    delay_seconds: Optional[int] = Field(default=0, ge=0, le=86400 * 30)
    max_attempts: Optional[int] = Field(default=3, ge=1, le=10)


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: uuid.UUID
    workspace_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    job_type: str
    status: str
    priority: Optional[str] = "normal"
    payload: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    attempts: Optional[int] = 0
    max_attempts: Optional[int] = 3
    available_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    lease_owner: Optional[str] = None
    lease_expires_at: Optional[datetime] = None
    heartbeat_at: Optional[datetime] = None
    idempotency_key: Optional[str] = None
    parent_job_id: Optional[uuid.UUID] = None
    progress: Dict[str, Any] = Field(default_factory=dict)
    created_by: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    queue_latency_ms: Optional[int] = None


class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int


class JobEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: uuid.UUID
    job_id: uuid.UUID
    workspace_id: uuid.UUID
    event_type: str
    status: str
    message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="metadata_json")
    created_at: datetime


class JobEventListResponse(BaseModel):
    events: List[JobEventResponse]
    total: int


class AsyncExecutionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    job_id: str
    status: str
    job_type: str
    created_at: datetime
    available_at: datetime
    poll_url: str
    cancel_url: str
    workflow_run_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class JobStatsResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    queued_count: int = 0
    running_count: int = 0
    retrying_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    cancelled_count: int = 0
    stale_leases_count: int = 0
    avg_queue_latency_ms: float = 0.0
    active_workers_count: int = 0
