"""
Pydantic schemas for Step 45: Control Tower & Unified Command Center.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# Attention
# ---------------------------------------------------------------------------

ATTENTION_TYPES = [
    "approval_required", "job_failed", "workflow_failed", "task_failed",
    "agent_failed", "agent_waiting", "team_conflict", "objective_at_risk",
    "outcome_blocked", "outcome_stale", "plan_stale", "planning_conflict",
    "security_incident", "governance_block", "simulation_failure",
    "regression_detected", "recovery_required", "connector_failure",
    "evaluation_failure", "budget_warning", "capacity_conflict",
    "data_governance_request", "notification_failure",
]

SEVERITY_LEVELS = ["critical", "high", "medium", "low", "info"]
ATTENTION_STATUSES = ["open", "acknowledged", "resolved", "dismissed", "expired"]

ACTOR_TYPES = ["HUMAN", "AI_AGENT", "AI_TEAM", "SYSTEM", "INTEGRATION"]


class AttentionItemCreate(BaseModel):
    workspace_id: str
    project_id: Optional[str] = None
    source_type: str
    source_id: str
    attention_type: str
    severity: str
    title: str
    description: Optional[str] = None
    reason: Optional[str] = None
    evidence_ids: List[str] = Field(default_factory=list)


class AttentionItemResponse(BaseModel):
    id: str
    workspace_id: str
    project_id: Optional[str]
    source_type: str
    source_id: str
    attention_type: str
    severity: str
    title: str
    description: Optional[str]
    reason: Optional[str]
    evidence_ids: List[str]
    status: str
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttentionAcknowledgeRequest(BaseModel):
    user_id: str


# ---------------------------------------------------------------------------
# Control Tower View
# ---------------------------------------------------------------------------

class ControlTowerViewCreate(BaseModel):
    name: str
    description: Optional[str] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)
    is_shared: bool = False
    shared_with_workspace: bool = False
    project_id: Optional[str] = None


class ControlTowerViewUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    is_shared: Optional[bool] = None
    shared_with_workspace: Optional[bool] = None


class ControlTowerViewResponse(BaseModel):
    id: str
    workspace_id: str
    project_id: Optional[str]
    name: str
    description: Optional[str]
    configuration: Dict[str, Any]
    is_shared: bool
    shared_with_workspace: bool
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Workstream
# ---------------------------------------------------------------------------

class WorkstreamCreate(BaseModel):
    name: str
    description: Optional[str] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)
    project_id: Optional[str] = None


class WorkstreamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None


class WorkstreamResponse(BaseModel):
    id: str
    workspace_id: str
    project_id: Optional[str]
    name: str
    description: Optional[str]
    configuration: Dict[str, Any]
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Overview / Snapshot
# ---------------------------------------------------------------------------

class SectionStatus(BaseModel):
    """Represents the status of one aggregated section."""
    available: bool
    data_freshness: str  # "live", "updated N seconds ago", "data_unavailable", "partial"
    fetched_at: Optional[datetime] = None
    count: Optional[int] = None
    extra: Optional[Dict[str, Any]] = None


class OverviewResponse(BaseModel):
    """Factual counts from existing source systems. No synthetic numbers."""
    workspace_id: str
    generated_at: datetime
    is_partial: bool  # True if some subsystems were unavailable
    partial_sections: List[str]  # Which sections had issues
    sections: Dict[str, SectionStatus]


# ---------------------------------------------------------------------------
# Activity Feed
# ---------------------------------------------------------------------------

class ActivityItem(BaseModel):
    event_id: str
    event_type: str
    actor_type: str  # HUMAN | AI_AGENT | AI_TEAM | SYSTEM | INTEGRATION
    actor_id: Optional[str]
    source_type: str
    source_id: str
    workspace_id: str
    project_id: Optional[str]
    timestamp: datetime
    summary: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ActivityFeedResponse(BaseModel):
    items: List[ActivityItem]
    total: int
    cursor: Optional[str] = None
    data_freshness: str


# ---------------------------------------------------------------------------
# Active Work
# ---------------------------------------------------------------------------

class ActiveWorkItem(BaseModel):
    type: str  # task | run | workflow | job | agent_run | team_run
    id: str
    title: str
    status: str
    actor_type: str
    actor_id: Optional[str]
    owner: Optional[str]
    resource: Optional[str]
    project_id: Optional[str]
    started_at: Optional[datetime]
    elapsed_seconds: Optional[int]
    current_stage: Optional[str]
    waiting_reason: Optional[str]
    source_url: Optional[str]  # navigation link to source system page


class ActiveWorkResponse(BaseModel):
    items: List[ActiveWorkItem]
    total: int
    data_freshness: str


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class SearchResult(BaseModel):
    type: str
    id: str
    title: str
    description: Optional[str]
    status: Optional[str]
    workspace_id: str
    project_id: Optional[str]
    updated_at: Optional[datetime]
    permissions: List[str] = Field(default_factory=list)
    source: str  # which backend system returned this
    source_url: Optional[str]


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total: int
    by_type: Dict[str, int] = Field(default_factory=dict)
    elapsed_ms: int


# ---------------------------------------------------------------------------
# Briefing
# ---------------------------------------------------------------------------

class BriefingRequest(BaseModel):
    mode: str = "standard"  # brief | standard | detailed
    project_id: Optional[str] = None
    since_hours: int = 24


class BriefingStatement(BaseModel):
    type: str  # observed | derived | recommendation
    text: str
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    source_label: Optional[str] = None


class BriefingResponse(BaseModel):
    mode: str
    generated_at: datetime
    statements: List[BriefingStatement]
    ai_generated: bool = True
    # Clear label: AI-generated summaries must be distinguishable
    disclaimer: str = (
        "AI-generated summary of authorized facts. Verify critical decisions from source records."
    )
    source_references: List[Dict[str, str]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Recommendation
# ---------------------------------------------------------------------------

class ControlTowerRecommendation(BaseModel):
    id: str
    title: str
    reason: str
    source_type: str
    source_id: str
    evidence: List[str]
    risk: str
    required_permission: Optional[str]
    action_endpoint: Optional[str]  # Link to existing domain API, never bypasses it


# ---------------------------------------------------------------------------
# Attention Analysis
# ---------------------------------------------------------------------------

class AttentionAnalysisRequest(BaseModel):
    workspace_id: str
    project_id: Optional[str] = None
    limit: int = 100


class AttentionAnalysisResponse(BaseModel):
    groups: List[Dict[str, Any]]  # Suggested groupings
    duplicates: List[List[str]]  # Groups of attention item IDs that may be duplicates
    related_items: List[Dict[str, Any]]  # Item relationships
    disclaimer: str = (
        "AI-suggested groupings. Critical security and safety items are never suppressed. "
        "No items were automatically closed."
    )
