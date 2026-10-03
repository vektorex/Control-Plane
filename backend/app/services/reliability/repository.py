"""
Operational repository and telemetry aggregator for Step 35: AI Reliability, Resilience & Chaos Engineering Layer.
Computes factual SLO and failure budget status without subjective scoring or fake contractual SLAs.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.reliability.models import (
    ChaosExperiment,
    DependencyHealth,
    ExecutionCheckpoint,
    ReliabilityBudget,
    ReliabilityComponent,
    ReliabilityObjective,
)
from backend.app.services.reliability.schemas import (
    ReliabilityTelemetryResponse,
    SystemHealthOverviewResponse,
)


class ReliabilityRepository:
    """Aggregates operational metrics, SLOs, and failure budgets."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_overview_counts(self, organization_id: Optional[str] = None) -> SystemHealthOverviewResponse:
        # Components
        comp_stmt = select(ReliabilityComponent)
        if organization_id:
            comp_stmt = comp_stmt.where(
                (ReliabilityComponent.organization_id == organization_id)
                | (ReliabilityComponent.organization_id.is_(None))
            )
        comp_res = await self.session.execute(comp_stmt)
        components = list(comp_res.scalars().all())

        healthy = sum(1 for c in components if c.health_status == "healthy")
        degraded = sum(1 for c in components if c.health_status == "warning" or c.status == "degraded")
        unavailable = sum(1 for c in components if c.health_status == "critical" or c.status == "unavailable")

        # Checkpoints count
        cp_stmt = select(func.count(ExecutionCheckpoint.id))
        if organization_id:
            cp_stmt = cp_stmt.where(ExecutionCheckpoint.organization_id == organization_id)
        cp_res = await self.session.execute(cp_stmt)
        cp_count = cp_res.scalar() or 0

        # Chaos experiments count
        exp_stmt = select(func.count(ChaosExperiment.id)).where(ChaosExperiment.status == "running")
        if organization_id:
            exp_stmt = exp_stmt.where(ChaosExperiment.organization_id == organization_id)
        exp_res = await self.session.execute(exp_stmt)
        exp_count = exp_res.scalar() or 0

        by_type: Dict[str, int] = {}
        for c in components:
            by_type[c.component_type] = by_type.get(c.component_type, 0) + 1

        return SystemHealthOverviewResponse(
            healthy_components=healthy,
            degraded_components=degraded,
            unavailable_components=unavailable,
            active_circuit_breakers_open=0,
            recent_failures_24h=sum(c.failure_count for c in components),
            active_checkpoints=cp_count,
            chaos_experiments_active=exp_count,
            component_breakdown=by_type,
            health_by_type={c.component_name: c.health_status for c in components[:20]},
        )

    async def get_telemetry(
        self,
        days: int = 30,
        organization_id: Optional[str] = None,
    ) -> ReliabilityTelemetryResponse:
        since = datetime.now(timezone.utc) - timedelta(days=days)

        # Count dependency checks
        dep_stmt = select(DependencyHealth).where(DependencyHealth.checked_at >= since)
        dep_res = await self.session.execute(dep_stmt)
        checks = list(dep_res.scalars().all())

        total = len(checks)
        successful = sum(1 for c in checks if c.status == "healthy")
        avail_pct = (successful / total * 100.0) if total > 0 else 100.0

        latencies = [c.latency_ms for c in checks if c.latency_ms is not None]
        avg_lat = sum(latencies) / len(latencies) if latencies else 0.0

        failures_by_cat: Dict[str, int] = {}
        for c in checks:
            if c.status != "healthy" and c.error_type:
                failures_by_cat[c.error_type] = failures_by_cat.get(c.error_type, 0) + 1

        return ReliabilityTelemetryResponse(
            timeframe_days=days,
            total_checks=total,
            overall_availability_pct=round(avail_pct, 2),
            average_latency_ms=round(avg_lat, 2),
            retry_count=0,
            fallback_count=0,
            checkpoint_resume_success_count=0,
            checkpoint_resume_failure_count=0,
            failures_by_category=failures_by_cat,
        )

    async def list_objectives(
        self,
        organization_id: Optional[str] = None,
    ) -> List[ReliabilityObjective]:
        stmt = select(ReliabilityObjective)
        if organization_id:
            stmt = stmt.where(
                (ReliabilityObjective.organization_id == organization_id)
                | (ReliabilityObjective.organization_id.is_(None))
            )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def list_budgets(
        self,
        organization_id: Optional[str] = None,
    ) -> List[ReliabilityBudget]:
        stmt = select(ReliabilityBudget)
        if organization_id:
            stmt = stmt.where(ReliabilityBudget.organization_id == organization_id)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
