import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class DatasetStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class TargetType(str, Enum):
    TASK = "task"
    WORKFLOW = "workflow"
    WORKFLOW_VERSION = "workflow_version"
    MODEL = "model"
    PROMPT = "prompt"
    REPLAY_SNAPSHOT = "replay_snapshot"


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CaseRunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    ERROR = "error"
    CANCELLED = "cancelled"


class AssertionType(str, Enum):
    EXACT_MATCH = "exact_match"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    REGEX = "regex"
    JSON_FIELDS = "json_fields"
    CITATION_EXISTS = "citation_exists"
    CITATION_MATCHES_SOURCE = "citation_matches_source"
    GROUNDED_CLAIMS = "grounded_claims"
    REQUIRED_FIELDS = "required_fields"
    OUTPUT_FORMAT = "output_format"
    EVALUATOR_CHECK = "evaluator_check"
    ENTITY_EXISTS = "entity_exists"
    RELATIONSHIP_EXISTS = "relationship_exists"
    RELATIONSHIP_MATCHES_SOURCE = "relationship_matches_source"
    SOURCE_REFERENCE_EXISTS = "source_reference_exists"
    IMAGE_CLAIM_SUPPORTED = "image_claim_supported"
    TABLE_VALUE_CORRECT = "table_value_correct"
    TRANSCRIPT_GROUNDED = "transcript_grounded"
    SOURCE_TIMESTAMP_EXISTS = "source_timestamp_exists"
    VISUAL_EVIDENCE_PRESENT = "visual_evidence_present"
    ARTIFACT_REFERENCE_EXISTS = "artifact_reference_exists"
    CACHE_HIT = "cache_hit"
    CACHE_MATCH_TYPE = "cache_match_type"
    CACHE_ELIGIBILITY = "cache_eligibility"


class AssertionDefinition(BaseModel):
    """Definition of a deterministic assertion on an evaluation case."""
    type: AssertionType
    path: Optional[str] = Field(default=None, description="Optional dot-notated path for JSON outputs (e.g. 'summary' or 'output.text')")
    value: Optional[Any] = Field(default=None, description="Expected value, substring, or regex pattern")
    fields: Optional[List[str]] = Field(default=None, description="Required fields or keys for json_fields/required_fields")
    check_name: Optional[str] = Field(default=None, description="Evaluator check name for evaluator_check (e.g. 'grounding', 'safety')")
    threshold: Optional[float] = Field(default=None, description="Optional numerical threshold")
    negate: Optional[bool] = Field(default=False, description="Whether to invert the pass/fail result")
    description: Optional[str] = Field(default=None, description="Optional description of the assertion")


class AssertionResult(BaseModel):
    """Outcome of evaluating a single assertion."""
    assertion_type: str
    passed: bool
    status: str = Field(default="passed", description="passed | failed | warning | error")
    path: Optional[str] = None
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    message: str
    details: Optional[Dict[str, Any]] = None


# Evaluation Target
class EvaluationTarget(BaseModel):
    target_type: TargetType
    target_id: Optional[str] = None
    version: Optional[str] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)


# Dataset schemas
class EvaluationDatasetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    project_id: Optional[uuid.UUID] = None
    initial_version_description: Optional[str] = None


class EvaluationDatasetUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    status: Optional[DatasetStatus] = None


class EvaluationDatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    name: str
    description: Optional[str] = None
    version: int
    status: str
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    case_count: Optional[int] = 0
    active_version_id: Optional[uuid.UUID] = None


class EvaluationDatasetListResponse(BaseModel):
    items: List[EvaluationDatasetResponse]
    total: int


# Dataset Version schemas
class EvaluationDatasetVersionCreate(BaseModel):
    description: Optional[str] = None
    clone_from_version_id: Optional[uuid.UUID] = None


class EvaluationDatasetVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dataset_id: uuid.UUID
    version: int
    created_by: Optional[uuid.UUID] = None
    description: Optional[str] = None
    created_at: datetime
    case_count: Optional[int] = 0
    is_locked: Optional[bool] = False


# Evaluation Case schemas
class EvaluationCaseCreate(BaseModel):
    case_key: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    input_data: Dict[str, Any] = Field(default_factory=dict)
    expected_output: Optional[str] = None
    expected_context: Optional[Dict[str, Any]] = None
    expected_sources: Optional[List[Any]] = None
    assertions: List[AssertionDefinition] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvaluationCaseUpdate(BaseModel):
    name: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    expected_output: Optional[str] = None
    expected_context: Optional[Dict[str, Any]] = None
    expected_sources: Optional[List[Any]] = None
    assertions: Optional[List[AssertionDefinition]] = None
    metadata: Optional[Dict[str, Any]] = None


class EvaluationCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dataset_version_id: uuid.UUID
    case_key: str
    name: str
    input_data: Dict[str, Any]
    expected_output: Optional[str] = None
    expected_context: Optional[Dict[str, Any]] = None
    expected_sources: Optional[List[Any]] = None
    assertions: List[Dict[str, Any]]
    metadata: Dict[str, Any] = Field(default_factory=dict, validation_alias="case_metadata")
    created_at: datetime
    updated_at: datetime


class EvaluationCaseListResponse(BaseModel):
    items: List[EvaluationCaseResponse]
    total: int


# Experiment schemas
class EvaluationExperimentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    project_id: Optional[uuid.UUID] = None
    dataset_version_id: uuid.UUID
    target_type: TargetType
    target_configuration: Dict[str, Any] = Field(default_factory=dict)


class EvaluationExperimentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    dataset_version_id: uuid.UUID
    target_type: str
    target_configuration: Dict[str, Any]
    name: str
    description: Optional[str] = None
    status: str
    created_by: Optional[uuid.UUID] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    summary_stats: Optional[Dict[str, Any]] = None


class EvaluationExperimentListResponse(BaseModel):
    items: List[EvaluationExperimentResponse]
    total: int


class EvaluationExperimentRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    experiment_id: uuid.UUID
    case_id: uuid.UUID
    status: str
    input_snapshot: Dict[str, Any]
    output_snapshot: Optional[Dict[str, Any]] = None
    evaluation_result: Optional[Dict[str, Any]] = None
    run_id: Optional[uuid.UUID] = None
    workflow_run_id: Optional[uuid.UUID] = None
    latency_ms: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    estimated_cost: Optional[float] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class EvaluationExperimentRunListResponse(BaseModel):
    items: List[EvaluationExperimentRunResponse]
    total: int


# Case Result
class EvaluationCaseResult(BaseModel):
    case_id: uuid.UUID
    case_key: str
    case_name: str
    experiment_run_id: uuid.UUID
    status: str  # passed | failed | warning | error
    assertions: List[AssertionResult]
    evaluation_findings: List[Dict[str, Any]] = Field(default_factory=list)
    latency_ms: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    estimated_cost: Optional[float] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


# Comparison and Regression schemas
class EvaluationComparisonRequest(BaseModel):
    experiment_a: uuid.UUID
    experiment_b: uuid.UUID


class EvaluationComparisonResponse(BaseModel):
    experiment_a: Dict[str, Any]
    experiment_b: Dict[str, Any]
    summary: Dict[str, Any]
    case_differences: List[Dict[str, Any]]
    assertion_differences: List[Dict[str, Any]]
    evaluation_differences: List[Dict[str, Any]]
    latency_difference: Dict[str, Any]
    token_difference: Dict[str, Any]
    cost_difference: Dict[str, Any]
    regressions: List[Dict[str, Any]]


class RegressionItem(BaseModel):
    case_id: str
    case_key: str
    check: str
    baseline_result: Any
    candidate_result: Any
    reason: str


class RegressionCheckRequest(BaseModel):
    baseline_experiment: uuid.UUID
    candidate_experiment: uuid.UUID


class RegressionCheckResponse(BaseModel):
    regression_detected: bool
    regressions: List[RegressionItem]
    metrics_deltas: Dict[str, Any]
