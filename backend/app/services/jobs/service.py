"""
JobService: High-level orchestration facade for durable jobs.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.db.models.job import Job, JobEvent
from backend.app.db.models.user import User
from backend.app.services.jobs.constants import JobEventType, JobPriority, JobStatus, JobType
from backend.app.services.jobs.errors import (
    JobCancellationError,
    JobNotFoundError,
    JobPermissionDeniedError,
    JobStateError,
    JobValidationError,
)
from backend.app.services.jobs.handlers import job_handler_registry
from backend.app.services.jobs.policies import JobPolicyEngine
from backend.app.services.jobs.repository import JobRepository
from backend.app.services.jobs.schemas import (
    AsyncExecutionResponse,
    JobCreateRequest,
    JobEventListResponse,
    JobEventResponse,
    JobListResponse,
    JobResponse,
    JobStatsResponse,
)


class JobService:
    """
    Central service for creating, inspecting, cancelling, and retrying durable background jobs.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = JobRepository(session)

    async def create_job(
        self,
        workspace_id: uuid.UUID,
        request: JobCreateRequest,
        user: Optional[User] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> Tuple[JobResponse, bool]:
        """
        Creates and enqueues a durable background job with idempotency and safety policies.
        Returns (job_response, is_newly_created: bool).
        """
        # 1. Idempotency verification: if key supplied, return existing job without duplicating work
        if request.idempotency_key:
            existing = await self.repo.get_by_idempotency_key(workspace_id, request.idempotency_key)
            if existing:
                logger.info(
                    f"[JobService] Idempotency match for key '{request.idempotency_key}' -> returning existing Job {existing.id}"
                )
                return self._format_job_response(existing), False

        # 2. Handler existence validation
        if not job_handler_registry.has_handler(request.job_type.value):
            raise JobValidationError(f"Unsupported job type: '{request.job_type.value}'")

        # 3. Payload safety & validation
        JobPolicyEngine.validate_payload_safety(request.job_type.value, request.payload)

        # 4. Workspace concurrency check
        await JobPolicyEngine.check_workspace_concurrency(self.session, workspace_id)

        # 5. Parent dependency validation
        if request.parent_job_id:
            await JobPolicyEngine.validate_parent_dependency(
                self.session, request.parent_job_id, workspace_id
            )

        # 6. Scheduled availability
        now = datetime.now(timezone.utc)
        available_at = now
        if request.delay_seconds and request.delay_seconds > 0:
            available_at = now + timedelta(seconds=request.delay_seconds)

        effective_user_id = user.id if user else (user_id if user_id else None)
        job = await self.repo.create_job(
            workspace_id=workspace_id,
            job_type=request.job_type.value,
            payload=request.payload,
            priority=request.priority.value,
            project_id=request.project_id,
            idempotency_key=request.idempotency_key,
            parent_job_id=request.parent_job_id,
            available_at=available_at,
            max_attempts=request.max_attempts or getattr(settings, "JOB_MAX_ATTEMPTS", 3),
            created_by=effective_user_id,
        )

        return self._format_job_response(job), True

    async def get_job_or_raise(
        self,
        job_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> Job:
        job = await self.repo.get_by_id(job_id, workspace_id=workspace_id)
        if not job:
            raise JobNotFoundError(f"Job '{job_id}' not found in workspace.")
        return job

    async def get_job(
        self,
        job_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> JobResponse:
        job = await self.get_job_or_raise(job_id, workspace_id)
        return self._format_job_response(job)

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
    ) -> JobListResponse:
        jobs, total = await self.repo.list_jobs(
            workspace_id=workspace_id,
            job_type=job_type,
            status=status,
            project_id=project_id,
            parent_job_id=parent_job_id,
            created_from=created_from,
            created_to=created_to,
            limit=limit,
            offset=offset,
        )
        return JobListResponse(
            jobs=[self._format_job_response(j) for j in jobs],
            total=total,
        )

    async def cancel_job(
        self,
        job_id: uuid.UUID,
        workspace_id: uuid.UUID,
        user: Optional[User] = None,
        reason: Optional[str] = None,
    ) -> JobResponse:
        """
        Cooperative cancellation: marks job cancelled if queued, or flags cancel_requested if running.
        """
        job = await self.get_job_or_raise(job_id, workspace_id)
        now = datetime.now(timezone.utc)

        if job.status in (JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value):
            raise JobStateError(f"Cannot cancel job in terminal status '{job.status}'.")

        msg = reason or f"Cancellation requested by {user.email if user else 'user'}."

        if job.status in (JobStatus.QUEUED.value, JobStatus.RETRYING.value):
            # Not currently claimed by a worker; cancel immediately
            job.status = JobStatus.CANCELLED.value
            job.cancelled_at = now
            job.updated_at = now

            event = JobEvent(
                job_id=job.id,
                workspace_id=workspace_id,
                event_type=JobEventType.CANCELLED.value,
                status=JobStatus.CANCELLED.value,
                message=msg,
            )
            self.session.add(event)
        else:
            # Job is running on a worker; record cancellation request event so worker stops at checkpoint
            event = JobEvent(
                job_id=job.id,
                workspace_id=workspace_id,
                event_type=JobEventType.CANCEL_REQUESTED.value,
                status=job.status,
                message=msg,
            )
            self.session.add(event)

        await self.session.commit()
        await self.session.refresh(job)
        return self._format_job_response(job)

    async def retry_job(
        self,
        job_id: uuid.UUID,
        workspace_id: uuid.UUID,
        user: Optional[User] = None,
    ) -> JobResponse:
        """
        Manually re-enqueues an eligible failed or cancelled job.
        """
        job = await self.get_job_or_raise(job_id, workspace_id)
        now = datetime.now(timezone.utc)

        if job.status not in (JobStatus.FAILED.value, JobStatus.CANCELLED.value):
            raise JobStateError(f"Only failed or cancelled jobs can be retried. Current status: '{job.status}'.")

        job.status = JobStatus.QUEUED.value
        job.available_at = now
        job.error_code = None
        job.error_message = None
        job.lease_owner = None
        job.lease_expires_at = None
        job.completed_at = None
        job.cancelled_at = None
        job.updated_at = now

        event = JobEvent(
            job_id=job.id,
            workspace_id=workspace_id,
            event_type=JobEventType.QUEUED.value,
            status=JobStatus.QUEUED.value,
            message=f"Manual retry initiated by {user.email if user else 'operator'}.",
        )
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(job)
        return self._format_job_response(job)

    async def list_job_events(
        self,
        job_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> JobEventListResponse:
        await self.get_job_or_raise(job_id, workspace_id)
        events = await self.repo.list_job_events(job_id, workspace_id)
        formatted = [JobEventResponse.model_validate(e) for e in events]
        return JobEventListResponse(events=formatted, total=len(formatted))

    async def get_stats(self, workspace_id: Optional[uuid.UUID] = None) -> JobStatsResponse:
        raw_stats = await self.repo.get_stats(workspace_id=workspace_id)
        return JobStatsResponse(**raw_stats)

    @classmethod
    def build_async_response(
        cls,
        job: Job,
        workflow_run_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AsyncExecutionResponse:
        """Normalized response for asynchronous execution endpoints."""
        return AsyncExecutionResponse(
            job_id=str(job.id),
            status=job.status,
            job_type=job.job_type,
            created_at=job.created_at,
            available_at=job.available_at,
            poll_url=f"/api/jobs/{job.id}",
            cancel_url=f"/api/jobs/{job.id}/cancel",
            workflow_run_id=workflow_run_id,
            details=details,
        )

    def _format_job_response(self, job: Job) -> JobResponse:
        duration_ms = None
        if job.started_at and job.completed_at:
            duration_ms = int((job.completed_at - job.started_at).total_seconds() * 1000)

        queue_latency_ms = None
        if job.started_at and job.available_at:
            queue_latency_ms = max(0, int((job.started_at - job.available_at).total_seconds() * 1000))

        resp = JobResponse.model_validate(job)
        resp.duration_ms = duration_ms
        resp.queue_latency_ms = queue_latency_ms
        return resp
