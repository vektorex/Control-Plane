from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    QUESTION_ANSWERING = "question_answering"
    SUMMARIZATION = "summarization"
    RESEARCH = "research"
    CODING = "coding"
    DEBUGGING = "debugging"
    DOCUMENT_ANALYSIS = "document_analysis"
    DATA_ANALYSIS = "data_analysis"
    CONTENT_GENERATION = "content_generation"
    TRANSFORMATION = "transformation"
    EXTRACTION = "extraction"
    COMPARISON = "comparison"
    PLANNING = "planning"
    WORKFLOW_EXECUTION = "workflow_execution"
    UNKNOWN = "unknown"


class ExecutionMode(str, Enum):
    DIRECT = "direct"
    RETRIEVAL = "retrieval"
    TOOL_ASSISTED = "tool_assisted"
    ORCHESTRATED = "orchestrated"
    WORKFLOW = "workflow"


class ComplexityLevel(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class RequirementSource(str, Enum):
    USER = "user"
    DETERMINISTIC_RULE = "deterministic_rule"
    LLM_ANALYSIS = "llm_analysis"
    POLICY = "policy"


class RequirementValue(BaseModel):
    """
    Indicates a single requirement item, its origin source, and assessment confidence.
    """
    value: Any = Field(..., description="Resolved value of the requirement")
    source: RequirementSource = Field(default=RequirementSource.DETERMINISTIC_RULE, description="Origin source of this requirement")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score of this requirement (0.0 to 1.0)")


class TaskRequirements(BaseModel):
    """
    Structured execution requirements with fine-grained tracking of provenance and confidence.
    """
    memory_required: RequirementValue = Field(default_factory=lambda: RequirementValue(value=False))
    document_retrieval_required: RequirementValue = Field(default_factory=lambda: RequirementValue(value=False))
    web_search_required: RequirementValue = Field(default_factory=lambda: RequirementValue(value=False))
    connector_required: RequirementValue = Field(default_factory=lambda: RequirementValue(value=False))
    tools_required: RequirementValue = Field(default_factory=lambda: RequirementValue(value=False))
    retrieval_strategy: RequirementValue = Field(default_factory=lambda: RequirementValue(value=None))
    retrieval_scope: RequirementValue = Field(default_factory=lambda: RequirementValue(value="project"))
    multi_query_allowed: RequirementValue = Field(default_factory=lambda: RequirementValue(value=False))
    structured_output_required: RequirementValue = Field(default_factory=lambda: RequirementValue(value=False))
    vision_required: RequirementValue = Field(default_factory=lambda: RequirementValue(value=False))
    streaming_required: RequirementValue = Field(default_factory=lambda: RequirementValue(value=True))
    evaluation_required: RequirementValue = Field(default_factory=lambda: RequirementValue(value=False))
    evaluation_mode: RequirementValue = Field(default_factory=lambda: RequirementValue(value="off"))
    human_approval_required: RequirementValue = Field(default_factory=lambda: RequirementValue(value=False))
    workflow_required: RequirementValue = Field(default_factory=lambda: RequirementValue(value=False))
    model_capabilities: RequirementValue = Field(default_factory=lambda: RequirementValue(value=[]))
    max_execution_complexity: RequirementValue = Field(default_factory=lambda: RequirementValue(value=ComplexityLevel.SIMPLE.value))


class TaskAnalysisRequirementsSummary(BaseModel):
    """
    Summary dictionary of boolean requirements returned in TaskAnalysis.
    """
    memory: bool = False
    documents: bool = False
    web_search: bool = False
    connectors: bool = False
    tools: bool = False
    retrieval: bool = False
    evaluation: bool = False
    structured_output: bool = False
    human_approval: bool = False


class TaskAnalysis(BaseModel):
    """
    Output model of the task analysis containing classification, requirements,
    and user-safe explanations without exposing internal chain-of-thought.
    """
    task_type: TaskType = Field(default=TaskType.UNKNOWN, description="Classified task category")
    intent: str = Field(..., description="Concise statement of task intent")
    requirements: TaskAnalysisRequirementsSummary = Field(
        default_factory=TaskAnalysisRequirementsSummary,
        description="Boolean summary of identified execution requirements",
    )
    constraints: List[str] = Field(default_factory=list, description="Explicit or inferred constraints")
    suggested_execution_mode: ExecutionMode = Field(
        default=ExecutionMode.DIRECT,
        description="Suggested execution mode (direct, retrieval, tool_assisted, orchestrated, workflow)",
    )
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence score of the analysis")
    explanation: str = Field(..., description="Short user-safe explanation of why these requirements are suggested")
    detected_entities: List[str] = Field(default_factory=list, description="Keywords or entities detected in the task")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of analysis")


class ExecutionRequirements(BaseModel):
    """
    Production-grade bounded execution configuration passed to the Orchestrator.
    Authoritative configuration resolved by TaskRequirementResolver and validated by ExecutionRequirementsValidator.
    """
    execution_mode: str = Field(default=ExecutionMode.DIRECT.value, description="Final resolved execution mode")
    task_type: str = Field(default=TaskType.UNKNOWN.value, description="Final resolved task type")
    complexity: str = Field(default=ComplexityLevel.SIMPLE.value, description="Factual execution complexity (simple, moderate, complex)")
    retrieval: Dict[str, Any] = Field(
        default_factory=lambda: {
            "enabled": False,
            "strategy": None,
            "scope": "project",
            "multi_query": False,
            "top_k": 8,
        }
    )
    tools: Dict[str, Any] = Field(
        default_factory=lambda: {
            "enabled": False,
            "allowed_tools": [],
            "web_search": False,
        }
    )
    connectors: Dict[str, Any] = Field(
        default_factory=lambda: {
            "enabled": False,
            "required_providers": [],
        }
    )
    memory: Dict[str, Any] = Field(
        default_factory=lambda: {
            "enabled": False,
            "read_enabled": False,
            "write_candidate": False,
        }
    )
    model_requirements: Dict[str, Any] = Field(
        default_factory=lambda: {
            "capabilities": [],
            "min_context_tokens": 8000,
            "structured_output": False,
            "vision": False,
            "requires_tools": False,
        }
    )
    evaluation: Dict[str, Any] = Field(
        default_factory=lambda: {
            "enabled": False,
            "mode": "off",
        }
    )
    human_approval: Dict[str, Any] = Field(
        default_factory=lambda: {
            "required": False,
            "action_type": None,
        }
    )
    workflow: Dict[str, Any] = Field(
        default_factory=lambda: {
            "required": False,
            "workflow_id": None,
        }
    )
    streaming: bool = True
    structured_output: bool = False
    limits: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_tokens": 8000,
            "max_iterations": 3,
            "timeout_seconds": 60,
        }
    )
    version: str = "1.0"


# =============================================================================
# API Request & Response Schemas
# =============================================================================

class TaskAnalysisRequest(BaseModel):
    task: str = Field(..., min_length=1, description="Task prompt or instruction text")
    context: Optional[str] = Field(default=None, description="Optional background context text")
    mode: Optional[str] = Field(default="auto", description="Intelligence mode: auto | deterministic | llm | hybrid")
    task_id: Optional[UUID] = Field(default=None, description="Optional existing task ID")
    workspace_id: Optional[str] = Field(default=None, description="Optional workspace ID")


class TaskAnalysisResponse(BaseModel):
    analysis: TaskAnalysis
    requirements: TaskRequirements
    execution_mode: str
    complexity: str


class ExecutionPreviewResponse(BaseModel):
    task_type: str
    execution_mode: str
    complexity: str
    retrieval: Dict[str, Any]
    tools: Dict[str, Any]
    connectors: Dict[str, Any]
    memory: Dict[str, Any]
    model_requirements: Dict[str, Any]
    evaluation: Dict[str, Any]
    human_approval: Dict[str, Any]
    workflow: Dict[str, Any]
    limits: Dict[str, Any]
    explanation: str
