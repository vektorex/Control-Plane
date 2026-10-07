"""
Pydantic V2 schemas for Step 44: AI Work Planning, Capacity & Resource Optimization Layer.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Work Plan Schemas
# ---------------------------------------------------------------------------

class WorkPlanBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    project_id: Optional[str] = None
    objective_id: Optional[str] = None
    planning_mode: str = "assisted"  # manual, assisted, optimized
    planning_horizon_start: Optional[datetime] = None
    planning_horizon_end: Optional[datetime] = None


class WorkPlanCreate(WorkPlanBase):
    pass


class WorkPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    planning_mode: Optional[str] = None
    planning_horizon_start: Optional[datetime] = None
    planning_horizon_end: Optional[datetime] = None
    status: Optional[str] = None


class WorkPlanResponse(WorkPlanBase):
    id: str
    workspace_id: str
    status: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Work Plan Version Schemas
# ---------------------------------------------------------------------------

class WorkPlanVersionCreate(BaseModel):
    plan_snapshot: Dict[str, Any] = Field(default_factory=dict)
    constraint_snapshot: Dict[str, Any] = Field(default_factory=dict)
    capacity_snapshot: Dict[str, Any] = Field(default_factory=dict)
    resource_snapshot: Dict[str, Any] = Field(default_factory=dict)


class WorkPlanVersionResponse(BaseModel):
    id: str
    work_plan_id: str
    version: int
    plan_snapshot: Dict[str, Any]
    constraint_snapshot: Dict[str, Any]
    capacity_snapshot: Dict[str, Any]
    resource_snapshot: Dict[str, Any]
    created_by: str
    created_at: datetime
    published_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Planning Item Schemas
# ---------------------------------------------------------------------------

class PlanningItemBase(BaseModel):
    resource_type: str  # task, workflow, agent_run, etc.
    resource_id: str
    name: str
    description: Optional[str] = None
    priority: str = "medium"
    estimated_duration: Optional[int] = None  # minutes
    estimated_cost: Optional[float] = None
    required_capabilities: List[str] = Field(default_factory=list)
    status: str = "planned"
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None


class PlanningItemCreate(PlanningItemBase):
    pass


class PlanningItemResponse(PlanningItemBase):
    id: str
    work_plan_version_id: str
    created_at: datetime
    updated_at: datetime
    is_estimate: bool = True
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Dependency Schemas
# ---------------------------------------------------------------------------

class PlanningDependencyCreate(BaseModel):
    predecessor_item_id: str
    successor_item_id: str
    dependency_type: str = "finish_to_start"  # finish_to_start, start_to_start, finish_to_finish, start_to_finish, blocks, requires, optional_after
    lag: int = 0


class PlanningDependencyResponse(BaseModel):
    id: str
    work_plan_version_id: str
    predecessor_item_id: str
    successor_item_id: str
    dependency_type: str
    lag: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Work Resource Schemas
# ---------------------------------------------------------------------------

class WorkResourceBase(BaseModel):
    resource_type: str  # human, agent, agent_team, workflow, tool, connector, system
    resource_ref: str
    name: str
    description: Optional[str] = None
    project_id: Optional[str] = None
    status: str = "active"
    capabilities: List[str] = Field(default_factory=list)
    availability_policy: Dict[str, Any] = Field(default_factory=dict)


class WorkResourceCreate(WorkResourceBase):
    pass


class WorkResourceResponse(WorkResourceBase):
    id: str
    workspace_id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Resource Availability Schemas
# ---------------------------------------------------------------------------

class ResourceAvailabilityCreate(BaseModel):
    start_at: datetime
    end_at: datetime
    capacity_units: float = 1.0
    reserved_units: float = 0.0
    source: str = "manual"  # manual, calendar, system, policy, derived, unknown


class ResourceAvailabilityResponse(BaseModel):
    id: str
    resource_id: str
    start_at: datetime
    end_at: datetime
    capacity_units: float
    reserved_units: float
    source: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Capacity Snapshot & Forecast Schemas
# ---------------------------------------------------------------------------

class CapacitySnapshotResponse(BaseModel):
    id: str
    workspace_id: str
    project_id: Optional[str] = None
    resource_id: str
    snapshot_at: datetime
    period_start: datetime
    period_end: datetime
    available_units: float
    reserved_units: float
    allocated_units: float
    remaining_units: float
    source: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CapacityReservationCreate(BaseModel):
    resource_id: str
    planning_item_id: Optional[str] = None
    start_at: datetime
    end_at: datetime
    units: float = 1.0


class CapacityReservationResponse(BaseModel):
    id: str
    resource_id: str
    planning_item_id: Optional[str] = None
    start_at: datetime
    end_at: datetime
    units: float
    status: str
    created_by: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Constraint Schemas
# ---------------------------------------------------------------------------

class PlanningConstraintCreate(BaseModel):
    constraint_type: str  # deadline, dependency, capacity, budget, approval, capability, security, etc.
    configuration: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 1
    hard_constraint: bool = True


class PlanningConstraintResponse(BaseModel):
    id: str
    work_plan_version_id: str
    constraint_type: str
    configuration: Dict[str, Any]
    priority: int
    hard_constraint: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Schedule Candidate Schemas
# ---------------------------------------------------------------------------

class ScheduleCandidateResponse(BaseModel):
    id: str
    work_plan_version_id: str
    name: str
    schedule: Dict[str, Any]
    assumptions: List[str]
    constraint_results: Dict[str, Any]
    resource_allocations: Dict[str, Any]
    estimated_duration: Optional[float] = None
    estimated_cost: Optional[float] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Blocker Schemas
# ---------------------------------------------------------------------------

class PlanningBlockerResponse(BaseModel):
    id: str
    work_plan_version_id: str
    planning_item_id: Optional[str] = None
    type: str
    description: str
    severity: str
    evidence_ids: List[str]
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Planning Scenario Schemas
# ---------------------------------------------------------------------------

class PlanningScenarioCreate(BaseModel):
    work_plan_id: str
    name: str
    description: Optional[str] = None
    modifications: Dict[str, Any] = Field(default_factory=dict)


class PlanningScenarioResponse(BaseModel):
    id: str
    workspace_id: str
    work_plan_id: str
    name: str
    description: Optional[str] = None
    modifications: Dict[str, Any]
    simulation_results: Dict[str, Any]
    comparison: Dict[str, Any]
    created_by: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Recommendation Schemas
# ---------------------------------------------------------------------------

class PlanningRecommendationResponse(BaseModel):
    id: str
    workspace_id: str
    work_plan_id: str
    recommendation_type: str
    description: str
    reason: str
    evidence_ids: List[str]
    affected_resources: List[str]
    affected_items: List[str]
    risk: Optional[str] = None
    assumptions: List[str]
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Forecast and Workload Schemas
# ---------------------------------------------------------------------------

class CapacityForecastResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    planned_demand: float
    available_capacity: float
    reserved_capacity: float
    remaining_capacity: float
    unknown_capacity_count: int
    is_forecast: bool = True
    sources: List[str]


class WorkloadSnapshotResponse(BaseModel):
    workspace_id: str
    project_id: Optional[str] = None
    resource_id: str
    resource_name: str
    resource_type: str
    scheduled_workload: float
    reserved_capacity: float
    remaining_capacity: float
    blocked_items_count: int
    overlapping_items_count: int


# ---------------------------------------------------------------------------
# Plan Generation & Validation Responses
# ---------------------------------------------------------------------------

class PlanGenerationRequest(BaseModel):
    planning_mode: str = "assisted"  # rules_only, ai_assisted, hybrid
    preferences: Dict[str, Any] = Field(default_factory=dict)


class PlanGenerationResult(BaseModel):
    work_plan_id: str
    version: int
    items_count: int
    dependencies_count: int
    candidates_count: int
    blockers_count: int
    recommendations_count: int
    candidates: List[ScheduleCandidateResponse]


class PlanValidationResult(BaseModel):
    is_valid: bool
    is_stale: bool
    cycle_detected: bool
    hard_violations: List[str]
    soft_violations: List[str]
    blockers: List[PlanningBlockerResponse]
    conflicts: List[Dict[str, Any]]


# ---------------------------------------------------------------------------
# Progress and Conflicts Schemas
# ---------------------------------------------------------------------------

class PlanProgressResponse(BaseModel):
    work_plan_id: str
    version: Optional[int] = None
    planned: int
    started: int
    blocked: int
    completed: int
    failed: int
    cancelled: int
    total_items: int
    is_derived_from_execution_state: bool = True
    completion_percentage_fabricated: bool = False


class PlanConflictItem(BaseModel):
    conflict_type: str
    affected_items: List[str]
    evidence: List[str]
    possible_resolutions: List[str]


class PlanConflictsResponse(BaseModel):
    work_plan_id: str
    version: Optional[int] = None
    conflicts: List[PlanConflictItem]
    conflict_count: int
