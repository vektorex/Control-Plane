import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.models.guid import GUID

if TYPE_CHECKING:
    from backend.app.db.models.workspace import Workspace
    from backend.app.db.models.user import User
    from backend.app.db.models.project import Project
    from backend.app.db.models.workflow import Workflow, WorkflowRun
    from backend.app.db.models.run import Run


class HumanInterventionRequest(Base):
    """
    Represents an action in a workflow, tool, or connector execution
    that is paused awaiting human approval, review, or input editing.
    """
    __tablename__ = "human_intervention_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    workflow_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("workflows.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    workflow_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    step_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    requested_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    intervention_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="approval",
        index=True,
    )  # approval, review, edit, confirmation, authorization
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )  # pending, approved, rejected, edited, expired, cancelled
    priority: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="normal",
    )  # low, normal, high, critical
    requested_action: Mapped[str] = mapped_column(String(100), nullable=False)
    input_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    safe_context: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    available_actions: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: ["approve", "reject", "edit", "cancel"],
    )
    selected_action: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    response_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", lazy="selectin")
    project: Mapped[Optional["Project"]] = relationship("Project", lazy="selectin")
    workflow: Mapped[Optional["Workflow"]] = relationship("Workflow", lazy="selectin")
    workflow_run: Mapped[Optional["WorkflowRun"]] = relationship("WorkflowRun", lazy="selectin")
    assigned_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to], lazy="selectin")
    requester_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[requested_by], lazy="selectin")
    decisions: Mapped[List["ApprovalDecision"]] = relationship(
        "ApprovalDecision",
        back_populates="intervention",
        cascade="all, delete-orphan",
        order_by="ApprovalDecision.created_at.desc()",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_hitl_ws_status", "workspace_id", "status"),
        Index("ix_hitl_ws_assigned", "workspace_id", "assigned_to", "status"),
        Index("ix_hitl_wf_run", "workflow_run_id", "status"),
        Index("ix_hitl_expires", "status", "expires_at"),
    )


class ApprovalDecision(Base):
    """
    Records an authorized human user's decision (approve, reject, edit, cancel)
    on an intervention request.
    """
    __tablename__ = "approval_decisions"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    intervention_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("human_intervention_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    decision: Mapped[str] = mapped_column(String(50), nullable=False)  # approve, reject, edit, cancel
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    edited_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # Relationships
    intervention: Mapped["HumanInterventionRequest"] = relationship(
        "HumanInterventionRequest",
        back_populates="decisions",
        lazy="selectin",
    )
    user: Mapped["User"] = relationship("User", lazy="selectin")

    __table_args__ = (
        Index("ix_approval_decisions_interv", "intervention_id", "created_at"),
    )


class HumanAction(Base):
    """
    Immutable audit log entry of any human intervention event.
    """
    __tablename__ = "human_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    intervention_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("human_intervention_requests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)  # request_created, approved, rejected, edited, expired, cancelled, execution_resumed
    target_type: Mapped[str] = mapped_column(String(100), nullable=False)  # workflow_run, tool, connector, intervention
    target_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")

    __table_args__ = (
        Index("ix_human_actions_ws_type", "workspace_id", "action_type", "created_at"),
    )


class WorkspaceApprovalPolicy(Base):
    """
    Workspace-level policy defining when human intervention is required.
    Destructive actions are mandatory and cannot be disabled.
    """
    __tablename__ = "workspace_approval_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    require_tool_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    require_connector_write_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    require_destructive_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)  # Cannot be bypassed
    require_external_action_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    require_evaluation_failure_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    max_auto_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


# Re-export unified Notification model from Step 25
from backend.app.db.models.notification import Notification

__all__ = [
    "HumanInterventionRequest",
    "ApprovalDecision",
    "HumanAction",
    "WorkspaceApprovalPolicy",
    "Notification",
]
