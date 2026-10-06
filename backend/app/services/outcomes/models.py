"""
SQLAlchemy models for Step 43:
AI Outcome Intelligence & Work Impact Layer.
"""
from datetime import datetime, timezone
import uuid
from typing import Optional, List, Dict, Any
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


class Objective(Base):
    """
    Intended strategic result or business objective, distinct from individual tasks.
    """
    __tablename__ = "objectives"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    workspace_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    objective_type = Column(
        String(32),
        nullable=False,
        default="business",
        index=True,
    )  # business, product, engineering, research, operations, security, compliance, personal, project
    status = Column(
        String(32),
        nullable=False,
        default="draft",
        index=True,
    )  # draft, active, at_risk, completed, cancelled, archived
    priority = Column(String(32), nullable=False, default="medium")  # low, medium, high, critical
    owner_user_id = Column(String(36), nullable=True, index=True)
    created_by = Column(String(36), nullable=False)
    requirements = Column(JSON, nullable=False, default=dict)  # required_evidence, required_approval, etc.
    start_at = Column(DateTime(timezone=True), nullable=True)
    target_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_objectives_ws_status", "workspace_id", "status"),
        Index("ix_objectives_ws_priority", "workspace_id", "priority"),
    )

    targets = relationship(
        "OutcomeTarget",
        back_populates="objective",
        cascade="all, delete-orphan",
        order_by="OutcomeTarget.created_at",
    )
    milestones = relationship(
        "OutcomeMilestone",
        back_populates="objective",
        cascade="all, delete-orphan",
        order_by="OutcomeMilestone.created_at",
    )
    outcomes = relationship(
        "Outcome",
        back_populates="objective",
        cascade="all, delete-orphan",
        order_by="Outcome.created_at",
    )


class OutcomeTarget(Base):
    """
    Key result / target metric specification associated with an Objective.
    """
    __tablename__ = "outcome_targets"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    objective_id = Column(String(36), ForeignKey("objectives.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    metric_type = Column(
        String(32),
        nullable=False,
        default="count",
    )  # count, percentage, duration, currency, boolean, rate, ratio, custom
    target_value = Column(Float, nullable=True)
    target_unit = Column(String(64), nullable=True)
    baseline_value = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)
    target_date = Column(DateTime(timezone=True), nullable=True)
    measurement_source = Column(
        String(64),
        nullable=False,
        default="system",
    )  # manual, system, connector, workflow, evaluation, event, artifact, document, external_reference
    status = Column(
        String(32),
        nullable=False,
        default="planned",
        index=True,
    )  # planned, on_track, at_risk, missed, achieved
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    objective = relationship("Objective", back_populates="targets")
    measurements = relationship("OutcomeMeasurement", back_populates="target", cascade="all, delete-orphan")


class Outcome(Base):
    """
    Evidence-backed intended deliverable or impact of AI work execution.
    """
    __tablename__ = "outcomes"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    workspace_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), nullable=True, index=True)
    objective_id = Column(String(36), ForeignKey("objectives.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    outcome_type = Column(
        String(64),
        nullable=False,
        default="deliverable",
        index=True,
    )  # deliverable, decision, resolution, optimization, risk_reduction, issue_resolution, research_finding, automation, approval, milestone, customer_outcome, operational_outcome, security_outcome
    status = Column(
        String(32),
        nullable=False,
        default="planned",
        index=True,
    )  # planned, in_progress, observed, verified, disputed, failed, cancelled
    confidence = Column(
        String(32),
        nullable=False,
        default="unverified",
    )  # unverified, supported, strongly_supported, verified, disputed (evidence state, NOT opaque score)
    owner_user_id = Column(String(36), nullable=True, index=True)
    created_by = Column(String(36), nullable=False)
    requirements = Column(JSON, nullable=False, default=dict)  # required conditions to verify
    observed_at = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_outcomes_ws_status", "workspace_id", "status"),
        Index("ix_outcomes_ws_type", "workspace_id", "outcome_type"),
    )

    objective = relationship("Objective", back_populates="outcomes")
    evidence = relationship(
        "OutcomeEvidence",
        back_populates="outcome",
        cascade="all, delete-orphan",
        order_by="OutcomeEvidence.created_at",
    )
    work_links = relationship(
        "OutcomeWorkLink",
        back_populates="outcome",
        cascade="all, delete-orphan",
        order_by="OutcomeWorkLink.created_at",
    )
    measurements = relationship(
        "OutcomeMeasurement",
        back_populates="outcome",
        cascade="all, delete-orphan",
        order_by="OutcomeMeasurement.created_at",
    )
    attributions = relationship(
        "OutcomeAttribution",
        back_populates="outcome",
        cascade="all, delete-orphan",
        order_by="OutcomeAttribution.created_at",
    )
    impact_analyses = relationship(
        "ImpactAnalysis",
        back_populates="outcome",
        cascade="all, delete-orphan",
        order_by="ImpactAnalysis.created_at",
    )


class OutcomeWorkLink(Base):
    """
    Connects outcomes to underlying work executions (Task, Workflow, Run, AgentRun, Artifact, etc.).
    """
    __tablename__ = "outcome_work_links"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    outcome_id = Column(String(36), ForeignKey("outcomes.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type = Column(
        String(64),
        nullable=False,
    )  # Task, Run, Workflow, WorkflowRun, AgentRun, AgentTeamRun, Document, Artifact, EvaluationRun, SimulationRun, Decision, CollaborationSession
    resource_id = Column(String(255), nullable=False, index=True)
    relationship_type = Column(
        String(64),
        nullable=False,
        default="contributes_to",
    )  # contributes_to, produced, supports, validated_by, blocked_by, derived_from, measures, implements
    evidence_ids = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    __table_args__ = (
        Index("ix_outcome_work_links_res", "resource_type", "resource_id"),
    )

    outcome = relationship("Outcome", back_populates="work_links")


class OutcomeEvidence(Base):
    """
    Concrete evidence artifact backing an outcome claim, retaining provenance and validation status.
    """
    __tablename__ = "outcome_evidence"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    outcome_id = Column(String(36), ForeignKey("outcomes.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(64), nullable=False)  # Task, Run, Workflow, Agent, Artifact, Document, User, Evaluation, Simulation, Connector, External
    source_id = Column(String(255), nullable=False)
    evidence_type = Column(
        String(64),
        nullable=False,
    )  # execution_result, evaluation_result, human_confirmation, artifact, document, connector_record, workflow_result, metric_observation, security_event, simulation_result, collaboration_decision, external_reference
    description = Column(Text, nullable=False)
    snapshot = Column(JSON, nullable=False, default=dict)  # Provenance, hashes, raw records, verified signatures
    status = Column(
        String(32),
        nullable=False,
        default="unreviewed",
        index=True,
    )  # unreviewed, supported, rejected, superseded
    is_human_confirmed = Column(Boolean, nullable=False, default=False)
    is_ai_generated = Column(Boolean, nullable=False, default=False)
    observed_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)

    outcome = relationship("Outcome", back_populates="evidence")


class OutcomeMeasurement(Base):
    """
    Factual observation of a metric associated with an outcome or target.
    """
    __tablename__ = "outcome_measurements"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    outcome_id = Column(String(36), ForeignKey("outcomes.id", ondelete="CASCADE"), nullable=False, index=True)
    target_id = Column(String(36), ForeignKey("outcome_targets.id", ondelete="SET NULL"), nullable=True, index=True)
    metric_name = Column(String(128), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(64), nullable=False)
    measurement_source = Column(String(64), nullable=False)  # manual, system, connector, workflow, evaluation, event, artifact, document, external_reference
    observed_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    evidence_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)

    outcome = relationship("Outcome", back_populates="measurements")
    target = relationship("OutcomeTarget", back_populates="measurements")


class OutcomeMilestone(Base):
    """
    Milestone event marking progress towards an Objective.
    """
    __tablename__ = "outcome_milestones"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    objective_id = Column(String(36), ForeignKey("objectives.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        String(32),
        nullable=False,
        default="planned",
        index=True,
    )  # planned, in_progress, blocked, completed, missed, cancelled
    due_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    owner_user_id = Column(String(36), nullable=True, index=True)
    connected_resource_type = Column(String(64), nullable=True)  # Task, Workflow, AgentRun, HumanApproval, Deliverable
    connected_resource_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    objective = relationship("Objective", back_populates="milestones")


class WorkDecision(Base):
    """
    Decision record affecting outcomes or objectives, with provenance and governance.
    """
    __tablename__ = "work_decisions"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    workspace_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), nullable=True, index=True)
    objective_id = Column(String(36), nullable=True, index=True)
    outcome_id = Column(String(36), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    decision_type = Column(
        String(32),
        nullable=False,
        default="human",
        index=True,
    )  # human, AI_assisted, policy, workflow, agent, team
    status = Column(
        String(32),
        nullable=False,
        default="proposed",
        index=True,
    )  # proposed, under_review, approved, rejected, superseded
    decision_owner = Column(String(255), nullable=False)
    evidence_ids = Column(JSON, nullable=False, default=list)
    provenance = Column(
        JSON,
        nullable=False,
        default=dict,
    )  # agent_id, agent_version_id, run_id, model_provider, prompt_version, evaluation_id, approval_id
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_work_decisions_ws_status", "workspace_id", "status"),
    )


class OutcomeAttribution(Base):
    """
    Attribution relationship linking resources to outcomes, clearly distinguishing direct causality from contribution.
    """
    __tablename__ = "outcome_attributions"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    outcome_id = Column(String(36), ForeignKey("outcomes.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(255), nullable=False, index=True)
    attribution_type = Column(
        String(32),
        nullable=False,
        default="contributing",
    )  # direct, supporting, contributing, blocking, unknown
    evidence_ids = Column(JSON, nullable=False, default=list)
    explanation = Column(Text, nullable=False)
    attribution_source = Column(
        String(32),
        nullable=False,
        default="deterministic",
    )  # deterministic, human, AI_GENERATED_ATTRIBUTION
    attribution_confidence = Column(
        String(32),
        nullable=False,
        default="inferred",
    )  # observed, estimated, inferred
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    outcome = relationship("Outcome", back_populates="attributions")


class ImpactAnalysis(Base):
    """
    Evidence-backed comparison of observed vs baseline impact across time, cost, risk, quality, etc.
    """
    __tablename__ = "impact_analyses"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    outcome_id = Column(String(36), ForeignKey("outcomes.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_type = Column(
        String(32),
        nullable=False,
    )  # time_saved, cost_change, risk_change, quality_change, throughput_change, resolution_change, process_change, operational_change
    summary = Column(Text, nullable=False)
    evidence_ids = Column(JSON, nullable=False, default=list)
    observations = Column(JSON, nullable=False, default=list)
    limitations = Column(Text, nullable=True)
    attribution_confidence = Column(
        String(32),
        nullable=False,
        default="observed",
    )  # observed, estimated, inferred
    baseline_value = Column(Float, nullable=True)
    observed_value = Column(Float, nullable=True)
    difference_value = Column(Float, nullable=True)
    unit = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    outcome = relationship("Outcome", back_populates="impact_analyses")


class OutcomeHealthRecord(Base):
    """
    Deterministic snapshot of objective/outcome health with explicit, explainable reasons.
    """
    __tablename__ = "outcome_health_records"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    objective_id = Column(String(36), nullable=True, index=True)
    outcome_id = Column(String(36), nullable=True, index=True)
    health_status = Column(
        String(32),
        nullable=False,
        default="healthy",
    )  # healthy, at_risk, blocked, stale, verified, disputed, failed
    reasons = Column(JSON, nullable=False, default=list)  # explicit deterministic reason strings
    checked_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
