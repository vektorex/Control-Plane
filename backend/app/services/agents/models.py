"""
SQLAlchemy models for Step 40: Governed AI Agent Runtime and Multi-Agent Teams Layer.
"""
from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from backend.app.db.base import Base


def _gen_uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Agent(Base):
    """Represents a first-class governed AI agent entity belonging to a workspace."""

    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    workspace_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), nullable=True, index=True)
    name = Column(String(128), nullable=False)
    slug = Column(String(128), nullable=False, index=True)
    description = Column(Text, nullable=True)
    purpose = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="draft", index=True)  # draft, active, paused, disabled, archived
    current_version_id = Column(String(36), nullable=True)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        UniqueConstraint("workspace_id", "slug", name="uq_agents_ws_slug"),
        Index("ix_agents_ws_status", "workspace_id", "status"),
    )

    versions = relationship(
        "AgentVersion",
        back_populates="agent",
        cascade="all, delete-orphan",
        order_by="AgentVersion.version.desc()",
    )
    runs = relationship(
        "AgentRun",
        back_populates="agent",
        cascade="all, delete-orphan",
    )


class AgentVersion(Base):
    """Immutable published or draft version of an Agent."""

    __tablename__ = "agent_versions"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    instructions = Column(Text, nullable=False)
    model_policy = Column(JSON, nullable=False, default=dict)
    capability_policy = Column(JSON, nullable=False, default=list)
    memory_policy = Column(JSON, nullable=False, default=dict)
    knowledge_policy = Column(JSON, nullable=False, default=dict)
    execution_policy = Column(JSON, nullable=False, default=dict)
    evaluation_policy = Column(JSON, nullable=False, default=dict)
    approval_policy = Column(JSON, nullable=False, default=dict)
    budget_policy = Column(JSON, nullable=False, default=dict)
    configuration = Column(JSON, nullable=False, default=dict)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    published_at = Column(DateTime(timezone=True), nullable=True)
    deprecated_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("agent_id", "version", name="uq_agent_versions_agent_ver"),
    )

    agent = relationship("Agent", back_populates="versions")


class AgentRun(Base):
    """Execution lifecycle record for a bounded agent run."""

    __tablename__ = "agent_runs"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_version_id = Column(String(36), ForeignKey("agent_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), nullable=True, index=True)
    initiated_by = Column(String(36), nullable=False)
    parent_agent_run_id = Column(String(36), nullable=True, index=True)
    task_id = Column(String(36), nullable=True, index=True)
    workflow_run_id = Column(String(36), nullable=True, index=True)
    collaboration_session_id = Column(String(36), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="created", index=True)
    input_snapshot = Column(JSON, nullable=False, default=dict)
    output = Column(JSON, nullable=True)
    execution_state = Column(JSON, nullable=False, default=dict)
    steps_executed = Column(Integer, nullable=False, default=0)
    delegations_count = Column(Integer, nullable=False, default=0)
    tool_calls_count = Column(Integer, nullable=False, default=0)
    connector_calls_count = Column(Integer, nullable=False, default=0)
    tokens = Column(JSON, nullable=False, default=dict)
    cost = Column(Float, nullable=False, default=0.0)
    latency = Column(Float, nullable=False, default=0.0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(JSON, nullable=True)
    reproducibility_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)

    agent = relationship("Agent", back_populates="runs")


class AgentDelegation(Base):
    """Controlled sub-agent delegation record enforcing bounded depth and budget allocation."""

    __tablename__ = "agent_delegations"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    parent_agent_run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    child_agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    child_agent_version_id = Column(String(36), ForeignKey("agent_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    child_agent_run_id = Column(String(36), nullable=True, index=True)
    reason = Column(String(512), nullable=False)
    task_snapshot = Column(JSON, nullable=False, default=dict)
    allowed_capabilities = Column(JSON, nullable=False, default=list)
    budget_allocation = Column(Float, nullable=False, default=0.0)
    depth = Column(Integer, nullable=False, default=1)
    status = Column(String(32), nullable=False, default="pending", index=True)  # pending, in_progress, completed, failed, cancelled
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class AgentTeam(Base):
    """Governed multi-agent team entity."""

    __tablename__ = "agent_teams"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    workspace_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), nullable=True, index=True)
    name = Column(String(128), nullable=False)
    slug = Column(String(128), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="draft", index=True)  # draft, active, paused, disabled, archived
    current_version_id = Column(String(36), nullable=True)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        UniqueConstraint("workspace_id", "slug", name="uq_agent_teams_ws_slug"),
        Index("ix_agent_teams_ws_status", "workspace_id", "status"),
    )

    versions = relationship(
        "AgentTeamVersion",
        back_populates="team",
        cascade="all, delete-orphan",
        order_by="AgentTeamVersion.version.desc()",
    )


class AgentTeamVersion(Base):
    """Immutable version of a multi-agent team configuration."""

    __tablename__ = "agent_team_versions"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    team_id = Column(String(36), ForeignKey("agent_teams.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    objective = Column(Text, nullable=False)
    coordination_policy = Column(JSON, nullable=False, default=dict)
    shared_context_policy = Column(JSON, nullable=False, default=dict)
    approval_policy = Column(JSON, nullable=False, default=dict)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    published_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("team_id", "version", name="uq_agent_team_versions_team_ver"),
    )

    team = relationship("AgentTeam", back_populates="versions")
    members = relationship("AgentTeamMember", back_populates="team_version", cascade="all, delete-orphan")


class AgentTeamMember(Base):
    """Membership of an agent in a specific team version."""

    __tablename__ = "agent_team_members"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    team_version_id = Column(String(36), ForeignKey("agent_team_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_version_id = Column(String(36), ForeignKey("agent_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(64), nullable=False, default="specialist")  # lead, researcher, analyst, builder, reviewer, specialist, executor
    capabilities = Column(JSON, nullable=False, default=list)
    responsibilities = Column(Text, nullable=False, default="")
    limits = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    team_version = relationship("AgentTeamVersion", back_populates="members")


class AgentTeamRun(Base):
    """Execution run of a multi-agent team."""

    __tablename__ = "agent_team_runs"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    team_id = Column(String(36), ForeignKey("agent_teams.id", ondelete="CASCADE"), nullable=False, index=True)
    team_version_id = Column(String(36), ForeignKey("agent_team_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), nullable=True, index=True)
    initiated_by = Column(String(36), nullable=False)
    objective = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="created", index=True)  # created, planning, executing, waiting_for_approval, evaluating, completed, failed, cancelled
    plan = Column(JSON, nullable=False, default=dict)
    shared_context = Column(JSON, nullable=False, default=dict)
    final_synthesis = Column(JSON, nullable=True)
    cost = Column(Float, nullable=False, default=0.0)
    latency = Column(Float, nullable=False, default=0.0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)

    messages = relationship("AgentMessage", back_populates="team_run", cascade="all, delete-orphan")
    conflicts = relationship("AgentConflict", back_populates="team_run", cascade="all, delete-orphan")


class AgentMessage(Base):
    """Normalized structured message passed between agents in a team run."""

    __tablename__ = "agent_messages"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    team_run_id = Column(String(36), ForeignKey("agent_team_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_agent_id = Column(String(36), nullable=True, index=True)
    message_type = Column(String(64), nullable=False, index=True)  # task_assignment, task_result, question, answer, status_update, handoff, review, correction, final_result
    content = Column(Text, nullable=False)
    message_metadata = Column("metadata", JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)

    team_run = relationship("AgentTeamRun", back_populates="messages")


class AgentConflict(Base):
    """Discrepancy or conflict detected between multiple agents in a team run."""

    __tablename__ = "agent_conflicts"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    team_run_id = Column(String(36), ForeignKey("agent_team_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    subject = Column(String(256), nullable=False)
    agent_a_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_b_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    position_a = Column(Text, nullable=False)
    position_b = Column(Text, nullable=False)
    evidence_a = Column(JSON, nullable=False, default=dict)
    evidence_b = Column(JSON, nullable=False, default=dict)
    status = Column(String(32), nullable=False, default="open", index=True)  # open, resolved_by_evidence, resolved_by_review, resolved_by_human, unresolved
    resolution = Column(Text, nullable=True)
    resolved_by = Column(String(36), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)

    team_run = relationship("AgentTeamRun", back_populates="conflicts")
