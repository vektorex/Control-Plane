"""
PostgreSQL-backed durable JobQueue with atomic row-locking, priority, and parent dependency checks.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy import case, select, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.db.models.job import Job, JobEvent
from backend.app.services.jobs.constants import (
    JobEventType,
    JobPriority,
    JobStatus,
    PRIORITY_WEIGHTS,
)


class JobQueue:
    """
    Durable queue backed by PostgreSQL transactional row-locking.
    Guarantees atomic, non-conflicting job claims using SKIP LOCKED.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def claim_next_jobs(
        self,
        worker_id: str,
        limit: int = 1,
        lease_seconds: Optional[int] = None,
    ) -> List[Job]:
        """
        Atomically claims up to `limit` executable jobs for worker_id.
        Orders by priority (high > normal > low) and created_at.
        Enforces parent dependency completion before claiming.
        """
        now = datetime.now(timezone.utc)
        effective_lease = lease_seconds or getattr(settings, "JOB_LEASE_SECONDS", 300)
        lease_expires = now + timedelta(seconds=effective_lease)

        # Build priority weight order: High=1, Normal=2, Low=3
        priority_order = case(
            (Job.priority == JobPriority.HIGH.value, 1),
            (Job.priority == JobPriority.NORMAL.value, 2),
            else_=3,
        )

        # Subquery or join for parent job condition:
        # A job is executable if:
        # 1. status is 'queued' or 'retrying'
        # 2. available_at <= now
        # 3. parent_job_id IS NULL OR parent job status == 'completed'
        stmt = (
            select(Job)
            .where(
                Job.status.in_([JobStatus.QUEUED.value, JobStatus.RETRYING.value]),
                Job.available_at <= now,
            )
            .order_by(priority_order, Job.created_at.asc())
            .limit(limit * 3)  # Fetch extra to evaluate parent conditions
        )

        # Apply PostgreSQL SKIP LOCKED if running against Postgres
        try:
            bind = getattr(self.session, "bind", None)
            dialect_name = getattr(getattr(bind, "dialect", None), "name", None)
            if not dialect_name and hasattr(self.session, "sync_session"):
                sync_bind = getattr(self.session.sync_session, "bind", None)
                dialect_name = getattr(getattr(sync_bind, "dialect", None), "name", None)
            if dialect_name == "postgresql":
                stmt = stmt.with_for_update(skip_locked=True)
        except Exception:
            pass

        res = await self.session.execute(stmt)
        candidate_jobs = list(res.scalars().all())

        claimed_jobs: List[Job] = []

        for job in candidate_jobs:
            if len(claimed_jobs) >= limit:
                break

            # Check parent job dependency
            if job.parent_job_id:
                parent_stmt = select(Job).where(Job.id == job.parent_job_id)
                parent_res = await self.session.execute(parent_stmt)
                parent_job = parent_res.scalar_one_or_none()

                if parent_job:
                    if parent_job.status != JobStatus.COMPLETED.value:
                        if parent_job.status in (JobStatus.FAILED.value, JobStatus.CANCELLED.value):
                            # Parent failed or was cancelled -> cancel dependent job
                            job.status = JobStatus.CANCELLED.value
                            job.error_code = "PARENT_JOB_FAILED"
                            job.error_message = f"Parent job {job.parent_job_id} {parent_job.status}."
                            job.cancelled_at = now
                            job.updated_at = now
                            event = JobEvent(
                                job_id=job.id,
                                workspace_id=job.workspace_id,
                                event_type=JobEventType.CANCELLED.value,
                                status=JobStatus.CANCELLED.value,
                                message=job.error_message,
                            )
                            self.session.add(event)
                        # Skip claiming this candidate
                        continue

            # Atomically update claimed state
            job.status = JobStatus.RUNNING.value
            job.lease_owner = worker_id
            job.lease_expires_at = lease_expires
            job.started_at = job.started_at or now
            job.heartbeat_at = now
            job.attempts += 1
            job.updated_at = now

            # Emit events
            claim_event = JobEvent(
                job_id=job.id,
                workspace_id=job.workspace_id,
                event_type=JobEventType.CLAIMED.value,
                status=JobStatus.RUNNING.value,
                message=f"Claimed by worker '{worker_id}' with lease expiring at {lease_expires.isoformat()}.",
                metadata_json={"worker_id": worker_id, "attempt": job.attempts},
            )
            start_event = JobEvent(
                job_id=job.id,
                workspace_id=job.workspace_id,
                event_type=JobEventType.STARTED.value,
                status=JobStatus.RUNNING.value,
                message=f"Started execution (attempt {job.attempts}/{job.max_attempts}).",
                metadata_json={"worker_id": worker_id, "attempt": job.attempts},
            )
            self.session.add(claim_event)
            self.session.add(start_event)

            claimed_jobs.append(job)

        if candidate_jobs:
            await self.session.commit()

        return claimed_jobs
