"""
SQLAlchemy models for Step 23: Workflow Triggers and Trigger Runs.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.models.guid import GUID

if TYPE_CHECKING:
    from backend.app.db.models.workspace import Workspace
    from backend.app.db.models.project import Project
    from backend.app.db.models.workflow import Workflow, WorkflowRun
    from backend.app.db.models.user import User


class WorkflowTrigger(Base):
    """
    Automated or manual trigger configuration that executes a workflow on events or schedules.
    """
    __tablename__ = "workflow_triggers"

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
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workflow_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # manual, schedule, webhook, connector_event
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # active, paused, disabled, archived
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active", index=True)
    
    configuration: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    filter_configuration: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    retry_configuration: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {"max_retries": 2, "backoff_factor": 2.0},
    )

    # Secure non-guessable identifier for public webhook endpoints
    public_trigger_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        index=True,
    )
    # Hashed webhook verification secret
    webhook_secret_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Debounce window in seconds (e.g. 60)
    debounce_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    next_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", lazy="selectin")
    project: Mapped[Optional["Project"]] = relationship("Project", lazy="selectin")
    workflow: Mapped["Workflow"] = relationship("Workflow", lazy="selectin")
    runs: Mapped[List["TriggerRun"]] = relationship(
        "TriggerRun",
        back_populates="trigger",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_workflow_triggers_ws_wf", "workspace_id", "workflow_id"),
        Index("ix_workflow_triggers_ws_status", "workspace_id", "status"),
        Index("ix_workflow_triggers_next_run", "status", "next_run_at"),
    )


class TriggerRun(Base):
    """
    Record of an event receipt and subsequent trigger execution attempting to start a workflow.
    """
    __tablename__ = "trigger_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    trigger_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("workflow_triggers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workflow_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("workflow_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # received, queued, running, completed, failed, skipped, cancelled
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="received",
        index=True,
    )
    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    input_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    filter_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    trigger: Mapped["WorkflowTrigger"] = relationship("WorkflowTrigger", back_populates="runs", lazy="selectin")
    workflow_run: Mapped[Optional["WorkflowRun"]] = relationship("WorkflowRun", lazy="selectin")
    workspace: Mapped["Workspace"] = relationship("Workspace", lazy="selectin")

    __table_args__ = (
        Index("ix_trigger_runs_trig_status", "trigger_id", "status"),
        Index("ix_trigger_runs_ws_created", "workspace_id", "created_at"),
        Index("ix_trigger_runs_idempotency", "trigger_id", "idempotency_key"),
    )
