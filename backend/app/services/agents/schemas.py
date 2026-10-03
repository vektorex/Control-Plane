"""
Pydantic Schemas for Step 40: Governed AI Agent Runtime and Multi-Agent Teams.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


# ==============================================================================
# ENUMS
# ==============================================================================

class AgentStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ARCHIVED = "archived"


class AgentTeamStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ARCHIVED = "archived"


class AgentExecutionState(str, Enum):
    CREATED = "created"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    DELEGATING = "delegating"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TeamMemberRole(str, Enum):
    LEAD = "lead"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    BUILDER = "builder"
    REVIEWER = "reviewer"
    SPECIALIST = "specialist"
    EXECUTOR = "executor"


class AgentMessageType(str, Enum):
    TASK_ASSIGNMENT = "task_assignment"
    TASK_RESULT = "task_result"
    QUESTION = "question"
    ANSWER = "answer"
    STATUS_UPDATE = "status_update"
    HANDOFF = "handoff"
    REVIEW = "review"
    CORRECTION = "correction"
    FINAL_RESULT = "final_result"


class ConflictStatus(str, Enum):
    OPEN = "open"
    RESOLVED_BY_EVIDENCE = "resolved_by_evidence"
    RESOLVED_BY_REVIEW = "resolved_by_review"
    RESOLVED_BY_HUMAN = "resolved_by_human"
    UNRESOLVED = "unresolved"


# ==============================================================================
# POLICY CONFIG SCHEMAS
# ==============================================================================

class ModelPolicyConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    allowed_providers: List[str] = Field(default_factory=lambda: ["openai", "anthropic", "mock"])
    allowed_models: List[str] = Field(default_factory=lambda: ["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet", "mock-model"])
    preferred_model: str = "gpt-4o-mini"
    fallback_models: List[str] = Field(default_factory=lambda: ["mock-model"])
    temperature: float = 0.2
    max_output_tokens: int = 4096
    structured_output_requirement: bool = True
    vision_requirement: bool = False
    context_limits: int = 16384
    cost_limits: float = 2.0


class MemoryPolicyConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    memory_enabled: bool = True
    read_scopes: List[str] = Field(default_factory=lambda: ["agent", "project"])
    write_scopes: List[str] = Field(default_factory=lambda: ["agent"])
    retention_policy: str = "standard_90d"
    write_requires_approval: bool = False
    shared_memory_enabled: bool = False


class KnowledgePolicyConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    allowed_documents: List[str] = Field(default_factory=list)
    allowed_graph_scopes: List[str] = Field(default_factory=lambda: ["workspace"])
    allowed_projects: List[str] = Field(default_factory=list)
    allowed_context_sources: List[str] = Field(default_factory=lambda: ["documents", "knowledge_graph"])
    retrieval_mode: str = "hybrid"
    max_context_tokens: int = 8192


class ExecutionPolicyConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    max_steps: int = 15
    max_iterations: int = 10
    max_delegations: int = 3
    max_parallel_agents: int = 2
    max_runtime_seconds: int = 300
    max_tool_calls: int = 20
    max_connector_calls: int = 10
    max_context_tokens: int = 16384
    max_output_tokens: int = 4096
    max_cost: float = 5.0
    max_retries: int = 2
    allow_parallel_execution: bool = True
    allow_delegation: bool = True
    allow_agent_team: bool = True
    allow_external_actions: bool = False


class EvaluationPolicyConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    required_evaluations: List[str] = Field(
        default_factory=lambda: ["output_correctness", "grounding", "policy_compliance"]
    )
    min_score: float = 0.75
    block_on_failure: bool = True


class ApprovalPolicyConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    requires_approval_for_tools: List[str] = Field(default_factory=list)
    requires_approval_for_connectors: List[str] = Field(default_factory=list)
    requires_approval_for_delegation: bool = False
    requires_approval_for_external_actions: bool = True
    requires_approval_for_memory_write: bool = False
    min_approvers: int = 1


class BudgetPolicyConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    max_budget_per_run: float = 5.0
    currency: str = "USD"
    alert_threshold: float = 0.8


# ==============================================================================
# AGENT SCHEMAS
# ==============================================================================

class AgentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    slug: Optional[str] = None
    description: Optional[str] = None
    purpose: str = Field(..., min_length=5)
    project_id: Optional[str] = None
    # Initial version config
    instructions: str = Field(default="You are a bounded, governed AI agent assisting with structured tasks.")
    model_policy: Optional[ModelPolicyConfig] = None
    capability_policy: List[str] = Field(default_factory=lambda: ["task_execute", "retrieve", "memory_read", "document_read"])
    memory_policy: Optional[MemoryPolicyConfig] = None
    knowledge_policy: Optional[KnowledgePolicyConfig] = None
    execution_policy: Optional[ExecutionPolicyConfig] = None
    evaluation_policy: Optional[EvaluationPolicyConfig] = None
    approval_policy: Optional[ApprovalPolicyConfig] = None
    budget_policy: Optional[BudgetPolicyConfig] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    purpose: Optional[str] = None
    project_id: Optional[str] = None


class AgentVersionCreate(BaseModel):
    instructions: str = Field(..., min_length=5)
    model_policy: Optional[ModelPolicyConfig] = None
    capability_policy: List[str] = Field(default_factory=list)
    memory_policy: Optional[MemoryPolicyConfig] = None
    knowledge_policy: Optional[KnowledgePolicyConfig] = None
    execution_policy: Optional[ExecutionPolicyConfig] = None
    evaluation_policy: Optional[EvaluationPolicyConfig] = None
    approval_policy: Optional[ApprovalPolicyConfig] = None
    budget_policy: Optional[BudgetPolicyConfig] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)


class AgentVersionResponse(BaseModel):
    id: str
    agent_id: str
    version: int
    instructions: str
    model_policy: Dict[str, Any]
    capability_policy: List[str]
    memory_policy: Dict[str, Any]
    knowledge_policy: Dict[str, Any]
    execution_policy: Dict[str, Any]
    evaluation_policy: Dict[str, Any]
    approval_policy: Dict[str, Any]
    budget_policy: Dict[str, Any]
    configuration: Dict[str, Any]
    created_by: str
    created_at: datetime
    published_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AgentResponse(BaseModel):
    id: str
    workspace_id: str
    project_id: Optional[str] = None
    name: str
    slug: str
    description: Optional[str] = None
    purpose: str
    status: AgentStatus
    current_version_id: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentDetailResponse(AgentResponse):
    current_version: Optional[AgentVersionResponse] = None
    versions_count: int = 0
    runs_count: int = 0


# ==============================================================================
# AGENT RUN & DELEGATION SCHEMAS
# ==============================================================================

class AgentRunCreate(BaseModel):
    agent_version_id: Optional[str] = None
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    workflow_run_id: Optional[str] = None
    collaboration_session_id: Optional[str] = None
    input: Dict[str, Any] = Field(default_factory=dict)
    budget_override: Optional[float] = None
    dry_run: bool = False


class AgentRunResponse(BaseModel):
    id: str
    agent_id: str
    agent_version_id: str
    workspace_id: str
    project_id: Optional[str] = None
    initiated_by: str
    parent_agent_run_id: Optional[str] = None
    task_id: Optional[str] = None
    workflow_run_id: Optional[str] = None
    collaboration_session_id: Optional[str] = None
    status: str
    input_snapshot: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    execution_state: Dict[str, Any]
    steps_executed: int
    delegations_count: int
    tool_calls_count: int
    connector_calls_count: int
    tokens: Dict[str, Any]
    cost: float
    latency: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[Dict[str, Any]] = None
    reproducibility_metadata: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentDelegationCreate(BaseModel):
    child_agent_id: str
    child_agent_version_id: Optional[str] = None
    reason: str
    task_snapshot: Dict[str, Any] = Field(default_factory=dict)
    allowed_capabilities: Optional[List[str]] = None
    budget_allocation: float = 0.5


class AgentDelegationResponse(BaseModel):
    id: str
    parent_agent_run_id: str
    parent_agent_id: str
    child_agent_id: str
    child_agent_version_id: str
    child_agent_run_id: Optional[str] = None
    reason: str
    task_snapshot: Dict[str, Any]
    allowed_capabilities: List[str]
    budget_allocation: float
    depth: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# MULTI-AGENT TEAM SCHEMAS
# ==============================================================================

class TeamMemberConfig(BaseModel):
    agent_id: str
    agent_version_id: Optional[str] = None
    role: TeamMemberRole = TeamMemberRole.SPECIALIST
    capabilities: List[str] = Field(default_factory=list)
    responsibilities: str = ""
    limits: Dict[str, Any] = Field(default_factory=dict)


class AgentTeamCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    slug: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[str] = None
    objective: str = Field(..., min_length=5)
    members: List[TeamMemberConfig] = Field(..., min_length=1)
    coordination_policy: Dict[str, Any] = Field(default_factory=dict)
    shared_context_policy: Dict[str, Any] = Field(default_factory=dict)
    approval_policy: Dict[str, Any] = Field(default_factory=dict)


class AgentTeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[str] = None


class AgentTeamMemberResponse(BaseModel):
    id: str
    team_version_id: str
    agent_id: str
    agent_version_id: str
    role: str
    capabilities: List[str]
    responsibilities: str
    limits: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentTeamVersionResponse(BaseModel):
    id: str
    team_id: str
    version: int
    objective: str
    coordination_policy: Dict[str, Any]
    shared_context_policy: Dict[str, Any]
    approval_policy: Dict[str, Any]
    created_by: str
    created_at: datetime
    published_at: Optional[datetime] = None
    members: List[AgentTeamMemberResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AgentTeamResponse(BaseModel):
    id: str
    workspace_id: str
    project_id: Optional[str] = None
    name: str
    slug: str
    description: Optional[str] = None
    status: AgentTeamStatus
    current_version_id: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentTeamDetailResponse(AgentTeamResponse):
    current_version: Optional[AgentTeamVersionResponse] = None
    members_count: int = 0
    runs_count: int = 0


class AgentTeamRunCreate(BaseModel):
    team_version_id: Optional[str] = None
    project_id: Optional[str] = None
    objective_override: Optional[str] = None
    input: Dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False


class AgentMessageCreate(BaseModel):
    recipient_agent_id: Optional[str] = None
    message_type: AgentMessageType
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentMessageResponse(BaseModel):
    id: str
    team_run_id: str
    sender_agent_id: str
    recipient_agent_id: Optional[str] = None
    message_type: str
    content: str
    metadata: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentConflictResponse(BaseModel):
    id: str
    team_run_id: str
    subject: str
    agent_a_id: str
    agent_b_id: str
    position_a: str
    position_b: str
    evidence_a: Dict[str, Any]
    evidence_b: Dict[str, Any]
    status: str
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentConflictResolveRequest(BaseModel):
    status: ConflictStatus
    resolution: str
    resolved_by: Optional[str] = None


class AgentTeamRunResponse(BaseModel):
    id: str
    team_id: str
    team_version_id: str
    workspace_id: str
    project_id: Optional[str] = None
    initiated_by: str
    objective: str
    status: str
    plan: Dict[str, Any]
    shared_context: Dict[str, Any]
    final_synthesis: Optional[Dict[str, Any]] = None
    cost: float
    latency: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[Dict[str, Any]] = None
    created_at: datetime
    messages_count: int = 0
    conflicts_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# EFFECTIVE POLICY & AUDIT PREVIEWS
# ==============================================================================

class EffectivePolicyPreview(BaseModel):
    agent_id: str
    version_id: Optional[str] = None
    allowed_capabilities: List[str]
    denied_capabilities: List[str]
    required_approvals: List[str]
    max_execution_limits: Dict[str, Any]
    data_scopes: Dict[str, Any]
    model_constraints: Dict[str, Any]
    budget_constraints: Dict[str, Any]
    is_safe: bool
    warnings: List[str] = Field(default_factory=list)


class AgentTraceResponse(BaseModel):
    run_id: str
    agent_id: str
    steps: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]]
    connector_calls: List[Dict[str, Any]]
    context_sources: List[Dict[str, Any]]
    memory_references: List[Dict[str, Any]]
    delegations: List[Dict[str, Any]]
    approvals: List[Dict[str, Any]]
    latency: float
    cost: float


class AgentReplayResponse(BaseModel):
    original_run_id: str
    replay_run_id: str
    status: str
    reproducibility_match: bool
    discrepancies: List[str]
    metadata_snapshot: Dict[str, Any]
