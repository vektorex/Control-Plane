"""
Pydantic schemas for Step 32: AI Governance, Policy Control Plane, and Safety Guardrails.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


from backend.app.services.governance.constants import (
    ActionCategory,
    DataClassification,
    ClassificationSource,
    EnforcementPoint,
    GovernanceDecisionType,
    PolicyAction,
    PolicyRuleType,
    PolicyScope,
    PolicyStatus,
    PolicyVersionStatus,
    RuleConditionOperator,
    VerificationRequirement,
    BudgetReservationStatus,
)


# ---------------------------------------------------------------------------
# Policy Rule Components
# ---------------------------------------------------------------------------

class RuleCondition(BaseModel):
    """A single safe deterministic condition."""
    field: str = Field(..., description="Trusted metadata field name (e.g. 'model_id', 'provider', 'action_category')")
    operator: RuleConditionOperator
    value: Union[str, int, float, bool, List[str], List[int], None] = None


class PolicyRule(BaseModel):
    """A single rule within a policy version."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_type: PolicyRuleType
    description: Optional[str] = None
    conditions: List[RuleCondition] = Field(default_factory=list)
    action: PolicyAction
    action_params: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=100, ge=0, le=10000)

    @field_validator("conditions")
    @classmethod
    def validate_conditions_count(cls, v: list) -> list:
        if len(v) > 20:
            raise ValueError("A single rule may not have more than 20 conditions")
        return v


# ---------------------------------------------------------------------------
# Policy CRUD Schemas
# ---------------------------------------------------------------------------

class GovernancePolicyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scope: PolicyScope = PolicyScope.WORKSPACE
    priority: int = Field(default=100, ge=0, le=10000)
    workspace_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None


class GovernancePolicyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[int] = Field(None, ge=0, le=10000)
    status: Optional[PolicyStatus] = None


class GovernancePolicyResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: Optional[uuid.UUID]
    project_id: Optional[uuid.UUID]
    name: str
    description: Optional[str]
    status: str
    priority: int
    scope: str
    active_version_id: Optional[uuid.UUID]
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Policy Version Schemas
# ---------------------------------------------------------------------------

class PolicyVersionCreate(BaseModel):
    rules: List[PolicyRule] = Field(default_factory=list)
    change_summary: Optional[str] = None

    @field_validator("rules")
    @classmethod
    def validate_rules_count(cls, v: list) -> list:
        if len(v) > 50:
            raise ValueError("A policy version may not have more than 50 rules")
        return v


class PolicyVersionResponse(BaseModel):
    id: uuid.UUID
    policy_id: uuid.UUID
    version_number: int
    rules: List[Dict[str, Any]]
    status: str
    change_summary: Optional[str]
    created_by: uuid.UUID
    created_at: datetime
    activated_at: Optional[datetime]
    deactivated_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Governance Decision
# ---------------------------------------------------------------------------

class GovernanceDecision(BaseModel):
    """Normalized output of a governance policy evaluation."""
    decision: GovernanceDecisionType
    reasons: List[str] = Field(default_factory=list)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    required_approvals: List[str] = Field(default_factory=list)
    required_verifications: List[str] = Field(default_factory=list)
    matched_policies: List[str] = Field(default_factory=list)
    policy_version: Optional[str] = None
    expires_at: Optional[datetime] = None
    evaluation_latency_ms: Optional[int] = None


# ---------------------------------------------------------------------------
# Governance Evaluation Request
# ---------------------------------------------------------------------------

class GovernanceEvaluationRequest(BaseModel):
    """Trusted metadata submitted for a governance evaluation."""
    enforcement_point: EnforcementPoint
    organization_id: uuid.UUID
    workspace_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    user_role: Optional[str] = None

    # Operation metadata
    task_type: Optional[str] = None
    execution_mode: Optional[str] = None
    action_category: Optional[ActionCategory] = None

    # Model / Provider
    model_id: Optional[str] = None
    provider: Optional[str] = None
    model_capabilities: List[str] = Field(default_factory=list)

    # Tool / Connector / Workflow / Prompt
    tool_id: Optional[str] = None
    connector_id: Optional[str] = None
    workflow_id: Optional[str] = None
    prompt_id: Optional[str] = None
    prompt_version_id: Optional[str] = None

    # Artifact / Data
    artifact_type: Optional[str] = None
    data_classification: Optional[DataClassification] = None

    # Cost
    estimated_cost_usd: Optional[float] = None

    # Cache
    cache_mode: Optional[str] = None

    # Job context
    job_type: Optional[str] = None

    # Extra safe metadata
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Simulate / Preview
# ---------------------------------------------------------------------------

class GovernanceSimulateRequest(BaseModel):
    """Dry-run simulation of a governance evaluation. Never executes the operation."""
    evaluation: GovernanceEvaluationRequest
    hypothetical_policy_ids: Optional[List[uuid.UUID]] = None


class GovernanceSimulateResponse(BaseModel):
    decision: GovernanceDecisionType
    matched_policies: List[str]
    constraints: Dict[str, Any]
    required_approvals: List[str]
    required_verifications: List[str]
    reasons: List[str]
    simulation_note: str = "This is a dry-run simulation. No operation was executed."


class GovernancePreviewRequest(BaseModel):
    """Test a hypothetical policy configuration. Never mutates production state."""
    hypothetical_rules: List[PolicyRule]
    evaluation: GovernanceEvaluationRequest


class GovernancePreviewResponse(BaseModel):
    decision: GovernanceDecisionType
    matched_rules: List[Dict[str, Any]]
    constraints: Dict[str, Any]
    reasons: List[str]
    preview_note: str = "This is a preview only. No policy was saved or activated."


# ---------------------------------------------------------------------------
# Budget Policy Schemas
# ---------------------------------------------------------------------------

class BudgetPolicyCreate(BaseModel):
    workspace_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    daily_limit_usd: Optional[float] = Field(None, ge=0)
    monthly_limit_usd: Optional[float] = Field(None, ge=0)
    per_run_limit_usd: Optional[float] = Field(None, ge=0)
    per_user_daily_limit_usd: Optional[float] = Field(None, ge=0)
    soft_threshold_pct: float = Field(default=0.80, ge=0.0, le=1.0)
    hard_threshold_pct: float = Field(default=1.00, ge=0.0, le=2.0)
    on_soft_breach: str = Field(default="warn")
    on_hard_breach: str = Field(default="deny")


class BudgetPolicyResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: Optional[uuid.UUID]
    project_id: Optional[uuid.UUID]
    daily_limit_usd: Optional[float]
    monthly_limit_usd: Optional[float]
    per_run_limit_usd: Optional[float]
    per_user_daily_limit_usd: Optional[float]
    soft_threshold_pct: float
    hard_threshold_pct: float
    on_soft_breach: str
    on_hard_breach: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BudgetReservationCreate(BaseModel):
    workspace_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    run_id: Optional[uuid.UUID] = None
    job_id: Optional[uuid.UUID] = None
    reserved_amount_usd: float = Field(..., ge=0)


class BudgetReservationResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    project_id: Optional[uuid.UUID]
    reserved_amount_usd: float
    actual_amount_usd: Optional[float]
    status: str
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Data Classification
# ---------------------------------------------------------------------------

class DataClassificationRequest(BaseModel):
    target_type: str  # "artifact", "document", "connector", "memory", "entity", "workflow", "task", "prompt"
    target_id: uuid.UUID
    classification: DataClassification
    source: ClassificationSource
    reason: Optional[str] = None


class DataClassificationResponse(BaseModel):
    target_type: str
    target_id: uuid.UUID
    classification: DataClassification
    source: str
    assigned_at: datetime


# ---------------------------------------------------------------------------
# Dashboard Stats
# ---------------------------------------------------------------------------

class GovernanceStatsResponse(BaseModel):
    active_policies: int
    blocked_operations_24h: int
    approval_required_24h: int
    verification_required_24h: int
    budget_usage_daily_usd: float
    budget_limit_daily_usd: Optional[float]
    policy_changes_7d: int
    recent_enforcement_events: List[Dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Decision Log
# ---------------------------------------------------------------------------

class GovernanceDecisionLogResponse(BaseModel):
    id: uuid.UUID
    enforcement_point: str
    decision: str
    reasons: List[str]
    matched_policy_ids: List[str]
    constraints: Dict[str, Any]
    required_approvals: List[str]
    required_verifications: List[str]
    evaluation_latency_ms: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}
