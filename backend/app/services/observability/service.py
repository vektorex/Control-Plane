import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.db.models.observability import ExecutionTraceEvent, RunTelemetry, UsageRecord
from backend.app.repositories.observability import ObservabilityRepository
from backend.app.services.observability.cost import default_cost_calculator
from backend.app.services.observability.errors import extract_error_code, sanitize_error_message
from backend.app.services.observability.sanitizer import sanitize_metadata
from backend.app.services.observability.schemas import (
    AnalyticsEvaluationResponse,
    AnalyticsLatencyResponse,
    AnalyticsModelResponse,
    AnalyticsOverviewResponse,
    AnalyticsProviderResponse,
    AnalyticsUsageResponse,
    ExecutionTraceEventResponse,
    ObservabilityCleanupResponse,
    RunTelemetryResponse,
    UsageRecordResponse,
)


class ObservabilityService:
    """
    Central service for execution tracing, usage tracking, token cost calculations,
    telemetry persistence, and workspace-isolated analytics aggregation.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ObservabilityRepository(session)

    async def record_run_telemetry(
        self,
        run_id: uuid.UUID,
        workspace_id: uuid.UUID,
        task_id: uuid.UUID,
        started_at: datetime,
        status: str,
        project_id: Optional[uuid.UUID] = None,
        completed_at: Optional[datetime] = None,
        duration_ms: Optional[int] = None,
        provider: Optional[str] = None,
        planner_model: Optional[str] = None,
        generation_model: Optional[str] = None,
        evaluator_model: Optional[str] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int = 0,
        estimated_cost: Optional[float] = None,
        retrieval_calls: int = 0,
        retrieval_results: int = 0,
        tool_calls: int = 0,
        tools_used: Optional[List[str]] = None,
        execution_steps: int = 0,
        planner_duration_ms: int = 0,
        retrieval_duration_ms: int = 0,
        tool_duration_ms: int = 0,
        generation_duration_ms: int = 0,
        evaluation_duration_ms: int = 0,
        revision_attempts: int = 0,
        evaluation_status: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[RunTelemetry]:
        """
        Records or updates a consolidated RunTelemetry entity.
        Fail-safe: catches any DB error so task execution is never blocked.
        """
        try:
            safe_err = sanitize_error_message(error_message)

            # Recalculate cost if not provided but tokens exist
            if estimated_cost is None and generation_model:
                estimated_cost = default_cost_calculator.calculate_generation_cost(
                    model_id=generation_model,
                    provider=provider,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )

            telemetry = RunTelemetry(
                id=uuid.uuid4(),
                run_id=run_id,
                workspace_id=workspace_id,
                task_id=task_id,
                project_id=project_id,
                started_at=started_at,
                completed_at=completed_at or datetime.now(timezone.utc),
                duration_ms=duration_ms,
                status=status,
                provider=provider,
                planner_model=planner_model,
                generation_model=generation_model,
                evaluator_model=evaluator_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens or (input_tokens + output_tokens),
                estimated_cost=estimated_cost,
                retrieval_calls=retrieval_calls,
                retrieval_results=retrieval_results,
                tool_calls=tool_calls,
                tools_used=tools_used,
                execution_steps=execution_steps,
                planner_duration_ms=planner_duration_ms,
                retrieval_duration_ms=retrieval_duration_ms,
                tool_duration_ms=tool_duration_ms,
                generation_duration_ms=generation_duration_ms,
                evaluation_duration_ms=evaluation_duration_ms,
                revision_attempts=revision_attempts,
                evaluation_status=evaluation_status,
                error_code=error_code,
                error_message_safe=safe_err,
            )
            self.session.add(telemetry)
            await self.session.flush()
            return telemetry
        except Exception as exc:
            logger.warning(f"[ObservabilityService] Failed to record run telemetry: {exc}")
            return None

    async def record_usage(
        self,
        workspace_id: uuid.UUID,
        run_id: uuid.UUID,
        provider: str,
        model: str,
        operation: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cached_input_tokens: int = 0,
        usage_source: str = "provider",
        estimated_cost: Optional[float] = None,
    ) -> Optional[UsageRecord]:
        """
        Records a granular token usage entry for a specific operation (planning, generation, evaluation, revision).
        """
        try:
            total_tokens = input_tokens + output_tokens
            if estimated_cost is None:
                estimated_cost = default_cost_calculator.calculate_generation_cost(
                    model_id=model,
                    provider=provider,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cached_input_tokens=cached_input_tokens,
                )

            record = UsageRecord(
                id=uuid.uuid4(),
                workspace_id=workspace_id,
                run_id=run_id,
                provider=provider,
                model=model,
                operation=operation,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                cached_input_tokens=cached_input_tokens,
                estimated_cost=estimated_cost,
                usage_source=usage_source,
            )
            self.session.add(record)
            await self.session.flush()
            return record
        except Exception as exc:
            logger.warning(f"[ObservabilityService] Failed to record usage record: {exc}")
            return None

    async def get_run_telemetry(self, run_id: uuid.UUID, workspace_id: uuid.UUID) -> Optional[RunTelemetryResponse]:
        """Fetches telemetry for a run verifying workspace ownership."""
        t = await self.repo.get_run_telemetry(run_id, workspace_id)
        if not t:
            return None
        return RunTelemetryResponse.model_validate(t)

    async def get_run_trace_events(self, run_id: uuid.UUID, workspace_id: uuid.UUID) -> List[ExecutionTraceEventResponse]:
        """Fetches sanitized trace events for a run."""
        events = await self.repo.get_run_trace_events(run_id, workspace_id)
        return [ExecutionTraceEventResponse.model_validate(e) for e in events]

    async def get_run_usage(self, run_id: uuid.UUID, workspace_id: uuid.UUID) -> List[UsageRecordResponse]:
        """Fetches usage records for a run."""
        records = await self.repo.get_run_usage_records(run_id, workspace_id)
        return [UsageRecordResponse.model_validate(r) for r in records]

    async def get_overview_analytics(
        self,
        workspace_id: uuid.UUID,
        filters: Dict[str, Any],
    ) -> AnalyticsOverviewResponse:
        return await self.repo.get_overview_analytics(workspace_id, filters)

    async def get_usage_analytics(
        self,
        workspace_id: uuid.UUID,
        filters: Dict[str, Any],
    ) -> AnalyticsUsageResponse:
        return await self.repo.get_usage_analytics(workspace_id, filters)

    async def get_models_analytics(
        self,
        workspace_id: uuid.UUID,
        filters: Dict[str, Any],
    ) -> AnalyticsModelResponse:
        return await self.repo.get_model_analytics(workspace_id, filters)

    async def get_providers_analytics(
        self,
        workspace_id: uuid.UUID,
        filters: Dict[str, Any],
    ) -> AnalyticsProviderResponse:
        return await self.repo.get_provider_analytics(workspace_id, filters)

    async def get_latency_analytics(
        self,
        workspace_id: uuid.UUID,
        filters: Dict[str, Any],
    ) -> AnalyticsLatencyResponse:
        return await self.repo.get_latency_analytics(workspace_id, filters)

    async def get_evaluations_analytics(
        self,
        workspace_id: uuid.UUID,
        filters: Dict[str, Any],
    ) -> AnalyticsEvaluationResponse:
        return await self.repo.get_evaluation_analytics(workspace_id, filters)

    async def cleanup_retention(
        self,
        workspace_id: uuid.UUID,
        retention_days: Optional[int] = None,
    ) -> ObservabilityCleanupResponse:
        """Cleans up old trace events, usage records, and telemetry records for a workspace."""
        days = retention_days if retention_days is not None else settings.OBSERVABILITY_RETENTION_DAYS
        counts = await self.repo.cleanup_old_data(workspace_id, retention_days=days)
        return ObservabilityCleanupResponse(
            workspace_id=workspace_id,
            retention_days=days,
            deleted_trace_events=counts.get("deleted_trace_events", 0),
            deleted_usage_records=counts.get("deleted_usage_records", 0),
            deleted_telemetry_records=counts.get("deleted_telemetry_records", 0),
            message=f"Cleaned up records older than {days} days for workspace.",
        )
