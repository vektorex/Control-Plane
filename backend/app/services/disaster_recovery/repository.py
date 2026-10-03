"""
Database repository for Step 36: Disaster Recovery, Backup & Business Continuity Layer.
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_

from backend.app.services.disaster_recovery.models import (
    BackupResource,
    BackupPolicy,
    BackupRun,
    BackupManifest,
    BackupVerification,
    RestorePlan,
    RestoreRun,
    RecoveryObjective,
    ContinuityPlan,
    RecoveryExercise,
)
from backend.app.services.disaster_recovery.schemas import DisasterRecoveryOverviewResponse


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DisasterRecoveryRepository:
    """
    Data access layer for disaster recovery, backups, restore plans, and readiness telemetry.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # ---------------------------------------------------------------------------
    # Policies
    # ---------------------------------------------------------------------------
    async def list_policies(
        self,
        organization_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[BackupPolicy]:
        res = await self.session.execute(
            select(BackupPolicy)
            .where(BackupPolicy.organization_id == organization_id)
            .order_by(BackupPolicy.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(res.scalars().all())

    async def get_policy(self, policy_id: str, organization_id: str) -> Optional[BackupPolicy]:
        res = await self.session.execute(
            select(BackupPolicy).where(
                BackupPolicy.id == policy_id,
                BackupPolicy.organization_id == organization_id,
            )
        )
        return res.scalar_one_or_none()

    async def create_policy(self, policy: BackupPolicy) -> BackupPolicy:
        self.session.add(policy)
        await self.session.commit()
        return policy

    async def delete_policy(self, policy_id: str, organization_id: str) -> bool:
        policy = await self.get_policy(policy_id, organization_id)
        if policy:
            await self.session.delete(policy)
            await self.session.commit()
            return True
        return False

    # ---------------------------------------------------------------------------
    # Backups & Manifests
    # ---------------------------------------------------------------------------
    async def list_backups(
        self,
        organization_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[BackupRun]:
        query = select(BackupRun).where(BackupRun.organization_id == organization_id)
        if status:
            query = query.where(BackupRun.status == status)
        query = query.order_by(BackupRun.created_at.desc()).limit(limit).offset(offset)
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def get_backup(self, backup_id: str, organization_id: Optional[str] = None) -> Optional[BackupRun]:
        query = select(BackupRun).where(BackupRun.id == backup_id)
        if organization_id:
            query = query.where(BackupRun.organization_id == organization_id)
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def get_manifest(self, manifest_id: str) -> Optional[BackupManifest]:
        res = await self.session.execute(
            select(BackupManifest).where(BackupManifest.id == manifest_id)
        )
        return res.scalar_one_or_none()

    # ---------------------------------------------------------------------------
    # Restore Plans & Runs
    # ---------------------------------------------------------------------------
    async def list_restore_plans(
        self,
        organization_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[RestorePlan]:
        res = await self.session.execute(
            select(RestorePlan)
            .where(RestorePlan.organization_id == organization_id)
            .order_by(RestorePlan.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(res.scalars().all())

    async def get_restore_plan(self, plan_id: str, organization_id: str) -> Optional[RestorePlan]:
        res = await self.session.execute(
            select(RestorePlan).where(
                RestorePlan.id == plan_id,
                RestorePlan.organization_id == organization_id,
            )
        )
        return res.scalar_one_or_none()

    async def list_restore_runs(
        self,
        organization_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[RestoreRun]:
        res = await self.session.execute(
            select(RestoreRun)
            .join(RestorePlan, RestoreRun.restore_plan_id == RestorePlan.id)
            .where(RestorePlan.organization_id == organization_id)
            .order_by(RestoreRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(res.scalars().all())

    async def get_restore_run(self, run_id: str) -> Optional[RestoreRun]:
        res = await self.session.execute(
            select(RestoreRun).where(RestoreRun.id == run_id)
        )
        return res.scalar_one_or_none()

    # ---------------------------------------------------------------------------
    # Overview Aggregation
    # ---------------------------------------------------------------------------
    async def get_overview(self, organization_id: str) -> DisasterRecoveryOverviewResponse:
        """
        Aggregate high-level operational statistics without subjective scoring.
        """
        # 1. Total backups
        res_total = await self.session.execute(
            select(func.count(BackupRun.id)).where(BackupRun.organization_id == organization_id)
        )
        total_backups = res_total.scalar() or 0

        # 2. Completed backups
        res_completed = await self.session.execute(
            select(func.count(BackupRun.id)).where(
                BackupRun.organization_id == organization_id,
                BackupRun.status == "completed",
            )
        )
        completed_backups = res_completed.scalar() or 0

        # 3. Verified backups
        res_verified = await self.session.execute(
            select(func.count(BackupManifest.id))
            .join(BackupRun, BackupManifest.backup_run_id == BackupRun.id)
            .where(
                BackupRun.organization_id == organization_id,
                BackupManifest.verification_status == "verified",
            )
        )
        verified_backups = res_verified.scalar() or 0

        # 4. Active policies
        res_pol = await self.session.execute(
            select(func.count(BackupPolicy.id)).where(
                BackupPolicy.organization_id == organization_id,
                BackupPolicy.enabled == True,
            )
        )
        active_policies = res_pol.scalar() or 0

        # 5. Latest backup and verified dates
        res_last = await self.session.execute(
            select(BackupRun.completed_at)
            .where(BackupRun.organization_id == organization_id, BackupRun.status == "completed")
            .order_by(desc(BackupRun.completed_at))
            .limit(1)
        )
        last_backup_at = res_last.scalar_one_or_none()

        res_last_ver = await self.session.execute(
            select(BackupManifest.created_at)
            .join(BackupRun, BackupManifest.backup_run_id == BackupRun.id)
            .where(
                BackupRun.organization_id == organization_id,
                BackupManifest.verification_status == "verified",
            )
            .order_by(desc(BackupManifest.created_at))
            .limit(1)
        )
        last_verified_at = res_last_ver.scalar_one_or_none()

        # 6. Recent restores
        res_rst = await self.session.execute(
            select(func.count(RestoreRun.id))
            .join(RestorePlan, RestoreRun.restore_plan_id == RestorePlan.id)
            .where(RestorePlan.organization_id == organization_id)
        )
        recent_restores = res_rst.scalar() or 0

        # 7. Completed exercises
        res_ex = await self.session.execute(
            select(func.count(RecoveryExercise.id)).where(
                RecoveryExercise.organization_id == organization_id,
                RecoveryExercise.status == "completed",
            )
        )
        completed_exercises = res_ex.scalar() or 0

        # Check staleness: backup > 24 hours old
        is_stale = False
        if last_backup_at:
            is_stale = (_utc_now() - last_backup_at).total_seconds() > 86400
        else:
            is_stale = total_backups > 0

        stale_count = 1 if is_stale else 0
        readiness_status = "ready" if verified_backups > 0 and not is_stale else "needs_attention" if completed_backups > 0 else "blocked"
        open_blockers = 1 if is_stale or verified_backups == 0 else 0

        return DisasterRecoveryOverviewResponse(
            total_backups=total_backups,
            completed_backups=completed_backups,
            verified_backups=verified_backups,
            stale_backups=stale_count,
            active_policies=active_policies,
            recovery_readiness_status=readiness_status,
            open_recovery_blockers=open_blockers,
            last_backup_at=last_backup_at,
            last_verified_at=last_verified_at,
            recent_restores_count=recent_restores,
            completed_exercises_count=completed_exercises,
        )
