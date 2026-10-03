"""
Pydantic contracts and schemas for Step 28: Prompt Management, Versioning, Release, and Experimentation.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


# -----------------------------------------------------------------------------
# Prompt Schemas
# -----------------------------------------------------------------------------

class PromptCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    key: str = Field(..., min_length=1, max_length=255, description="Unique prompt key (e.g. planner.execution_plan)")
    prompt_type: str = Field(default="instruction", description="system, instruction, task, planner, evaluator, transform, workflow")
    description: Optional[str] = None
    workspace_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    initial_content: Optional[str] = Field(default=None, description="Initial draft prompt content")
    initial_variable_schema: Optional[Dict[str, Any]] = None
    variable_schema: Optional[Dict[str, Any]] = None
    initial_model_requirements: Optional[Dict[str, Any]] = None
    initial_execution_config: Optional[Dict[str, Any]] = None
    change_summary: Optional[str] = None


class PromptUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    prompt_type: Optional[str] = None


class PromptReleaseSummary(BaseModel):
    environment: str
    version_id: uuid.UUID
    version_number: int
    released_at: datetime
    released_by: uuid.UUID


class PromptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    owner_user_id: uuid.UUID
    key: str
    name: str
    description: Optional[str] = None
    prompt_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None
    releases: Dict[str, Optional[PromptReleaseSummary]] = Field(default_factory=dict)
    latest_version: Optional[int] = None
    draft_version_id: Optional[uuid.UUID] = None


# -----------------------------------------------------------------------------
# Prompt Version Schemas
# -----------------------------------------------------------------------------

class PromptVersionCreateRequest(BaseModel):
    content: str = Field(..., min_length=1)
    variable_schema: Optional[Dict[str, Any]] = Field(default_factory=dict)
    model_requirements: Optional[Dict[str, Any]] = None
    execution_config: Optional[Dict[str, Any]] = None
    change_summary: Optional[str] = None


class PromptVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    prompt_id: uuid.UUID
    version_number: int
    status: str
    content: str
    variable_schema: Dict[str, Any] = Field(default_factory=dict)
    model_requirements: Optional[Dict[str, Any]] = None
    execution_config: Optional[Dict[str, Any]] = None
    change_summary: Optional[str] = None
    created_by: uuid.UUID
    created_at: datetime
    published_at: Optional[datetime] = None
    content_hash: Optional[str] = None


class PromptDiffResponse(BaseModel):
    prompt_id: uuid.UUID
    from_version_number: int
    to_version_number: int
    diff_unified: str
    diff_lines: List[str] = Field(default_factory=list)
    added_lines: List[str] = Field(default_factory=list)
    removed_lines: List[str] = Field(default_factory=list)
    variable_schema_changes: Dict[str, Any] = Field(default_factory=dict)
    execution_config_changes: Dict[str, Any] = Field(default_factory=dict)
    model_requirements_changes: Dict[str, Any] = Field(default_factory=dict)


# -----------------------------------------------------------------------------
# Prompt Release Schemas
# -----------------------------------------------------------------------------

class PromptReleaseRequest(BaseModel):
    environment: str = Field(..., description="development, staging, or production")
    version_id: uuid.UUID


class PromptReleaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    prompt_id: uuid.UUID
    environment: str
    version_id: uuid.UUID
    version_number: Optional[int] = None
    status: str
    released_by: uuid.UUID
    released_at: datetime
    previous_version_id: Optional[uuid.UUID] = None


class PromptRollbackRequest(BaseModel):
    environment: str = Field(..., description="Target release environment")
    target_version_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Explicit target version to roll back to. If None, rolls back to previous_version_id.",
    )


# -----------------------------------------------------------------------------
# Preview and Test Execution Schemas
# -----------------------------------------------------------------------------

class PromptPreviewRequest(BaseModel):
    version_id: Optional[uuid.UUID] = None
    content: Optional[str] = None
    variables: Dict[str, Any] = Field(default_factory=dict)
    variable_schema: Optional[Dict[str, Any]] = None


class PromptPreviewResponse(BaseModel):
    rendered_content: str
    is_valid: bool
    validation_result: Dict[str, Any] = Field(default_factory=dict)
    validation_errors: List[str] = Field(default_factory=list)
    estimated_tokens: int
    unresolved_variables: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    content_hash: str


class PromptTestExecutionRequest(BaseModel):
    version_id: Optional[uuid.UUID] = None
    variables: Dict[str, Any] = Field(default_factory=dict)
    model_override: Optional[str] = None
    temperature_override: Optional[float] = None
    max_tokens_override: Optional[int] = None
    evaluate: bool = False


class PromptTestExecutionResponse(BaseModel):
    prompt_id: uuid.UUID
    version_id: uuid.UUID
    version_number: int
    rendered_prompt: str
    output_text: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: int
    estimated_cost: float
    evaluation: Optional[Dict[str, Any]] = None
    telemetry: Dict[str, Any] = Field(default_factory=dict)


# -----------------------------------------------------------------------------
# Experiment Schemas
# -----------------------------------------------------------------------------

class PromptExperimentVariantInput(BaseModel):
    prompt_version_id: uuid.UUID
    label: str = Field(..., description="Neutral label: A, B, C, or neutral variant name")
    allocation_weight: float = Field(default=1.0, gt=0.0)


class PromptExperimentCreateRequest(BaseModel):
    prompt_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    allocation_key: str = Field(default="user_id", description="user_id, task_id, or workflow_run_id")
    workspace_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    variants: List[PromptExperimentVariantInput] = Field(default_factory=list, min_length=2)


class PromptExperimentUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PromptExperimentVariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    experiment_id: uuid.UUID
    prompt_version_id: uuid.UUID
    version_number: Optional[int] = None
    label: str
    allocation_weight: float
    created_at: datetime


class PromptExperimentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    prompt_id: uuid.UUID
    name: str
    description: Optional[str] = None
    status: str
    allocation_key: str
    created_by: uuid.UUID
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    variants: List[PromptExperimentVariantResponse] = Field(default_factory=list)


class VariantMetricResult(BaseModel):
    variant_id: uuid.UUID
    prompt_version_id: uuid.UUID
    version_number: Optional[int] = None
    label: str
    allocation_weight: float
    executions: int = 0
    passed_evaluations: int = 0
    failed_evaluations: int = 0
    warning_evaluations: int = 0
    total_tokens: int = 0
    avg_latency_ms: float = 0.0
    total_cost: float = 0.0
    format_compliance_rate: float = 1.0
    errors: int = 0


class PromptExperimentResultsResponse(BaseModel):
    experiment_id: uuid.UUID
    prompt_id: uuid.UUID
    name: str
    status: str
    total_executions: int
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    variants: List[VariantMetricResult] = Field(default_factory=list)
