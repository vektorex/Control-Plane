"""
Main facade service for Workflow Triggers and Event Automation.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select, and_, desc, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.db.models.trigger import WorkflowTrigger, TriggerRun
from backend.app.db.models.user import User
from backend.app.db.models.workflow import Workflow, WorkflowRun
from backend.app.repositories.workflow import WorkflowRepository
from backend.app.services.observability.events import TraceEventType, TraceEventStatus
from backend.app.services.observability.tracer import ExecutionTracer
from backend.app.services.triggers.deduplication import TriggerDeduplicationService
from backend.app.services.triggers.errors import (
    TriggerDisabledError,
    TriggerNotFoundError,
    TriggerPolicyError,
    TriggerValidationError,
)
from backend.app.services.triggers.events import EventTriggerService, TriggerEvent
from backend.app.services.triggers.executor import TriggerExecutor, TriggerPayloadMapper
from backend.app.services.triggers.filters import TriggerFilterEngine
from backend.app.services.triggers.policies import TriggerPolicyEngine
from backend.app.services.triggers.registry import trigger_registry
from backend.app.services.triggers.scheduler import TriggerScheduler
from backend.app.services.triggers.schemas import (
    FilterConfiguration,
    TriggerRunListResponse,
    TriggerRunResponse,
    TriggerTestRequest,
    TriggerTestResponse,
    WebhookSecretResponse,
    WebhookStatusResponse,
    WorkflowTriggerCreateRequest,
    WorkflowTriggerListResponse,
    WorkflowTriggerResponse,
    WorkflowTriggerUpdateRequest,
)
from backend.app.services.triggers.webhook import WebhookSecretStore, WebhookTriggerService
from backend.app.services.workflows.validator import WorkflowValidator


class TriggerService:
    """
    High-level trigger orchestration service for CRUD, execution, webhook dispatch, and testing.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.wf_repo = WorkflowRepository(session)
        self.secret_store = WebhookSecretStore()

    async def create_trigger(
        self,
        workspace_id: uuid.UUID,
        workflow_id: uuid.UUID,
        request: WorkflowTriggerCreateRequest,
        user: User,
    ) -> Tuple[WorkflowTriggerResponse, Optional[str]]:
        """
        Creates a new workflow trigger. Returns (response, plain_secret_if_generated).
        """
        # Validate workflow exists in workspace
        wf = await self.wf_repo.get_workflow_by_id_or_raise(workflow_id, workspace_id)

        config_dict = dict(request.configuration)
        public_trigger_id: Optional[str] = None
        encrypted_secret: Optional[str] = None
        plain_secret: Optional[str] = None
        next_run: Optional[datetime] = None

        # Type-specific initializations
        if request.trigger_type.value == "webhook":
            public_trigger_id = self.secret_store.generate_public_trigger_id()
            plain_secret = self.secret_store.generate_secret()
            encrypted_secret = self.secret_store.encrypt_secret(plain_secret)

        elif request.trigger_type.value == "schedule":
            validated_sched = await TriggerScheduler.validate_schedule_config(
                config=config_dict,
                session=self.session,
                workspace_id=workspace_id,
            )
            config_dict["schedule"] = validated_sched
            expr = validated_sched.get("expression", "0 * * * *")
            tz_str = validated_sched.get("timezone", "UTC")
            next_run = TriggerScheduler.compute_next_run(expr, tz_str)

        elif request.trigger_type.value == "connector_event":
            # For connector events, if webhook endpoint is desired, create public trigger ID
            public_trigger_id = self.secret_store.generate_public_trigger_id()
            plain_secret = self.secret_store.generate_secret()
            encrypted_secret = self.secret_store.encrypt_secret(plain_secret)

        filter_dict = request.filter_configuration.model_dump() if request.filter_configuration else None
        retry_dict = request.retry_configuration.model_dump() if request.retry_configuration else {"max_retries": 2, "backoff_factor": 2.0}

        trigger = WorkflowTrigger(
            workspace_id=workspace_id,
            project_id=request.project_id or wf.project_id,
            workflow_id=workflow_id,
            workflow_version=request.workflow_version or wf.version,
            name=request.name,
            description=request.description,
            trigger_type=request.trigger_type.value,
            status="active",
            configuration=config_dict,
            filter_configuration=filter_dict,
            retry_configuration=retry_dict,
            public_trigger_id=public_trigger_id,
            webhook_secret_hash=encrypted_secret,
            debounce_seconds=request.debounce_seconds or 0,
            created_by=user.id,
            next_run_at=next_run,
        )

        self.session.add(trigger)
        await self.session.commit()
        await self.session.refresh(trigger)

        resp = await self._format_trigger_response(trigger, workflow_name=wf.name)
        return resp, plain_secret

    async def list_triggers(
        self,
        workspace_id: uuid.UUID,
        workflow_id: Optional[uuid.UUID] = None,
    ) -> WorkflowTriggerListResponse:
        """Lists triggers in workspace, optionally filtered by workflow."""
        stmt = select(WorkflowTrigger).where(WorkflowTrigger.workspace_id == workspace_id)
        if workflow_id:
            stmt = stmt.where(WorkflowTrigger.workflow_id == workflow_id)
        stmt = stmt.order_by(desc(WorkflowTrigger.created_at))

        res = await self.session.execute(stmt)
        triggers = list(res.scalars().all())

        formatted: List[WorkflowTriggerResponse] = []
        for t in triggers:
            wf_name = t.workflow.name if t.workflow else None
            formatted.append(await self._format_trigger_response(t, workflow_name=wf_name))

        return WorkflowTriggerListResponse(triggers=formatted, total=len(formatted))

    async def get_trigger_or_raise(
        self,
        trigger_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> WorkflowTrigger:
        """Retrieves trigger or raises TriggerNotFoundError."""
        stmt = select(WorkflowTrigger).where(
            WorkflowTrigger.id == trigger_id,
            WorkflowTrigger.workspace_id == workspace_id,
        )
        res = await self.session.execute(stmt)
        trigger = res.scalar_one_or_none()
        if not trigger:
            raise TriggerNotFoundError(f"Trigger '{trigger_id}' not found in workspace.")
        return trigger

    async def get_trigger(
        self,
        trigger_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> WorkflowTriggerResponse:
        trigger = await self.get_trigger_or_raise(trigger_id, workspace_id)
        wf_name = trigger.workflow.name if trigger.workflow else None
        return await self._format_trigger_response(trigger, workflow_name=wf_name)

    async def update_trigger(
        self,
        trigger_id: uuid.UUID,
        workspace_id: uuid.UUID,
        request: WorkflowTriggerUpdateRequest,
    ) -> WorkflowTriggerResponse:
        trigger = await self.get_trigger_or_raise(trigger_id, workspace_id)

        if request.name is not None:
            trigger.name = request.name
        if request.description is not None:
            trigger.description = request.description
        if request.status is not None:
            trigger.status = request.status.value
        if request.workflow_version is not None:
            trigger.workflow_version = request.workflow_version
        if request.debounce_seconds is not None:
            trigger.debounce_seconds = request.debounce_seconds

        if request.configuration is not None:
            cfg = dict(request.configuration)
            if trigger.trigger_type == "schedule":
                validated = await TriggerScheduler.validate_schedule_config(cfg, self.session, workspace_id)
                cfg["schedule"] = validated
                expr = validated.get("expression", "0 * * * *")
                tz_str = validated.get("timezone", "UTC")
                trigger.next_run_at = TriggerScheduler.compute_next_run(expr, tz_str)
            trigger.configuration = cfg

        if request.filter_configuration is not None:
            trigger.filter_configuration = request.filter_configuration.model_dump()
        if request.retry_configuration is not None:
            trigger.retry_configuration = request.retry_configuration.model_dump()

        trigger.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(trigger)

        wf_name = trigger.workflow.name if trigger.workflow else None
        return await self._format_trigger_response(trigger, workflow_name=wf_name)

    async def delete_trigger(
        self,
        trigger_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> bool:
        trigger = await self.get_trigger_or_raise(trigger_id, workspace_id)
        await self.session.delete(trigger)
        await self.session.commit()
        return True

    async def pause_trigger(
        self,
        trigger_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> WorkflowTriggerResponse:
        trigger = await self.get_trigger_or_raise(trigger_id, workspace_id)
        trigger.status = "paused"
        trigger.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(trigger)
        return await self._format_trigger_response(trigger, workflow_name=trigger.workflow.name if trigger.workflow else None)

    async def resume_trigger(
        self,
        trigger_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> WorkflowTriggerResponse:
        trigger = await self.get_trigger_or_raise(trigger_id, workspace_id)
        trigger.status = "active"
        if trigger.trigger_type == "schedule":
            sched_cfg = trigger.configuration.get("schedule", trigger.configuration)
            expr = sched_cfg.get("expression", "0 * * * *")
            tz_str = sched_cfg.get("timezone", "UTC")
            trigger.next_run_at = TriggerScheduler.compute_next_run(expr, tz_str)
        trigger.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(trigger)
        return await self._format_trigger_response(trigger, workflow_name=trigger.workflow.name if trigger.workflow else None)

    async def test_trigger(
        self,
        trigger_id: uuid.UUID,
        workspace_id: uuid.UUID,
        request: TriggerTestRequest,
    ) -> TriggerTestResponse:
        """
        Test mode: Evaluates configuration, filters, and variable mapping without executing external side-effects.
        """
        trigger = await self.get_trigger_or_raise(trigger_id, workspace_id)
        wf = await self.wf_repo.get_workflow_by_id_or_raise(trigger.workflow_id, workspace_id)

        sample_payload = request.sample_payload or {}
        policy_warnings: List[str] = []

        if trigger.status != "active":
            policy_warnings.append(f"Trigger is currently '{trigger.status}'. Must be active to run in production.")
        if wf.status == "draft":
            policy_warnings.append("Target workflow is in draft mode. Publishing is recommended.")

        # 1. Filter evaluation
        matches, filter_details = TriggerFilterEngine.evaluate(
            trigger.filter_configuration,
            sample_payload,
        )

        # 2. Input mapping
        mapping_tmpl = trigger.configuration.get("input_mapping", {})
        try:
            mapped_inputs = TriggerPayloadMapper.map_inputs(mapping_tmpl, sample_payload)
        except Exception as e:
            mapped_inputs = {}
            policy_warnings.append(f"Input mapping failed: {str(e)}")

        # 3. Schema validation check
        if mapped_inputs and wf.input_schema:
            try:
                WorkflowValidator.validate_runtime_input(wf.input_schema, mapped_inputs)
            except Exception as e:
                policy_warnings.append(f"Mapped inputs do not satisfy workflow input schema: {str(e)}")

        status_str = "accepted" if matches and not policy_warnings else ("filtered" if not matches else "warning")

        return TriggerTestResponse(
            accepted=matches and len(policy_warnings) == 0,
            filter_matched=matches,
            filter_details=filter_details,
            mapped_inputs=mapped_inputs,
            policy_warnings=policy_warnings,
            status=status_str,
        )

    async def run_manual_trigger(
        self,
        workflow_id: uuid.UUID,
        trigger_id: uuid.UUID,
        workspace_id: uuid.UUID,
        user: User,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> TriggerRunResponse:
        """
        Executes a manual trigger synchronously through WorkflowExecutor.
        """
        trigger = await self.get_trigger_or_raise(trigger_id, workspace_id)
        if trigger.workflow_id != workflow_id:
            raise TriggerValidationError("Trigger does not belong to specified workflow.")

        wf = await self.wf_repo.get_workflow_by_id_or_raise(workflow_id, workspace_id)

        # Validate trigger policy
        await TriggerPolicyEngine.validate_trigger_execution(self.session, trigger, wf)

        # Create TriggerRun
        trig_run = TriggerRun(
            trigger_id=trigger.id,
            workspace_id=workspace_id,
            event_id=f"man_{uuid.uuid4().hex[:12]}",
            status="queued",
            input_snapshot=input_data or {},
        )
        self.session.add(trig_run)
        await self.session.commit()
        await self.session.refresh(trig_run)

        # Build normalized TriggerEvent
        event = TriggerEvent(
            event_id=trig_run.event_id,
            event_type="manual.workflow.run",
            source="manual",
            workspace_id=workspace_id,
            payload=input_data or {},
            metadata={"user_id": str(user.id)},
        )

        executor = TriggerExecutor(self.session)
        trig_run = await executor.execute_trigger_run(
            trigger=trigger,
            trigger_run=trig_run,
            event=event,
            user=user,
        )

        return self._format_run_response(trig_run)

    async def regenerate_webhook_secret(
        self,
        trigger_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> WebhookSecretResponse:
        """Regenerates the webhook secret for a trigger. Returns secret once."""
        trigger = await self.get_trigger_or_raise(trigger_id, workspace_id)
        if trigger.trigger_type not in ("webhook", "connector_event"):
            raise TriggerValidationError("Only webhook and connector_event triggers support webhook secrets.")

        if not trigger.public_trigger_id:
            trigger.public_trigger_id = self.secret_store.generate_public_trigger_id()

        plain_secret = self.secret_store.generate_secret()
        trigger.webhook_secret_hash = self.secret_store.encrypt_secret(plain_secret)
        trigger.updated_at = datetime.now(timezone.utc)

        await self.session.commit()

        webhook_url = f"/api/webhooks/{trigger.public_trigger_id}"
        return WebhookSecretResponse(
            webhook_url=webhook_url,
            secret=plain_secret,
            message="Webhook secret successfully regenerated. Store this secret securely; it cannot be viewed again.",
        )

    async def get_webhook_status(
        self,
        trigger_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> WebhookStatusResponse:
        trigger = await self.get_trigger_or_raise(trigger_id, workspace_id)
        webhook_url = f"/api/webhooks/{trigger.public_trigger_id}" if trigger.public_trigger_id else ""
        return WebhookStatusResponse(
            configured=bool(trigger.public_trigger_id and trigger.webhook_secret_hash),
            webhook_url=webhook_url,
            public_trigger_id=trigger.public_trigger_id or "",
            last_received_at=trigger.last_triggered_at,
        )

    async def handle_webhook_event(
        self,
        identifier: str,
        raw_body: bytes,
        headers: Dict[str, str],
        parsed_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        High-performance webhook ingestion:
        Validates trigger -> Verifies signature -> Normalizes event -> Idempotency -> Filters -> TriggerRun -> Dispatches.
        """
        # Lookup trigger by public_trigger_id or trigger_id
        if self._is_valid_uuid(identifier):
            stmt = select(WorkflowTrigger).where(
                (WorkflowTrigger.public_trigger_id == identifier) | (WorkflowTrigger.id == uuid.UUID(identifier))
            )
        else:
            stmt = select(WorkflowTrigger).where(WorkflowTrigger.public_trigger_id == identifier)
        res = await self.session.execute(stmt)
        trigger = res.scalar_one_or_none()
        if not trigger:
            raise TriggerNotFoundError(f"Webhook trigger '{identifier}' not found.")

        # 1. Telemetry: trigger_received
        tracer = ExecutionTracer(run_id=trigger.id, workspace_id=trigger.workspace_id)
        tracer.record_event(
            event_type=TraceEventType.TRIGGER_RECEIVED,
            step_type=trigger.trigger_type,
            metadata={"trigger_id": str(trigger.id), "content_length": len(raw_body)},
        )
        await tracer.flush_to_db(self.session)

        # 2. Check trigger status
        if trigger.status != "active":
            raise TriggerDisabledError(f"Webhook trigger is {trigger.status}.")

        # 3. Verify HMAC Signature
        WebhookTriggerService.verify_request(
            raw_body=raw_body,
            headers=headers,
            encrypted_secret=trigger.webhook_secret_hash,
        )

        # 4. Normalize Event
        if "x-github-event" in {k.lower(): v for k, v in headers.items()}:
            event = EventTriggerService.normalize_github_event(
                raw_payload=parsed_payload,
                headers=headers,
                workspace_id=trigger.workspace_id,
            )
        else:
            event = EventTriggerService.normalize_generic_webhook(
                raw_payload=parsed_payload,
                headers=headers,
                workspace_id=trigger.workspace_id,
            )

        # 5. Idempotency Check
        idempotency_key = headers.get("x-idempotency-key") or headers.get("idempotency-key") or event.event_id
        is_dup, dup_reason = await TriggerDeduplicationService.check_and_record_idempotency(
            session=self.session,
            trigger_id=trigger.id,
            idempotency_key=idempotency_key,
            event_id=event.event_id,
        )
        if is_dup:
            # Mark skipped and return fast
            skip_run = TriggerRun(
                trigger_id=trigger.id,
                workspace_id=trigger.workspace_id,
                event_id=event.event_id,
                status="skipped",
                idempotency_key=idempotency_key,
                error_code="TRIGGER_DEDUPLICATED",
                error_message=dup_reason,
                completed_at=datetime.now(timezone.utc),
            )
            self.session.add(skip_run)
            await self.session.commit()
            return {"accepted": False, "status": "skipped", "reason": dup_reason, "run_id": str(skip_run.id)}

        # 6. Debouncing Check
        is_debounced, rem_sec = await TriggerDeduplicationService.check_debounce(
            session=self.session,
            trigger_id=trigger.id,
            debounce_seconds=trigger.debounce_seconds,
        )
        if is_debounced:
            skip_run = TriggerRun(
                trigger_id=trigger.id,
                workspace_id=trigger.workspace_id,
                event_id=event.event_id,
                status="skipped",
                idempotency_key=idempotency_key,
                error_code="TRIGGER_DEBOUNCED",
                error_message=f"Debounced: run suppressed within {trigger.debounce_seconds}s window ({rem_sec}s remaining).",
                completed_at=datetime.now(timezone.utc),
            )
            self.session.add(skip_run)
            await self.session.commit()
            return {"accepted": False, "status": "debounced", "run_id": str(skip_run.id)}

        # 7. Policy Checks (Rate limits, concurrency)
        try:
            await TriggerPolicyEngine.validate_trigger_execution(self.session, trigger)
        except Exception as e:
            err_code = getattr(e, "code", "TRIGGER_POLICY_DENIED")
            skip_run = TriggerRun(
                trigger_id=trigger.id,
                workspace_id=trigger.workspace_id,
                event_id=event.event_id,
                status="skipped",
                idempotency_key=idempotency_key,
                error_code=err_code,
                error_message=str(e),
                completed_at=datetime.now(timezone.utc),
            )
            self.session.add(skip_run)
            await self.session.commit()
            raise

        # 8. Event Filtering
        matched, filter_details = TriggerFilterEngine.evaluate(
            trigger.filter_configuration,
            event.payload,
        )
        if not matched:
            skip_run = TriggerRun(
                trigger_id=trigger.id,
                workspace_id=trigger.workspace_id,
                event_id=event.event_id,
                status="skipped",
                idempotency_key=idempotency_key,
                filter_result=filter_details,
                error_code="FILTER_MISMATCH",
                error_message="Event did not match trigger filter conditions.",
                completed_at=datetime.now(timezone.utc),
            )
            self.session.add(skip_run)
            await self.session.commit()
            tracer = ExecutionTracer(run_id=skip_run.id, workspace_id=trigger.workspace_id)
            tracer.record_event(
                event_type=TraceEventType.TRIGGER_FILTERED,
                step_type=trigger.trigger_type,
                metadata={"trigger_id": str(trigger.id), "filter_details": filter_details},
            )
            await tracer.flush_to_db(self.session)
            return {"accepted": False, "status": "filtered", "run_id": str(skip_run.id), "filter_details": filter_details}

        # 9. Create TriggerRun in queued state
        trig_run = TriggerRun(
            trigger_id=trigger.id,
            workspace_id=trigger.workspace_id,
            event_id=event.event_id,
            status="queued",
            idempotency_key=idempotency_key,
            filter_result=filter_details,
        )
        self.session.add(trig_run)
        trigger.last_triggered_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(trig_run)

        # 10. Execute asynchronously or dispatch immediately
        executor = TriggerExecutor(self.session)
        await executor.execute_trigger_run(
            trigger=trigger,
            trigger_run=trig_run,
            event=event,
        )

        return {
            "accepted": True,
            "status": "queued",
            "trigger_run_id": str(trig_run.id),
            "workflow_run_id": str(trig_run.workflow_run_id) if trig_run.workflow_run_id else None,
            "event_id": event.event_id,
        }

    async def list_trigger_runs(
        self,
        trigger_id: uuid.UUID,
        workspace_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> TriggerRunListResponse:
        """Retrieves history of executions for a trigger."""
        await self.get_trigger_or_raise(trigger_id, workspace_id)

        stmt = (
            select(TriggerRun)
            .where(
                TriggerRun.trigger_id == trigger_id,
                TriggerRun.workspace_id == workspace_id,
            )
            .order_by(desc(TriggerRun.created_at))
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        runs = list(res.scalars().all())

        count_stmt = select(func.count(TriggerRun.id)).where(
            TriggerRun.trigger_id == trigger_id,
            TriggerRun.workspace_id == workspace_id,
        )
        count_res = await self.session.execute(count_stmt)
        total = count_res.scalar() or 0

        formatted = [self._format_run_response(r) for r in runs]
        return TriggerRunListResponse(runs=formatted, total=total)

    async def get_trigger_run(
        self,
        trigger_run_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> TriggerRunResponse:
        stmt = select(TriggerRun).where(
            TriggerRun.id == trigger_run_id,
            TriggerRun.workspace_id == workspace_id,
        )
        res = await self.session.execute(stmt)
        trig_run = res.scalar_one_or_none()
        if not trig_run:
            raise TriggerNotFoundError(f"Trigger run '{trigger_run_id}' not found.")
        return self._format_run_response(trig_run)

    async def _format_trigger_response(
        self,
        trigger: WorkflowTrigger,
        workflow_name: Optional[str] = None,
    ) -> WorkflowTriggerResponse:
        # Compute success / failure counts
        succ_stmt = select(func.count(TriggerRun.id)).where(
            TriggerRun.trigger_id == trigger.id,
            TriggerRun.status == "completed",
        )
        succ_res = await self.session.execute(succ_stmt)
        succ_cnt = succ_res.scalar() or 0

        fail_stmt = select(func.count(TriggerRun.id)).where(
            TriggerRun.trigger_id == trigger.id,
            TriggerRun.status == "failed",
        )
        fail_res = await self.session.execute(fail_stmt)
        fail_cnt = fail_res.scalar() or 0

        resp = WorkflowTriggerResponse.model_validate(trigger)
        resp.workflow_name = workflow_name
        resp.has_webhook_secret = bool(trigger.webhook_secret_hash)
        resp.success_count = succ_cnt
        resp.failure_count = fail_cnt
        return resp

    def _format_run_response(self, run: TriggerRun) -> TriggerRunResponse:
        dur = None
        if run.started_at and run.completed_at:
            dur = int((run.completed_at - run.started_at).total_seconds() * 1000)

        resp = TriggerRunResponse.model_validate(run)
        resp.duration_ms = dur
        return resp

    @staticmethod
    def _is_valid_uuid(val: Any) -> bool:
        try:
            uuid.UUID(str(val))
            return True
        except ValueError:
            return False
