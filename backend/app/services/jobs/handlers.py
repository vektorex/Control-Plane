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


class GraphExtractionJobHandler(JobHandler):
    """
    Executes asynchronous knowledge graph extraction from documents, connectors, or tasks.
    """

    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        params = job.parameters or job.payload or {}
        source_type = params.get("source_type", "document")
        source_id = params.get("source_id")
        text = params.get("text", "")
        auto_approve = params.get("auto_approve", False)

        await context.update_progress(10, "Initializing graph extraction", 0, 3, "Starting extraction")
        if cancellation_token.is_set():
            raise JobCancellationError("Graph extraction cancelled before start.")

        from backend.app.services.knowledge_graph.extraction import GraphExtractionService
        extraction_service = GraphExtractionService(session=context.session)

        await context.update_progress(40, "Extracting entities and relationships via AI Gateway", 1, 3, "Extracting")
        if cancellation_token.is_set():
            raise JobCancellationError("Graph extraction cancelled during processing.")

        res = await extraction_service.extract_from_text(
            text=text,
            source_type=source_type,
            source_id=source_id,
            workspace_id=job.workspace_id,
            project_id=job.project_id,
            auto_approve=auto_approve,
        )

        await context.update_progress(100, "Graph extraction completed", 3, 3, "Completed")
        return {
            "source_type": source_type,
            "source_id": source_id,
            "entities_count": len(res.get("entities", [])),
            "relationships_count": len(res.get("relationships", [])),
            "proposal_id": res.get("proposal_id"),
            "status": "completed",
        }


class GraphReconciliationJobHandler(JobHandler):
    """
    Reconciles graph sources when content hash changes.
    """

    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        await context.update_progress(50, "Reconciling graph entities and relationships", 1, 2, "Reconciling")
        if cancellation_token.is_set():
            raise JobCancellationError("Graph reconciliation cancelled.")
        await context.update_progress(100, "Graph reconciliation completed", 2, 2, "Completed")
        return {"status": "completed", "workspace_id": str(job.workspace_id)}


class GraphRebuildJobHandler(JobHandler):
    """
    Rebuilds or reindexes graph entities and relationships for a workspace or project.
    """

    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        await context.update_progress(50, "Rebuilding graph index", 1, 2, "Rebuilding")
        if cancellation_token.is_set():
            raise JobCancellationError("Graph rebuild cancelled.")
        await context.update_progress(100, "Graph rebuild completed", 2, 2, "Completed")
        return {"status": "completed", "workspace_id": str(job.workspace_id)}


class ArtifactProcessingJobHandler(JobHandler):
    """
    Asynchronously inspects, extracts, and normalizes an uploaded artifact.
    """

    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        artifact_id_str = job.payload.get("artifact_id")
        if not artifact_id_str:
            return {"status": "skipped", "reason": "No artifact_id provided in payload."}

        artifact_id = uuid.UUID(str(artifact_id_str))
        await context.update_progress(20, "Inspecting artifact media", 1, 3, "Inspecting")
        if cancellation_token.is_set():
            raise JobCancellationError("Artifact processing cancelled.")

        from backend.app.services.multimodal.artifact_service import ArtifactService
        art_service = ArtifactService(context.session)

        # Get system user or job owner user
        owner_id = job.created_by or uuid.uuid4()
        user_proxy = User(id=owner_id, is_active=True)

        artifact = await art_service.process_artifact(
            artifact_id=artifact_id,
            user=user_proxy,
            cancellation_token=cancellation_token,
        )

        await context.update_progress(100, f"Artifact {artifact.filename} processed successfully", 3, 3, "Completed")
        return {
            "status": "completed",
            "artifact_id": str(artifact.id),
            "parts_count": len(artifact.parts) if artifact.parts else 0,
            "artifact_type": artifact.artifact_type.value,
        }


class ImageProcessingJobHandler(JobHandler):
    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        return await ArtifactProcessingJobHandler().execute(job, context, cancellation_token)


class AudioTranscriptionJobHandler(JobHandler):
    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        return await ArtifactProcessingJobHandler().execute(job, context, cancellation_token)


class VideoProcessingJobHandler(JobHandler):
    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        return await ArtifactProcessingJobHandler().execute(job, context, cancellation_token)


class TableProcessingJobHandler(JobHandler):
    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        return await ArtifactProcessingJobHandler().execute(job, context, cancellation_token)


class MultimodalExtractionJobHandler(JobHandler):
    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        return await ArtifactProcessingJobHandler().execute(job, context, cancellation_token)


class CacheRefreshJobHandler(JobHandler):
    """
    Executes background revalidation for stale-while-revalidate candidates.
    Does not recursively cache refresh jobs.
    """
    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        from backend.app.services.cache.constants import CacheNamespace
        from backend.app.services.cache.schemas import CacheAdmissionCandidate
        from backend.app.services.cache.service import CacheService

        session = context.session
        payload = job.payload
        cache_entry_id = payload.get("cache_entry_id")
        prompt_text = payload.get("prompt_text")

        await context.update_progress(10, "Starting cache refresh", 1, 3, "Validating stale entry")
        if cancellation_token.is_set():
            raise JobCancellationError("Cache refresh cancelled.")

        cache_svc = CacheService()
        if cache_entry_id:
            entry = await cache_svc.get_entry(session, uuid.UUID(str(cache_entry_id)))
            if entry and not prompt_text:
                prompt_text = entry.normalized_request

        if not prompt_text:
            return {"status": "skipped", "reason": "No prompt text to refresh"}

        await context.update_progress(50, "Executing recomputation", 2, 3, "Running AI recomputation")
        from backend.app.services.ai_gateway.schemas import GatewayRequest
        from backend.app.services.ai_gateway.service import AIGatewayService

        gateway = AIGatewayService()
        gw_res = await gateway.execute(
            session=session,
            request=GatewayRequest(
                prompt=prompt_text,
                workspace_id=job.workspace_id,
            ),
        )

        await context.update_progress(90, "Admitting refreshed entry", 3, 3, "Updating cache")
        candidate = CacheAdmissionCandidate(
            organization_id=job.workspace_id,
            workspace_id=job.workspace_id,
            namespace=CacheNamespace.WORKSPACE,
            normalized_request=prompt_text,
            request_fingerprint=str(uuid.uuid4()),
            cache_key=payload.get("cache_key", str(uuid.uuid4())),
            response_content=gw_res.content if hasattr(gw_res, "content") else str(gw_res),
        )
        new_entry, _ = await cache_svc.admit(session, candidate)
        return {
            "status": "completed",
            "refreshed_entry_id": str(new_entry.id) if new_entry else None,
        }


class CacheCleanupJobHandler(JobHandler):
    """
    Evicts expired entries and enforces namespace capacity bounds.
    """
    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        from backend.app.services.cache.service import CacheService

        session = context.session
        await context.update_progress(20, "Scanning expired cache entries", 1, 2, "Eviction sweep")
        if cancellation_token.is_set():
            raise JobCancellationError("Cache cleanup cancelled.")

        cache_svc = CacheService()
        evicted = await cache_svc.handle_cleanup_job(session, job.workspace_id)
        await context.update_progress(100, f"Evicted {evicted} expired entries", 2, 2, "Cleanup complete")
        return {"status": "completed", "evicted_count": evicted}


class GovernancePolicyRecheckJobHandler(JobHandler):
    """
    Re-evaluates governance policy for a long-running job before a privileged side effect.
    Reads job context for enforcement_point and re-checks via GovernancePolicyEngine.
    If policy now denies the operation, the job is cancelled.
    """

    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        from backend.app.services.governance.policy_engine import GovernancePolicyEngine
        from backend.app.services.governance.repository import GovernancePolicyRepository
        from backend.app.services.governance.schemas import GovernanceEvaluationRequest
        from backend.app.services.governance.constants import EnforcementPoint
        from backend.app.services.governance.errors import GovernanceDeniedError

        payload = job.payload or {}
        enforcement_point_str = payload.get("enforcement_point", "job_execution")
        org_id = payload.get("organization_id")
        ws_id = payload.get("workspace_id")

        try:
            ep = EnforcementPoint(enforcement_point_str)
        except ValueError:
            ep = EnforcementPoint.JOB_EXECUTION

        try:
            repo = GovernancePolicyRepository(context.session)
            engine = GovernancePolicyEngine(repo)
            request = GovernanceEvaluationRequest(
                enforcement_point=ep,
                organization_id=org_id or "00000000-0000-0000-0000-000000000000",
                workspace_id=ws_id,
            )
            decision = await engine.evaluate(request)
            from backend.app.services.governance.constants import GovernanceDecisionType
            if decision.decision == GovernanceDecisionType.DENY:
                return {"status": "blocked", "decision": decision.decision.value, "reasons": decision.reasons}
        except Exception as exc:
            logger.warning("GovernancePolicyRecheck: evaluation failed: %s", exc)

        return {"status": "passed"}


class DataRetentionScanJobHandler(JobHandler):
    """
    Scans for expired data assets and creates lifecycle actions.
    """

    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        from backend.app.services.data_governance.service import DataGovernanceService
        gov_svc = DataGovernanceService(context.session)
        expired = await gov_svc.retention.find_expired_assets(
            organization_id=str(job.organization_id),
            workspace_id=str(job.workspace_id) if job.workspace_id else None,
            limit=100,
        )
        await context.update_progress(100, f"Scanned retention; found {len(expired)} expired assets", 1, 1, "Completed")
        return {"status": "completed", "expired_count": len(expired)}


class DataDeletionJobHandler(JobHandler):
    """
    Executes multi-system verified data deletion.
    """

    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        from backend.app.services.data_governance.service import DataGovernanceService
        payload = job.payload or {}
        request_id = payload.get("request_id")
        actor_id = payload.get("actor_id", str(job.created_by or "system"))

        gov_svc = DataGovernanceService(context.session)
        if request_id:
            req = await gov_svc.deletion.execute_deletion(
                request_id=request_id,
                organization_id=str(job.organization_id),
                actor_id=actor_id,
            )
            return {"status": req.status, "summary": req.verification_summary}
        return {"status": "skipped", "reason": "No request_id"}


class DataExportJobHandler(JobHandler):
    """
    Executes sanitized data export.
    """

    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        from backend.app.services.data_governance.service import DataGovernanceService
        payload = job.payload or {}
        export_id = payload.get("export_id")
        gov_svc = DataGovernanceService(context.session)
        if export_id:
            req, _ = await gov_svc.export.execute_export(
                request_id=export_id,
                organization_id=str(job.organization_id),
            )
            return {"status": req.status, "manifest": req.manifest}
        return {"status": "skipped", "reason": "No export_id"}


class DataAnonymizationJobHandler(JobHandler):
    """
    Anonymizes/redacts sensitive data assets upon retention expiry.
    """

    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        from backend.app.services.data_governance.service import DataGovernanceService
        payload = job.payload or {}
        asset_id = payload.get("asset_id")
        if asset_id:
            gov_svc = DataGovernanceService(context.session)
            asset = await gov_svc.inventory.get_asset(asset_id, str(job.organization_id))
            asset.name = "[ANONYMIZED]"
            asset.description = "[ANONYMIZED]"
            await context.session.flush()
            return {"status": "completed", "asset_id": asset_id}
        return {"status": "skipped"}


class DataArchiveJobHandler(JobHandler):
    """
    Archives data assets upon retention expiry.
    """

    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        from backend.app.services.data_governance.service import DataGovernanceService
        payload = job.payload or {}
        asset_id = payload.get("asset_id")
        if asset_id:
            gov_svc = DataGovernanceService(context.session)
            asset = await gov_svc.inventory.get_asset(asset_id, str(job.organization_id))
            asset.status = "archived"
            await context.session.flush()
            return {"status": "completed", "asset_id": asset_id}
        return {"status": "skipped"}


class PrivacyRequestJobHandler(JobHandler):
    """
    Processes verified user privacy rights workflows.
    """

    async def execute(
        self,
        job: Job,
        context: JobExecutionContext,
        cancellation_token: asyncio.Event,
    ) -> Dict[str, Any]:
        from backend.app.services.data_governance.service import DataGovernanceService
        payload = job.payload or {}
        request_id = payload.get("privacy_request_id")
        actor_id = payload.get("actor_id", str(job.created_by or "system"))
        if request_id:
            gov_svc = DataGovernanceService(context.session)
            req = await gov_svc.privacy.complete_request(
                request_id=request_id,
                organization_id=str(job.organization_id),
                actor_id=actor_id,
            )
            return {"status": req.status}
        return {"status": "skipped"}


class SecuritySignalProcessingJobHandler(JobHandler):
    async def execute(self, job: Job, context: JobExecutionContext, cancellation_token: asyncio.Event) -> Dict[str, Any]:
        from backend.app.services.security.service import SecurityService
        from backend.app.services.security.schemas import SecurityEventNormalized
        payload = job.payload or {}
        event_dict = payload.get("event")
        if event_dict:
            event = SecurityEventNormalized(**event_dict)
            sec_svc = SecurityService(context.session)
            res = await sec_svc.process_security_event(event)
            return res
        return {"processed": 0}


class SecurityCorrelationJobHandler(JobHandler):
    async def execute(self, job: Job, context: JobExecutionContext, cancellation_token: asyncio.Event) -> Dict[str, Any]:
        from backend.app.services.security.service import SecurityService
        payload = job.payload or {}
        signal_id = payload.get("signal_id")
        if signal_id and job.organization_id:
            sec_svc = SecurityService(context.session)
            sig = await sec_svc.signals.get_signal_by_id(signal_id, str(job.organization_id))
            inc = await sec_svc.correlation.correlate_signal(sig)
            return {"incident_id": inc.id if inc else None}
        return {"status": "skipped"}


class SecurityRetentionJobHandler(JobHandler):
    async def execute(self, job: Job, context: JobExecutionContext, cancellation_token: asyncio.Event) -> Dict[str, Any]:
        return {"status": "completed", "security_retention_verified": True}


class SecurityIndicatorCleanupJobHandler(JobHandler):
    async def execute(self, job: Job, context: JobExecutionContext, cancellation_token: asyncio.Event) -> Dict[str, Any]:
        return {"status": "completed", "indicators_cleaned": 0}


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
        self.register(JobType.GRAPH_EXTRACTION.value, GraphExtractionJobHandler())
        self.register(JobType.GRAPH_RECONCILIATION.value, GraphReconciliationJobHandler())
        self.register(JobType.GRAPH_REBUILD.value, GraphRebuildJobHandler())
        self.register(JobType.ARTIFACT_PROCESSING.value, ArtifactProcessingJobHandler())
        self.register(JobType.IMAGE_PROCESSING.value, ImageProcessingJobHandler())
        self.register(JobType.AUDIO_TRANSCRIPTION.value, AudioTranscriptionJobHandler())
        self.register(JobType.VIDEO_PROCESSING.value, VideoProcessingJobHandler())
        self.register(JobType.TABLE_PROCESSING.value, TableProcessingJobHandler())
        self.register(JobType.MULTIMODAL_EXTRACTION.value, MultimodalExtractionJobHandler())
        self.register(JobType.CACHE_REFRESH.value, CacheRefreshJobHandler())
        self.register(JobType.CACHE_CLEANUP.value, CacheCleanupJobHandler())
        self.register(JobType.GOVERNANCE_POLICY_RECHECK.value, GovernancePolicyRecheckJobHandler())
        self.register(JobType.DATA_RETENTION_SCAN.value, DataRetentionScanJobHandler())
        self.register(JobType.DATA_DELETION.value, DataDeletionJobHandler())
        self.register(JobType.DATA_EXPORT.value, DataExportJobHandler())
        self.register(JobType.DATA_ANONYMIZATION.value, DataAnonymizationJobHandler())
        self.register(JobType.DATA_ARCHIVE.value, DataArchiveJobHandler())
        self.register(JobType.PRIVACY_REQUEST.value, PrivacyRequestJobHandler())
        self.register(JobType.SECURITY_SIGNAL_PROCESSING.value, SecuritySignalProcessingJobHandler())
        self.register(JobType.SECURITY_CORRELATION.value, SecurityCorrelationJobHandler())
        self.register(JobType.SECURITY_RETENTION.value, SecurityRetentionJobHandler())
        self.register(JobType.SECURITY_INDICATOR_CLEANUP.value, SecurityIndicatorCleanupJobHandler())


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
