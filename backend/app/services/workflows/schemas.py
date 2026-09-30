"""
Pydantic schemas for the Workflow System.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class StepType(str, Enum):
    INPUT = "input"
    CONTEXT = "context"
    RETRIEVE = "retrieve"
    TOOL = "tool"
    CONNECTOR = "connector"
    MEMORY = "memory"
    GENERATE = "generate"
    EVALUATE = "evaluate"
    TRANSFORM = "transform"
    CONDITION = "condition"
    OUTPUT = "output"



class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class WorkflowRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InputFieldType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


class InputFieldDefinition(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: str = "string"
    description: Optional[str] = None
    required: bool = True
    default: Optional[Any] = None


class WorkflowStepDefinition(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(..., description="Unique step identifier within the workflow definition")
    name: str = Field(..., description="Human-readable step name")
    type: StepType = Field(..., description="Step type")
    description: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict, description="Step configuration payload")
    enabled: bool = True
    on_failure: str = Field(default="fail", description="Action on failure: 'fail' | 'skip' | 'retry'")
    max_retries: int = Field(default=0, ge=0, le=2, description="Maximum retry attempts (0-2)")


class WorkflowDefinition(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    description: Optional[str] = None
    version: int = 1
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Optional[Dict[str, Any]] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)
    steps: List[WorkflowStepDefinition] = Field(default_factory=list)


# Workflow CRUD Schemas
class WorkflowCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    slug: Optional[str] = None
    project_id: Optional[UUID] = None
    input_schema: Optional[Dict[str, Any]] = Field(default_factory=dict)
    output_schema: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = Field(default_factory=dict)
    steps: Optional[List[WorkflowStepDefinition]] = Field(default_factory=list)


class WorkflowUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    project_id: Optional[UUID] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None
    status: Optional[WorkflowStatus] = None


class WorkflowDefinitionUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    steps: List[WorkflowStepDefinition] = Field(default_factory=list)
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None


class WorkflowStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    workflow_id: UUID
    step_order: int
    name: str
    description: Optional[str] = None
    step_type: str
    configuration: Dict[str, Any]
    enabled: bool
    created_at: datetime
    updated_at: datetime


class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    workspace_id: UUID
    project_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    slug: str
    status: str
    version: int
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None
    configuration: Dict[str, Any]
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    steps: List[WorkflowStepResponse] = Field(default_factory=list)
    runs_count: int = 0
    latest_run_status: Optional[str] = None


class WorkflowListResponse(BaseModel):
    workflows: List[WorkflowResponse]
    total: int


# Validation Schemas
class WorkflowValidationIssue(BaseModel):
    level: str = "error"  # error | warning
    step_id: Optional[str] = None
    field: Optional[str] = None
    message: str


class WorkflowValidationResponse(BaseModel):
    valid: bool
    issues: List[WorkflowValidationIssue] = Field(default_factory=list)
    step_count: int = 0
    tool_call_count: int = 0
    retrieval_call_count: int = 0


# Execution & Run Schemas
class WorkflowRunRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    input_data: Dict[str, Any] = Field(default_factory=dict)
    project_id: Optional[UUID] = None
    version: Optional[int] = None


class WorkflowStepRunResult(BaseModel):
    step_id: str
    step_name: str
    step_type: str
    status: str  # completed | failed | skipped
    duration_ms: int = 0
    output_summary: Optional[str] = None
    output_data: Optional[Any] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    workflow_id: UUID
    workflow_version: int
    workspace_id: UUID
    project_id: Optional[UUID] = None
    status: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    execution_state: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    workflow_name: Optional[str] = None
    step_results: List[WorkflowStepRunResult] = Field(default_factory=list)


class WorkflowRunListResponse(BaseModel):
    runs: List[WorkflowRunResponse]
    total: int


# Template Schemas
class WorkflowTemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    icon: str = "Workflow"
    definition: WorkflowDefinition


class WorkflowTemplateListResponse(BaseModel):
    templates: List[WorkflowTemplateResponse]
