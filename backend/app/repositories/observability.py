import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, delete, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.db.models.observability import ExecutionTraceEvent, RunTelemetry, UsageRecord
from backend.app.db.models.task import Task
from backend.app.services.observability.metrics import calculate_average, calculate_percentile

from backend.app.services.observability.schemas import (
    AnalyticsEvaluationResponse,
    AnalyticsLatencyResponse,
    AnalyticsModelResponse,
    AnalyticsOverviewResponse,
    AnalyticsProviderResponse,
    AnalyticsUsageResponse,
    CostMetric,
    EvaluationMetric,
    LatencyMetric,
    LatencyStageBreakdown,
    ModelUsageStat,
    PeriodFilter,
    ProviderUsageStat,
    RunsMetric,
    TokensMetric,
    UsageDataPoint,
)


class ObservabilityRepository:
    """
    Repository for storing and querying RunTelemetry, ExecutionTraceEvents, UsageRecords,
    and computing workspace-isolated analytics aggregations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_run_telemetry(self, run_id: uuid.UUID, workspace_id: uuid.UUID) -> Optional[RunTelemetry]:
        """Fetch telemetry for a specific run enforcing workspace isolation."""
        stmt = select(RunTelemetry).where(
            and_(
                RunTelemetry.run_id == run_id,
                RunTelemetry.workspace_id == workspace_id,
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_run_trace_events(self, run_id: uuid.UUID, workspace_id: uuid.UUID) -> List[ExecutionTraceEvent]:
        """Fetch ordered execution trace events for a run enforcing workspace isolation."""
        stmt = (
            select(ExecutionTraceEvent)
            .where(
                and_(
                    ExecutionTraceEvent.run_id == run_id,
                    ExecutionTraceEvent.workspace_id == workspace_id,
                )
            )
            .order_by(ExecutionTraceEvent.sequence_number.asc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_run_usage_records(self, run_id: uuid.UUID, workspace_id: uuid.UUID) -> List[UsageRecord]:
        """Fetch granular usage records for a run enforcing workspace isolation."""
        stmt = (
            select(UsageRecord)
            .where(
                and_(
                    UsageRecord.run_id == run_id,
                    UsageRecord.workspace_id == workspace_id,
                )
            )
            .order_by(UsageRecord.created_at.asc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    def _build_telemetry_filters(self, workspace_id: uuid.UUID, filters: Dict[str, Any]):
        clauses = [RunTelemetry.workspace_id == workspace_id]

        if filters.get("project_id"):
            clauses.append(RunTelemetry.project_id == filters["project_id"])
        if filters.get("task_id"):
            clauses.append(RunTelemetry.task_id == filters["task_id"])
        if filters.get("model"):
            clauses.append(
                or_(
                    RunTelemetry.generation_model == filters["model"],
                    RunTelemetry.planner_model == filters["model"],
                )
            )
        if filters.get("provider"):
            clauses.append(RunTelemetry.provider == filters["provider"])
        if filters.get("status"):
            clauses.append(RunTelemetry.status == filters["status"])
        if filters.get("start_date"):
            clauses.append(RunTelemetry.created_at >= filters["start_date"])
        if filters.get("end_date"):
            clauses.append(RunTelemetry.created_at <= filters["end_date"])

        return and_(*clauses)

    async def get_overview_analytics(
        self,
        workspace_id: uuid.UUID,
        filters: Dict[str, Any],
    ) -> AnalyticsOverviewResponse:
        """Computes comprehensive high-level analytics for a workspace."""
        where_cond = self._build_telemetry_filters(workspace_id, filters)
        stmt = select(RunTelemetry).where(where_cond)
        res = await self.session.execute(stmt)
        records = list(res.scalars().all())

        total_runs = len(records)
        successful_runs = sum(1 for r in records if r.status == "completed")
        failed_runs = sum(1 for r in records if r.status == "failed")
        success_rate = round((successful_runs / total_runs) * 100.0, 2) if total_runs > 0 else 0.0

        in_tok = sum(r.input_tokens for r in records)
        out_tok = sum(r.output_tokens for r in records)
        total_tok = sum(r.total_tokens for r in records)

        costs = [r.estimated_cost for r in records if r.estimated_cost is not None]
        total_cost = round(sum(costs), 6) if costs else None

        durations = [r.duration_ms for r in records if r.duration_ms is not None and r.duration_ms > 0]
        avg_lat = calculate_average(durations)
        p50_lat = calculate_percentile(durations, 50.0)
        p95_lat = calculate_percentile(durations, 95.0)

        eval_passed = sum(1 for r in records if r.evaluation_status == "passed")
        eval_warning = sum(1 for r in records if r.evaluation_status == "warning")
        eval_failed = sum(1 for r in records if r.evaluation_status == "failed")
        revisions = sum(r.revision_attempts for r in records)
        total_evaluated = eval_passed + eval_warning + eval_failed

        return AnalyticsOverviewResponse(
            period=PeriodFilter(
                start=str(filters.get("start_date")) if filters.get("start_date") else None,
                end=str(filters.get("end_date")) if filters.get("end_date") else None,
            ),
            runs=RunsMetric(
                total=total_runs,
                successful=successful_runs,
                failed=failed_runs,
                success_rate=success_rate,
            ),
            tokens=TokensMetric(
                input=in_tok,
                output=out_tok,
                total=total_tok,
            ),
            cost=CostMetric(
                estimated=total_cost,
                currency="USD",
                source="configured_pricing",
            ),
            latency=LatencyMetric(
                average_ms=avg_lat,
                p50_ms=p50_lat,
                p95_ms=p95_lat,
            ),
            evaluation=EvaluationMetric(
                passed=eval_passed,
                warning=eval_warning,
                failed=eval_failed,
                total_evaluated=total_evaluated,
                revision_attempts=revisions,
            ),
        )

    async def get_usage_analytics(
        self,
        workspace_id: uuid.UUID,
        filters: Dict[str, Any],
    ) -> AnalyticsUsageResponse:
        """Computes daily usage and cost aggregation points for time series charts."""
        where_cond = self._build_telemetry_filters(workspace_id, filters)
        stmt = select(RunTelemetry).where(where_cond).order_by(RunTelemetry.created_at.asc())
        res = await self.session.execute(stmt)
        records = list(res.scalars().all())

        # Group by YYYY-MM-DD
        grouped: Dict[str, Dict[str, Any]] = {}
        total_tokens = 0
        total_cost = 0.0
        has_cost = False

        for r in records:
            day_str = r.created_at.strftime("%Y-%m-%d") if r.created_at else "Unknown"
            if day_str not in grouped:
                grouped[day_str] = {
                    "date": day_str,
                    "runs": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "costs": [],
                }
            g = grouped[day_str]
            g["runs"] += 1
            g["input_tokens"] += r.input_tokens
            g["output_tokens"] += r.output_tokens
            g["total_tokens"] += r.total_tokens
            total_tokens += r.total_tokens
            if r.estimated_cost is not None:
                g["costs"].append(r.estimated_cost)
                total_cost += r.estimated_cost
                has_cost = True

        points: List[UsageDataPoint] = []
        for day_str, data in grouped.items():
            day_cost = round(sum(data["costs"]), 6) if data["costs"] else None
            points.append(
                UsageDataPoint(
                    date=day_str,
                    runs=data["runs"],
                    input_tokens=data["input_tokens"],
                    output_tokens=data["output_tokens"],
                    total_tokens=data["total_tokens"],
                    estimated_cost=day_cost,
                )
            )

        return AnalyticsUsageResponse(
            period=PeriodFilter(
                start=str(filters.get("start_date")) if filters.get("start_date") else None,
                end=str(filters.get("end_date")) if filters.get("end_date") else None,
            ),
            points=points,
            total_tokens=total_tokens,
            total_cost=round(total_cost, 6) if has_cost else None,
        )

    async def get_model_analytics(
        self,
        workspace_id: uuid.UUID,
        filters: Dict[str, Any],
    ) -> AnalyticsModelResponse:
        """Computes usage and performance metrics grouped by model."""
        where_cond = self._build_telemetry_filters(workspace_id, filters)
        stmt = select(RunTelemetry).where(where_cond)
        res = await self.session.execute(stmt)
        records = list(res.scalars().all())

        grouped: Dict[str, Dict[str, Any]] = {}
        for r in records:
            m_id = r.generation_model or "unknown"
            prov = r.provider or "unknown"
            key = f"{prov}:{m_id}"

            if key not in grouped:
                from backend.app.services.models.registry import default_model_registry
                m_def = default_model_registry.get_model(m_id, provider=prov)

                grouped[key] = {
                    "model": m_id,
                    "provider": prov,
                    "display_name": m_def.display_name if m_def else m_id,
                    "capabilities": [str(c) for c in m_def.capabilities] if m_def else [],
                    "runs": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "costs": [],
                    "durations": [],
                    "failures": 0,
                }
            g = grouped[key]
            g["runs"] += 1
            g["input_tokens"] += r.input_tokens
            g["output_tokens"] += r.output_tokens
            g["total_tokens"] += r.total_tokens
            if r.status == "failed":
                g["failures"] += 1
            if r.estimated_cost is not None:
                g["costs"].append(r.estimated_cost)
            if r.duration_ms and r.duration_ms > 0:
                g["durations"].append(r.duration_ms)

        stats: List[ModelUsageStat] = []
        for key, data in grouped.items():
            durations = data["durations"]
            costs = data["costs"]
            stats.append(
                ModelUsageStat(
                    model=data["model"],
                    provider=data["provider"],
                    display_name=data["display_name"],
                    runs=data["runs"],
                    input_tokens=data["input_tokens"],
                    output_tokens=data["output_tokens"],
                    total_tokens=data["total_tokens"],
                    estimated_cost=round(sum(costs), 6) if costs else None,
                    avg_latency_ms=calculate_average(durations),
                    p50_latency_ms=calculate_percentile(durations, 50.0),
                    p95_latency_ms=calculate_percentile(durations, 95.0),
                    failures=data["failures"],
                    capabilities=data["capabilities"],
                )
            )

        # Sort by total_tokens desc
        stats.sort(key=lambda s: s.total_tokens, reverse=True)
        return AnalyticsModelResponse(models=stats)

    async def get_provider_analytics(
        self,
        workspace_id: uuid.UUID,
        filters: Dict[str, Any],
    ) -> AnalyticsProviderResponse:
        """Computes usage and failure metrics grouped by provider."""
        where_cond = self._build_telemetry_filters(workspace_id, filters)
        stmt = select(RunTelemetry).where(where_cond)
        res = await self.session.execute(stmt)
        records = list(res.scalars().all())

        grouped: Dict[str, Dict[str, Any]] = {}
        for r in records:
            prov = r.provider or "unknown"
            if prov not in grouped:
                grouped[prov] = {
                    "provider": prov,
                    "runs": 0,
                    "total_tokens": 0,
                    "costs": [],
                    "failures": 0,
                }
            g = grouped[prov]
            g["runs"] += 1
            g["total_tokens"] += r.total_tokens
            if r.status == "failed":
                g["failures"] += 1
            if r.estimated_cost is not None:
                g["costs"].append(r.estimated_cost)

        stats: List[ProviderUsageStat] = []
        for prov, data in grouped.items():
            costs = data["costs"]
            stats.append(
                ProviderUsageStat(
                    provider=prov,
                    runs=data["runs"],
                    total_tokens=data["total_tokens"],
                    estimated_cost=round(sum(costs), 6) if costs else None,
                    failures=data["failures"],
                )
            )

        stats.sort(key=lambda s: s.total_tokens, reverse=True)
        return AnalyticsProviderResponse(providers=stats)

    async def get_latency_analytics(
        self,
        workspace_id: uuid.UUID,
        filters: Dict[str, Any],
    ) -> AnalyticsLatencyResponse:
        """Computes overall and stage-by-stage latency distributions."""
        where_cond = self._build_telemetry_filters(workspace_id, filters)
        stmt = select(RunTelemetry).where(where_cond)
        res = await self.session.execute(stmt)
        records = list(res.scalars().all())

        overall_durations = [r.duration_ms for r in records if r.duration_ms and r.duration_ms > 0]
        planner_durations = [r.planner_duration_ms for r in records if r.planner_duration_ms > 0]
        retrieval_durations = [r.retrieval_duration_ms for r in records if r.retrieval_duration_ms > 0]
        tool_durations = [r.tool_duration_ms for r in records if r.tool_duration_ms > 0]
        gen_durations = [r.generation_duration_ms for r in records if r.generation_duration_ms > 0]
        eval_durations = [r.evaluation_duration_ms for r in records if r.evaluation_duration_ms > 0]

        stage_names = [
            ("Planning", planner_durations),
            ("Retrieval", retrieval_durations),
            ("Tools", tool_durations),
            ("Generation", gen_durations),
            ("Evaluation", eval_durations),
        ]

        stages: List[LatencyStageBreakdown] = []
        for name, durs in stage_names:
            stages.append(
                LatencyStageBreakdown(
                    stage=name,
                    avg_duration_ms=calculate_average(durs) or 0.0,
                    p50_duration_ms=calculate_percentile(durs, 50.0) or 0.0,
                    p95_duration_ms=calculate_percentile(durs, 95.0) or 0.0,
                )
            )

        return AnalyticsLatencyResponse(
            overall=LatencyMetric(
                average_ms=calculate_average(overall_durations),
                p50_ms=calculate_percentile(overall_durations, 50.0),
                p95_ms=calculate_percentile(overall_durations, 95.0),
            ),
            stages=stages,
        )

    async def get_evaluation_analytics(
        self,
        workspace_id: uuid.UUID,
        filters: Dict[str, Any],
    ) -> AnalyticsEvaluationResponse:
        """Computes verification and revision analytics for a workspace."""
        where_cond = self._build_telemetry_filters(workspace_id, filters)
        stmt = select(RunTelemetry).where(where_cond)
        res = await self.session.execute(stmt)
        records = list(res.scalars().all())

        passed = sum(1 for r in records if r.evaluation_status == "passed")
        warning = sum(1 for r in records if r.evaluation_status == "warning")
        failed = sum(1 for r in records if r.evaluation_status == "failed")
        revisions = sum(r.revision_attempts for r in records)
        total = passed + warning + failed
        pass_rate = round((passed / total) * 100.0, 2) if total > 0 else 0.0

        return AnalyticsEvaluationResponse(
            passed=passed,
            warning=warning,
            failed=failed,
            total=total,
            pass_rate=pass_rate,
            revision_attempts=revisions,
        )

    async def cleanup_old_data(
        self,
        workspace_id: uuid.UUID,
        retention_days: int = 30,
    ) -> Dict[str, int]:
        """
        Deletes trace events, usage records, and telemetry records older than retention_days.
        CRITICAL: Never deletes Tasks, Runs, Documents, or Evaluation records.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

        # 1. Delete trace events
        del_traces = delete(ExecutionTraceEvent).where(
            and_(
                ExecutionTraceEvent.workspace_id == workspace_id,
                ExecutionTraceEvent.created_at < cutoff,
            )
        )
        res_traces = await self.session.execute(del_traces)
        deleted_traces = res_traces.rowcount or 0

        # 2. Delete usage records
        del_usage = delete(UsageRecord).where(
            and_(
                UsageRecord.workspace_id == workspace_id,
                UsageRecord.created_at < cutoff,
            )
        )
        res_usage = await self.session.execute(del_usage)
        deleted_usage = res_usage.rowcount or 0

        # 3. Delete telemetry records
        del_telem = delete(RunTelemetry).where(
            and_(
                RunTelemetry.workspace_id == workspace_id,
                RunTelemetry.created_at < cutoff,
            )
        )
        res_telem = await self.session.execute(del_telem)
        deleted_telem = res_telem.rowcount or 0

        await self.session.flush()

        logger.info(
            f"[ObservabilityRepository] Cleaned up workspace {workspace_id} records older than {retention_days}d: "
            f"{deleted_traces} traces, {deleted_usage} usage records, {deleted_telem} telemetry records."
        )

        return {
            "deleted_trace_events": deleted_traces,
            "deleted_usage_records": deleted_usage,
            "deleted_telemetry_records": deleted_telem,
        }
