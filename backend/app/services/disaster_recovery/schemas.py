"""
Pydantic V2 schemas for Step 36: Disaster Recovery, Backup & Business Continuity Layer.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# 1. Backup Resources & Policies
# ---------------------------------------------------------------------------
class BackupResourceCreate(BaseModel):
    organization_id: str
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    resource_type: str
    resource_id: str
    classification: str = "internal"
    backup_required: bool = True
    backup_strategy: str = "logical_export"
    dependency_policy: str = "required"
    retention_policy_id: Optional[str] = None


class BackupResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    resource_type: str
    resource_id: str
    classification: str
    backup_required: bool
    backup_strategy: str
    dependency_policy: str
    retention_policy_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BackupPolicyCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    resource_type: str = "all"
    frequency: str = "daily"  # hourly, daily, weekly
    retention_days: int = Field(30, ge=1, le=3650)
    strategy: str = "logical_export"  # full, incremental, logical_export
    enabled: bool = True
    verification_frequency: str = "after_backup"


class BackupPolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    frequency: Optional[str] = None
    retention_days: Optional[int] = Field(None, ge=1, le=3650)
    strategy: Optional[str] = None
    enabled: Optional[bool] = None
    verification_frequency: Optional[str] = None


class BackupPolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    workspace_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    resource_type: str
    frequency: str
    retention_days: int
    strategy: str
    enabled: bool
    verification_frequency: str
    created_by: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# 2. Backup Runs, Manifests & Verifications
# ---------------------------------------------------------------------------
class BackupRunCreate(BaseModel):
    policy_id: Optional[str] = None
    workspace_id: Optional[str] = None
    resource_types: Optional[List[str]] = None
    strategy: Optional[str] = "logical_export"


class BackupManifestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    backup_run_id: str
    version: str
    format: str
    resource_count: int
    content_hash: str
    manifest_hash: str
    previous_manifest_hash: Optional[str] = None
    storage_reference: str
    encryption_metadata: Dict[str, Any]
    verification_status: str
    resources_metadata: List[Dict[str, Any]]
    created_at: datetime


class BackupVerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    backup_run_id: str
    verification_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    details: Dict[str, Any]
    created_at: datetime


class BackupRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    workspace_id: Optional[str] = None
    policy_id: Optional[str] = None
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    resource_count: int
    byte_estimate: Optional[int] = None
    backup_version: str
    manifest_id: Optional[str] = None
    classification: str
    error: Optional[str] = None
    created_at: datetime
    manifest: Optional[BackupManifestResponse] = None
    verifications: List[BackupVerificationResponse] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 3. Restore Plans & Runs
# ---------------------------------------------------------------------------
class RestorePlanCreate(BaseModel):
    backup_run_id: str
    workspace_id: Optional[str] = None
    target_environment: str = "sandbox"  # sandbox, staging, production
    scope: Dict[str, Any] = Field(default_factory=dict)
    mode: str = "dry_run"  # dry_run, sandbox, authorized_restore
    conflict_policy: str = "skip_existing"  # fail, skip_existing, restore_missing, replace_existing


class RestorePlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    workspace_id: Optional[str] = None
    backup_run_id: str
    target_environment: str
    scope: Dict[str, Any]
    mode: str
    conflict_policy: str
    status: str
    approval_id: Optional[str] = None
    approved_by: Optional[str] = None
    blast_radius_summary: Dict[str, Any]
    created_by: str
    created_at: datetime
    updated_at: datetime


class RestoreRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    restore_plan_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    resource_count: int
    restored_count: int
    skipped_count: int
    failed_count: int
    error: Optional[str] = None
    execution_log: List[Dict[str, Any]]
    created_at: datetime


class RestorePlanDryRunResult(BaseModel):
    plan_id: str
    backup_run_id: str
    is_valid: bool
    manifest_verified: bool
    hashes_verified: bool
    resource_count: int
    affected_resources: List[Dict[str, Any]]
    detected_conflicts: List[Dict[str, Any]]
    legal_hold_checks_passed: bool
    deleted_data_conflicts_passed: bool
    requires_hitl: bool
    blast_radius_summary: Dict[str, Any]


# ---------------------------------------------------------------------------
# 4. Recovery Objectives & Readiness
# ---------------------------------------------------------------------------
class RecoveryObjectiveCreate(BaseModel):
    workspace_id: Optional[str] = None
    resource_type: str
    resource_scope: str = "all"
    rto_seconds: int = Field(..., ge=60, description="Recovery Time Objective in seconds")
    rpo_seconds: int = Field(..., ge=60, description="Recovery Point Objective in seconds")
    priority: str = "tier_1"
    enabled: bool = True


class RecoveryObjectiveUpdate(BaseModel):
    resource_scope: Optional[str] = None
    rto_seconds: Optional[int] = Field(None, ge=60)
    rpo_seconds: Optional[int] = Field(None, ge=60)
    priority: Optional[str] = None
    enabled: Optional[bool] = None


class RecoveryObjectiveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    workspace_id: Optional[str] = None
    resource_type: str
    resource_scope: str
    rto_seconds: int
    rpo_seconds: int
    priority: str
    enabled: bool
    created_at: datetime
    updated_at: datetime


class RecoveryReadinessResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    workspace_id: Optional[str] = None
    resource_type: str
    backup_status: str
    verification_status: str
    restore_test_status: str
    last_successful_backup: Optional[datetime] = None
    last_successful_verification: Optional[datetime] = None
    last_successful_restore_test: Optional[datetime] = None
    observed_backup_age_seconds: Optional[int] = None
    estimated_restore_duration_seconds: Optional[int] = None
    overall_status: str
    known_blockers: List[str]
    updated_at: datetime


# ---------------------------------------------------------------------------
# 5. Continuity Plans & Recovery Exercises
# ---------------------------------------------------------------------------
class ContinuityPlanCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    critical_services: List[str] = Field(default_factory=list)
    dependencies: Dict[str, Any] = Field(default_factory=dict)
    fallback_modes: Dict[str, Any] = Field(default_factory=dict)
    communication_plan: Dict[str, Any] = Field(default_factory=dict)
    recovery_order: List[str] = Field(default_factory=list)
    enabled: bool = True


class ContinuityPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    critical_services: Optional[List[str]] = None
    dependencies: Optional[Dict[str, Any]] = None
    fallback_modes: Optional[Dict[str, Any]] = None
    communication_plan: Optional[Dict[str, Any]] = None
    recovery_order: Optional[List[str]] = None
    enabled: Optional[bool] = None


class ContinuityPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    name: str
    description: Optional[str] = None
    critical_services: List[str]
    dependencies: Dict[str, Any]
    fallback_modes: Dict[str, Any]
    communication_plan: Dict[str, Any]
    recovery_order: List[str]
    owner_id: str
    enabled: bool
    created_at: datetime
    updated_at: datetime


class RecoveryExerciseObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    exercise_id: str
    timestamp: datetime
    metric: str
    value: str
    expected_value: Optional[str] = None
    status: str
    details: Dict[str, Any]


class RecoveryExerciseCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    environment: str = "sandbox"  # test, staging, sandbox, production
    scope: Dict[str, Any] = Field(default_factory=dict)
    scenario: str = "database_restore_simulation"
    expected_recovery: str
    abort_conditions: Optional[str] = None


class RecoveryExerciseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    name: str
    description: Optional[str] = None
    environment: str
    scope: Dict[str, Any]
    scenario: str
    expected_recovery: str
    abort_conditions: Optional[str] = None
    status: str
    created_by: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    observations: List[RecoveryExerciseObservationResponse] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 6. Disaster Recovery Overview
# ---------------------------------------------------------------------------
class DisasterRecoveryOverviewResponse(BaseModel):
    total_backups: int
    completed_backups: int
    verified_backups: int
    stale_backups: int
    active_policies: int
    recovery_readiness_status: str  # ready, needs_attention, blocked
    open_recovery_blockers: int
    last_backup_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None
    recent_restores_count: int
    completed_exercises_count: int
