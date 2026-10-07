"""
SQLAlchemy models for Step 45: Control Tower.
Only creates tables for new persistent resources (views, attention items, snapshots, workstreams).
Does NOT duplicate tasks, runs, agents, workflows, jobs, approvals, security incidents, objectives, outcomes, or plans.
"""
from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from backend.app.db.base import Base


def _gen_uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ControlTowerView(Base):
    """
    Saved personalized dashboard configuration.
    Never grants permissions beyond the user's existing RBAC.
    """
    __tablename__ = "control_tower_views"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    workspace_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    # JSON: visible_sections, filters, grouping, sort_order, time_window, refresh_policy
    configuration = Column(JSON, nullable=False, default=dict)
    is_shared = Column(Boolean, nullable=False, default=False)
    shared_with_workspace = Column(Boolean, nullable=False, default=False)
    created_by = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ct_views_workspace_user", "workspace_id", "created_by"),
    )


class AttentionItem(Base):
    """
    Derived attention item aggregating signals from existing platform systems.
    Always references a source_type + source_id from an existing system.
    Never fabricated.
    """
    __tablename__ = "attention_items"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    workspace_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), nullable=True, index=True)

    # Source system reference – always required
    source_type = Column(String(64), nullable=False, index=True)
    source_id = Column(String(36), nullable=False, index=True)

    # Classification
    attention_type = Column(String(64), nullable=False, index=True)
    severity = Column(String(16), nullable=False, index=True)  # critical, high, medium, low, info

    # Human-readable
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)

    # Evidence references (list of IDs from source systems)
    evidence_ids = Column(JSON, nullable=False, default=list)

    # Lifecycle
    status = Column(String(32), nullable=False, default="open", index=True)  # open, acknowledged, resolved, dismissed, expired
    acknowledged_by = Column(String(36), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        # Deduplication: only one active attention item per source + type
        UniqueConstraint("workspace_id", "source_type", "source_id", "attention_type", "status",
                         name="uq_attention_dedup"),
        Index("ix_attention_ws_status", "workspace_id", "status"),
        Index("ix_attention_ws_severity", "workspace_id", "severity"),
        Index("ix_attention_source", "source_type", "source_id"),
        Index("ix_attention_created", "created_at"),
    )


class ControlTowerSnapshot(Base):
    """
    Derived read model representing a point-in-time summary of system state.
    Labeled as DERIVED. Never the source of truth.
    Always includes source_watermarks and generated_at.
    """
    __tablename__ = "control_tower_snapshots"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    workspace_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), nullable=True)

    generated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    # JSON: {source_name: last_updated_at} watermarks from each subsystem
    source_watermarks = Column(JSON, nullable=False, default=dict)
    # JSON: aggregated count/status summary (labeled DERIVED)
    summary = Column(JSON, nullable=False, default=dict)
    # JSON: list of subsystems that were unavailable (partial data)
    partial_failures = Column(JSON, nullable=False, default=list)
    is_stale = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    __table_args__ = (
        Index("ix_snapshot_ws_generated", "workspace_id", "generated_at"),
    )


class Workstream(Base):
    """
    Organizational view grouping related objectives, outcomes, tasks, workflows, agents, plans.
    NOT an execution primitive. Does not duplicate execution records.
    """
    __tablename__ = "workstreams"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    workspace_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    # JSON configuration: linked objective_ids, outcome_ids, etc.
    configuration = Column(JSON, nullable=False, default=dict)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_workstream_workspace", "workspace_id"),
    )


class WorkstreamMember(Base):
    """
    Members (users/teams) associated with a workstream for collaboration.
    """
    __tablename__ = "workstream_members"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    workstream_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=False, index=True)
    member_id = Column(String(36), nullable=False)
    member_type = Column(String(32), nullable=False, default="user")  # user, team
    role = Column(String(32), nullable=False, default="member")
    added_by = Column(String(36), nullable=False)
    added_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    __table_args__ = (
        UniqueConstraint("workstream_id", "member_id", "member_type", name="uq_workstream_member"),
        Index("ix_workstream_member_ws", "workspace_id"),
    )
