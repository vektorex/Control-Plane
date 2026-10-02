"""
TriggerExecutor: Maps event payloads to workflow inputs and orchestrates execution through WorkflowExecutor.
"""
import asyncio
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.db.models.trigger import WorkflowTrigger, TriggerRun
from backend.app.db.models.user import User
from backend.app.db.models.workflow import Workflow, WorkflowRun
from backend.app.repositories.workflow import WorkflowRepository
from backend.app.services.observability.events import TraceEventType, TraceEventStatus
from backend.app.services.observability.tracer import ExecutionTracer
from backend.app.services.triggers.events import TriggerEvent
from backend.app.services.triggers.retries import TriggerRetryManager
from backend.app.services.workflows.executor import WorkflowExecutor
from backend.app.services.workflows.schemas import WorkflowDefinition
from backend.app.services.workflows.validator import WorkflowValidator


class TriggerPayloadMapper:
    """
    Safely resolves {{payload.x.y}} templates into workflow input variables.
    Reuses the safe deterministic interpolation mechanism from the Workflow Engine.
    """

    @classmethod
    def map_inputs(
        cls,
        mapping_template: Dict[str, Any],
        event_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Maps event payload fields into target workflow input structure.
        """
        if not mapping_template:
            # If no explicit mapping defined, pass the payload directly
            return dict(event_payload)

        result: Dict[str, Any] = {}
        for k, expr in mapping_template.items():
            result[k] = cls._resolve_value(expr, event_payload)
        return result

    @classmethod
    def _resolve_value(cls, expr: Any, payload: Dict[str, Any]) -> Any:
        if not isinstance(expr, str):
            if isinstance(expr, dict):
                return {k: cls._resolve_value(v, payload) for k, v in expr.items()}
            elif isinstance(expr, list):
                return [cls._resolve_value(item, payload) for item in expr]
            return expr

        # Exact match replacement for non-string types
        exact_pattern = r"^\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}$"
        exact_match = re.match(exact_pattern, expr.strip())
        if exact_match:
            path = exact_match.group(1)
            return cls._get_path_value(path, payload)

        # Substring interpolation
        def replacer(match):
            path = match.group(1).strip()
            val = cls._get_path_value(path, payload)
            return str(val) if val is not None else ""

        return re.sub(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}", replacer, expr)

    @classmethod
    def _get_path_value(cls, path: str, payload: Dict[str, Any]) -> Any:
        parts = path.split(".")
        # Strip leading 'payload' or 'event' if present
        if parts[0] in ("payload", "event") and len(parts) > 1:
            parts = parts[1:]

        curr: Any = payload
        for p in parts:
            if isinstance(curr, dict):
                curr = curr.get(p)
            elif isinstance(curr, list):
                try:
                    curr = curr[int(p)]
                except (ValueError, IndexError):
                    return None
            else:
                return None
            if curr is None:
                return None

        return curr


class TriggerExecutor:
    """
    Executes a TriggerRun by preparing workflow inputs and delegating strictly
    to the authoritative WorkflowExecutor.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.wf_repo = WorkflowRepository(session)
        self.wf_executor = WorkflowExecutor(session)

    async def execute_trigger_run(
        self,
        trigger: WorkflowTrigger,
        trigger_run: TriggerRun,
        event: TriggerEvent,
        user: Optional[User] = None,
    ) -> TriggerRun:
        """
        Executes a workflow trigger run with retries, telemetry recording, and state persistence.
        """
        start_time = time.time()
        trigger_run.started_at = datetime.now(timezone.utc)
        trigger_run.status = "running"
        await self.session.commit()

        tracer = ExecutionTracer(run_id=trigger_run.id, workspace_id=trigger.workspace_id)
        tracer.record_event(
            event_type=TraceEventType.TRIGGER_STARTED,
            step_type=trigger.trigger_type,
            status=TraceEventStatus.STARTED,
            metadata={
                "trigger_id": str(trigger.id),
                "trigger_run_id": str(trigger_run.id),
                "trigger_type": trigger.trigger_type,
                "event_id": event.event_id,
            },
        )
        await tracer.flush_to_db(self.session)

        retry_cfg = trigger.retry_configuration or {}
        max_retries = retry_cfg.get("max_retries", 2)
        backoff_factor = retry_cfg.get("backoff_factor", 2.0)

        # 1. Map input payload
        mapping_tmpl = trigger.configuration.get("input_mapping", {})
        try:
            mapped_input = TriggerPayloadMapper.map_inputs(mapping_tmpl, event.payload)
        except Exception as e:
            trigger_run.status = "failed"
            trigger_run.error_code = "INPUT_MAPPING_ERROR"
            trigger_run.error_message = f"Failed to map event payload to inputs: {str(e)}"
            trigger_run.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
            return trigger_run

        trigger_run.input_snapshot = mapped_input

        # 2. Retrieve workflow and definition
        wf = await self.wf_repo.get_workflow_by_id_or_raise(trigger.workflow_id, trigger.workspace_id)
        target_version = trigger.workflow_version or wf.version
        version_snapshot = await self.wf_repo.get_version(wf.id, target_version)

        if version_snapshot:
            definition = WorkflowDefinition.model_validate(version_snapshot.definition)
        else:
            from backend.app.services.workflows.service import WorkflowService
            wf_service = WorkflowService(self.session)
            definition = await wf_service.get_workflow_definition(wf.id, trigger.workspace_id)

        # 3. Validate runtime inputs against schema
        try:
            validated_inputs = WorkflowValidator.validate_runtime_input(
                input_schema=wf.input_schema or {},
                runtime_input=mapped_input,
            )
        except Exception as e:
            trigger_run.status = "failed"
            trigger_run.error_code = "SCHEMA_VALIDATION_ERROR"
            trigger_run.error_message = f"Inputs failed workflow schema validation: {str(e)}"
            trigger_run.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
            return trigger_run

        # 4. Create WorkflowRun with trigger metadata in execution_state
        trigger_meta = {
            "trigger_id": str(trigger.id),
            "trigger_run_id": str(trigger_run.id),
            "trigger_type": trigger.trigger_type,
            "trigger_source": getattr(event, "source", trigger.trigger_type),
            "trigger_name": trigger.name,
            "event_type": getattr(event, "event_type", None),
        }

        wf_run = await self.wf_repo.create_run(
            workflow_id=wf.id,
            workflow_version=target_version,
            workspace_id=trigger.workspace_id,
            project_id=trigger.project_id or wf.project_id,
            input_data=validated_inputs,
        )
        wf_run.execution_state = dict(trigger_meta)
        trigger_run.workflow_run_id = wf_run.id
        await self.session.commit()

        # 5. Execute via WorkflowExecutor with bounded retries
        current_retry = 0
        while True:
            try:
                # Default system user if none provided
                exec_user = user or User(
                    id=trigger.created_by or uuid.uuid4(),
                    email="automation@internal",
                    workspace_id=trigger.workspace_id,
                )

                wf_run = await self.wf_executor.execute_workflow(
                    workflow=wf,
                    run=wf_run,
                    definition=definition,
                    user=exec_user,
                    input_data=validated_inputs,
                )

                # Ensure trigger metadata is preserved in workflow execution state
                if wf_run:
                    if not isinstance(wf_run.execution_state, dict):
                        wf_run.execution_state = {}
                    wf_run.execution_state.update(trigger_meta)

                if wf_run.status in ("completed", "waiting_for_approval", "paused"):
                    trigger_run.status = "completed"
                    trigger_run.completed_at = datetime.now(timezone.utc)
                    tracer.record_event(
                        event_type=TraceEventType.TRIGGER_COMPLETED,
                        step_type=trigger.trigger_type,
                        status=TraceEventStatus.COMPLETED,
                        duration_ms=int((time.time() - start_time) * 1000),
                        metadata={
                            "trigger_id": str(trigger.id),
                            "trigger_run_id": str(trigger_run.id),
                            "workflow_run_id": str(wf_run.id),
                            "status": wf_run.status,
                        },
                    )
                    await tracer.flush_to_db(self.session)
                    break
                else:
                    # Workflow run ended in failed or cancelled
                    err_code = wf_run.error_code or "WORKFLOW_EXECUTION_FAILED"
                    err_msg = wf_run.error_message or "Workflow execution finished in failed state."

                    if TriggerRetryManager.should_retry(err_code, err_msg, current_retry, max_retries):
                        current_retry += 1
                        trigger_run.retry_count = current_retry
                        delay = TriggerRetryManager.calculate_backoff_delay(current_retry, backoff_factor)
                        logger.info(f"[TriggerRetry] Retrying run {trigger_run.id} in {delay:.2f}s (attempt {current_retry}/{max_retries})")
                        tracer.record_event(
                            event_type=TraceEventType.TRIGGER_RETRY,
                            step_type=trigger.trigger_type,
                            metadata={"attempt": current_retry, "max_retries": max_retries, "delay_seconds": delay},
                        )
                        await tracer.flush_to_db(self.session)
                        await asyncio.sleep(min(delay, 5.0))  # bounded non-blocking wait
                        continue

                    trigger_run.status = "failed"
                    trigger_run.error_code = err_code
                    trigger_run.error_message = err_msg
                    trigger_run.completed_at = datetime.now(timezone.utc)
                    tracer.record_event(
                        event_type=TraceEventType.TRIGGER_FAILED,
                        step_type=trigger.trigger_type,
                        status=TraceEventStatus.FAILED,
                        error_code=err_code,
                        metadata={
                            "trigger_id": str(trigger.id),
                            "trigger_run_id": str(trigger_run.id),
                            "error": err_msg,
                        },
                    )
                    await tracer.flush_to_db(self.session)
                    break

            except Exception as e:
                err_code = "TRIGGER_EXECUTION_EXCEPTION"
                err_msg = str(e)
                if TriggerRetryManager.should_retry(err_code, err_msg, current_retry, max_retries):
                    current_retry += 1
                    trigger_run.retry_count = current_retry
                    delay = TriggerRetryManager.calculate_backoff_delay(current_retry, backoff_factor)
                    tracer.record_event(
                        event_type=TraceEventType.TRIGGER_RETRY,
                        step_type=trigger.trigger_type,
                        metadata={"attempt": current_retry, "max_retries": max_retries, "delay_seconds": delay},
                    )
                    await tracer.flush_to_db(self.session)
                    await asyncio.sleep(min(delay, 5.0))
                    continue

                trigger_run.status = "failed"
                trigger_run.error_code = err_code
                trigger_run.error_message = err_msg
                trigger_run.completed_at = datetime.now(timezone.utc)
                tracer.record_event(
                    event_type=TraceEventType.TRIGGER_FAILED,
                    step_type=trigger.trigger_type,
                    status=TraceEventStatus.FAILED,
                    error_code=err_code,
                    metadata={
                        "trigger_id": str(trigger.id),
                        "trigger_run_id": str(trigger_run.id),
                        "error": err_msg,
                    },
                )
                await tracer.flush_to_db(self.session)
                break

        await self.session.commit()
        return trigger_run
