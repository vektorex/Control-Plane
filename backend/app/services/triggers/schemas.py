"""
Pydantic schemas for Step 23: Workflow Triggers and Event Automation.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TriggerType(str, Enum):
    MANUAL = "manual"
    SCHEDULE = "schedule"
    WEBHOOK = "webhook"
    CONNECTOR_EVENT = "connector_event"


class TriggerStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ARCHIVED = "archived"


class TriggerRunStatus(str, Enum):
    RECEIVED = "received"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class FilterOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    EXISTS = "exists"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_OR_EQUAL = "less_or_equal"


class FilterLogic(str, Enum):
    AND = "AND"
    OR = "OR"


class FilterRule(BaseModel):
    model_config = ConfigDict(extra="ignore")

    field: str = Field(..., description="Target field path, e.g. payload.repository.full_name or payload.issue.title")
    operator: FilterOperator = Field(..., description="Comparison operator")
    value: Optional[Any] = Field(default=None, description="Expected comparison value")


class FilterConfiguration(BaseModel):
    model_config = ConfigDict(extra="ignore")

    logic: FilterLogic = Field(default=FilterLogic.AND, description="AND or OR evaluation")
    rules: List[FilterRule] = Field(default_factory=list, description="List of filter conditions")


class ScheduleConfiguration(BaseModel):
    model_config = ConfigDict(extra="ignore")

    kind: str = Field(default="cron", description="cron or frequency")
    expression: str = Field(default="0 * * * *", description="Standard 5-part cron or frequency string")
    timezone: str = Field(default="UTC", description="IANA timezone name, e.g. Asia/Kolkata or UTC")


class RetryConfiguration(BaseModel):
    model_config = ConfigDict(extra="ignore")

    max_retries: int = Field(default=2, ge=0, le=10)
    backoff_factor: float = Field(default=2.0, ge=1.0, le=10.0)


class WorkflowTriggerCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    trigger_type: TriggerType = Field(...)
    project_id: Optional[uuid.UUID] = None
    workflow_version: Optional[int] = Field(default=None, ge=1)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    filter_configuration: Optional[FilterConfiguration] = None
    retry_configuration: Optional[RetryConfiguration] = Field(default_factory=RetryConfiguration)
    debounce_seconds: Optional[int] = Field(default=0, ge=0, le=3600)


class WorkflowTriggerUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: Optional[TriggerStatus] = None
    workflow_version: Optional[int] = Field(default=None, ge=1)
    configuration: Optional[Dict[str, Any]] = None
    filter_configuration: Optional[FilterConfiguration] = None
    retry_configuration: Optional[RetryConfiguration] = None
    debounce_seconds: Optional[int] = Field(default=None, ge=0, le=3600)


class WorkflowTriggerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: uuid.UUID
    workspace_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    workflow_id: uuid.UUID
    workflow_name: Optional[str] = None
    workflow_version: Optional[int] = None
    name: str
    description: Optional[str] = None
    trigger_type: TriggerType
    status: TriggerStatus
    configuration: Dict[str, Any]
    filter_configuration: Optional[Dict[str, Any]] = None
    retry_configuration: Dict[str, Any]
    public_trigger_id: Optional[str] = None
    has_webhook_secret: bool = False
    debounce_seconds: Optional[int] = 0
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    last_triggered_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0


class WorkflowTriggerListResponse(BaseModel):
    triggers: List[WorkflowTriggerResponse]
    total: int


class TriggerRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: uuid.UUID
    trigger_id: uuid.UUID
    workflow_run_id: Optional[uuid.UUID] = None
    workspace_id: uuid.UUID
    event_id: Optional[str] = None
    status: TriggerRunStatus
    idempotency_key: Optional[str] = None
    input_snapshot: Dict[str, Any]
    filter_result: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None


class TriggerRunListResponse(BaseModel):
    runs: List[TriggerRunResponse]
    total: int


class ManualTriggerRunRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    input_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TriggerTestRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sample_payload: Dict[str, Any] = Field(default_factory=dict)
    sample_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TriggerTestResponse(BaseModel):
    accepted: bool
    filter_matched: bool
    filter_details: Dict[str, Any]
    mapped_inputs: Dict[str, Any]
    policy_warnings: List[str]
    status: str


class WebhookSecretResponse(BaseModel):
    webhook_url: str
    secret: str
    message: str


class WebhookStatusResponse(BaseModel):
    configured: bool
    webhook_url: str
    public_trigger_id: str
    last_received_at: Optional[datetime] = None
