"""
Pydantic Schemas for Step 37: Public API, Developer Platform & SDK Layer.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Scope & Resource Scope Schemas
# ---------------------------------------------------------------------------

class ResourceScopeCreate(BaseModel):
    resource_scope_type: str = Field(default="organization", description="organization, workspace, or project")
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None


class ResourceScopeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    resource_scope_type: str
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Developer Application Schemas
# ---------------------------------------------------------------------------

class DeveloperApplicationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    environment: str = Field(default="development", description="development, staging, or production")


class DeveloperApplicationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, description="active, suspended, or revoked")


class DeveloperApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    name: str
    description: Optional[str] = None
    status: str
    environment: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DeveloperApplicationListResponse(BaseModel):
    applications: List[DeveloperApplicationResponse]
    total: int


# ---------------------------------------------------------------------------
# API Credential Schemas
# ---------------------------------------------------------------------------

class APICredentialCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    scopes: List[str] = Field(default_factory=list, description="Requested API permission scopes")
    resource_scope: Optional[ResourceScopeCreate] = None
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class APICredentialRotateRequest(BaseModel):
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class APICredentialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    application_id: str
    name: str
    key_prefix: str
    credential_type: str
    environment: str
    status: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_by: Optional[str] = None
    scopes: List[str] = Field(default_factory=list)
    resource_scopes: List[ResourceScopeResponse] = Field(default_factory=list)


class APICredentialCreatedResponse(APICredentialResponse):
    """
    Returned ONLY once at creation or rotation time. Contains the plaintext secret_key.
    """
    secret_key: str = Field(..., description="Plaintext API key. Displayed ONLY ONCE.")


class APICredentialListResponse(BaseModel):
    credentials: List[APICredentialResponse]
    total: int


# ---------------------------------------------------------------------------
# Quota Schemas
# ---------------------------------------------------------------------------

class APIQuotaCreate(BaseModel):
    resource_type: str = Field(..., description="requests, task_runs, workflow_runs, tokens, artifact_bytes, execution_seconds")
    limit: int = Field(..., gt=0)
    period: str = Field(default="minute", description="minute, hour, day, month")
    enabled: bool = True


class APIQuotaUpdate(BaseModel):
    limit: Optional[int] = Field(None, gt=0)
    period: Optional[str] = None
    enabled: Optional[bool] = None


class APIQuotaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    application_id: str
    resource_type: str
    limit: int
    period: str
    enabled: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Webhook Subscription Schemas
# ---------------------------------------------------------------------------

class WebhookSubscriptionCreate(BaseModel):
    url: str = Field(..., min_length=8, max_length=1024, description="Target HTTPS callback endpoint")
    events: List[str] = Field(..., min_length=1, description="Event types to subscribe to")


class WebhookSubscriptionUpdate(BaseModel):
    url: Optional[str] = Field(None, min_length=8, max_length=1024)
    events: Optional[List[str]] = None
    status: Optional[str] = Field(None, description="active, suspended")


class WebhookSubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    application_id: str
    organization_id: str
    url: str
    status: str
    events: List[str]
    created_at: datetime
    updated_at: datetime
    last_delivery_at: Optional[datetime] = None
    failure_count: int


class WebhookSubscriptionCreatedResponse(WebhookSubscriptionResponse):
    """
    Returned ONLY once at subscription creation. Contains plaintext webhook signing secret.
    """
    webhook_secret: str = Field(..., description="Plaintext secret for verifying HMAC signatures. Shown only once.")


class WebhookSubscriptionListResponse(BaseModel):
    webhooks: List[WebhookSubscriptionResponse]
    total: int


# ---------------------------------------------------------------------------
# Application Approval Schemas
# ---------------------------------------------------------------------------

class ApplicationApprovalReview(BaseModel):
    decision: str = Field(..., description="approved, rejected, revoked")
    notes: Optional[str] = None


class ApplicationApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    application_id: str
    organization_id: str
    requested_environment: str
    status: str
    requested_by: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Environment Config Schemas
# ---------------------------------------------------------------------------

class APIEnvironmentConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    environment: str
    require_approval: bool
    default_rate_limit_rpm: int
    default_rate_limit_rph: int
    max_payload_bytes: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Usage Telemetry Schemas
# ---------------------------------------------------------------------------

class APIUsageRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    application_id: str
    credential_id: str
    endpoint: str
    method: str
    status_code: int
    request_bytes: int
    response_bytes: int
    latency_ms: float
    tokens: Optional[int] = None
    cost: Optional[float] = None
    timestamp: datetime
    request_id: str
    run_id: Optional[str] = None


class APIUsageAggregateResponse(BaseModel):
    total_requests: int
    total_errors: int
    error_rate: float
    average_latency_ms: float
    total_tokens: int
    total_cost: float
    task_runs: int
    workflow_runs: int
    by_endpoint: Dict[str, int] = Field(default_factory=dict)
    by_status: Dict[str, int] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Public API Request & Response Contracts
# ---------------------------------------------------------------------------

class PublicTaskRunRequest(BaseModel):
    input: str = Field(..., description="Prompt or goal instructions for the task")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    stream: bool = False
    enable_web_search: bool = False


class PublicTaskRunResponse(BaseModel):
    run_id: str
    task_id: str
    status: str
    created_at: str
    links: Dict[str, str] = Field(default_factory=dict)


class PublicWorkflowRunRequest(BaseModel):
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Input parameters matching workflow definition")
    stream: bool = False


class PublicWorkflowRunResponse(BaseModel):
    run_id: str
    workflow_id: str
    status: str
    created_at: str
    links: Dict[str, str] = Field(default_factory=dict)


class PublicRunResultResponse(BaseModel):
    run_id: str
    status: str
    output: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


class PublicModelItem(BaseModel):
    provider: str
    model_id: str
    capabilities: List[str]
    context_window: int
    supports_streaming: bool
    supports_structured_output: bool
    supports_vision: bool
    availability_state: str


class PublicModelListResponse(BaseModel):
    models: List[PublicModelItem]


class PublicMemoryItem(BaseModel):
    id: str
    key: str
    content: str
    created_at: str
    tags: List[str] = Field(default_factory=list)


class PublicMemoryCreateRequest(BaseModel):
    key: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    tags: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Public Error Envelope
# ---------------------------------------------------------------------------

class PublicErrorDetail(BaseModel):
    type: str
    code: str
    message: str
    request_id: str
    details: Optional[Dict[str, Any]] = None


class PublicErrorResponse(BaseModel):
    error: PublicErrorDetail


# ---------------------------------------------------------------------------
# Developer Dashboard Overview
# ---------------------------------------------------------------------------

class DeveloperOverviewResponse(BaseModel):
    total_applications: int
    active_credentials: int
    active_webhooks: int
    total_requests_24h: int
    error_rate_24h: float
    average_latency_ms: float
    active_environments: List[str]
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list)
