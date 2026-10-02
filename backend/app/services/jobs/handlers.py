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
        doc = await pipeline.process_document(document_id, session)

        await context.update_progress(100, "Ingestion completed", 4, 4, f"Document indexed: {doc.filename}")

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

        return {
            "connector_id": str(result.connector_id) if result.connector_id else None,
            "operation": result.operation,
            "status": result.status,
            "data": result.data,
            "error": result.error,
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
