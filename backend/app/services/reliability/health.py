"""
Bounded, lightweight health check service for Step 35: AI Reliability, Resilience & Chaos Engineering Layer.
Checks liveness, readiness, and dependency health without performing expensive AI calls.
"""
from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.reliability.exceptions import ComponentNotFoundError
from backend.app.services.reliability.models import DependencyHealth, ReliabilityComponent
from backend.app.services.reliability.schemas import (
    DependencyHealthCreate,
    ReliabilityComponentCreate,
    SystemHealthOverviewResponse,
)


class HealthCheckService:
    """Performs cheap, deterministic health checks and evaluates component health."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_or_get_component(
        self,
        component_type: str,
        component_name: str,
        organization_id: Optional[str] = None,
        version: Optional[str] = None,
    ) -> ReliabilityComponent:
        stmt = select(ReliabilityComponent).where(
            ReliabilityComponent.component_type == component_type,
            ReliabilityComponent.component_name == component_name,
        )
        if organization_id:
            stmt = stmt.where(ReliabilityComponent.organization_id == organization_id)

        res = await self.session.execute(stmt)
        comp = res.scalars().first()
        if not comp:
            comp = ReliabilityComponent(
                organization_id=organization_id,
                component_type=component_type,
                component_name=component_name,
                version=version or "1.0.0",
                status="active",
                health_status="healthy",
                metadata_payload={},
            )
            self.session.add(comp)
            await self.session.commit()
            await self.session.refresh(comp)
        return comp

    async def record_dependency_result(self, data: DependencyHealthCreate) -> DependencyHealth:
        """Records a lightweight dependency check result."""
        dep = DependencyHealth(
            component_id=data.component_id,
            check_type=data.check_type,
            status=data.status,
            latency_ms=data.latency_ms,
            error_type=data.error_type,
            metadata_payload=data.metadata,
        )
        self.session.add(dep)

        # Update parent component health status accordingly
        comp = await self.session.get(ReliabilityComponent, data.component_id)
        if comp:
            now = datetime.now(timezone.utc)
            comp.last_heartbeat_at = now
            if data.status == "healthy":
                comp.last_success_at = now
                comp.success_count += 1
                if comp.health_status == "critical":
                    comp.health_status = "warning"
                elif comp.health_status == "warning":
                    comp.health_status = "healthy"
            else:
                comp.last_failure_at = now
                comp.failure_count += 1
                comp.health_status = "critical" if data.status == "critical" else "warning"
                if comp.status == "active" and data.status == "critical":
                    comp.status = "degraded"

        await self.session.commit()
        await self.session.refresh(dep)
        return dep

    async def get_component(self, component_id: str) -> ReliabilityComponent:
        comp = await self.session.get(ReliabilityComponent, component_id)
        if not comp:
            raise ComponentNotFoundError(f"Component '{component_id}' not found.")
        return comp

    async def list_components(
        self,
        component_type: Optional[str] = None,
        health_status: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ReliabilityComponent]:
        stmt = select(ReliabilityComponent)
        if component_type:
            stmt = stmt.where(ReliabilityComponent.component_type == component_type)
        if health_status:
            stmt = stmt.where(ReliabilityComponent.health_status == health_status)
        if status:
            stmt = stmt.where(ReliabilityComponent.status == status)

        stmt = stmt.order_by(ReliabilityComponent.component_name).offset(offset).limit(limit)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def list_dependencies(
        self,
        component_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[DependencyHealth]:
        stmt = select(DependencyHealth)
        if component_id:
            stmt = stmt.where(DependencyHealth.component_id == component_id)
        if status:
            stmt = stmt.where(DependencyHealth.status == status)

        stmt = stmt.order_by(DependencyHealth.checked_at.desc()).limit(limit)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_system_health(self) -> Dict[str, Any]:
        """Returns aggregate factual health across all registered components."""
        comps = await self.list_components(limit=500)

        healthy = sum(1 for c in comps if c.health_status == "healthy")
        warning = sum(1 for c in comps if c.health_status == "warning")
        critical = sum(1 for c in comps if c.health_status == "critical")
        unknown = sum(1 for c in comps if c.health_status == "unknown")

        return {
            "overall_status": "critical" if critical > 0 else ("warning" if warning > 0 else "healthy"),
            "total_components": len(comps),
            "healthy": healthy,
            "warning": warning,
            "critical": critical,
            "unknown": unknown,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
