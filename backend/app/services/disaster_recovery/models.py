"""
SQLAlchemy ORM models for Step 36: Disaster Recovery, Backup & Business Continuity Layer.
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


class BackupResource(Base):
    """
    Catalog of platform assets marked for backup orchestration and lifecycle tracking.
    """
    __tablename__ = "backup_resources"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=True, index=True)
    project_id = Column(String(36), nullable=True)

    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(255), nullable=False, index=True)
    classification = Column(String(50), nullable=False, default="internal")  # public, internal, confidential, restricted

    backup_required = Column(Boolean, nullable=False, default=True)
    backup_strategy = Column(String(50), nullable=False, default="logical_export")  # full, incremental, logical_export
    dependency_policy = Column(String(50), nullable=False, default="required")  # required, optional, isolated
    retention_policy_id = Column(String(36), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)


class BackupPolicy(Base):
    """
    Organization-level backup policies defining frequency, retention, and verification cadence.
    """
    __tablename__ = "backup_policies"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=True, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    resource_type = Column(String(100), nullable=False, default="all")  # all or specific type
    frequency = Column(String(50), nullable=False, default="daily")  # hourly, daily, weekly
    retention_days = Column(Integer, nullable=False, default=30)
    strategy = Column(String(50), nullable=False, default="logical_export")  # full, incremental, logical_export
    enabled = Column(Boolean, nullable=False, default=True)
    verification_frequency = Column(String(50), nullable=False, default="after_backup")  # after_backup, weekly, manual

    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)

    # Relationships
    runs = orm_relationship("BackupRun", back_populates="policy", cascade="all, delete-orphan")


class BackupRun(Base):
    """
    Execution instance of an orchestrated backup snapshot.
    """
    __tablename__ = "backup_runs"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=True, index=True)
    policy_id = Column(String(36), ForeignKey("backup_policies.id"), nullable=True, index=True)

    status = Column(String(50), nullable=False, default="planned", index=True)  # planned, queued, running, verifying, completed, failed, cancelled, expired
    started_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    resource_count = Column(Integer, nullable=False, default=0)
    byte_estimate = Column(Integer, nullable=True)
    backup_version = Column(String(50), nullable=False, default="1.0")
    manifest_id = Column(String(36), nullable=True)
    classification = Column(String(50), nullable=False, default="internal")
    error = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, index=True)

    # Relationships
    policy = orm_relationship("BackupPolicy", back_populates="runs")
    manifest = orm_relationship("BackupManifest", back_populates="backup_run", uselist=False, cascade="all, delete-orphan")
    verifications = orm_relationship("BackupVerification", back_populates="backup_run", cascade="all, delete-orphan")
    restore_plans = orm_relationship("RestorePlan", back_populates="backup_run")


class BackupManifest(Base):
    """
    Cryptographic manifest detailing backup content inventory, SHA-256 hashes, and storage references.
    """
    __tablename__ = "backup_manifests"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    backup_run_id = Column(String(36), ForeignKey("backup_runs.id"), nullable=False, unique=True, index=True)

    version = Column(String(50), nullable=False, default="1.0")
    format = Column(String(50), nullable=False, default="json_logical")
    resource_count = Column(Integer, nullable=False, default=0)

    content_hash = Column(String(64), nullable=False)  # SHA-256 of resources package
    manifest_hash = Column(String(64), nullable=False)  # SHA-256 of manifest body
    previous_manifest_hash = Column(String(64), nullable=True)

    storage_reference = Column(String(512), nullable=False)
    encryption_metadata = Column(JSON, nullable=False, default=dict)
    verification_status = Column(String(50), nullable=False, default="unverified")  # unverified, verified, failed
    resources_metadata = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)

    # Relationships
    backup_run = orm_relationship("BackupRun", back_populates="manifest")


class BackupVerification(Base):
    """
    Verification records confirming backup integrity, schema correctness, and simulation results.
    """
    __tablename__ = "backup_verifications"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    backup_run_id = Column(String(36), ForeignKey("backup_runs.id"), nullable=False, index=True)

    verification_type = Column(String(50), nullable=False)  # manifest, integrity, schema, dependency, restore_simulation
    status = Column(String(50), nullable=False, default="pending", index=True)  # pending, passed, failed, warning
    started_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    details = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)

    # Relationships
    backup_run = orm_relationship("BackupRun", back_populates="verifications")


class RestorePlan(Base):
    """
    Execution blueprint for restoring scoped resources from an integrity-verified backup.
    """
    __tablename__ = "restore_plans"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=True, index=True)
    backup_run_id = Column(String(36), ForeignKey("backup_runs.id"), nullable=False, index=True)

    target_environment = Column(String(50), nullable=False, default="sandbox")  # sandbox, staging, production
    scope = Column(JSON, nullable=False, default=dict)  # resource_types, specific_ids
    mode = Column(String(50), nullable=False, default="dry_run", index=True)  # dry_run, sandbox, authorized_restore
    conflict_policy = Column(String(50), nullable=False, default="skip_existing")  # fail, skip_existing, restore_missing, replace_existing

    status = Column(String(50), nullable=False, default="planned", index=True)  # planned, awaiting_approval, approved, rejected, executing, completed, failed
    approval_id = Column(String(36), nullable=True)
    approved_by = Column(String(255), nullable=True)
    blast_radius_summary = Column(JSON, nullable=False, default=dict)

    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)

    # Relationships
    backup_run = orm_relationship("BackupRun", back_populates="restore_plans")
    runs = orm_relationship("RestoreRun", back_populates="plan", cascade="all, delete-orphan")


class RestoreRun(Base):
    """
    Execution run of a restore plan.
    """
    __tablename__ = "restore_runs"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    restore_plan_id = Column(String(36), ForeignKey("restore_plans.id"), nullable=False, index=True)

    status = Column(String(50), nullable=False, default="planned", index=True)  # planned, awaiting_approval, queued, running, verifying, completed, failed, cancelled, rolled_back
    started_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    resource_count = Column(Integer, nullable=False, default=0)
    restored_count = Column(Integer, nullable=False, default=0)
    skipped_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    error = Column(Text, nullable=True)
    execution_log = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)

    # Relationships
    plan = orm_relationship("RestorePlan", back_populates="runs")


class RecoveryObjective(Base):
    """
    Recovery Time Objective (RTO) and Recovery Point Objective (RPO) targets per resource type.
    """
    __tablename__ = "recovery_objectives"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=True, index=True)

    resource_type = Column(String(100), nullable=False, index=True)
    resource_scope = Column(String(255), nullable=False, default="all")
    rto_seconds = Column(Integer, nullable=False)  # Target recovery duration
    rpo_seconds = Column(Integer, nullable=False)  # Target maximum data loss interval
    priority = Column(String(50), nullable=False, default="tier_1")  # tier_1, tier_2, tier_3
    enabled = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)


class RecoveryReadiness(Base):
    """
    Operational readiness state comparing observed backup/restore measurements with configured RTO/RPO.
    """
    __tablename__ = "recovery_readiness"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=True, index=True)

    resource_type = Column(String(100), nullable=False, index=True)
    backup_status = Column(String(50), nullable=False, default="unknown")  # ready, warning, missing
    verification_status = Column(String(50), nullable=False, default="unknown")  # verified, unverified, failed
    restore_test_status = Column(String(50), nullable=False, default="unknown")  # passed, failed, not_tested

    last_successful_backup = Column(DateTime(timezone=True), nullable=True)
    last_successful_verification = Column(DateTime(timezone=True), nullable=True)
    last_successful_restore_test = Column(DateTime(timezone=True), nullable=True)

    observed_backup_age_seconds = Column(Integer, nullable=True)
    estimated_restore_duration_seconds = Column(Integer, nullable=True)
    overall_status = Column(String(50), nullable=False, default="unknown", index=True)  # ready, needs_attention, blocked, unknown
    known_blockers = Column(JSON, nullable=False, default=list)

    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)


class ContinuityPlan(Base):
    """
    Documented business continuity plan defining critical service tiers, dependencies, and fallback workflows.
    """
    __tablename__ = "continuity_plans"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    critical_services = Column(JSON, nullable=False, default=list)
    dependencies = Column(JSON, nullable=False, default=dict)
    fallback_modes = Column(JSON, nullable=False, default=dict)
    communication_plan = Column(JSON, nullable=False, default=dict)
    recovery_order = Column(JSON, nullable=False, default=list)

    owner_id = Column(String(255), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)


class RecoveryExercise(Base):
    """
    Controlled disaster-recovery simulation exercise conducted in non-production environments.
    """
    __tablename__ = "recovery_exercises"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    environment = Column(String(50), nullable=False, default="sandbox", index=True)  # test, staging, sandbox, production
    scope = Column(JSON, nullable=False, default=dict)
    scenario = Column(String(100), nullable=False)  # database_restore_simulation, workflow_recovery, etc.

    expected_recovery = Column(Text, nullable=False)
    abort_conditions = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="planned", index=True)  # planned, approved, running, completed, aborted, failed

    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    observations = orm_relationship("RecoveryExerciseObservation", back_populates="exercise", cascade="all, delete-orphan")


class RecoveryExerciseObservation(Base):
    """
    Empirical measurements and observations recorded during a recovery exercise.
    """
    __tablename__ = "recovery_exercise_observations"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    exercise_id = Column(String(36), ForeignKey("recovery_exercises.id"), nullable=False, index=True)

    timestamp = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    metric = Column(String(100), nullable=False)
    value = Column(String(255), nullable=False)
    expected_value = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="passed")  # passed, failed, warning
    details = Column(JSON, nullable=False, default=dict)

    # Relationships
    exercise = orm_relationship("RecoveryExercise", back_populates="observations")
