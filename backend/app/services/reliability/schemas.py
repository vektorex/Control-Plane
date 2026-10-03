"""
Pydantic schemas for Step 35: AI Reliability, Resilience & Chaos Engineering Layer.
Uses Pydantic v2 model_config.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# 1. Component Schemas
# ---------------------------------------------------------------------------
class ReliabilityComponentCreate(BaseModel):
    organization_id: Optional[str] = None
    component_type: str = Field(..., description="api, worker, ai_gateway, model_provider, etc.")
    component_name: str
    version: Optional[str] = None
    status: str = "active"
    health_status: str = "healthy"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReliabilityComponentUpdate(BaseModel):
    status: Optional[str] = None
    health_status: Optional[str] = None
    version: Optional[str] = None
    last_heartbeat_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class ReliabilityComponentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: Optional[str] = None
    component_type: str
    component_name: str
    version: Optional[str] = None
    status: str
    health_status: str
    last_heartbeat_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    failure_count: int = 0
    success_count: int = 0
    metadata_payload: Dict[str, Any] = Field(default_factory=dict, alias="metadata")
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# 2. Dependency Health Schemas
# ---------------------------------------------------------------------------
class DependencyHealthCreate(BaseModel):
    component_id: str
    check_type: str = Field(..., description="connectivity, authentication, availability, latency, capacity, functional")
    status: str = "healthy"
    latency_ms: Optional[float] = None
    error_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DependencyHealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    component_id: str
    check_type: str
    status: str
    latency_ms: Optional[float] = None
    error_type: Optional[str] = None
    checked_at: datetime
    metadata_payload: Dict[str, Any] = Field(default_factory=dict, alias="metadata")


# ---------------------------------------------------------------------------
# 3. Checkpoint & Resume Schemas
# ---------------------------------------------------------------------------
class ExecutionCheckpointCreate(BaseModel):
    organization_id: str
    workspace_id: str
    project_id: str
    run_id: str
    workflow_run_id: Optional[str] = None
    job_id: Optional[str] = None
    step_id: Optional[str] = None
    sequence_number: int = 1
    checkpoint_type: str
    state_snapshot: Dict[str, Any] = Field(default_factory=dict)
    input_fingerprint: str
    context_fingerprint: str
    expires_at: Optional[datetime] = None


class ExecutionCheckpointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    workspace_id: str
    project_id: str
    run_id: str
    workflow_run_id: Optional[str] = None
    job_id: Optional[str] = None
    step_id: Optional[str] = None
    sequence_number: int
    checkpoint_type: str
    state_snapshot: Dict[str, Any]
    input_fingerprint: str
    context_fingerprint: str
    created_at: datetime
    expires_at: Optional[datetime] = None


class CheckpointResumeRequest(BaseModel):
    override_parameters: Optional[Dict[str, Any]] = None
    skip_completed_steps: bool = True
    reason: str = Field(..., description="Mandatory operational rationale for resuming execution")


class CheckpointResumeResponse(BaseModel):
    success: bool
    checkpoint_id: str
    resumed_from_step: Optional[str] = None
    execution_status: str
    verification_passed: bool
    governance_decision: str
    details: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# 4. Failure, Retry & Circuit Breaker Schemas
# ---------------------------------------------------------------------------
class FailureClassificationResult(BaseModel):
    classification: str
    retryable: bool
    recoverable: bool
    requires_human: bool
    recommended_action: str
    rationale: str


class RetryDecisionResult(BaseModel):
    should_retry: bool
    attempt_number: int
    max_attempts: int
    delay_seconds: float
    reason: str


class CircuitBreakerStateResponse(BaseModel):
    component: str
    state: str  # closed, open, half_open
    failure_count: int
    failure_threshold: int
    last_failure_at: Optional[datetime] = None
    cooldown_remaining_seconds: Optional[float] = None


class FallbackDecisionResult(BaseModel):
    fallback_used: bool
    original_target: str
    fallback_target: Optional[str] = None
    fallback_tier: Optional[str] = None  # alternate_model, alternate_provider, deterministic, degraded, safe_failure
    reason: str
    governance_verified: bool


class DegradationDecisionResult(BaseModel):
    degraded: bool
    degraded_components: List[str]
    mode: str
    allowed_by_policy: bool
    reasons: List[str]


# ---------------------------------------------------------------------------
# 5. Objectives & Budgets
# ---------------------------------------------------------------------------
class ReliabilityObjectiveCreate(BaseModel):
    organization_id: Optional[str] = None
    component_type: str
    component_name: str
    metric: str
    target: float
    window: str = "30d"
    enabled: bool = True


class ReliabilityObjectiveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: Optional[str] = None
    component_type: str
    component_name: str
    metric: str
    target: float
    window: str
    enabled: bool
    created_at: datetime
    updated_at: datetime


class ReliabilityBudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    component: str
    metric: str
    window: str
    allowed_failure_amount: float
    current_failure_amount: float
    enabled: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# 6. Chaos Experiment Schemas
# ---------------------------------------------------------------------------
class ChaosExperimentCreate(BaseModel):
    organization_id: str
    workspace_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    environment: str = "test"  # test, staging, sandbox, production
    target_type: str
    target_id: str
    failure_type: str
    duration_seconds: int = 60
    expected_behavior: str
    abort_conditions: Dict[str, Any] = Field(default_factory=dict)


class ChaosExperimentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    duration_seconds: Optional[int] = None
    expected_behavior: Optional[str] = None
    abort_conditions: Optional[Dict[str, Any]] = None


class ChaosObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    experiment_id: str
    run_id: Optional[str] = None
    timestamp: datetime
    metric: str
    value: Optional[float] = None
    expected_value: Optional[float] = None
    status: str
    metadata_payload: Dict[str, Any] = Field(default_factory=dict, alias="metadata")


class ChaosRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    experiment_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    outcome: Optional[str] = None
    error_summary: Optional[str] = None
    logs: List[Any] = Field(default_factory=list)
    metadata_payload: Dict[str, Any] = Field(default_factory=dict, alias="metadata")
    observations: List[ChaosObservationResponse] = Field(default_factory=list)


class ChaosExperimentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    workspace_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    environment: str
    target_type: str
    target_id: str
    failure_type: str
    duration_seconds: int
    expected_behavior: str
    abort_conditions: Dict[str, Any]
    status: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    runs: List[ChaosRunResponse] = Field(default_factory=list)


class ChaosExperimentSafetySummary(BaseModel):
    experiment_id: str
    environment: str
    target_type: str
    target_id: str
    failure_type: str
    duration_seconds: int
    is_production: bool
    requires_hitl_approval: bool
    governance_status: str
    blast_radius: str


# ---------------------------------------------------------------------------
# 7. Telemetry & Overview Schemas
# ---------------------------------------------------------------------------
class SystemHealthOverviewResponse(BaseModel):
    healthy_components: int
    degraded_components: int
    unavailable_components: int
    active_circuit_breakers_open: int
    recent_failures_24h: int
    active_checkpoints: int
    chaos_experiments_active: int
    component_breakdown: Dict[str, int] = Field(default_factory=dict)
    health_by_type: Dict[str, str] = Field(default_factory=dict)


class ReliabilityTelemetryResponse(BaseModel):
    timeframe_days: int
    total_checks: int
    overall_availability_pct: float
    average_latency_ms: float
    retry_count: int
    fallback_count: int
    checkpoint_resume_success_count: int
    checkpoint_resume_failure_count: int
    failures_by_category: Dict[str, int] = Field(default_factory=dict)
