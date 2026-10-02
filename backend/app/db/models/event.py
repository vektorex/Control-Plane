"""
SQLAlchemy models for Step 26: Unified Event Bus and Real-Time Execution Updates.
Durable event store and consumer delivery tracking persisted in PostgreSQL.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, TYPE_CHECKING
from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
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
    from backend.app.db.models.project import Project


class Event(Base):
    """
    Durable event record in the PostgreSQL Event Store.
    Every state transition (workflow, job, trigger, approval, evaluation, etc.)
    is persisted once before dispatch to consumers or real-time SSE streams.
    """
    __tablename__ = "events"

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

    # Actor: user, system, worker, connector, scheduler
    actor_type: Mapped[str] = mapped_column(String(50), nullable=False, default="system")
    actor_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Event identification & aggregate classification
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    aggregate_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    aggregate_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Distributed tracing & lineage
    parent_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    causation_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Monotonic sequence ordering within aggregate
    sequence_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Idempotency deduplication key
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Sanitized payload & metadata (no secrets, credentials, or internal thoughts)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # Relationships
    deliveries = relationship("EventDelivery", back_populates="event", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_events_ws_created", "workspace_id", "created_at"),
        Index("ix_events_ws_event_type", "workspace_id", "event_type"),
        Index("ix_events_ws_aggregate", "workspace_id", "aggregate_type", "aggregate_id"),
        Index("ix_events_aggregate_sequence", "workspace_id", "aggregate_type", "aggregate_id", "sequence_number"),
        Index("ix_events_ws_correlation", "workspace_id", "correlation_id"),
        UniqueConstraint("workspace_id", "idempotency_key", name="uq_events_workspace_idempotency"),
    )


class EventDelivery(Base):
    """
    Tracks durable delivery of an event to a registered background consumer.
    Provides isolation, bounded retry tracking, and error persistence.
    """
    __tablename__ = "event_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    consumer_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # pending, processing, completed, retrying, failed
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending", index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)

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

    # Relationships
    event = relationship("Event", back_populates="deliveries")

    __table_args__ = (
        UniqueConstraint("event_id", "consumer_name", name="uq_event_deliveries_event_consumer"),
        Index("ix_event_deliveries_status_available", "status", "available_at"),
    )
