import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class ReplayMode(str, Enum):
    INSPECT = "inspect"
    DRY_RUN = "dry_run"
    REPLAY = "replay"
    COMPARE = "compare"


class ReplayStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RetrievalReplayMode(str, Enum):
    LIVE_RETRIEVAL = "live_retrieval"
    SNAPSHOT_RETRIEVAL = "snapshot_retrieval"


class ExecutionSnapshot(BaseModel):
    """
    Deterministic, sanitized snapshot of an execution run or workflow run.
    Contains no secrets, authorization tokens, or sensitive credentials.
    """
    snapshot_version: str = Field(default="1.0", description="Snapshot format version")
    run_id: str = Field(..., description="Original run identifier")
    workflow_run_id: Optional[str] = Field(default=None, description="Original workflow run identifier if applicable")
    task_id: str = Field(..., description="Associated Task identifier")
    workspace_id: str = Field(..., description="Workspace boundary identifier")
    project_id: Optional[str] = Field(default=None, description="Project identifier if applicable")
    task_configuration: Dict[str, Any] = Field(default_factory=dict, description="Task instructions, title, and initial context")
    execution_requirements: Dict[str, Any] = Field(default_factory=dict, description="Resolved execution requirements from Task Intelligence")
    model_configuration: Dict[str, Any] = Field(default_factory=dict, description="Model, provider, temperature, and routing rules")
    retrieval_configuration: Dict[str, Any] = Field(default_factory=dict, description="Retrieval strategy, scope, top_k, and sources")
    tool_configuration: Dict[str, Any] = Field(default_factory=dict, description="Enabled tools, modes, and parameters")
    connector_configuration: Dict[str, Any] = Field(default_factory=dict, description="Active connectors and permissions (sanitized)")
    memory_configuration: Dict[str, Any] = Field(default_factory=dict, description="Memory mode and historical context bounds")
    evaluation_configuration: Dict[str, Any] = Field(default_factory=dict, description="Evaluation mode, verification policies, and format")
    workflow_version: Optional[int] = Field(default=None, description="Workflow version executed if applicable")
    relevant_context_metadata: Dict[str, Any] = Field(default_factory=dict, description="Sanitized context item metadata and sources")
    prompt_configuration: Optional[Dict[str, Any]] = Field(default=None, description="Captured prompt management snapshot (prompt_id, prompt_version_id, content_hash, release_environment)")
    trace_metadata: Dict[str, Any] = Field(default_factory=dict, description="High-level telemetry timestamps and counts")
    created_at: str = Field(..., description="Timestamp of snapshot creation")


class ReplayEligibility(BaseModel):
    """Result of replay eligibility check."""
    eligible: bool = Field(..., description="Whether the original run can be replayed")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings or reasons for ineligibility")


class ReplayRunCreateRequest(BaseModel):
    """Request payload to create a new execution replay."""
    mode: ReplayMode = Field(default=ReplayMode.DRY_RUN, description="Replay mode (inspect, dry_run, replay, compare)")
    dry_run: bool = Field(default=True, description="Enforce dry-run simulation for external side-effects")
    overrides: Optional[Dict[str, Any]] = Field(default=None, description="Safe user overrides (model, temperature, planner_mode, etc.)")
    retrieval_replay_mode: RetrievalReplayMode = Field(
        default=RetrievalReplayMode.LIVE_RETRIEVAL,
        description="Retrieval mode during replay (live_retrieval or snapshot_retrieval)",
    )


class ReplayStepRequest(BaseModel):
    """Request payload to replay a single individual step."""
    dry_run: bool = Field(default=True, description="Enforce dry-run simulation for external side-effects")
    overrides: Optional[Dict[str, Any]] = Field(default=None, description="Safe overrides for the step")


class FailureInsights(BaseModel):
    """Factual failure diagnostics for debugging."""
    failure_code: str = Field(..., description="Normalized error code")
    stage: str = Field(..., description="Execution pipeline stage where failure occurred")
    provider: Optional[str] = Field(default=None, description="Target AI provider if applicable")
    model: Optional[str] = Field(default=None, description="Target model if applicable")
    retry_attempts: int = Field(default=0, description="Number of retry attempts executed")
    fallback_attempts: int = Field(default=0, description="Number of fallback model attempts")
    duration_ms: Optional[int] = Field(default=None, description="Execution duration prior to failure")
    suggested_action: str = Field(..., description="Factual diagnostic recommendation")


class ReplayComparisonResult(BaseModel):
    """Factual comparison between original and replay executions."""
    replay_id: str
    original_run_id: str
    output_diff: Dict[str, Any] = Field(default_factory=dict)
    context_diff: Dict[str, Any] = Field(default_factory=dict)
    model_diff: Dict[str, Any] = Field(default_factory=dict)
    usage_diff: Dict[str, Any] = Field(default_factory=dict)
    evaluation_diff: Dict[str, Any] = Field(default_factory=dict)
    tool_diff: Dict[str, Any] = Field(default_factory=dict)
    determinism_indicators: Dict[str, Any] = Field(default_factory=dict)


class ReplayRunResponse(BaseModel):
    """API response representation of a ReplayRun."""
    id: uuid.UUID
    workspace_id: uuid.UUID
    original_run_id: uuid.UUID
    original_workflow_run_id: Optional[uuid.UUID] = None
    replay_mode: str
    status: str
    snapshot_version: str
    dry_run: bool
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    snapshot: Optional[Dict[str, Any]] = None
    replay_output: Optional[str] = None
    execution_steps: Optional[List[Dict[str, Any]]] = None
    comparison_id: Optional[uuid.UUID] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="replay_metadata",
    )
    created_by: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ReplayListResponse(BaseModel):
    """Paginated list of ReplayRun entries."""
    replays: List[ReplayRunResponse]
    total: int
    page: int
    limit: int
