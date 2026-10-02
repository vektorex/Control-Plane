"""
JobScheduler: Evaluates and activates delayed and scheduled background jobs.
"""
from datetime import datetime, timezone
from typing import List
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.db.models.job import Job, JobEvent
from backend.app.services.jobs.constants import JobEventType, JobStatus


class JobScheduler:
    """
    Identifies scheduled or delayed jobs that have reached their execution window (available_at <= now).
    """

    @classmethod
    async def get_due_scheduled_count(cls, session: AsyncSession) -> int:
        now = datetime.now(timezone.utc)
        stmt = (
            select(func.count(Job.id))
            .where(
                Job.status.in_([JobStatus.QUEUED.value, JobStatus.RETRYING.value]),
                Job.available_at <= now,
            )
        )
        res = await session.execute(stmt)
        return res.scalar() or 0

    @classmethod
    async def preview_due_jobs(
        cls,
        session: AsyncSession,
        limit: int = 50,
    ) -> List[Job]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(Job)
            .where(
                Job.status.in_([JobStatus.QUEUED.value, JobStatus.RETRYING.value]),
                Job.available_at <= now,
            )
            .order_by(Job.available_at.asc())
            .limit(limit)
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())
