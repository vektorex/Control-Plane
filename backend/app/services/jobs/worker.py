"""
JobWorker: Continuous polling, atomic lease execution, heartbeat, and graceful shutdown.
"""
import asyncio
import os
import socket
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.db.database import async_session_factory
from backend.app.db.models.job import Job, JobEvent
from backend.app.services.jobs.constants import JobEventType, JobStatus
from backend.app.services.jobs.errors import JobCancellationError
from backend.app.services.jobs.handlers import JobExecutionContext, job_handler_registry
from backend.app.services.jobs.leasing import JobLeaseManager
from backend.app.services.jobs.queue import JobQueue
from backend.app.services.jobs.repository import JobRepository
from backend.app.services.jobs.retry import JobRetryPolicy


class JobWorker:
    """
    Production-grade background worker executing durable jobs with bounded concurrency,
    heartbeats, automatic retry evaluation, and graceful shutdown.
    """

    def __init__(
        self,
        worker_id: Optional[str] = None,
        concurrency: Optional[int] = None,
        poll_interval: Optional[float] = None,
        lease_seconds: Optional[int] = None,
        heartbeat_interval: Optional[float] = None,
    ):
        host = socket.gethostname()
        pid = os.getpid()
        self.worker_id = worker_id or f"worker_{host}_{pid}_{uuid.uuid4().hex[:6]}"
        self.concurrency = concurrency or getattr(settings, "JOB_WORKER_CONCURRENCY", 5)
        self.poll_interval = poll_interval or getattr(settings, "JOB_POLL_INTERVAL_SECONDS", 2.0)
        self.lease_seconds = lease_seconds or getattr(settings, "JOB_LEASE_SECONDS", 300)
        self.heartbeat_interval = heartbeat_interval or getattr(settings, "JOB_HEARTBEAT_SECONDS", 30)

        self._running = False
        self._semaphore = asyncio.Semaphore(self.concurrency)
        self._active_tasks: Set[asyncio.Task] = set()
        self._cancellation_events: Dict[uuid.UUID, asyncio.Event] = {}
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        """
        Starts the worker polling and heartbeat background tasks.
        """
        self._running = True
        self._stop_event.clear()
        logger.info(
            f"[JobWorker] Starting worker '{self.worker_id}' with concurrency={self.concurrency}, "
            f"poll_interval={self.poll_interval}s, lease={self.lease_seconds}s"
        )

        heartbeat_task = asyncio.create_task(self._heartbeat_and_maintenance_loop())
        poll_task = asyncio.create_task(self._poll_loop())

        try:
            await self._stop_event.wait()
        finally:
            logger.info(f"[JobWorker] Stopping worker '{self.worker_id}' gracefully...")
            self._running = False
            heartbeat_task.cancel()
            poll_task.cancel()

            # Wait for active tasks to complete or time out
            if self._active_tasks:
                logger.info(f"[JobWorker] Awaiting {len(self._active_tasks)} active tasks...")
                done, pending = await asyncio.wait(self._active_tasks, timeout=15.0)
                for p in pending:
                    p.cancel()

            logger.info(f"[JobWorker] Worker '{self.worker_id}' shutdown complete.")

    def stop(self) -> None:
        """Signals graceful shutdown."""
        self._running = False
        self._stop_event.set()

    async def _poll_loop(self) -> None:
        """
        Continuously polls the queue for eligible jobs and launches execution tasks.
        """
        while self._running:
            try:
                # Check concurrency available slots
                if self._semaphore.locked():
                    await asyncio.sleep(self.poll_interval)
                    continue

                async with async_session_factory() as session:
                    queue = JobQueue(session)
                    claimed = await queue.claim_next_jobs(
                        worker_id=self.worker_id,
                        limit=max(1, self.concurrency - len(self._active_tasks)),
                        lease_seconds=self.lease_seconds,
                    )

                if claimed:
                    for job in claimed:
                        task = asyncio.create_task(self._execute_job_wrapper(job.id, job.workspace_id))
                        self._active_tasks.add(task)
                        task.add_done_callback(self._active_tasks.discard)
                else:
                    await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[JobWorker] Error in poll loop: {e}", exc_info=True)
                await asyncio.sleep(self.poll_interval)

    async def _heartbeat_and_maintenance_loop(self) -> None:
        """
        Periodically extends lease heartbeats for running jobs and recovers abandoned leases.
        """
        while self._running:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                async with async_session_factory() as session:
                    # 1. Extend heartbeats for jobs owned by this worker
                    for job_id in list(self._cancellation_events.keys()):
                        await JobLeaseManager.extend_heartbeat(
                            session=session,
                            job_id=job_id,
                            worker_id=self.worker_id,
                            lease_seconds=self.lease_seconds,
                        )

                    # 2. Recover abandoned expired leases
                    await JobLeaseManager.recover_expired_leases(session)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[JobWorker] Error in heartbeat maintenance loop: {e}")

    async def _execute_job_wrapper(self, job_id: uuid.UUID, workspace_id: uuid.UUID) -> None:
        """
        Executes an individual claimed job inside bounded semaphore with full error handling.
        """
        async with self._semaphore:
            cancel_token = asyncio.Event()
            self._cancellation_events[job_id] = cancel_token

            try:
                async with async_session_factory() as session:
                    repo = JobRepository(session)
                    job = await repo.get_by_id(job_id)
                    if not job or job.status != JobStatus.RUNNING.value:
                        return

                    # Progress callback for the handler
                    async def progress_cb(pct, step, completed, total, msg):
                        async with async_session_factory() as p_session:
                            p_repo = JobRepository(p_session)
                            await p_repo.update_progress(
                                job_id=job_id,
                                percentage=pct,
                                current_step=step,
                                completed_steps=completed,
                                total_steps=total,
                                message=msg,
                            )

                    ctx = JobExecutionContext(session=session, update_progress=progress_cb)
                    handler = job_handler_registry.get(job.job_type)

                    start_time = time.time()
                    try:
                        result = await handler.execute(job, ctx, cancel_token)

                        # Success
                        now = datetime.now(timezone.utc)
                        job.status = JobStatus.COMPLETED.value
                        job.result = result
                        job.completed_at = now
                        job.lease_owner = None
                        job.lease_expires_at = None
                        job.updated_at = now

                        completed_event = JobEvent(
                            job_id=job.id,
                            workspace_id=workspace_id,
                            event_type=JobEventType.COMPLETED.value,
                            status=JobStatus.COMPLETED.value,
                            message="Job completed successfully.",
                            metadata_json={"duration_ms": int((time.time() - start_time) * 1000)},
                        )
                        session.add(completed_event)
                        await session.commit()
                        logger.info(f"[JobWorker] Job {job.id} ({job.job_type}) completed in {time.time() - start_time:.2f}s.")

                        if job.job_type != JobType.NOTIFICATION_DELIVERY.value:
                            try:
                                from backend.app.services.notifications.dispatcher import NotificationEventBus
                                from backend.app.services.notifications.constants import NotificationEventType
                                await NotificationEventBus.publish({
                                    "workspace_id": workspace_id,
                                    "event_type": NotificationEventType.JOB_COMPLETED.value,
                                    "source_type": "job",
                                    "source_id": str(job.id),
                                    "metadata": {"job_type": job.job_type, "duration_ms": int((time.time() - start_time) * 1000)},
                                })
                            except Exception as notif_err:
                                logger.warning(f"[JobWorker] Failed to publish job.completed notification: {notif_err}")

                    except JobCancellationError as cancel_err:
                        now = datetime.now(timezone.utc)
                        job.status = JobStatus.CANCELLED.value
                        job.cancelled_at = now
                        job.error_message = str(cancel_err)
                        job.lease_owner = None
                        job.lease_expires_at = None
                        job.updated_at = now

                        cancel_event = JobEvent(
                            job_id=job.id,
                            workspace_id=workspace_id,
                            event_type=JobEventType.CANCELLED.value,
                            status=JobStatus.CANCELLED.value,
                            message=str(cancel_err),
                        )
                        session.add(cancel_event)
                        await session.commit()
                        logger.info(f"[JobWorker] Job {job.id} cancelled.")

                    except Exception as exc:
                        err_code = type(exc).__name__
                        err_msg = str(exc)
                        now = datetime.now(timezone.utc)

                        # Retry evaluation
                        if JobRetryPolicy.should_retry(
                            attempts=job.attempts,
                            max_attempts=job.max_attempts,
                            error_code=err_code,
                            error_message=err_msg,
                        ):
                            delay = JobRetryPolicy.calculate_backoff_delay(job.attempts)
                            next_avail = now + timedelta(seconds=delay)
                            job.status = JobStatus.RETRYING.value
                            job.available_at = next_avail
                            job.error_code = err_code
                            job.error_message = err_msg
                            job.lease_owner = None
                            job.lease_expires_at = None
                            job.updated_at = now

                            retry_event = JobEvent(
                                job_id=job.id,
                                workspace_id=workspace_id,
                                event_type=JobEventType.RETRY_SCHEDULED.value,
                                status=JobStatus.RETRYING.value,
                                message=f"Transient failure: {err_msg}. Retrying in {delay}s.",
                                metadata_json={"delay_seconds": delay, "attempt": job.attempts},
                            )
                            session.add(retry_event)
                            await session.commit()
                            logger.info(f"[JobWorker] Job {job.id} failed transiently. Scheduled retry in {delay}s.")

                            if job.job_type != JobType.NOTIFICATION_DELIVERY.value:
                                try:
                                    from backend.app.services.notifications.dispatcher import NotificationEventBus
                                    from backend.app.services.notifications.constants import NotificationEventType
                                    await NotificationEventBus.publish({
                                        "workspace_id": workspace_id,
                                        "event_type": NotificationEventType.JOB_RETRYING.value,
                                        "source_type": "job",
                                        "source_id": str(job.id),
                                        "metadata": {"job_type": job.job_type, "attempt": job.attempts, "error_code": err_code},
                                    })
                                except Exception as notif_err:
                                    logger.warning(f"[JobWorker] Failed to publish job.retrying notification: {notif_err}")
                        else:
                            # Permanent failure
                            job.status = JobStatus.FAILED.value
                            job.completed_at = now
                            job.error_code = err_code
                            job.error_message = err_msg
                            job.lease_owner = None
                            job.lease_expires_at = None
                            job.updated_at = now

                            fail_event = JobEvent(
                                job_id=job.id,
                                workspace_id=workspace_id,
                                event_type=JobEventType.FAILED.value,
                                status=JobStatus.FAILED.value,
                                message=f"Job failed permanently: {err_msg}",
                                metadata_json={"error_code": err_code, "final_attempt": job.attempts},
                            )
                            session.add(fail_event)
                            await session.commit()
                            logger.warning(f"[JobWorker] Job {job.id} failed permanently: {err_msg}")

                            if job.job_type != JobType.NOTIFICATION_DELIVERY.value:
                                try:
                                    from backend.app.services.notifications.dispatcher import NotificationEventBus
                                    from backend.app.services.notifications.constants import NotificationEventType
                                    await NotificationEventBus.publish({
                                        "workspace_id": workspace_id,
                                        "event_type": NotificationEventType.JOB_FAILED.value,
                                        "source_type": "job",
                                        "source_id": str(job.id),
                                        "metadata": {"job_type": job.job_type, "error_code": err_code, "final_attempt": job.attempts},
                                    })
                                except Exception as notif_err:
                                    logger.warning(f"[JobWorker] Failed to publish job.failed notification: {notif_err}")

            finally:
                self._cancellation_events.pop(job_id, None)
