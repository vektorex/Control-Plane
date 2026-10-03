"""
SQLAlchemy models for Step 39: Multi-User Collaboration, Shared AI Workspaces & Real-Time Co-Execution.
"""
from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from backend.app.db.database import Base


def _gen_uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CollaborationSession(Base):
    """Temporary real-time collaboration session bound to an underlying platform resource."""

    __tablename__ = "collaboration_sessions"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    organization_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), nullable=True, index=True)
    resource_type = Column(String(64), nullable=False, index=True)
    resource_id = Column(String(128), nullable=False, index=True)
    created_by = Column(String(36), nullable=False)
    status = Column(String(32), nullable=False, default="active", index=True)  # active, paused, closed, expired
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)
    last_activity_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_collab_sessions_org_ws", "organization_id", "workspace_id"),
        Index("ix_collab_sessions_resource", "resource_type", "resource_id"),
    )

    participants = relationship(
        "CollaborationParticipant",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    comments = relationship(
        "CollaborationComment",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class CollaborationParticipant(Base):
    """Participant in a collaboration session."""

    __tablename__ = "collaboration_participants"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    session_id = Column(String(36), ForeignKey("collaboration_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    role = Column(String(32), nullable=False, default="editor")  # owner, editor, reviewer, viewer
    status = Column(String(32), nullable=False, default="active", index=True)  # active, idle, offline, removed
    joined_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    last_seen_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    left_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("session_id", "user_id", name="uq_collab_session_participant"),
    )

    session = relationship("CollaborationSession", back_populates="participants")


class PresenceState(Base):
    """Ephemeral presence state for connected users in a session."""

    __tablename__ = "presence_states"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    session_id = Column(String(36), ForeignKey("collaboration_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="active")  # active, idle, away, offline
    cursor_context = Column(JSON, nullable=True)  # Lightweight safe cursor coordinates / section
    active_resource = Column(String(128), nullable=True)
    last_heartbeat_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    __table_args__ = (
        UniqueConstraint("session_id", "user_id", name="uq_presence_session_user"),
    )


class CollaborationActivity(Base):
    """Audit and timeline event in a shared collaboration session."""

    __tablename__ = "collaboration_activities"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    session_id = Column(String(36), ForeignKey("collaboration_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_type = Column(String(32), nullable=False, default="user")  # user, ai, system
    actor_id = Column(String(36), nullable=True)
    activity_type = Column(String(64), nullable=False, index=True)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(128), nullable=False)
    summary = Column(String(512), nullable=False)
    activity_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)


class CollaborationComment(Base):
    """User and AI comments in a collaborative workspace."""

    __tablename__ = "collaboration_comments"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    session_id = Column(String(36), ForeignKey("collaboration_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type = Column(String(64), nullable=False, index=True)
    resource_id = Column(String(128), nullable=False, index=True)
    author_id = Column(String(36), nullable=False, index=True)
    author_type = Column(String(32), nullable=False, default="user")  # user, ai
    body = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="active", index=True)  # active, resolved, deleted
    parent_comment_id = Column(String(36), ForeignKey("collaboration_comments.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    session = relationship("CollaborationSession", back_populates="comments")
    mentions = relationship("CommentMention", back_populates="comment", cascade="all, delete-orphan")


class CommentMention(Base):
    """User @mention in a collaboration comment."""

    __tablename__ = "comment_mentions"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    comment_id = Column(String(36), ForeignKey("collaboration_comments.id", ondelete="CASCADE"), nullable=False, index=True)
    mentioned_user_id = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    notified_at = Column(DateTime(timezone=True), nullable=True)

    comment = relationship("CollaborationComment", back_populates="mentions")


class CollaborationAssignment(Base):
    """Actionable assignment for human review or execution."""

    __tablename__ = "collaboration_assignments"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    session_id = Column(String(36), ForeignKey("collaboration_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(128), nullable=False)
    assigned_to = Column(String(36), nullable=False, index=True)
    assigned_by = Column(String(36), nullable=False)
    assignment_type = Column(String(64), nullable=False)  # review, execution, approval, investigation, implementation
    status = Column(String(32), nullable=False, default="pending", index=True)  # pending, accepted, completed, cancelled
    due_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class CollaborationAnnotation(Base):
    """Targeted annotation on document chunks, artifact parts, workflow steps, or graph entities."""

    __tablename__ = "collaboration_annotations"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    session_id = Column(String(36), ForeignKey("collaboration_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type = Column(String(64), nullable=False, index=True)
    resource_id = Column(String(128), nullable=False, index=True)
    author_id = Column(String(36), nullable=False)
    annotation_type = Column(String(64), nullable=False)  # text, highlight, comment, decision, question, warning, evidence
    target = Column(JSON, nullable=False)  # Target coordinates/identifier
    content = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class CollaborationDecision(Base):
    """Shared decision log for collaborative approvals or rejections."""

    __tablename__ = "collaboration_decisions"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    session_id = Column(String(36), ForeignKey("collaboration_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(128), nullable=False)
    decision_type = Column(String(64), nullable=False)  # approve, reject, accept, request_changes, mark_reviewed, mark_blocked
    decision = Column(JSON, nullable=False, default=dict)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)
    supersedes_id = Column(String(36), nullable=True)


class CoExecutionSession(Base):
    """AI + Human co-execution lifecycle session."""

    __tablename__ = "co_execution_sessions"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    collaboration_session_id = Column(String(36), ForeignKey("collaboration_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    run_id = Column(String(36), nullable=True, index=True)
    workflow_run_id = Column(String(36), nullable=True, index=True)
    initiated_by = Column(String(36), nullable=False)
    mode = Column(String(64), nullable=False, default="human_assisted")  # human_assisted, ai_assisted, review_before_execute, shared_execution
    status = Column(String(32), nullable=False, default="planning", index=True)  # planning, awaiting_input, awaiting_approval, executing, evaluating, completed, failed, cancelled
    context_config = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class CollaborationLock(Base):
    """Optional short-lived advisory lock for high-conflict operations."""

    __tablename__ = "collaboration_locks"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(128), nullable=False)
    owner_id = Column(String(36), nullable=False)
    acquired_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("resource_type", "resource_id", name="uq_collab_lock_resource"),
    )


class CollaborationChange(Base):
    """Audit record of collaborative resource changes."""

    __tablename__ = "collaboration_changes"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    session_id = Column(String(36), ForeignKey("collaboration_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(128), nullable=False)
    actor_id = Column(String(36), nullable=False)
    change_type = Column(String(64), nullable=False)
    before_version = Column(Integer, nullable=False)
    after_version = Column(Integer, nullable=False)
    summary = Column(String(512), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)


class CollaborationConflict(Base):
    """Record of optimistic concurrency conflicts and their resolution."""

    __tablename__ = "collaboration_conflicts"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    session_id = Column(String(36), ForeignKey("collaboration_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(128), nullable=False)
    base_version = Column(Integer, nullable=False)
    current_version = Column(Integer, nullable=False)
    incoming_version = Column(Integer, nullable=False)
    actor_id = Column(String(36), nullable=False)
    status = Column(String(32), nullable=False, default="open", index=True)  # open, resolved, discarded
    resolution_strategy = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class CollaborativeState(Base):
    """Bounded, versioned collaborative state storage."""

    __tablename__ = "collaborative_states"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    session_id = Column(String(36), ForeignKey("collaboration_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(128), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    state = Column(JSON, nullable=False, default=dict)
    updated_by = Column(String(36), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    __table_args__ = (
        UniqueConstraint("session_id", "resource_type", "resource_id", name="uq_collab_state_session_resource"),
    )


class CollaborationSnapshot(Base):
    """Collaboration-specific checkpoint snapshot."""

    __tablename__ = "collaboration_snapshots"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    session_id = Column(String(36), ForeignKey("collaboration_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(128), nullable=False)
    version = Column(Integer, nullable=False)
    state_hash = Column(String(64), nullable=False)
    state = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)
