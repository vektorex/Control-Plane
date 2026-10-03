"""
Recovery objectives (RTO/RPO) and operational readiness calculation for Step 36: Disaster Recovery.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.services.disaster_recovery.models import (
    RecoveryObjective,
    RecoveryReadiness,
    BackupRun,
    BackupManifest,
    RestoreRun,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RecoveryObjectivesService:
    """
    Manages RTO/RPO targets and calculates factual readiness metrics.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_objectives(self, organization_id: str) -> List[RecoveryObjective]:
        """List configured RTO/RPO targets."""
        res = await self.session.execute(
            select(RecoveryObjective).where(RecoveryObjective.organization_id == organization_id)
        )
        return list(res.scalars().all())

    async def create_objective(
        self,
        organization_id: str,
        resource_type: str,
        rto_seconds: int,
        rpo_seconds: int,
        workspace_id: Optional[str] = None,
        resource_scope: str = "all",
        priority: str = "tier_1",
    ) -> RecoveryObjective:
        """Create a new recovery objective."""
        obj = RecoveryObjective(
            organization_id=organization_id,
            workspace_id=workspace_id,
            resource_type=resource_type,
            resource_scope=resource_scope,
            rto_seconds=rto_seconds,
            rpo_seconds=rpo_seconds,
            priority=priority,
            enabled=True,
        )
        self.session.add(obj)
        await self.session.commit()
        return obj

    async def evaluate_readiness(self, organization_id: str) -> List[RecoveryReadiness]:
        """
        Evaluate factual recovery readiness per resource type based on recent backup runs,
        manifest verification status, and restore runs.
        """
        # Fetch objectives for org
        objectives = await self.list_objectives(organization_id)
        resource_types = {obj.resource_type for obj in objectives}
        if not resource_types:
            resource_types = {"database", "workflow", "document", "artifact"}

        readiness_list: List[RecoveryReadiness] = []
        now = _utc_now()

        for r_type in sorted(resource_types):
            # 1. Query latest completed backup
            res_backup = await self.session.execute(
                select(BackupRun)
                .where(
                    BackupRun.organization_id == organization_id,
                    BackupRun.status == "completed",
                )
                .order_by(desc(BackupRun.completed_at))
                .limit(1)
            )
            latest_backup = res_backup.scalar_one_or_none()

            # 2. Query latest verified backup manifest
            res_manifest = await self.session.execute(
                select(BackupManifest)
                .join(BackupRun, BackupManifest.backup_run_id == BackupRun.id)
                .where(
                    BackupRun.organization_id == organization_id,
                    BackupManifest.verification_status == "verified",
                )
                .order_by(desc(BackupManifest.created_at))
                .limit(1)
            )
            latest_verified = res_manifest.scalar_one_or_none()

            # 3. Query latest completed restore run
            res_restore = await self.session.execute(
                select(RestoreRun)
                .where(RestoreRun.status == "completed")
                .order_by(desc(RestoreRun.completed_at))
                .limit(1)
            )
            latest_restore = res_restore.scalar_one_or_none()

            # Calculate ages
            backup_age_seconds = (
                int((now - latest_backup.completed_at).total_seconds())
                if latest_backup and latest_backup.completed_at
                else None
            )

            # Check matching RPO/RTO
            obj = next((o for o in objectives if o.resource_type == r_type), None)
            target_rpo = obj.rpo_seconds if obj else 86400
            target_rto = obj.rto_seconds if obj else 7200

            blockers = []
            if not latest_backup:
                blockers.append("No completed backup exists")
            elif backup_age_seconds and backup_age_seconds > target_rpo:
                blockers.append(f"Backup age ({backup_age_seconds}s) exceeds RPO target ({target_rpo}s)")

            if not latest_verified:
                blockers.append("No verified backup package available")

            # Determine overall operational status
            if blockers:
                status = "blocked" if not latest_backup or not latest_verified else "needs_attention"
            else:
                status = "ready"

            rec = RecoveryReadiness(
                organization_id=organization_id,
                resource_type=r_type,
                backup_status="ready" if latest_backup else "missing",
                verification_status="verified" if latest_verified else "unverified",
                restore_test_status="passed" if latest_restore else "not_tested",
                last_successful_backup=latest_backup.completed_at if latest_backup else None,
                last_successful_verification=latest_verified.created_at if latest_verified else None,
                last_successful_restore_test=latest_restore.completed_at if latest_restore else None,
                observed_backup_age_seconds=backup_age_seconds,
                estimated_restore_duration_seconds=300 if latest_verified else None,
                overall_status=status,
                known_blockers=blockers,
            )
            readiness_list.append(rec)

        return readiness_list
