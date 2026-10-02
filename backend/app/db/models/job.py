"""
SQLAlchemy models for Step 24: Durable Background Job System.
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
    from backend.app.db.models.user import User


class Job(Base):
    """
    Durable background job record persisted in PostgreSQL.
    Guarantees asynchronous execution across workers with lease management,
    idempotency, bounded retries, and fair priority scheduling.
    """
    __tablename__ = "jobs"

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
    
    # workflow_run, trigger_run, document_processing, evaluation_experiment, replay_run, connector_operation
    job_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # queued, running, retrying, completed, failed, cancelled
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="queued", index=True)
    
    # low, normal, high
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="normal", index=True)
    
    # Safe untrusted input payload (no secrets or raw credentials)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Worker lease claiming and heartbeat
    lease_owner: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    lease_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    heartbeat_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Workspace-scoped idempotency key
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    
    # Hierarchical dependency / parent job
    parent_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Structured progress: percentage, current_step, completed_steps, total_steps, message
    progress: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {
            "percentage": 0,
            "current_step": None,
            "completed_steps": 0,
            "total_steps": 0,
            "message": None,
        },
    )
    
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if getattr(self, "status", None) is None:
            self.status = "queued"
        if getattr(self, "priority", None) is None:
            self.priority = "normal"
        if getattr(self, "attempts", None) is None:
            self.attempts = 0
        if getattr(self, "max_attempts", None) is None:
            self.max_attempts = 3
        if getattr(self, "payload", None) is None:
            self.payload = {}
        if getattr(self, "progress", None) is None:
            self.progress = {
                "percentage": 0,
                "current_step": None,
                "completed_steps": 0,
                "total_steps": 0,
                "message": None,
            }
        from datetime import timezone
        now = datetime.now(timezone.utc)
        if getattr(self, "created_at", None) is None:
            self.created_at = now
        if getattr(self, "updated_at", None) is None:
            self.updated_at = now
        if getattr(self, "available_at", None) is None:
            self.available_at = now

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", lazy="selectin")
    project: Mapped[Optional["Project"]] = relationship("Project", lazy="selectin")
    events: Mapped[List["JobEvent"]] = relationship(
        "JobEvent",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="JobEvent.created_at.asc()",
    )

    __table_args__ = (
        Index("ix_jobs_ws_status", "workspace_id", "status"),
        Index("ix_jobs_claim", "status", "available_at", "priority"),
        Index("ix_jobs_lease_recovery", "status", "lease_expires_at"),
        Index("ix_jobs_ws_idemp", "workspace_id", "idempotency_key"),
        Index("ix_jobs_created", "workspace_id", "created_at"),
    )


class JobEvent(Base):
    """
    Immutable audit log event emitted during job lifecycle transitions.
    """
    __tablename__ = "job_events"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # created, queued, claimed, started, heartbeat, progress, retry_scheduled, cancel_requested, cancelled, completed, failed, recovered
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="events", lazy="selectin")

    __table_args__ = (
        Index("ix_job_events_job_created", "job_id", "created_at"),
        Index("ix_job_events_ws_type", "workspace_id", "event_type"),
    )
