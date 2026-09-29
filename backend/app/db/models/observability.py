import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.models.guid import GUID

if TYPE_CHECKING:
    from backend.app.db.models.run import Run
    from backend.app.db.models.workspace import Workspace
    from backend.app.db.models.task import Task
    from backend.app.db.models.project import Project


class RunTelemetry(Base):
    """
    Consolidated execution telemetry record for a Run across all orchestration stages.
    """
    __tablename__ = "run_telemetry"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="running",
        index=True,
    )
    provider: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    planner_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    generation_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    evaluator_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    retrieval_calls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retrieval_results: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tool_calls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tools_used: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    execution_steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    planner_duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retrieval_duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tool_duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generation_duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evaluation_duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    revision_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evaluation_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message_safe: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    run: Mapped["Run"] = relationship(
        "Run",
        back_populates="telemetry",
    )

    __table_args__ = (
        Index("ix_run_telemetry_workspace_created", "workspace_id", "created_at"),
        Index("ix_run_telemetry_workspace_status", "workspace_id", "status"),
        Index("ix_run_telemetry_workspace_model", "workspace_id", "generation_model"),
        Index("ix_run_telemetry_workspace_provider", "workspace_id", "provider"),
    )

    def __repr__(self) -> str:
        return f"<RunTelemetry(id={self.id}, run_id={self.run_id}, status='{self.status}', tokens={self.total_tokens})>"


class ExecutionTraceEvent(Base):
    """
    Discrete execution timeline event for a Run, capturing stage lifecycle and safe execution metadata.
    """
    __tablename__ = "execution_trace_events"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    step_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed", index=True)
    
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    provider: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    run: Mapped["Run"] = relationship(
        "Run",
        back_populates="trace_events",
    )

    __table_args__ = (
        Index("ix_trace_events_run_seq", "run_id", "sequence_number"),
        Index("ix_trace_events_workspace_created", "workspace_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ExecutionTraceEvent(id={self.id}, run_id={self.run_id}, event='{self.event_type}', seq={self.sequence_number})>"


class UsageRecord(Base):
    """
    Granular LLM token usage and cost record for a specific operation within a Run.
    """
    __tablename__ = "usage_records"

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
    run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # planning, generation, evaluation, revision
    
    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cached_input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    usage_source: Mapped[str] = mapped_column(String(50), default="provider", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    run: Mapped["Run"] = relationship(
        "Run",
        back_populates="usage_records",
    )

    __table_args__ = (
        Index("ix_usage_records_workspace_created", "workspace_id", "created_at"),
        Index("ix_usage_records_workspace_model", "workspace_id", "model"),
        Index("ix_usage_records_workspace_provider", "workspace_id", "provider"),
        Index("ix_usage_records_run_op", "run_id", "operation"),
    )

    def __repr__(self) -> str:
        return f"<UsageRecord(id={self.id}, run_id={self.run_id}, model='{self.model}', op='{self.operation}', tokens={self.total_tokens})>"
