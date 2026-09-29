import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ExecutionTraceEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    run_id: uuid.UUID
    workspace_id: uuid.UUID
    sequence_number: int
    event_type: str
    step_type: Optional[str] = None
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_json", serialization_alias="metadata")
    error_code: Optional[str] = None
    created_at: datetime



class RunTelemetryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    run_id: uuid.UUID
    workspace_id: uuid.UUID
    task_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: str
    provider: Optional[str] = None
    planner_model: Optional[str] = None
    generation_model: Optional[str] = None
    evaluator_model: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: Optional[float] = None
    retrieval_calls: int = 0
    retrieval_results: int = 0
    tool_calls: int = 0
    tools_used: Optional[List[str]] = None
    execution_steps: int = 0
    planner_duration_ms: int = 0
    retrieval_duration_ms: int = 0
    tool_duration_ms: int = 0
    generation_duration_ms: int = 0
    evaluation_duration_ms: int = 0
    revision_attempts: int = 0
    evaluation_status: Optional[str] = None
    error_code: Optional[str] = None
    error_message_safe: Optional[str] = None
    created_at: datetime


class UsageRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    run_id: uuid.UUID
    provider: str
    model: str
    operation: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cached_input_tokens: int = 0
    estimated_cost: Optional[float] = None
    usage_source: str = "provider"
    created_at: datetime


class PeriodFilter(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None


class RunsMetric(BaseModel):
    total: int = 0
    successful: int = 0
    failed: int = 0
    success_rate: float = 0.0


class TokensMetric(BaseModel):
    input: int = 0
    output: int = 0
    total: int = 0


class CostMetric(BaseModel):
    estimated: Optional[float] = None
    currency: str = "USD"
    source: str = "configured_pricing"


class LatencyMetric(BaseModel):
    average_ms: Optional[float] = None
    p50_ms: Optional[float] = None
    p95_ms: Optional[float] = None


class EvaluationMetric(BaseModel):
    passed: int = 0
    warning: int = 0
    failed: int = 0
    total_evaluated: int = 0
    revision_attempts: int = 0


class AnalyticsOverviewResponse(BaseModel):
    period: PeriodFilter
    runs: RunsMetric
    tokens: TokensMetric
    cost: CostMetric
    latency: LatencyMetric
    evaluation: EvaluationMetric


class UsageDataPoint(BaseModel):
    date: str
    runs: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: Optional[float] = None


class AnalyticsUsageResponse(BaseModel):
    period: PeriodFilter
    points: List[UsageDataPoint]
    total_tokens: int = 0
    total_cost: Optional[float] = None


class ModelUsageStat(BaseModel):
    model: str
    provider: str
    display_name: Optional[str] = None
    runs: int = 0
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: Optional[float] = None
    avg_latency_ms: Optional[float] = None
    p50_latency_ms: Optional[float] = None
    p95_latency_ms: Optional[float] = None
    failures: int = 0
    capabilities: List[str] = Field(default_factory=list)


class AnalyticsModelResponse(BaseModel):
    models: List[ModelUsageStat]


class ProviderUsageStat(BaseModel):
    provider: str
    runs: int = 0
    total_tokens: int = 0
    estimated_cost: Optional[float] = None
    failures: int = 0


class AnalyticsProviderResponse(BaseModel):
    providers: List[ProviderUsageStat]


class LatencyStageBreakdown(BaseModel):
    stage: str
    avg_duration_ms: float = 0.0
    p50_duration_ms: float = 0.0
    p95_duration_ms: float = 0.0


class AnalyticsLatencyResponse(BaseModel):
    overall: LatencyMetric
    stages: List[LatencyStageBreakdown]


class AnalyticsEvaluationResponse(BaseModel):
    passed: int = 0
    warning: int = 0
    failed: int = 0
    total: int = 0
    pass_rate: float = 0.0
    revision_attempts: int = 0


class ObservabilityCleanupResponse(BaseModel):
    workspace_id: uuid.UUID
    retention_days: int
    deleted_trace_events: int = 0
    deleted_usage_records: int = 0
    deleted_telemetry_records: int = 0
    message: str
