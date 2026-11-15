"""
Pydantic schemas for Step 34: AI Security Operations, Threat Detection & Incident Response Layer.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Normalized Security Event Schema
# ---------------------------------------------------------------------------

class SecurityEventNormalized(BaseModel):
    """
    Normalized security event abstraction fed into the SecurityDetectionEngine.
    """
    organization_id: str
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None

    actor_type: Optional[str] = "user"
    actor_id: Optional[str] = None

    resource_type: Optional[str] = None
    resource_id: Optional[str] = None

    action: str
    result: str = "success"  # success, denied, failed, blocked, rate_limited

    source_type: str = "api"  # auth, rbac, governance, gateway, tool, connector, workflow, job, trigger, artifact, memory, cache
    source_id: Optional[str] = None

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None

    payload: Dict[str, Any] = Field(default_factory=dict)
    risk_metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Security Signal Schemas
# ---------------------------------------------------------------------------

class SecuritySignalCreate(BaseModel):
    organization_id: str
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    signal_type: str
    source_type: str
    source_id: Optional[str] = None
    actor_type: Optional[str] = None
    actor_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    severity: str = "low"  # info, low, medium, high, critical
    confidence: float = 1.0
    timestamp: Optional[datetime] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    metadata_payload: Dict[str, Any] = Field(default_factory=dict, alias="metadata")


class SecuritySignalUpdate(BaseModel):
    status: Optional[str] = None
    severity: Optional[str] = None
    metadata_payload: Optional[Dict[str, Any]] = Field(None, alias="metadata")


class SecuritySignalResponse(BaseModel):
    id: str
    organization_id: str
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    signal_type: str
    source_type: str
    source_id: Optional[str] = None
    actor_type: Optional[str] = None
    actor_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    severity: str
    confidence: float
    timestamp: datetime
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="metadata_payload")
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


# ---------------------------------------------------------------------------
# Incident Schemas
# ---------------------------------------------------------------------------

class SecurityIncidentCreate(BaseModel):
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    category: str = "unknown"
    severity: str = "medium"
    assigned_to: Optional[str] = None
    signal_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SecurityIncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    resolution_summary: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SecurityIncidentResponse(BaseModel):
    id: str
    organization_id: str
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    category: str
    severity: str
    status: str
    detected_at: datetime
    first_seen_at: datetime
    last_seen_at: datetime
    assigned_to: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_summary: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="metadata_payload")
    signal_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


# ---------------------------------------------------------------------------
# Incident Timeline & Investigation Schemas
# ---------------------------------------------------------------------------

class IncidentTimelineEventResponse(BaseModel):
    id: str
    incident_id: str
    timestamp: datetime
    event_type: str
    source_type: str
    source_id: Optional[str] = None
    actor_type: Optional[str] = None
    actor_id: Optional[str] = None
    summary: str
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="metadata_payload")

    class Config:
        from_attributes = True
        populate_by_name = True


class IncidentInvestigationResponse(BaseModel):
    incident: SecurityIncidentResponse
    signals: List[SecuritySignalResponse] = Field(default_factory=list)
    timeline: List[IncidentTimelineEventResponse] = Field(default_factory=list)
    related_assets: List[Dict[str, Any]] = Field(default_factory=list)
    governance_decisions: List[Dict[str, Any]] = Field(default_factory=list)
    compliance_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    containment_actions: List[Dict[str, Any]] = Field(default_factory=list)
    affected_actors: List[str] = Field(default_factory=list)
    affected_classifications: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Containment Schemas
# ---------------------------------------------------------------------------

class ContainmentActionCreate(BaseModel):
    action_type: str  # pause_workflow, pause_trigger, cancel_job, disable_connector_credential, revoke_session, quarantine_artifact, invalidate_cache, require_approval
    target_type: str
    target_id: str
    reason: str


class ContainmentActionResponse(BaseModel):
    id: str
    incident_id: str
    action_type: str
    target_type: str
    target_id: str
    status: str
    requested_by: str
    approved_by: Optional[str] = None
    requested_at: datetime
    completed_at: Optional[datetime] = None
    result: Dict[str, Any] = Field(default_factory=dict)
    reason: str

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Security Indicator Schemas
# ---------------------------------------------------------------------------

class SecurityIndicatorCreate(BaseModel):
    indicator_type: str
    value_display: str
    source: str
    confidence: float = 1.0
    status: str = "active"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SecurityIndicatorResponse(BaseModel):
    id: str
    organization_id: str
    indicator_type: str
    value_hash: str
    value_display: str
    source: str
    confidence: float
    first_seen_at: datetime
    last_seen_at: datetime
    status: str
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="metadata_payload")

    class Config:
        from_attributes = True
        populate_by_name = True


# ---------------------------------------------------------------------------
# Security Playbook Schemas
# ---------------------------------------------------------------------------

class SecurityPlaybookCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_conditions: Dict[str, Any] = Field(default_factory=dict)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    enabled: bool = True


class SecurityPlaybookUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_conditions: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    enabled: Optional[bool] = None


class SecurityPlaybookResponse(BaseModel):
    id: str
    organization_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    trigger_conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    enabled: bool
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlaybookTestRequest(BaseModel):
    signal_type: str = "prompt_injection"
    severity: str = "high"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PlaybookTestResponse(BaseModel):
    matched: bool
    reasons: List[str] = Field(default_factory=list)
    planned_actions: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Overview & Statistics Schemas
# ---------------------------------------------------------------------------

class SecurityOverviewResponse(BaseModel):
    open_incidents_count: int = 0
    critical_signals_count: int = 0
    high_signals_count: int = 0
    recent_signals_count: int = 0
    active_indicators_count: int = 0
    active_playbooks_count: int = 0
    pending_containments_count: int = 0
    signals_by_category: Dict[str, int] = Field(default_factory=dict)
    incidents_by_severity: Dict[str, int] = Field(default_factory=dict)


class SecurityStatisticsResponse(BaseModel):
    total_signals: int = 0
    total_incidents: int = 0
    contained_incidents: int = 0
    resolved_incidents: int = 0
    avg_resolution_time_seconds: Optional[float] = None
    containment_actions_by_type: Dict[str, int] = Field(default_factory=dict)
    detectors_trigger_counts: Dict[str, int] = Field(default_factory=dict)
