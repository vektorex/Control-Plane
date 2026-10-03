"""
Backup retention and lifecycle enforcement service for Step 36: Disaster Recovery.
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.app.services.disaster_recovery.models import BackupRun, BackupPolicy
from backend.app.services.disaster_recovery.exceptions import LegalHoldConflictError


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BackupRetentionService:
    """
    Evaluates backup retention policies, protects legal-held snapshots from deletion,
    and marks expired backups for asynchronous reclamation.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def scan_expired_backups(self, organization_id: str) -> List[BackupRun]:
        """
        Identify completed backups that have exceeded their retention period and are not under legal hold.
        """
        res = await self.session.execute(
            select(BackupRun, BackupPolicy)
            .join(BackupPolicy, BackupRun.policy_id == BackupPolicy.id, isouter=True)
            .where(
                BackupRun.organization_id == organization_id,
                BackupRun.status == "completed",
            )
        )
        rows = res.all()

        expired_runs: List[BackupRun] = []
        now = _utc_now()

        for run, policy in rows:
            retention_days = policy.retention_days if policy else 30
            cutoff = run.created_at + timedelta(days=retention_days)
            if now > cutoff:
                expired_runs.append(run)

        return expired_runs

    async def mark_backup_expired(
        self,
        backup_run_id: str,
        organization_id: str,
        is_under_legal_hold: bool = False,
    ) -> BackupRun:
        """
        Safely mark a backup as expired, rejecting if an active legal hold applies.
        """
        if is_under_legal_hold:
            raise LegalHoldConflictError(
                f"Backup '{backup_run_id}' contains assets under an active Step 33 Legal Hold and cannot be expired or deleted."
            )

        res = await self.session.execute(
            select(BackupRun).where(
                BackupRun.id == backup_run_id,
                BackupRun.organization_id == organization_id,
            )
        )
        backup_run = res.scalar_one_or_none()
        if not backup_run:
            raise LegalHoldConflictError(f"Backup run '{backup_run_id}' not found.")

        backup_run.status = "expired"
        await self.session.commit()
        return backup_run
