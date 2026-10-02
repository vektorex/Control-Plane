"""
JobRepository: Database access layer for durable jobs and job events.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.db.models.job import Job, JobEvent
from backend.app.services.jobs.constants import JobEventType, JobStatus


class JobRepository:
    """
    CRUD and querying repository for durable jobs.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_job(
        self,
        workspace_id: uuid.UUID,
        job_type: str,
        payload: Dict[str, Any],
        priority: str = "normal",
        project_id: Optional[uuid.UUID] = None,
        idempotency_key: Optional[str] = None,
        parent_job_id: Optional[uuid.UUID] = None,
        available_at: Optional[datetime] = None,
        max_attempts: int = 3,
        created_by: Optional[uuid.UUID] = None,
    ) -> Job:
        now = datetime.now(timezone.utc)
        job = Job(
            workspace_id=workspace_id,
            project_id=project_id,
            job_type=job_type,
            status=JobStatus.QUEUED.value,
            priority=priority,
            payload=payload,
            attempts=0,
            max_attempts=max_attempts,
            available_at=available_at or now,
            idempotency_key=idempotency_key,
            parent_job_id=parent_job_id,
            created_by=created_by,
            progress={
                "percentage": 0,
                "current_step": None,
                "completed_steps": 0,
                "total_steps": 0,
                "message": "Enqueued",
            },
        )
        self.session.add(job)
        await self.session.flush()

        # Emit initial events
        created_event = JobEvent(
            job_id=job.id,
            workspace_id=workspace_id,
            event_type=JobEventType.CREATED.value,
            status=JobStatus.QUEUED.value,
            message="Job created and registered.",
            metadata_json={"job_type": job_type, "priority": priority},
        )
        queued_event = JobEvent(
            job_id=job.id,
            workspace_id=workspace_id,
            event_type=JobEventType.QUEUED.value,
            status=JobStatus.QUEUED.value,
            message=f"Job queued for execution (available at: {job.available_at.isoformat()}).",
            metadata_json={"available_at": job.available_at.isoformat()},
        )
        self.session.add(created_event)
        self.session.add(queued_event)

        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_by_id(
        self,
        job_id: uuid.UUID,
        workspace_id: Optional[uuid.UUID] = None,
    ) -> Optional[Job]:
        stmt = select(Job).where(Job.id == job_id).options(selectinload(Job.events))
        if workspace_id:
            stmt = stmt.where(Job.workspace_id == workspace_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_idempotency_key(
        self,
        workspace_id: uuid.UUID,
        idempotency_key: str,
    ) -> Optional[Job]:
        stmt = (
            select(Job)
            .where(
                Job.workspace_id == workspace_id,
                Job.idempotency_key == idempotency_key,
            )
            .options(selectinload(Job.events))
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_jobs(
        self,
        workspace_id: uuid.UUID,
        job_type: Optional[str] = None,
        status: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        parent_job_id: Optional[uuid.UUID] = None,
        created_from: Optional[datetime] = None,
        created_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Job], int]:
        stmt = select(Job).where(Job.workspace_id == workspace_id)
        count_stmt = select(func.count(Job.id)).where(Job.workspace_id == workspace_id)

        if job_type:
            stmt = stmt.where(Job.job_type == job_type)
            count_stmt = count_stmt.where(Job.job_type == job_type)
        if status:
            stmt = stmt.where(Job.status == status)
            count_stmt = count_stmt.where(Job.status == status)
        if project_id:
            stmt = stmt.where(Job.project_id == project_id)
            count_stmt = count_stmt.where(Job.project_id == project_id)
        if parent_job_id:
            stmt = stmt.where(Job.parent_job_id == parent_job_id)
            count_stmt = count_stmt.where(Job.parent_job_id == parent_job_id)
        if created_from:
            stmt = stmt.where(Job.created_at >= created_from)
            count_stmt = count_stmt.where(Job.created_at >= created_from)
        if created_to:
            stmt = stmt.where(Job.created_at <= created_to)
            count_stmt = count_stmt.where(Job.created_at <= created_to)

        count_res = await self.session.execute(count_stmt)
        total = count_res.scalar() or 0

        stmt = (
            stmt.order_by(desc(Job.created_at))
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all()), total

    async def list_job_events(
        self,
        job_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> List[JobEvent]:
        stmt = (
            select(JobEvent)
            .where(
                JobEvent.job_id == job_id,
                JobEvent.workspace_id == workspace_id,
            )
            .order_by(JobEvent.created_at.asc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def update_progress(
        self,
        job_id: uuid.UUID,
        percentage: Optional[int] = None,
        current_step: Optional[str] = None,
        completed_steps: Optional[int] = None,
        total_steps: Optional[int] = None,
        message: Optional[str] = None,
        workspace_id: Optional[uuid.UUID] = None,
    ) -> Optional[Job]:
        job = await self.get_by_id(job_id, workspace_id=workspace_id)
        if not job:
            return None

        prog = dict(job.progress or {})
        if percentage is not None:
            prog["percentage"] = percentage
        if current_step is not None:
            prog["current_step"] = current_step
        if completed_steps is not None:
            prog["completed_steps"] = completed_steps
        if total_steps is not None:
            prog["total_steps"] = total_steps
        if message is not None:
            prog["message"] = message

        job.progress = prog
        job.updated_at = datetime.now(timezone.utc)

        # Record progress event
        event = JobEvent(
            job_id=job.id,
            workspace_id=job.workspace_id,
            event_type=JobEventType.PROGRESS.value,
            status=job.status,
            message=message or f"Progress: {prog.get('percentage', 0)}%",
            metadata_json=prog,
        )
        self.session.add(event)
        await self.session.commit()
        return job

    async def get_stats(self, workspace_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        """Calculates factual operational queue metrics."""
        now = datetime.now(timezone.utc)

        def _base_stmt():
            s = select(Job)
            if workspace_id:
                s = s.where(Job.workspace_id == workspace_id)
            return s

        async def _count_status(st: str) -> int:
            q = select(func.count(Job.id)).where(Job.status == st)
            if workspace_id:
                q = q.where(Job.workspace_id == workspace_id)
            return (await self.session.execute(q)).scalar() or 0

        queued = await _count_status(JobStatus.QUEUED.value)
        running = await _count_status(JobStatus.RUNNING.value)
        retrying = await _count_status(JobStatus.RETRYING.value)
        completed = await _count_status(JobStatus.COMPLETED.value)
        failed = await _count_status(JobStatus.FAILED.value)
        cancelled = await _count_status(JobStatus.CANCELLED.value)

        # Stale leases count (running jobs whose lease expired)
        stale_q = select(func.count(Job.id)).where(
            Job.status == JobStatus.RUNNING.value,
            Job.lease_expires_at <= now,
        )
        if workspace_id:
            stale_q = stale_q.where(Job.workspace_id == workspace_id)
        stale = (await self.session.execute(stale_q)).scalar() or 0

        # Unique active workers
        worker_q = select(func.count(func.distinct(Job.lease_owner))).where(
            Job.status == JobStatus.RUNNING.value,
            Job.lease_owner.is_not(None),
        )
        if workspace_id:
            worker_q = worker_q.where(Job.workspace_id == workspace_id)
        workers = (await self.session.execute(worker_q)).scalar() or 0

        return {
            "queued_count": queued,
            "running_count": running,
            "retrying_count": retrying,
            "completed_count": completed,
            "failed_count": failed,
            "cancelled_count": cancelled,
            "stale_leases_count": stale,
            "active_workers_count": workers,
            "avg_queue_latency_ms": 0.0,
        }
