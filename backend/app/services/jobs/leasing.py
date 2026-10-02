"""
JobLeaseManager: Lease acquisition, heartbeat, and crash recovery.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.db.models.job import Job, JobEvent
from backend.app.services.jobs.constants import JobEventType, JobStatus
from backend.app.services.jobs.retry import JobRetryPolicy


class JobLeaseManager:
    """
    Manages worker leases, periodic heartbeats, and recovery of expired leases from crashed workers.
    """

    @classmethod
    async def extend_heartbeat(
        cls,
        session: AsyncSession,
        job_id: uuid.UUID,
        worker_id: str,
        lease_seconds: Optional[int] = None,
    ) -> bool:
        """
        Extends lease expiration for an active running job owned by worker_id.
        """
        now = datetime.now(timezone.utc)
        effective_lease = lease_seconds or getattr(settings, "JOB_LEASE_SECONDS", 300)
        new_expires_at = now + timedelta(seconds=effective_lease)

        stmt = (
            update(Job)
            .where(
                Job.id == job_id,
                Job.status == JobStatus.RUNNING.value,
                Job.lease_owner == worker_id,
            )
            .values(
                heartbeat_at=now,
                lease_expires_at=new_expires_at,
                updated_at=now,
            )
        )
        res = await session.execute(stmt)
        if res.rowcount > 0:
            # Emit heartbeat event
            event = JobEvent(
                job_id=job_id,
                workspace_id=(await session.scalar(select(Job.workspace_id).where(Job.id == job_id))),
                event_type=JobEventType.HEARTBEAT.value,
                status=JobStatus.RUNNING.value,
                message=f"Heartbeat extended lease to {new_expires_at.isoformat()}",
                metadata_json={"worker_id": worker_id, "lease_seconds": effective_lease},
            )
            session.add(event)
            await session.commit()
            return True

        return False

    @classmethod
    async def recover_expired_leases(
        cls,
        session: AsyncSession,
    ) -> List[uuid.UUID]:
        """
        Identifies running jobs whose lease has expired without heartbeat.
        If attempts < max_attempts: resets to 'retrying' with backoff.
        Else: marks 'failed' with LEASE_EXPIRED error.
        """
        now = datetime.now(timezone.utc)

        stmt = (
            select(Job)
            .where(
                Job.status == JobStatus.RUNNING.value,
                Job.lease_expires_at <= now,
            )
        )
        result = await session.execute(stmt)
        expired_jobs = list(result.scalars().all())

        recovered_ids: List[uuid.UUID] = []

        for job in expired_jobs:
            crashed_worker = job.lease_owner or "unknown"
            logger.warning(
                f"[JobLeaseManager] Job {job.id} lease expired from worker '{crashed_worker}'. Initiating recovery."
            )

            # Check if eligible for retry
            if job.attempts < job.max_attempts:
                delay = JobRetryPolicy.calculate_backoff_delay(job.attempts)
                next_avail = now + timedelta(seconds=delay)
                job.status = JobStatus.RETRYING.value
                job.available_at = next_avail
                job.lease_owner = None
                job.lease_expires_at = None
                job.updated_at = now

                event = JobEvent(
                    job_id=job.id,
                    workspace_id=job.workspace_id,
                    event_type=JobEventType.RECOVERED.value,
                    status=JobStatus.RETRYING.value,
                    message=f"Lease expired from worker '{crashed_worker}'. Recovered and rescheduled to {next_avail.isoformat()}.",
                    metadata_json={
                        "crashed_worker": crashed_worker,
                        "attempt": job.attempts,
                        "retry_delay_seconds": delay,
                    },
                )
                session.add(event)
            else:
                job.status = JobStatus.FAILED.value
                job.error_code = "LEASE_EXPIRED_MAX_ATTEMPTS"
                job.error_message = (
                    f"Job worker '{crashed_worker}' lease expired and maximum attempts ({job.max_attempts}) reached."
                )
                job.completed_at = now
                job.lease_owner = None
                job.lease_expires_at = None
                job.updated_at = now

                event = JobEvent(
                    job_id=job.id,
                    workspace_id=job.workspace_id,
                    event_type=JobEventType.FAILED.value,
                    status=JobStatus.FAILED.value,
                    message=job.error_message,
                    metadata_json={
                        "crashed_worker": crashed_worker,
                        "final_attempt": job.attempts,
                    },
                )
                session.add(event)

            recovered_ids.append(job.id)

        if expired_jobs:
            await session.commit()

        return recovered_ids
