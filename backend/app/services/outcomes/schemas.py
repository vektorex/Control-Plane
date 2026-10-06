"""
Pydantic schemas for Step 43:
AI Outcome Intelligence & Work Impact Layer.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ObjectiveBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    objective_type: str = Field(
        default="business",
        description="business, product, engineering, research, operations, security, compliance, personal, project",
    )
    priority: str = Field(default="medium", description="low, medium, high, critical")
    owner_user_id: Optional[str] = None
    requirements: Dict[str, Any] = Field(default_factory=dict)
    start_at: Optional[datetime] = None
    target_at: Optional[datetime] = None


class ObjectiveCreate(ObjectiveBase):
    project_id: Optional[str] = None


class ObjectiveUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    objective_type: Optional[str] = None
    status: Optional[str] = Field(None, description="draft, active, at_risk, completed, cancelled, archived")
    priority: Optional[str] = None
    owner_user_id: Optional[str] = None
    requirements: Optional[Dict[str, Any]] = None
    start_at: Optional[datetime] = None
    target_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class OutcomeTargetBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    metric_type: str = Field(
        default="count",
        description="count, percentage, duration, currency, boolean, rate, ratio, custom",
    )
    target_value: Optional[float] = None
    target_unit: Optional[str] = None
    baseline_value: Optional[float] = None
    target_date: Optional[datetime] = None
    measurement_source: str = Field(
        default="system",
        description="manual, system, connector, workflow, evaluation, event, artifact, document, external_reference",
    )


class OutcomeTargetCreate(OutcomeTargetBase):
    pass


class OutcomeTargetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_value: Optional[float] = None
    target_unit: Optional[str] = None
    baseline_value: Optional[float] = None
    current_value: Optional[float] = None
    target_date: Optional[datetime] = None
    measurement_source: Optional[str] = None
    status: Optional[str] = None


class OutcomeTargetResponse(OutcomeTargetBase):
    id: str
    objective_id: str
    current_value: Optional[float] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OutcomeMilestoneBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    due_at: Optional[datetime] = None
    owner_user_id: Optional[str] = None
    connected_resource_type: Optional[str] = None
    connected_resource_id: Optional[str] = None


class OutcomeMilestoneCreate(OutcomeMilestoneBase):
    pass


class OutcomeMilestoneUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = Field(None, description="planned, in_progress, blocked, completed, missed, cancelled")
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    owner_user_id: Optional[str] = None
    connected_resource_type: Optional[str] = None
    connected_resource_id: Optional[str] = None


class OutcomeMilestoneResponse(OutcomeMilestoneBase):
    id: str
    objective_id: str
    status: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OutcomeBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    outcome_type: str = Field(
        default="deliverable",
        description="deliverable, decision, resolution, optimization, risk_reduction, issue_resolution, research_finding, automation, approval, milestone, customer_outcome, operational_outcome, security_outcome",
    )
    owner_user_id: Optional[str] = None
    requirements: Dict[str, Any] = Field(default_factory=dict)


class OutcomeCreate(OutcomeBase):
    project_id: Optional[str] = None
    objective_id: Optional[str] = None


class OutcomeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    outcome_type: Optional[str] = None
    status: Optional[str] = Field(None, description="planned, in_progress, observed, verified, disputed, failed, cancelled")
    owner_user_id: Optional[str] = None
    requirements: Optional[Dict[str, Any]] = None


class OutcomeResponse(OutcomeBase):
    id: str
    workspace_id: str
    project_id: Optional[str] = None
    objective_id: Optional[str] = None
    status: str
    confidence: str
    created_by: str
    observed_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OutcomeEvidenceCreate(BaseModel):
    source_type: str
    source_id: str
    evidence_type: str
    description: str
    snapshot: Dict[str, Any] = Field(default_factory=dict)
    is_human_confirmed: bool = False
    is_ai_generated: bool = False
    observed_at: Optional[datetime] = None


class OutcomeEvidenceResponse(BaseModel):
    id: str
    outcome_id: str
    source_type: str
    source_id: str
    evidence_type: str
    description: str
    snapshot: Dict[str, Any]
    status: str
    is_human_confirmed: bool
    is_ai_generated: bool
    observed_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OutcomeMeasurementCreate(BaseModel):
    target_id: Optional[str] = None
    metric_name: str
    value: float
    unit: str
    measurement_source: str
    observed_at: Optional[datetime] = None
    evidence_id: Optional[str] = None


class OutcomeMeasurementResponse(BaseModel):
    id: str
    outcome_id: str
    target_id: Optional[str] = None
    metric_name: str
    value: float
    unit: str
    measurement_source: str
    observed_at: datetime
    evidence_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OutcomeWorkLinkCreate(BaseModel):
    resource_type: str
    resource_id: str
    relationship_type: str = "contributes_to"
    evidence_ids: List[str] = Field(default_factory=list)


class OutcomeWorkLinkResponse(BaseModel):
    id: str
    outcome_id: str
    resource_type: str
    resource_id: str
    relationship_type: str
    evidence_ids: List[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkDecisionCreate(BaseModel):
    project_id: Optional[str] = None
    objective_id: Optional[str] = None
    outcome_id: Optional[str] = None
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    decision_type: str = Field(
        default="human",
        description="human, AI_assisted, policy, workflow, agent, team",
    )
    decision_owner: str
    evidence_ids: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(
        default_factory=dict,
        description="For AI-assisted: agent_id, agent_version_id, run_id, model_provider, prompt_version, evaluation_id, approval_id",
    )


class WorkDecisionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = Field(None, description="proposed, under_review, approved, rejected, superseded")
    decision_owner: Optional[str] = None
    evidence_ids: Optional[List[str]] = None
    provenance: Optional[Dict[str, Any]] = None


class WorkDecisionResponse(BaseModel):
    id: str
    workspace_id: str
    project_id: Optional[str] = None
    objective_id: Optional[str] = None
    outcome_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    decision_type: str
    status: str
    decision_owner: str
    evidence_ids: List[str]
    provenance: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OutcomeAttributionCreate(BaseModel):
    resource_type: str
    resource_id: str
    attribution_type: str = Field(
        default="contributing",
        description="direct, supporting, contributing, blocking, unknown",
    )
    evidence_ids: List[str] = Field(default_factory=list)
    explanation: str
    attribution_source: str = "deterministic"
    attribution_confidence: str = "inferred"


class OutcomeAttributionResponse(BaseModel):
    id: str
    outcome_id: str
    resource_type: str
    resource_id: str
    attribution_type: str
    evidence_ids: List[str]
    explanation: str
    attribution_source: str
    attribution_confidence: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ImpactAnalysisCreate(BaseModel):
    analysis_type: str
    summary: str
    evidence_ids: List[str] = Field(default_factory=list)
    observations: List[Dict[str, Any]] = Field(default_factory=list)
    limitations: Optional[str] = None
    attribution_confidence: str = "observed"
    baseline_value: Optional[float] = None
    observed_value: Optional[float] = None
    difference_value: Optional[float] = None
    unit: Optional[str] = None


class ImpactAnalysisResponse(BaseModel):
    id: str
    outcome_id: str
    analysis_type: str
    summary: str
    evidence_ids: List[str]
    observations: List[Dict[str, Any]]
    limitations: Optional[str] = None
    attribution_confidence: str
    baseline_value: Optional[float] = None
    observed_value: Optional[float] = None
    difference_value: Optional[float] = None
    unit: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OutcomeHealthResponse(BaseModel):
    status: str
    is_healthy: bool
    reasons: List[str]
    checked_at: datetime
    details: Dict[str, Any] = Field(default_factory=dict)


class OutcomeVerifyRequest(BaseModel):
    evidence_ids: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    human_confirmed: bool = True


class OutcomeDisputeRequest(BaseModel):
    reason: str
    evidence_ids: List[str] = Field(default_factory=list)


class ObjectiveResponse(ObjectiveBase):
    id: str
    workspace_id: str
    project_id: Optional[str] = None
    status: str
    created_by: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ObjectiveDetailResponse(ObjectiveResponse):
    targets: List[OutcomeTargetResponse] = Field(default_factory=list)
    milestones: List[OutcomeMilestoneResponse] = Field(default_factory=list)
    outcomes: List[OutcomeResponse] = Field(default_factory=list)
    health: Optional[OutcomeHealthResponse] = None


class OutcomeDetailResponse(OutcomeResponse):
    objective: Optional[ObjectiveResponse] = None
    evidence: List[OutcomeEvidenceResponse] = Field(default_factory=list)
    work_links: List[OutcomeWorkLinkResponse] = Field(default_factory=list)
    measurements: List[OutcomeMeasurementResponse] = Field(default_factory=list)
    attributions: List[OutcomeAttributionResponse] = Field(default_factory=list)
    impact_analyses: List[ImpactAnalysisResponse] = Field(default_factory=list)
    health: Optional[OutcomeHealthResponse] = None


class OutcomeRecommendationResponse(BaseModel):
    recommendation_id: str
    outcome_id: Optional[str] = None
    objective_id: Optional[str] = None
    action_type: str  # continue_work, request_human_review, collect_missing_evidence, run_evaluation, run_simulation, assign_task, resolve_blocker, review_decision, reassess_objective, rollback_change
    title: str
    reason: str
    evidence_ids: List[str] = Field(default_factory=list)
    suggested_task: Optional[Dict[str, Any]] = None
    requires_approval: bool = True


class WorkMapNode(BaseModel):
    id: str
    label: str
    node_type: str  # objective, milestone, task, run, agent, artifact, evidence, outcome, measurement, decision
    status: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkMapEdge(BaseModel):
    source: str
    target: str
    relationship: str  # supports, contributes_to, achieved_by, produced, validated_by, measures, decided_by, blocks
    evidence_ids: List[str] = Field(default_factory=list)


class OutcomeWorkMapResponse(BaseModel):
    root_id: str
    root_type: str
    nodes: List[WorkMapNode]
    edges: List[WorkMapEdge]
