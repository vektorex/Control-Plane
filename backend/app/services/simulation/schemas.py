"""
Pydantic Schemas for Step 41: AI Agent Simulation, Sandbox & Scenario Testing Layer.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SimulationStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class SimulationType(str, Enum):
    SINGLE_AGENT = "single_agent"
    AGENT_TEAM = "agent_team"
    WORKFLOW = "workflow"
    TASK = "task"
    REPLAY = "replay"
    SCENARIO_SUITE = "scenario_suite"


class TargetType(str, Enum):
    AGENT = "agent"
    AGENT_TEAM = "agent_team"
    WORKFLOW = "workflow"
    TASK = "task"
    REPLAY = "replay"


class EnvironmentMode(str, Enum):
    ISOLATED = "isolated"
    SNAPSHOT = "snapshot"
    SYNTHETIC = "synthetic"


class ScenarioType(str, Enum):
    NORMAL = "normal"
    EDGE_CASE = "edge_case"
    FAILURE = "failure"
    SECURITY = "security"
    ADVERSARIAL = "adversarial"
    REGRESSION = "regression"
    PERFORMANCE = "performance"
    POLICY = "policy"


class FaultDistributionMode(str, Enum):
    FIXED = "fixed"
    PERCENTAGE = "percentage"
    COUNT = "count"
    SEQUENCE = "sequence"


class ToolExecutionMode(str, Enum):
    REAL_READ_ONLY = "real_read_only"
    SYNTHETIC = "synthetic"
    BLOCKED = "blocked"
    RECORD_ONLY = "record_only"


class ConnectorExecutionMode(str, Enum):
    SNAPSHOT = "snapshot"
    SYNTHETIC = "synthetic"
    READ_ONLY = "read_only"
    BLOCKED = "blocked"


class WebSearchExecutionMode(str, Enum):
    LIVE_READ_ONLY = "live_read_only"
    SNAPSHOT = "snapshot"
    SYNTHETIC = "synthetic"
    DISABLED = "disabled"


class MemoryExecutionMode(str, Enum):
    EMPTY = "empty"
    SNAPSHOT = "snapshot"
    SYNTHETIC = "synthetic"


class KnowledgeExecutionMode(str, Enum):
    GRAPH_SNAPSHOT = "graph_snapshot"
    SYNTHETIC_GRAPH = "synthetic_graph"
    EMPTY_GRAPH = "empty_graph"


class ArtifactExecutionMode(str, Enum):
    SNAPSHOT = "snapshot"
    SYNTHETIC = "synthetic"
    READ_ONLY = "read_only"
    BLOCKED = "blocked"


# Aliases
SimulationEnvironmentMode = EnvironmentMode
SimulationExecutionMode = ToolExecutionMode


# --- Simulation CRUD Schemas ---

class SimulationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    slug: Optional[str] = Field(None, max_length=128)
    description: Optional[str] = None
    simulation_type: SimulationType = SimulationType.SINGLE_AGENT
    target_type: TargetType
    target_id: str
    target_version_id: Optional[str] = None
    project_id: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = Field(default_factory=dict)
    environment_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    scenario_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    fault_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    policy_overrides: Optional[Dict[str, Any]] = Field(default_factory=dict)
    assertions: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class SimulationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = None
    status: Optional[SimulationStatus] = None
    target_version_id: Optional[str] = None


class SimulationResponse(BaseModel):
    id: str
    workspace_id: str
    project_id: Optional[str] = None
    name: str
    slug: str
    description: Optional[str] = None
    status: str
    simulation_type: str
    target_type: str
    target_id: str
    target_version_id: Optional[str] = None
    current_version_id: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SimulationVersionCreate(BaseModel):
    configuration: Optional[Dict[str, Any]] = Field(default_factory=dict)
    environment_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    scenario_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    fault_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    policy_overrides: Optional[Dict[str, Any]] = Field(default_factory=dict)
    assertions: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    publish_immediately: bool = False


class SimulationVersionResponse(BaseModel):
    id: str
    simulation_id: str
    version: int
    configuration: Dict[str, Any]
    environment_config: Dict[str, Any]
    scenario_config: Dict[str, Any]
    fault_config: Dict[str, Any]
    policy_overrides: Dict[str, Any]
    assertions: List[Dict[str, Any]]
    created_by: str
    created_at: datetime
    published_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SimulationDetailResponse(SimulationResponse):
    versions: List[SimulationVersionResponse] = Field(default_factory=list)
    current_version: Optional[SimulationVersionResponse] = None


# --- Environment Schemas ---

class SimulationEnvironmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = None
    mode: EnvironmentMode = EnvironmentMode.ISOLATED
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SimulationEnvironmentResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: Optional[str] = None
    mode: str
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Scenario Schemas ---

class SimulationScenarioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = None
    scenario_type: ScenarioType = ScenarioType.NORMAL
    simulation_version_id: Optional[str] = None
    suite_id: Optional[str] = None
    input: Optional[Union[Dict[str, Any], str]] = Field(default_factory=dict)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    environment_state: Optional[Dict[str, Any]] = Field(default_factory=dict)
    expected_behavior: Optional[Dict[str, Any]] = Field(default_factory=dict)
    fault_configuration: Optional[Dict[str, Any]] = Field(default_factory=dict)
    assertions: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    @field_validator("input", mode="before")
    @classmethod
    def normalize_input(cls, v: Any) -> Any:
        if isinstance(v, str):
            return {"prompt": v}
        return v



class SimulationScenarioUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = None
    scenario_type: Optional[ScenarioType] = None
    input: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    environment_state: Optional[Dict[str, Any]] = None
    expected_behavior: Optional[Dict[str, Any]] = None
    fault_configuration: Optional[Dict[str, Any]] = None
    assertions: Optional[List[Dict[str, Any]]] = None


class SimulationScenarioResponse(BaseModel):
    id: str
    workspace_id: str
    simulation_version_id: Optional[str] = None
    suite_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    scenario_type: str
    input: Dict[str, Any]
    context: Dict[str, Any]
    environment_state: Dict[str, Any]
    expected_behavior: Dict[str, Any]
    fault_configuration: Dict[str, Any]
    assertions: List[Dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Fault Profile Schemas ---

class FaultProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = None
    faults: Dict[str, Any] = Field(default_factory=dict)
    distribution_mode: FaultDistributionMode = FaultDistributionMode.FIXED


class FaultProfileResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: Optional[str] = None
    faults: Dict[str, Any]
    distribution_mode: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FaultInjectionRecord(BaseModel):
    id: str
    run_id: str
    fault_type: str
    target: str
    parameters: Dict[str, Any]
    trigger_condition: Dict[str, Any]
    injected_at: datetime
    result: str

    model_config = ConfigDict(from_attributes=True)


# --- Assertion and Side Effect Schemas ---

class SimulationAssertionResponse(BaseModel):
    id: str
    run_id: str
    assertion_type: str
    parameters: Dict[str, Any]
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    passed: bool
    severity: str
    details: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SimulationSideEffectResponse(BaseModel):
    id: str
    run_id: str
    intended_action: str
    actor: str
    target: str
    parameters: Dict[str, Any]
    policy_decision: str
    would_require_approval: bool
    simulated_result: Dict[str, Any]
    intercepted_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Simulation Run Schemas ---

class SimulationRunCreate(BaseModel):
    simulation_version_id: Optional[str] = None
    scenario_id: Optional[str] = None
    seed: Optional[int] = 42
    target_version_id: Optional[str] = None
    environment_overrides: Optional[Dict[str, Any]] = None
    policy_overrides: Optional[Dict[str, Any]] = None
    fault_overrides: Optional[Dict[str, Any]] = None
    scenario_override: Optional[Dict[str, Any]] = None
    budget_limit: Optional[float] = None
    async_execution: bool = False


class SimulationRunResponse(BaseModel):
    id: str
    simulation_id: str
    simulation_version_id: Optional[str] = None
    scenario_id: Optional[str] = None
    suite_id: Optional[str] = None
    seed: int
    status: str
    target_type: str
    target_id: str
    target_version_id: Optional[str] = None
    environment_snapshot_id: Optional[str] = None
    execution_snapshot_id: Optional[str] = None
    policy_snapshot: Dict[str, Any]
    fault_snapshot: Dict[str, Any]
    output: Dict[str, Any]
    assertion_results: List[Dict[str, Any]]
    side_effects: List[Dict[str, Any]]
    events_count: int
    tool_calls: List[Dict[str, Any]]
    connector_calls: List[Dict[str, Any]]
    delegations: List[Dict[str, Any]]
    tokens: Dict[str, Any]
    cost: float
    latency: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    reproducibility_metadata: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SimulationRunDetailResponse(SimulationRunResponse):
    assertions_detail: List[SimulationAssertionResponse] = Field(default_factory=list)
    side_effects_detail: List[SimulationSideEffectResponse] = Field(default_factory=list)
    fault_injections_detail: List[FaultInjectionRecord] = Field(default_factory=list)


# --- Simulation Suite Schemas ---

class SimulationSuiteCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = None
    target_type: TargetType
    target_id: str
    project_id: Optional[str] = None
    scenario_ids: Optional[List[str]] = Field(default_factory=list)


class SimulationSuiteResponse(BaseModel):
    id: str
    workspace_id: str
    project_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    target_type: str
    target_id: str
    status: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SimulationSuiteDetailResponse(SimulationSuiteResponse):
    scenarios: List[SimulationScenarioResponse] = Field(default_factory=list)


class SimulationSuiteRunRequest(BaseModel):
    target_version_id: Optional[str] = None
    seed: Optional[int] = 42
    rerun_failed_only: bool = False
    baseline_suite_run_id: Optional[str] = None


class SimulationSuiteRunResult(BaseModel):
    suite_id: str
    total_scenarios: int
    completed_scenarios: int
    failed_scenarios: int
    run_ids: List[str]
    runs: List[SimulationRunResponse]
    regressions_detected: List[Dict[str, Any]] = Field(default_factory=list)


# --- Comparison and Report Schemas ---

class SimulationComparisonRequest(BaseModel):
    comparison_run_id: str


class SimulationComparisonResponse(BaseModel):
    id: str
    workspace_id: str
    baseline_run_id: str
    comparison_run_id: str
    factual_differences: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SimulationReportResponse(BaseModel):
    simulation_id: str
    run_id: str
    executive_summary: Dict[str, Any]
    scenario: Dict[str, Any]
    target: Dict[str, Any]
    environment: Dict[str, Any]
    execution_trace: List[Dict[str, Any]]
    policy_decisions: List[Dict[str, Any]]
    faults_injected: List[Dict[str, Any]]
    agent_behavior: Dict[str, Any]
    team_behavior: Optional[Dict[str, Any]] = None
    side_effects_intercepted: List[Dict[str, Any]]
    assertions: List[Dict[str, Any]]
    security_findings: List[Dict[str, Any]]
    evaluation_findings: List[Dict[str, Any]]
    resource_usage: Dict[str, Any]
    differences: Optional[Dict[str, Any]] = None
    reproducibility_metadata: Dict[str, Any]
