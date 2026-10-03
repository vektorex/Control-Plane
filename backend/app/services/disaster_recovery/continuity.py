"""
Business continuity planning service for Step 36: Disaster Recovery.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.services.disaster_recovery.models import ContinuityPlan
from backend.app.services.disaster_recovery.dependencies import resolve_recovery_service_order


class ContinuityService:
    """
    Manages organization continuity plans, critical service definitions,
    and documented recovery ordering.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_plans(self, organization_id: str) -> List[ContinuityPlan]:
        """List active continuity plans for organization."""
        res = await self.session.execute(
            select(ContinuityPlan).where(ContinuityPlan.organization_id == organization_id)
        )
        return list(res.scalars().all())

    async def get_plan(self, plan_id: str, organization_id: str) -> Optional[ContinuityPlan]:
        """Fetch single continuity plan."""
        res = await self.session.execute(
            select(ContinuityPlan).where(
                ContinuityPlan.id == plan_id,
                ContinuityPlan.organization_id == organization_id,
            )
        )
        return res.scalar_one_or_none()

    async def create_plan(
        self,
        organization_id: str,
        name: str,
        owner_id: str,
        description: Optional[str] = None,
        critical_services: Optional[List[str]] = None,
        dependencies: Optional[Dict[str, Any]] = None,
        fallback_modes: Optional[Dict[str, Any]] = None,
        communication_plan: Optional[Dict[str, Any]] = None,
        recovery_order: Optional[List[str]] = None,
    ) -> ContinuityPlan:
        """Create a new business continuity plan with automated dependency ordering."""
        services = critical_services or [
            "database", "authentication", "governance", "security",
            "ai_gateway", "jobs", "events", "workflows", "notifications"
        ]
        computed_order = recovery_order or resolve_recovery_service_order(services)

        plan = ContinuityPlan(
            organization_id=organization_id,
            name=name,
            description=description,
            critical_services=services,
            dependencies=dependencies or {},
            fallback_modes=fallback_modes or {},
            communication_plan=communication_plan or {},
            recovery_order=computed_order,
            owner_id=owner_id,
            enabled=True,
        )
        self.session.add(plan)
        await self.session.commit()
        return plan

    async def update_plan(
        self,
        plan_id: str,
        organization_id: str,
        updates: Dict[str, Any],
    ) -> Optional[ContinuityPlan]:
        """Update existing continuity plan."""
        plan = await self.get_plan(plan_id, organization_id)
        if not plan:
            return None

        for k, v in updates.items():
            if hasattr(plan, k) and v is not None:
                setattr(plan, k, v)

        if "critical_services" in updates and "recovery_order" not in updates:
            plan.recovery_order = resolve_recovery_service_order(plan.critical_services)

        await self.session.commit()
        return plan
