"""
REST API routes for Step 36: Disaster Recovery, Backup & Business Continuity Layer.
Thin endpoints delegating strictly to DisasterRecoveryService and domain engines.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.disaster_recovery.service import DisasterRecoveryService
from backend.app.services.disaster_recovery.models import BackupPolicy
from backend.app.services.disaster_recovery.schemas import (
    BackupPolicyCreate,
    BackupPolicyUpdate,
    BackupPolicyResponse,
    BackupRunCreate,
    BackupRunResponse,
    BackupManifestResponse,
    BackupVerificationResponse,
    RestorePlanCreate,
    RestorePlanResponse,
    RestorePlanDryRunResult,
    RestoreRunResponse,
    RecoveryObjectiveCreate,
    RecoveryObjectiveUpdate,
    RecoveryObjectiveResponse,
    RecoveryReadinessResponse,
    ContinuityPlanCreate,
    ContinuityPlanUpdate,
    ContinuityPlanResponse,
    RecoveryExerciseCreate,
    RecoveryExerciseResponse,
    DisasterRecoveryOverviewResponse,
)
from backend.app.services.disaster_recovery.exceptions import (
    BackupNotFoundError,
    RestorePreconditionFailedError,
    CrossTenantRestoreBlockedError,
    ElevatedAuthorizationRequiredError,
    ReplaceExistingNotPermittedError,
    ProductionExerciseBlockedError,
    LegalHoldConflictError,
    DeletedDataResurrectionBlockedError,
    DisasterRecoveryError,
)

router = APIRouter(prefix="/recovery", tags=["Disaster Recovery & Business Continuity"])


# ---------------------------------------------------------------------------
# 1. Overview
# ---------------------------------------------------------------------------
@router.get("/overview", response_model=DisasterRecoveryOverviewResponse)
async def get_overview(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve high-level disaster recovery, backup, and readiness overview."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    return await svc.repository.get_overview(organization_id=org_id)


# ---------------------------------------------------------------------------
# 2. Backup Policies
# ---------------------------------------------------------------------------
@router.get("/policies", response_model=List[BackupPolicyResponse])
async def list_policies(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List configured backup policies."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    return await svc.repository.list_policies(organization_id=org_id, limit=limit, offset=offset)


@router.post("/policies", response_model=BackupPolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    payload: BackupPolicyCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new backup policy."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    user_id = str(current_user.id)
    policy = BackupPolicy(
        organization_id=org_id,
        name=payload.name,
        description=payload.description,
        resource_type=payload.resource_type,
        frequency=payload.frequency,
        retention_days=payload.retention_days,
        strategy=payload.strategy,
        enabled=payload.enabled,
        verification_frequency=payload.verification_frequency,
        created_by=user_id,
    )
    return await svc.repository.create_policy(policy)


@router.patch("/policies/{policy_id}", response_model=BackupPolicyResponse)
async def update_policy(
    policy_id: str,
    payload: BackupPolicyUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing backup policy."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    policy = await svc.repository.get_policy(policy_id, organization_id=org_id)
    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy '{policy_id}' not found.")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(policy, k, v)
    await session.commit()
    return policy


@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a backup policy."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    deleted = await svc.repository.delete_policy(policy_id, organization_id=org_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Policy '{policy_id}' not found.")


# ---------------------------------------------------------------------------
# 3. Backups & Manifests
# ---------------------------------------------------------------------------
@router.get("/backups", response_model=List[BackupRunResponse])
async def list_backups(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List historical and active backup snapshots."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    return await svc.repository.list_backups(organization_id=org_id, status=status, limit=limit, offset=offset)


@router.post("/backups", response_model=BackupRunResponse, status_code=status.HTTP_201_CREATED)
async def create_backup(
    payload: BackupRunCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Orchestrate and execute a logical backup snapshot."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    try:
        return await svc.backup.execute_backup(
            organization_id=org_id,
            workspace_id=payload.workspace_id,
            policy_id=payload.policy_id,
            resource_types=payload.resource_types,
            strategy=payload.strategy or "logical_export",
        )
    except DisasterRecoveryError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/backups/{backup_id}", response_model=BackupRunResponse)
async def get_backup(
    backup_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve single backup run details with manifest and verifications."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else None
    backup = await svc.repository.get_backup(backup_id, organization_id=org_id)
    if not backup:
        raise HTTPException(status_code=404, detail=f"Backup '{backup_id}' not found.")
    return backup


@router.post("/backups/{backup_id}/verify", response_model=List[BackupVerificationResponse])
async def verify_backup(
    backup_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run cryptographic manifest, integrity, schema, and dry-run simulation checks on backup."""
    svc = DisasterRecoveryService(session)
    try:
        return await svc.verification.verify_backup(backup_id)
    except BackupNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except DisasterRecoveryError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/backups/{backup_id}/expire", response_model=BackupRunResponse)
async def expire_backup(
    backup_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Safely mark a backup as expired, respecting legal holds."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    try:
        return await svc.retention.mark_backup_expired(backup_id, organization_id=org_id)
    except LegalHoldConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/manifests/{manifest_id}", response_model=BackupManifestResponse)
async def get_manifest(
    manifest_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve backup manifest detailing content hashes and resource inventory."""
    svc = DisasterRecoveryService(session)
    manifest = await svc.repository.get_manifest(manifest_id)
    if not manifest:
        raise HTTPException(status_code=404, detail=f"Manifest '{manifest_id}' not found.")
    return manifest


# ---------------------------------------------------------------------------
# 4. Restore Planning & Execution
# ---------------------------------------------------------------------------
@router.post("/restore-plans", response_model=RestorePlanResponse, status_code=status.HTTP_201_CREATED)
async def create_restore_plan(
    payload: RestorePlanCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Construct a restore plan evaluating tenant boundaries and elevated authorization."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    user_id = str(current_user.id)
    role = getattr(current_user, "role", "admin")
    try:
        return await svc.restore_planner.create_plan(
            organization_id=org_id,
            backup_run_id=payload.backup_run_id,
            workspace_id=payload.workspace_id,
            target_environment=payload.target_environment,
            scope=payload.scope,
            mode=payload.mode,
            conflict_policy=payload.conflict_policy,
            actor_id=user_id,
            actor_role=role,
        )
    except (CrossTenantRestoreBlockedError, ElevatedAuthorizationRequiredError, ReplaceExistingNotPermittedError) as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except DisasterRecoveryError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/restore-plans", response_model=List[RestorePlanResponse])
async def list_restore_plans(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List defined restore plans."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    return await svc.repository.list_restore_plans(organization_id=org_id, limit=limit, offset=offset)


@router.get("/restore-plans/{plan_id}", response_model=RestorePlanResponse)
async def get_restore_plan(
    plan_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get single restore plan details."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    plan = await svc.repository.get_restore_plan(plan_id, organization_id=org_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Restore plan '{plan_id}' not found.")
    return plan


@router.post("/restore-plans/{plan_id}/dry-run", response_model=RestorePlanDryRunResult)
async def dry_run_restore_plan(
    plan_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute a non-destructive dry-run simulation of a restore plan."""
    svc = DisasterRecoveryService(session)
    try:
        return await svc.restore_planner.execute_dry_run(plan_id)
    except DisasterRecoveryError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/restore-plans/{plan_id}/approve", response_model=RestorePlanResponse)
async def approve_restore_plan(
    plan_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a restore plan requiring elevated HITL review."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    plan = await svc.repository.get_restore_plan(plan_id, organization_id=org_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Restore plan '{plan_id}' not found.")
    plan.status = "approved"
    plan.approved_by = str(current_user.id)
    await session.commit()
    return plan


@router.post("/restore-plans/{plan_id}/execute", response_model=RestoreRunResponse)
async def execute_restore_plan(
    plan_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute an approved restore plan."""
    svc = DisasterRecoveryService(session)
    user_id = str(current_user.id)
    role = getattr(current_user, "role", "admin")
    try:
        return await svc.restore.execute_restore(
            plan_id=plan_id,
            actor_id=user_id,
            actor_role=role,
            has_hitl_approval=True,
        )
    except (CrossTenantRestoreBlockedError, RestorePreconditionFailedError, DeletedDataResurrectionBlockedError) as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except DisasterRecoveryError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/restores", response_model=List[RestoreRunResponse])
async def list_restores(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List restore execution runs."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    return await svc.repository.list_restore_runs(organization_id=org_id, limit=limit, offset=offset)


@router.get("/restores/{restore_id}", response_model=RestoreRunResponse)
async def get_restore(
    restore_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get single restore run details and execution log."""
    svc = DisasterRecoveryService(session)
    run = await svc.repository.get_restore_run(restore_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Restore run '{restore_id}' not found.")
    return run


# ---------------------------------------------------------------------------
# 5. Recovery Objectives & Readiness
# ---------------------------------------------------------------------------
@router.get("/objectives", response_model=List[RecoveryObjectiveResponse])
async def list_objectives(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List configured RTO and RPO targets."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    return await svc.objectives.list_objectives(organization_id=org_id)


@router.post("/objectives", response_model=RecoveryObjectiveResponse, status_code=status.HTTP_201_CREATED)
async def create_objective(
    payload: RecoveryObjectiveCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a recovery objective (RTO/RPO target)."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    return await svc.objectives.create_objective(
        organization_id=org_id,
        resource_type=payload.resource_type,
        rto_seconds=payload.rto_seconds,
        rpo_seconds=payload.rpo_seconds,
        workspace_id=payload.workspace_id,
        resource_scope=payload.resource_scope,
        priority=payload.priority,
    )


@router.get("/readiness", response_model=List[RecoveryReadinessResponse])
async def get_recovery_readiness(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Evaluate factual recovery readiness comparing backup/verification age with RTO/RPO targets."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    return await svc.objectives.evaluate_readiness(organization_id=org_id)


# ---------------------------------------------------------------------------
# 6. Continuity Plans
# ---------------------------------------------------------------------------
@router.get("/continuity-plans", response_model=List[ContinuityPlanResponse])
async def list_continuity_plans(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List documented business continuity plans."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    return await svc.continuity.list_plans(organization_id=org_id)


@router.post("/continuity-plans", response_model=ContinuityPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_continuity_plan(
    payload: ContinuityPlanCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new business continuity plan with automated service ordering."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    user_id = str(current_user.id)
    return await svc.continuity.create_plan(
        organization_id=org_id,
        name=payload.name,
        description=payload.description,
        critical_services=payload.critical_services,
        dependencies=payload.dependencies,
        fallback_modes=payload.fallback_modes,
        communication_plan=payload.communication_plan,
        recovery_order=payload.recovery_order,
        owner_id=user_id,
    )


@router.patch("/continuity-plans/{plan_id}", response_model=ContinuityPlanResponse)
async def update_continuity_plan(
    plan_id: str,
    payload: ContinuityPlanUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a business continuity plan."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    plan = await svc.continuity.update_plan(
        plan_id=plan_id,
        organization_id=org_id,
        updates=payload.model_dump(exclude_unset=True),
    )
    if not plan:
        raise HTTPException(status_code=404, detail=f"Continuity plan '{plan_id}' not found.")
    return plan


# ---------------------------------------------------------------------------
# 7. Recovery Exercises
# ---------------------------------------------------------------------------
@router.get("/exercises", response_model=List[RecoveryExerciseResponse])
async def list_exercises(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List recovery simulation exercises."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    return await svc.exercises.list_exercises(organization_id=org_id, limit=limit, offset=offset)


@router.post("/exercises", response_model=RecoveryExerciseResponse, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    payload: RecoveryExerciseCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a planned recovery simulation exercise in sandbox/test environments."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    user_id = str(current_user.id)
    try:
        return await svc.exercises.create_exercise(
            organization_id=org_id,
            name=payload.name,
            scenario=payload.scenario,
            expected_recovery=payload.expected_recovery,
            created_by=user_id,
            description=payload.description,
            environment=payload.environment,
            scope=payload.scope,
            abort_conditions=payload.abort_conditions,
        )
    except ProductionExerciseBlockedError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except DisasterRecoveryError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/exercises/{exercise_id}", response_model=RecoveryExerciseResponse)
async def get_exercise(
    exercise_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get single recovery exercise details and observations."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    exercise = await svc.exercises.get_exercise(exercise_id, organization_id=org_id)
    if not exercise:
        raise HTTPException(status_code=404, detail=f"Exercise '{exercise_id}' not found.")
    return exercise


@router.post("/exercises/{exercise_id}/run", response_model=RecoveryExerciseResponse)
async def run_exercise(
    exercise_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute a planned recovery simulation exercise."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    user_id = str(current_user.id)
    try:
        return await svc.exercises.run_exercise(
            exercise_id=exercise_id,
            organization_id=org_id,
            actor_id=user_id,
        )
    except DisasterRecoveryError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/exercises/{exercise_id}/abort", response_model=RecoveryExerciseResponse)
async def abort_exercise(
    exercise_id: str,
    reason: str = Query("Operator manual abort"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Abort an active recovery exercise."""
    svc = DisasterRecoveryService(session)
    org_id = str(current_user.organization_id) if hasattr(current_user, "organization_id") else "default-org"
    try:
        return await svc.exercises.abort_exercise(
            exercise_id=exercise_id,
            organization_id=org_id,
            reason=reason,
        )
    except DisasterRecoveryError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
