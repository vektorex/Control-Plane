"""
Pydantic schemas for the Human-in-the-Loop (HITL) system.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class InterventionType(str, Enum):
    APPROVAL = "approval"
    REVIEW = "review"
    EDIT = "edit"
    CONFIRMATION = "confirmation"
    AUTHORIZATION = "authorization"


class InterventionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class InterventionPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalDecisionType(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    EDIT = "edit"
    CANCEL = "cancel"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskAssessment(BaseModel):
    level: RiskLevel = RiskLevel.LOW
    reasons: List[str] = Field(default_factory=list)
    requires_approval: bool = False
    is_destructive: bool = False


class StepApprovalConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    required: bool = True
    policy: Optional[str] = "before_external_action"
    timeout_seconds: Optional[int] = 3600
    assigned_role: Optional[str] = None


# =============================================================================
# Intervention Requests
# =============================================================================

class InterventionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    project_id: Optional[UUID] = None
    workflow_id: Optional[UUID] = None
    workflow_run_id: Optional[UUID] = None
    run_id: Optional[UUID] = None
    step_id: Optional[str] = None
    assigned_to: Optional[UUID] = None
    intervention_type: InterventionType = InterventionType.APPROVAL
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="")
    priority: InterventionPriority = InterventionPriority.NORMAL
    requested_action: str = Field(..., min_length=1, max_length=100)
    input_snapshot: Dict[str, Any] = Field(default_factory=dict)
    safe_context: Dict[str, Any] = Field(default_factory=dict)
    available_actions: List[str] = Field(default_factory=lambda: ["approve", "reject", "edit", "cancel"])
    timeout_seconds: Optional[int] = 3600


class ApprovalActionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    comment: Optional[str] = None
    edited_data: Optional[Dict[str, Any]] = None


class InterventionAssignRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    assigned_to: UUID


class ApprovalDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    intervention_id: UUID
    workspace_id: UUID
    user_id: UUID
    decision: str
    comment: Optional[str] = None
    edited_data: Optional[Dict[str, Any]] = None
    created_at: datetime


class HumanInterventionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    project_id: Optional[UUID] = None
    workflow_id: Optional[UUID] = None
    workflow_run_id: Optional[UUID] = None
    run_id: Optional[UUID] = None
    step_id: Optional[str] = None
    requested_by: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    intervention_type: str
    title: str
    description: str
    status: str
    priority: str
    requested_action: str
    input_snapshot: Dict[str, Any]
    safe_context: Dict[str, Any]
    available_actions: List[str]
    selected_action: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    decisions: List[ApprovalDecisionResponse] = Field(default_factory=list)


class HumanActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    intervention_id: Optional[UUID] = None
    user_id: UUID
    action_type: str
    target_type: str
    target_id: Optional[str] = None
    metadata_json: Dict[str, Any]
    created_at: datetime


# =============================================================================
# Workspace Policies
# =============================================================================

class WorkspaceApprovalPolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    workspace_id: UUID
    require_tool_approval: bool = False
    require_connector_write_approval: bool = True
    require_destructive_approval: bool = True
    require_external_action_approval: bool = True
    require_evaluation_failure_review: bool = False
    max_auto_cost: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class WorkspaceApprovalPolicyUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    require_tool_approval: Optional[bool] = None
    require_connector_write_approval: Optional[bool] = None
    # require_destructive_approval cannot be disabled; remains True always
    require_external_action_approval: Optional[bool] = None
    require_evaluation_failure_review: Optional[bool] = None
    max_auto_cost: Optional[float] = None


# =============================================================================
# Notifications
# =============================================================================

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    user_id: UUID
    type: str
    title: str
    message: str
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    read: bool
    created_at: datetime
