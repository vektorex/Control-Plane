"""
Pydantic V2 schemas for Step 39: Multi-User Collaboration, Shared AI Workspaces & Real-Time Co-Execution.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CollaborationSessionCreate(BaseModel):
    workspace_id: str
    project_id: Optional[str] = None
    resource_type: str = Field(..., description="task, run, workflow, document, artifact, evaluation, replay, etc.")
    resource_id: str
    expires_at: Optional[datetime] = None


class CollaborationSessionUpdate(BaseModel):
    status: Optional[str] = None  # active, paused, closed


class CollaborationSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    workspace_id: str
    project_id: Optional[str] = None
    resource_type: str
    resource_id: str
    created_by: str
    status: str
    created_at: datetime
    last_activity_at: datetime
    expires_at: Optional[datetime] = None


class CollaborationParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    user_id: str
    role: str
    status: str
    joined_at: datetime
    last_seen_at: datetime
    left_at: Optional[datetime] = None


class ParticipantRoleUpdate(BaseModel):
    role: str  # owner, editor, reviewer, viewer


class PresenceHeartbeatRequest(BaseModel):
    status: str = "active"  # active, idle, away, offline
    cursor_context: Optional[Dict[str, Any]] = None
    active_resource: Optional[str] = None


class PresenceStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    user_id: str
    status: str
    cursor_context: Optional[Dict[str, Any]] = None
    active_resource: Optional[str] = None
    last_heartbeat_at: datetime
    updated_at: datetime


class CollaborationActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    actor_type: str
    actor_id: Optional[str] = None
    activity_type: str
    resource_type: str
    resource_id: str
    summary: str
    activity_metadata: Dict[str, Any]
    created_at: datetime


class CollaborationCommentCreate(BaseModel):
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    body: str = Field(..., min_length=1, max_length=10000)
    parent_comment_id: Optional[str] = None


class CollaborationCommentUpdate(BaseModel):
    body: Optional[str] = None
    status: Optional[str] = None  # active, resolved, deleted


class CommentMentionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    comment_id: str
    mentioned_user_id: str
    created_at: datetime
    notified_at: Optional[datetime] = None


class CollaborationCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    resource_type: str
    resource_id: str
    author_id: str
    author_type: str
    body: str
    status: str
    parent_comment_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    mentions: List[CommentMentionResponse] = []


class CollaborationAssignmentCreate(BaseModel):
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    assigned_to: str
    assignment_type: str  # review, execution, approval, investigation, implementation
    due_at: Optional[datetime] = None


class CollaborationAssignmentUpdate(BaseModel):
    status: Optional[str] = None  # pending, accepted, completed, cancelled
    due_at: Optional[datetime] = None


class CollaborationAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    resource_type: str
    resource_id: str
    assigned_to: str
    assigned_by: str
    assignment_type: str
    status: str
    due_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CollaborationAnnotationCreate(BaseModel):
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    annotation_type: str  # text, highlight, comment, decision, question, warning, evidence
    target: Dict[str, Any]  # target element/part coordinates
    content: str


class CollaborationAnnotationUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[str] = None


class CollaborationAnnotationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    resource_type: str
    resource_id: str
    author_id: str
    annotation_type: str
    target: Dict[str, Any]
    content: str
    status: str
    created_at: datetime
    updated_at: datetime


class CollaborationDecisionCreate(BaseModel):
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    decision_type: str  # approve, reject, accept, request_changes, mark_reviewed, mark_blocked
    decision: Dict[str, Any] = Field(default_factory=dict)
    supersedes_id: Optional[str] = None


class CollaborationDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    resource_type: str
    resource_id: str
    decision_type: str
    decision: Dict[str, Any]
    created_by: str
    created_at: datetime
    supersedes_id: Optional[str] = None


class CoExecutionInitiateRequest(BaseModel):
    mode: str = "human_assisted"  # human_assisted, ai_assisted, review_before_execute, shared_execution
    task_id: Optional[str] = None
    workflow_id: Optional[str] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)
    include_comments: bool = True
    include_annotations: bool = True
    comment_ids: Optional[List[str]] = None


class CoExecutionSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    collaboration_session_id: str
    run_id: Optional[str] = None
    workflow_run_id: Optional[str] = None
    initiated_by: str
    mode: str
    status: str
    context_config: Dict[str, Any]
    created_at: datetime
    completed_at: Optional[datetime] = None


class CollaborativeStateUpdateRequest(BaseModel):
    resource_type: str
    resource_id: str
    expected_version: int
    state: Dict[str, Any]


class CollaborativeStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    resource_type: str
    resource_id: str
    version: int
    state: Dict[str, Any]
    updated_by: str
    updated_at: datetime


class CollaborationConflictResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    resource_type: str
    resource_id: str
    base_version: int
    current_version: int
    incoming_version: int
    actor_id: str
    status: str
    resolution_strategy: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None


class CollaborationConflictResolveRequest(BaseModel):
    strategy: str  # keep_current, apply_changes, manual_merge
    merged_state: Optional[Dict[str, Any]] = None


class CollaborationLockAcquireRequest(BaseModel):
    resource_type: str
    resource_id: str
    ttl_seconds: int = 60  # Default 60 seconds advisory lock


class CollaborationLockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    resource_type: str
    resource_id: str
    owner_id: str
    acquired_at: datetime
    expires_at: datetime


class CollaborationSessionJoinRequest(BaseModel):
    role: str = "editor"  # owner, editor, reviewer, viewer


class CollaborationMentionCreateRequest(BaseModel):
    comment_id: str
    user_handle_or_id: str


class WorkspaceCollaborationSummaryResponse(BaseModel):
    session_id: str
    resource_type: str
    resource_id: str
    active_participants_count: int
    open_comments_count: int
    pending_assignments_count: int
    active_presence: List[PresenceStateResponse]

