"""
SQLAlchemy ORM models for Step 35: AI Reliability, Resilience & Chaos Engineering Layer.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship as orm_relationship

from backend.app.db.database import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid_str() -> str:
    return str(uuid.uuid4())


class ReliabilityComponent(Base):
    """
    Registered subsystem or dependency tracking operational status, health, and heartbeat.
    """
    __tablename__ = "reliability_components"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=True, index=True)

    component_type = Column(String(50), nullable=False, index=True)
    component_name = Column(String(255), nullable=False, index=True)
    version = Column(String(50), nullable=True)

    status = Column(String(50), nullable=False, default="active", index=True)  # active, degraded, unavailable, maintenance, disabled
    health_status = Column(String(50), nullable=False, default="healthy", index=True)  # healthy, warning, critical, unknown

    last_heartbeat_at = Column(DateTime(timezone=True), nullable=True)
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    last_failure_at = Column(DateTime(timezone=True), nullable=True)

    failure_count = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)

    metadata_payload = Column("metadata", JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)

    # Relationships
    dependencies = orm_relationship(
        "DependencyHealth",
        back_populates="component",
        cascade="all, delete-orphan",
    )


class DependencyHealth(Base):
    """
    Lightweight, bounded health check results for a dependency of a component.
    Never performs expensive AI calls or leaks credentials.
    """
    __tablename__ = "dependency_health"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    component_id = Column(String(36), ForeignKey("reliability_components.id", ondelete="CASCADE"), nullable=False, index=True)

    check_type = Column(String(50), nullable=False, index=True)  # connectivity, authentication, availability, latency, capacity, functional
    status = Column(String(50), nullable=False, default="healthy", index=True)  # healthy, warning, critical, unknown

    latency_ms = Column(Float, nullable=True)
    error_type = Column(String(100), nullable=True)
    checked_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, index=True)

    metadata_payload = Column("metadata", JSON, nullable=False, default=dict)

    # Relationships
    component = orm_relationship("ReliabilityComponent", back_populates="dependencies")


class ExecutionCheckpoint(Base):
    """
    Durable, sanitized state snapshot of an in-flight execution step.
    Enables safe resume without repeating completed side effects.
    """
    __tablename__ = "execution_checkpoints"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), nullable=False, index=True)

    run_id = Column(String(255), nullable=False, index=True)
    workflow_run_id = Column(String(255), nullable=True, index=True)
    job_id = Column(String(255), nullable=True, index=True)
    step_id = Column(String(255), nullable=True)

    sequence_number = Column(Integer, nullable=False, default=1)
    checkpoint_type = Column(String(50), nullable=False, index=True)  # workflow_step, orchestration_step, retrieval, tool, connector, evaluation, revision, artifact_processing, document_processing

    state_snapshot = Column(JSON, nullable=False, default=dict)
    input_fingerprint = Column(String(64), nullable=False, index=True)  # SHA-256
    context_fingerprint = Column(String(64), nullable=False)  # SHA-256

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)


class ReliabilityObjective(Base):
    """
    Configured SLO defining target metrics over a rolling evaluation window.
    Reports factual adherence without claiming contractual SLA guarantees.
    """
    __tablename__ = "reliability_objectives"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=True, index=True)

    component_type = Column(String(50), nullable=False, index=True)
    component_name = Column(String(255), nullable=False, index=True)

    metric = Column(String(50), nullable=False)  # availability, latency, success_rate, failure_rate, recovery_time
    target = Column(Float, nullable=False)
    window = Column(String(50), nullable=False, default="30d")
    enabled = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)


class ReliabilityBudget(Base):
    """
    Failure budget tracking operational error thresholds before alerting or degradation.
    """
    __tablename__ = "reliability_budgets"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)

    component = Column(String(255), nullable=False, index=True)
    metric = Column(String(50), nullable=False)
    window = Column(String(50), nullable=False, default="30d")

    allowed_failure_amount = Column(Float, nullable=False)
    current_failure_amount = Column(Float, nullable=False, default=0.0)
    enabled = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)


class ChaosExperiment(Base):
    """
    Controlled chaos experiment definition strictly restricted to test/sandbox environments by default.
    Production runs strictly require Step 32 Governance and HITL authorization.
    """
    __tablename__ = "chaos_experiments"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=True, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    environment = Column(String(50), nullable=False, default="test", index=True)  # test, staging, sandbox, production

    target_type = Column(String(100), nullable=False)
    target_id = Column(String(255), nullable=False)
    failure_type = Column(String(100), nullable=False)  # simulate_timeout, simulate_provider_unavailable, simulate_rate_limit, simulate_connector_failure, etc.

    duration_seconds = Column(Integer, nullable=False, default=60)
    expected_behavior = Column(Text, nullable=False)
    abort_conditions = Column(JSON, nullable=False, default=dict)

    status = Column(String(50), nullable=False, default="planned", index=True)  # planned, approved, running, completed, aborted, failed
    created_by = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)

    # Relationships
    runs = orm_relationship(
        "ChaosRun",
        back_populates="experiment",
        cascade="all, delete-orphan",
        order_by="desc(ChaosRun.started_at)",
    )
    observations = orm_relationship(
        "ChaosObservation",
        back_populates="experiment",
        cascade="all, delete-orphan",
        order_by="desc(ChaosObservation.timestamp)",
    )


class ChaosRun(Base):
    """
    Individual execution run of a chaos experiment tracking execution logs and abort outcomes.
    """
    __tablename__ = "chaos_runs"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    experiment_id = Column(String(36), ForeignKey("chaos_experiments.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(String(50), nullable=False, default="running", index=True)  # running, completed, aborted, failed
    started_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    outcome = Column(Text, nullable=True)
    error_summary = Column(Text, nullable=True)
    logs = Column(JSON, nullable=False, default=list)
    metadata_payload = Column("metadata", JSON, nullable=False, default=dict)

    # Relationships
    experiment = orm_relationship("ChaosExperiment", back_populates="runs")
    observations = orm_relationship("ChaosObservation", back_populates="run", cascade="all, delete-orphan")


class ChaosObservation(Base):
    """
    Recorded observation telemetry during a chaos run validating resilience assumptions.
    """
    __tablename__ = "chaos_observations"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    experiment_id = Column(String(36), ForeignKey("chaos_experiments.id", ondelete="CASCADE"), nullable=False, index=True)
    run_id = Column(String(36), ForeignKey("chaos_runs.id", ondelete="CASCADE"), nullable=True, index=True)

    timestamp = Column(DateTime(timezone=True), nullable=False, default=_utc_now, index=True)
    metric = Column(String(100), nullable=False)
    value = Column(Float, nullable=True)
    expected_value = Column(Float, nullable=True)
    status = Column(String(50), nullable=False, default="matched", index=True)  # matched, deviated, critical

    metadata_payload = Column("metadata", JSON, nullable=False, default=dict)

    # Relationships
    experiment = orm_relationship("ChaosExperiment", back_populates="observations")
    run = orm_relationship("ChaosRun", back_populates="observations")
