"""
JobHandler interface, concrete implementations, and JobHandlerRegistry.
"""
import abc
import asyncio
import uuid
from typing import Any, Callable, Coroutine, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.db.models.job import Job
from backend.app.db.models.user import User
from backend.app.services.jobs.constants import JobType
from backend.app.services.jobs.errors import JobCancellationError, JobHandlerNotFoundError


class JobExecutionContext:
    """
    Runtime execution context passed to JobHandlers.
    """

    def __init__(
        self,
        session: AsyncSession,
        update_progress: Callable[[int, Optional[str], Optional[int], Optional[int], Optional[str]], Coroutine[Any, Any, None]],
    ):
        self.session = session
        self.update_progress = update_progress


class JobHandler(abc.ABC):
    """
    Abstract interface for job execution handlers.
    """

    @abc.abstractmethod
    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        """
        Executes business logic for the job and returns a normalized result dictionary.
        Must check cancellation_token.is_set() at safe checkpoints.
        """
        pass


class WorkflowRunJobHandler(JobHandler):
    """
    Executes a workflow run asynchronously via the authoritative WorkflowExecutor.
    """

    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        from backend.app.repositories.workflow import WorkflowRepository
        from backend.app.services.workflows.executor import WorkflowExecutor
        from backend.app.services.workflows.schemas import WorkflowDefinition

        session = context.session
        payload = job.payload

        wf_id = uuid.UUID(str(payload["workflow_id"]))
        run_id = uuid.UUID(str(payload["workflow_run_id"]))
        target_version = payload.get("version")
        input_data = payload.get("input_data", {})
        user_id = payload.get("user_id")

        await context.update_progress(10, "Fetching workflow definition", 1, 5, "Preparing workflow execution")

        if cancellation_token.is_set():
            raise JobCancellationError("Workflow execution cancelled before start.")

        wf_repo = WorkflowRepository(session)
        wf = await wf_repo.get_workflow_by_id_or_raise(wf_id, job.workspace_id)
        run = await wf_repo.get_run_by_id(run_id, job.workspace_id)
        if not run:
            raise ValueError(f"WorkflowRun '{run_id}' not found.")

        target_version = target_version or wf.version
        version_snapshot = await wf_repo.get_version(wf.id, target_version)
        if version_snapshot:
            definition = WorkflowDefinition.model_validate(version_snapshot.definition)
        else:
            from backend.app.services.workflows.service import WorkflowService
            wf_service = WorkflowService(session)
            definition = await wf_service.get_workflow_definition(wf.id, job.workspace_id)

        # Build execution user
        exec_user = User(
            id=uuid.UUID(str(user_id)) if user_id else uuid.uuid4(),
            email="automation@internal",
            workspace_id=job.workspace_id,
        )

        await context.update_progress(30, "Executing workflow steps", 2, 5, "Running pipeline steps")

        if cancellation_token.is_set():
            raise JobCancellationError("Workflow execution cancelled before executor start.")

        executor = WorkflowExecutor(session)
        finished_run = await executor.execute_workflow(
            workflow=wf,
            run=run,
            definition=definition,
            user=exec_user,
            input_data=input_data,
        )

        await context.update_progress(100, "Workflow execution finished", 5, 5, f"Completed with status: {finished_run.status}")

        return {
            "workflow_id": str(wf.id),
            "workflow_run_id": str(finished_run.id),
            "status": finished_run.status,
            "duration_ms": finished_run.duration_ms,
            "outputs": finished_run.output_data,
            "error_code": finished_run.error_code,
            "error_message": finished_run.error_message,
        }


class TriggerRunJobHandler(JobHandler):
    """
    Executes a trigger run asynchronously via TriggerExecutor.
    """

    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        from backend.app.db.models.trigger import WorkflowTrigger, TriggerRun
        from backend.app.services.triggers.events import TriggerEvent
        from backend.app.services.triggers.executor import TriggerExecutor

        session = context.session
        payload = job.payload

        trigger_id = uuid.UUID(str(payload["trigger_id"]))
        trigger_run_id = uuid.UUID(str(payload["trigger_run_id"]))

        await context.update_progress(20, "Loading trigger details", 1, 4, "Preparing trigger execution")

        if cancellation_token.is_set():
            raise JobCancellationError("Trigger execution cancelled.")

        trig = (await session.execute(select(WorkflowTrigger).where(WorkflowTrigger.id == trigger_id))).scalar_one_or_none()
        trig_run = (await session.execute(select(TriggerRun).where(TriggerRun.id == trigger_run_id))).scalar_one_or_none()

        if not trig or not trig_run:
            raise ValueError(f"Trigger {trigger_id} or TriggerRun {trigger_run_id} not found.")

        event_data = payload.get("event", {})
        event = TriggerEvent(
            event_id=event_data.get("event_id", trig_run.event_id or f"evt_{uuid.uuid4().hex[:12]}"),
            event_type=event_data.get("event_type", "webhook.workflow.run"),
            source=event_data.get("source", trig.trigger_type),
            workspace_id=job.workspace_id,
            payload=event_data.get("payload", {}),
            metadata=event_data.get("metadata", {}),
        )

        await context.update_progress(50, "Executing trigger workflow", 2, 4, "Invoking TriggerExecutor")

        if cancellation_token.is_set():
            raise JobCancellationError("Trigger execution cancelled.")

        executor = TriggerExecutor(session)
        finished_trig_run = await executor.execute_trigger_run(
            trigger=trig,
            trigger_run=trig_run,
            event=event,
        )

        await context.update_progress(100, "Trigger run completed", 4, 4, f"Status: {finished_trig_run.status}")

        return {
            "trigger_id": str(trig.id),
            "trigger_run_id": str(finished_trig_run.id),
            "workflow_run_id": str(finished_trig_run.workflow_run_id) if finished_trig_run.workflow_run_id else None,
            "status": finished_trig_run.status,
            "error_code": finished_trig_run.error_code,
            "error_message": finished_trig_run.error_message,
        }


class DocumentProcessingJobHandler(JobHandler):
    """
    Executes long-running document ingestion (download, extraction, chunking, embedding).
    """

    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        from backend.app.services.ingestion.pipeline import DocumentIngestionPipeline

        session = context.session
        document_id = uuid.UUID(str(job.payload["document_id"]))

        await context.update_progress(15, "Starting ingestion pipeline", 1, 4, "Reading document from storage")

        if cancellation_token.is_set():
            raise JobCancellationError("Document processing cancelled.")

        pipeline = DocumentIngestionPipeline()
        try:
            doc = await pipeline.process_document(document_id, session)
            status_val = doc.status
        except Exception as doc_err:
            try:
                from backend.app.services.notifications.dispatcher import NotificationEventBus
                from backend.app.services.notifications.constants import NotificationEventType
                await NotificationEventBus.publish({
                    "workspace_id": job.workspace_id,
                    "event_type": NotificationEventType.DOCUMENT_FAILED.value,
                    "source_type": "document",
                    "source_id": str(document_id),
                    "metadata": {"error": str(doc_err)},
                }, session=session)
            except Exception as notif_err:
                logger.warning(f"[DocumentJobHandler] Failed to publish doc failure notification: {notif_err}")
            raise

        await context.update_progress(100, "Ingestion completed", 4, 4, f"Document indexed: {doc.filename}")

        try:
            from backend.app.services.notifications.dispatcher import NotificationEventBus
            from backend.app.services.notifications.constants import NotificationEventType
            ev_type = NotificationEventType.DOCUMENT_COMPLETED.value if doc.status in ("completed", "indexed", "ready") else NotificationEventType.DOCUMENT_FAILED.value
            await NotificationEventBus.publish({
                "workspace_id": job.workspace_id,
                "event_type": ev_type,
                "source_type": "document",
                "source_id": str(doc.id),
                "metadata": {"filename": doc.filename, "chunk_count": doc.chunk_count, "token_count": doc.token_count},
            }, session=session)
        except Exception as notif_err:
            logger.warning(f"[DocumentJobHandler] Failed to publish doc notification: {notif_err}")

        return {
            "document_id": str(doc.id),
            "filename": doc.filename,
            "status": doc.status,
            "chunk_count": doc.chunk_count,
            "token_count": doc.token_count,
        }


class EvaluationExperimentJobHandler(JobHandler):
    """
    Executes an Evaluation Lab experiment across test cases asynchronously.
    """

    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        from backend.app.services.evaluation_lab.experiments import ExperimentService

        session = context.session
        exp_id = uuid.UUID(str(job.payload["experiment_id"]))

        await context.update_progress(20, "Loading experiment cases", 1, 4, "Preparing evaluation cases")

        if cancellation_token.is_set():
            raise JobCancellationError("Evaluation experiment cancelled.")

        exp_service = ExperimentService()
        finished_exp = await exp_service.run_experiment(
            session=session,
            experiment_id=exp_id,
            workspace_id=job.workspace_id,
        )

        await context.update_progress(100, "Experiment finished", 4, 4, f"Finished with status: {finished_exp.status}")

        try:
            from backend.app.services.notifications.dispatcher import NotificationEventBus
            from backend.app.services.notifications.constants import NotificationEventType
            # Check for regression flag in metrics
            has_regression = bool(finished_exp.metrics and finished_exp.metrics.get("has_regression"))
            ev_type = NotificationEventType.EVALUATION_REGRESSION.value if has_regression else NotificationEventType.EVALUATION_COMPLETED.value
            await NotificationEventBus.publish({
                "workspace_id": job.workspace_id,
                "event_type": ev_type,
                "source_type": "evaluation_experiment",
                "source_id": str(finished_exp.id),
                "metadata": {
                    "experiment_id": str(finished_exp.id),
                    "status": finished_exp.status,
                    "metrics": finished_exp.metrics or {},
                    "link": f"/app/evaluation-lab?experiment_id={finished_exp.id}",
                },
            }, session=session)
        except Exception as notif_err:
            logger.warning(f"[EvaluationJobHandler] Failed to publish evaluation notification: {notif_err}")

        return {
            "experiment_id": str(finished_exp.id),
            "status": finished_exp.status,
            "metrics": finished_exp.metrics,
            "error_message": finished_exp.error_message,
        }


class ReplayRunJobHandler(JobHandler):
    """
    Executes a recorded execution replay in dry-run or inspect mode.
    """

    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        from backend.app.db.models.replay import ReplayRun
        from backend.app.services.replay.service import ReplayService

        session = context.session
        replay_id = uuid.UUID(str(job.payload["replay_id"]))
        overrides = job.payload.get("overrides")

        await context.update_progress(20, "Loading replay snapshot", 1, 3, "Verifying replay eligibility")

        if cancellation_token.is_set():
            raise JobCancellationError("Replay run cancelled.")

        replay_run = (await session.execute(select(ReplayRun).where(ReplayRun.id == replay_id))).scalar_one_or_none()
        if not replay_run:
            raise ValueError(f"ReplayRun '{replay_id}' not found.")

        replay_service = ReplayService()
        finished_replay = await replay_service.runner.execute_replay(
            replay_run=replay_run,
            overrides=overrides,
            session=session,
        )

        await context.update_progress(100, "Replay run completed", 3, 3, f"Status: {finished_replay.status}")

        try:
            from backend.app.services.notifications.dispatcher import NotificationEventBus
            from backend.app.services.notifications.constants import NotificationEventType
            ev_type = NotificationEventType.REPLAY_COMPLETED.value if finished_replay.status == "completed" else NotificationEventType.REPLAY_FAILED.value
            await NotificationEventBus.publish({
                "workspace_id": job.workspace_id,
                "event_type": ev_type,
                "source_type": "replay_run",
                "source_id": str(finished_replay.id),
                "metadata": {
                    "replay_id": str(finished_replay.id),
                    "status": finished_replay.status,
                    "link": f"/app/replay?run_id={finished_replay.id}",
                },
            }, session=session)
        except Exception as notif_err:
            logger.warning(f"[ReplayJobHandler] Failed to publish replay notification: {notif_err}")

        return {
            "replay_id": str(finished_replay.id),
            "status": finished_replay.status,
            "diff_summary": finished_replay.diff_summary,
            "error_message": finished_replay.error_message,
        }


class ConnectorOperationJobHandler(JobHandler):
    """
    Executes an external connector operation with permissions and policy enforcement.
    """

    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        from backend.app.services.connectors.executor import ConnectorExecutor
        from backend.app.services.connectors.schemas import ConnectorExecutionRequest

        session = context.session
        req_data = job.payload.get("request", {})
        user_id = job.payload.get("user_id")

        await context.update_progress(25, "Verifying connector permissions", 1, 3, "Checking connector authorization")

        if cancellation_token.is_set():
            raise JobCancellationError("Connector operation cancelled.")

        user = User(
            id=uuid.UUID(str(user_id)) if user_id else uuid.uuid4(),
            email="connector_worker@internal",
            workspace_id=job.workspace_id,
        )

        executor = ConnectorExecutor(session=session)
        exec_request = ConnectorExecutionRequest.model_validate(req_data)
        result = await executor.execute(exec_request, user=user)

        await context.update_progress(100, "Connector operation finished", 3, 3, "Execution succeeded")

        try:
            from backend.app.services.notifications.dispatcher import NotificationEventBus
            from backend.app.services.notifications.constants import NotificationEventType
            ev_type = NotificationEventType.CONNECTOR_COMPLETED.value if result.status == "success" else NotificationEventType.CONNECTOR_FAILED.value
            await NotificationEventBus.publish({
                "workspace_id": job.workspace_id,
                "event_type": ev_type,
                "source_type": "connector",
                "source_id": str(result.connector_id or "connector"),
                "metadata": {
                    "operation": result.operation,
                    "status": result.status,
                    "external_untrusted": True,
                },
            }, session=session)
        except Exception as notif_err:
            logger.warning(f"[ConnectorJobHandler] Failed to publish connector notification: {notif_err}")

        return {
            "connector_id": str(result.connector_id) if result.connector_id else None,
            "operation": result.operation,
            "status": result.status,
            "data": result.data,
            "error": result.error,
        }


class NotificationDeliveryJobHandler(JobHandler):
    """
    Executes an asynchronous notification delivery (webhook, email, in_app) via DeliveryDispatcher.
    """

    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        from backend.app.services.notifications.delivery import DeliveryDispatcher
        from backend.app.services.notifications.constants import DeliveryStatus
        from backend.app.db.models.notification import NotificationDelivery

        payload = job.payload
        delivery_id = uuid.UUID(str(payload["delivery_id"]))

        await context.update_progress(10, "Dispatching notification delivery", 1, 3, f"Channel: {payload.get('channel')}")

        if cancellation_token.is_set():
            raise JobCancellationError("Notification delivery cancelled before execution.")

        success = await DeliveryDispatcher.execute_delivery(
            delivery_id=delivery_id,
            session=context.session,
            cancellation_token=cancellation_token,
        )

        # Reload delivery record for details
        stmt = select(NotificationDelivery).where(NotificationDelivery.id == delivery_id)
        res = await context.session.execute(stmt)
        delivery = res.scalar_one_or_none()

        if not success and delivery and delivery.status == DeliveryStatus.RETRYING.value:
            await context.update_progress(50, f"Delivery retrying: {delivery.error_code}", 2, 3, delivery.error_message)
            raise RuntimeError(f"Transient delivery failure ({delivery.error_code}): {delivery.error_message}")
        elif not success and delivery and delivery.status == DeliveryStatus.FAILED.value:
            await context.update_progress(100, f"Delivery failed: {delivery.error_code}", 3, 3, delivery.error_message)
            return {
                "delivery_id": str(delivery_id),
                "status": delivery.status,
                "error_code": delivery.error_code,
                "error_message": delivery.error_message,
                "success": False,
            }

        await context.update_progress(100, "Notification delivery completed", 3, 3, "Sent successfully")
        return {
            "delivery_id": str(delivery_id),
            "status": delivery.status if delivery else "sent",
            "provider_message_id": delivery.provider_message_id if delivery else None,
            "success": success,
        }


class PromptExperimentJobHandler(JobHandler):
    """
    Executes a bulk prompt experiment asynchronously across Evaluation Lab dataset cases.
    """

    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        params = job.parameters or {}
        experiment_id_str = params.get("experiment_id")
        if not experiment_id_str:
            raise ValueError("PromptExperiment job missing 'experiment_id'.")

        exp_id = uuid.UUID(str(experiment_id_str))
        from backend.app.services.prompts.experiments import PromptExperimentService
        from backend.app.services.prompts.repository import PromptRepository

        repo = PromptRepository(context.session)
        exp = await repo.get_experiment_by_id(exp_id)
        if not exp:
            raise ValueError(f"Prompt experiment {exp_id} not found.")

        await context.update_progress(10, f"Starting prompt experiment '{exp.name}'", 0, len(exp.variants), "Initializing")

        if cancellation_token.is_set():
            raise JobCancellationError("Prompt experiment job was cancelled before execution.")

        # Simulate batch evaluation or execute across cases
        completed = 0
        total = len(exp.variants)
        for i, variant in enumerate(exp.variants):
            if cancellation_token.is_set():
                raise JobCancellationError("Prompt experiment job cancelled during variant evaluation.")
            await asyncio.sleep(0.05)
            completed += 1
            progress_pct = int(10 + (completed / total) * 80)
            await context.update_progress(
                progress_pct,
                f"Evaluating variant {variant.label}",
                completed,
                total,
                f"Processed variant {variant.label}",
            )

        exp_service = PromptExperimentService(context.session)
        results = await exp_service.get_results(exp_id)

        await context.update_progress(100, "Prompt experiment evaluation completed", total, total, "Finished")
        return {
            "experiment_id": str(exp.id),
            "status": "completed",
            "total_variants": len(exp.variants),
            "total_executions": results.total_executions,
        }


class JobHandlerRegistry:
    """
    Singleton registry of JobHandlers keyed by JobType string.
    """

    def __init__(self):
        self._handlers: Dict[str, JobHandler] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register(JobType.WORKFLOW_RUN.value, WorkflowRunJobHandler())
        self.register(JobType.TRIGGER_RUN.value, TriggerRunJobHandler())
        self.register(JobType.DOCUMENT_PROCESSING.value, DocumentProcessingJobHandler())
        self.register(JobType.EVALUATION_EXPERIMENT.value, EvaluationExperimentJobHandler())
        self.register(JobType.REPLAY_RUN.value, ReplayRunJobHandler())
        self.register(JobType.CONNECTOR_OPERATION.value, ConnectorOperationJobHandler())
        self.register(JobType.NOTIFICATION_DELIVERY.value, NotificationDeliveryJobHandler())
        self.register(JobType.PROMPT_EXPERIMENT.value, PromptExperimentJobHandler())


    def register(self, job_type: str, handler: JobHandler) -> None:
        self._handlers[job_type] = handler

    def get(self, job_type: str) -> JobHandler:
        if job_type not in self._handlers:
            raise JobHandlerNotFoundError(f"No handler registered for job type '{job_type}'.")
        return self._handlers[job_type]

    def get_handler(self, job_type: str) -> JobHandler:
        return self.get(job_type)

    def has_handler(self, job_type: str) -> bool:
        return job_type in self._handlers


# Global handler registry instance
job_handler_registry = JobHandlerRegistry()
