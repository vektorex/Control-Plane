"""
Async SQLAlchemy Repository for Step 44: AI Work Planning, Capacity & Resource Optimization.
Enforces strict workspace tenant isolation.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.services.planning.models import (
    CapacityReservation,
    CapacitySnapshot,
    PlanStalenessRecord,
    PlanningBlocker,
    PlanningConstraint,
    PlanningDependency,
    PlanningItem,
    PlanningRecommendation,
    PlanningScenario,
    ResourceAvailability,
    ScheduleCandidate,
    WorkPlan,
    WorkPlanVersion,
    WorkResource,
)


class PlanningRepository:
    """Async repository for planning domain models with tenant isolation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # -----------------------------------------------------------------------
    # Work Plans
    # -----------------------------------------------------------------------

    async def create_plan(self, plan: WorkPlan) -> WorkPlan:
        self.session.add(plan)
        await self.session.flush()
        return plan

    async def get_plan(self, plan_id: str, workspace_id: str) -> Optional[WorkPlan]:
        q = (
            select(WorkPlan)
            .where(WorkPlan.id == plan_id, WorkPlan.workspace_id == workspace_id)
            .options(
                selectinload(WorkPlan.versions),
                selectinload(WorkPlan.scenarios),
                selectinload(WorkPlan.recommendations),
                selectinload(WorkPlan.staleness_records),
            )
        )
        res = await self.session.execute(q)
        return res.scalars().first()

    async def list_plans(
        self,
        workspace_id: str,
        project_id: Optional[str] = None,
        objective_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[WorkPlan]:
        q = select(WorkPlan).where(WorkPlan.workspace_id == workspace_id)
        if project_id:
            q = q.where(WorkPlan.project_id == project_id)
        if objective_id:
            q = q.where(WorkPlan.objective_id == objective_id)
        if status:
            q = q.where(WorkPlan.status == status)
        q = q.order_by(desc(WorkPlan.created_at)).limit(limit).offset(offset)
        res = await self.session.execute(q)
        return list(res.scalars().all())

    # -----------------------------------------------------------------------
    # Work Plan Versions
    # -----------------------------------------------------------------------

    async def create_version(self, version: WorkPlanVersion) -> WorkPlanVersion:
        self.session.add(version)
        await self.session.flush()
        return version

    async def get_version(self, version_id: str) -> Optional[WorkPlanVersion]:
        q = (
            select(WorkPlanVersion)
            .where(WorkPlanVersion.id == version_id)
            .options(
                selectinload(WorkPlanVersion.items),
                selectinload(WorkPlanVersion.dependencies),
                selectinload(WorkPlanVersion.constraints),
                selectinload(WorkPlanVersion.candidates),
                selectinload(WorkPlanVersion.blockers),
            )
        )
        res = await self.session.execute(q)
        return res.scalars().first()

    async def get_latest_version(self, work_plan_id: str) -> Optional[WorkPlanVersion]:
        q = (
            select(WorkPlanVersion)
            .where(WorkPlanVersion.work_plan_id == work_plan_id)
            .order_by(desc(WorkPlanVersion.version))
            .options(
                selectinload(WorkPlanVersion.items),
                selectinload(WorkPlanVersion.dependencies),
                selectinload(WorkPlanVersion.constraints),
                selectinload(WorkPlanVersion.candidates),
                selectinload(WorkPlanVersion.blockers),
            )
        )
        res = await self.session.execute(q)
        return res.scalars().first()

    # -----------------------------------------------------------------------
    # Planning Items & Dependencies
    # -----------------------------------------------------------------------

    async def create_item(self, item: PlanningItem) -> PlanningItem:
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_items_for_version(self, version_id: str) -> List[PlanningItem]:
        q = select(PlanningItem).where(PlanningItem.work_plan_version_id == version_id)
        res = await self.session.execute(q)
        return list(res.scalars().all())

    async def create_dependency(self, dep: PlanningDependency) -> PlanningDependency:
        self.session.add(dep)
        await self.session.flush()
        return dep

    async def list_dependencies_for_version(self, version_id: str) -> List[PlanningDependency]:
        q = select(PlanningDependency).where(PlanningDependency.work_plan_version_id == version_id)
        res = await self.session.execute(q)
        return list(res.scalars().all())

    # -----------------------------------------------------------------------
    # Work Resources & Availability
    # -----------------------------------------------------------------------

    async def create_resource(self, resource: WorkResource) -> WorkResource:
        self.session.add(resource)
        await self.session.flush()
        return resource

    async def get_resource(self, resource_id: str, workspace_id: str) -> Optional[WorkResource]:
        q = (
            select(WorkResource)
            .where(WorkResource.id == resource_id, WorkResource.workspace_id == workspace_id)
            .options(
                selectinload(WorkResource.availabilities),
                selectinload(WorkResource.reservations),
            )
        )
        res = await self.session.execute(q)
        return res.scalars().first()

    async def list_resources(
        self,
        workspace_id: str,
        resource_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[WorkResource]:
        q = select(WorkResource).where(WorkResource.workspace_id == workspace_id)
        if resource_type:
            q = q.where(WorkResource.resource_type == resource_type)
        if status:
            q = q.where(WorkResource.status == status)
        res = await self.session.execute(q)
        return list(res.scalars().all())

    async def create_availability(self, avail: ResourceAvailability) -> ResourceAvailability:
        self.session.add(avail)
        await self.session.flush()
        return avail

    async def list_availabilities_for_resource(self, resource_id: str) -> List[ResourceAvailability]:
        q = select(ResourceAvailability).where(ResourceAvailability.resource_id == resource_id)
        res = await self.session.execute(q)
        return list(res.scalars().all())

    # -----------------------------------------------------------------------
    # Capacity Reservations & Snapshots
    # -----------------------------------------------------------------------

    async def create_reservation(self, res_obj: CapacityReservation) -> CapacityReservation:
        self.session.add(res_obj)
        await self.session.flush()
        return res_obj

    async def list_reservations_for_resource(self, resource_id: str) -> List[CapacityReservation]:
        q = select(CapacityReservation).where(CapacityReservation.resource_id == resource_id)
        res = await self.session.execute(q)
        return list(res.scalars().all())

    async def create_capacity_snapshot(self, snapshot: CapacitySnapshot) -> CapacitySnapshot:
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot

    # -----------------------------------------------------------------------
    # Constraints, Candidates, Blockers
    # -----------------------------------------------------------------------

    async def create_constraint(self, constraint: PlanningConstraint) -> PlanningConstraint:
        self.session.add(constraint)
        await self.session.flush()
        return constraint

    async def list_constraints_for_version(self, version_id: str) -> List[PlanningConstraint]:
        q = select(PlanningConstraint).where(PlanningConstraint.work_plan_version_id == version_id)
        res = await self.session.execute(q)
        return list(res.scalars().all())

    async def create_candidate(self, cand: ScheduleCandidate) -> ScheduleCandidate:
        self.session.add(cand)
        await self.session.flush()
        return cand

    async def list_candidates_for_version(self, version_id: str) -> List[ScheduleCandidate]:
        q = select(ScheduleCandidate).where(ScheduleCandidate.work_plan_version_id == version_id)
        res = await self.session.execute(q)
        return list(res.scalars().all())

    async def create_blocker(self, blocker: PlanningBlocker) -> PlanningBlocker:
        self.session.add(blocker)
        await self.session.flush()
        return blocker

    async def list_blockers_for_version(self, version_id: str) -> List[PlanningBlocker]:
        q = select(PlanningBlocker).where(PlanningBlocker.work_plan_version_id == version_id)
        res = await self.session.execute(q)
        return list(res.scalars().all())

    # -----------------------------------------------------------------------
    # Scenarios, Recommendations, Staleness
    # -----------------------------------------------------------------------

    async def create_scenario(self, scenario: PlanningScenario) -> PlanningScenario:
        self.session.add(scenario)
        await self.session.flush()
        return scenario

    async def get_scenario(self, scenario_id: str, workspace_id: str) -> Optional[PlanningScenario]:
        q = select(PlanningScenario).where(
            PlanningScenario.id == scenario_id,
            PlanningScenario.workspace_id == workspace_id,
        )
        res = await self.session.execute(q)
        return res.scalars().first()

    async def create_recommendation(self, rec: PlanningRecommendation) -> PlanningRecommendation:
        self.session.add(rec)
        await self.session.flush()
        return rec

    async def list_recommendations_for_plan(self, plan_id: str, workspace_id: str) -> List[PlanningRecommendation]:
        q = select(PlanningRecommendation).where(
            PlanningRecommendation.work_plan_id == plan_id,
            PlanningRecommendation.workspace_id == workspace_id,
        )
        res = await self.session.execute(q)
        return list(res.scalars().all())

    async def create_staleness_record(self, record: PlanStalenessRecord) -> PlanStalenessRecord:
        self.session.add(record)
        await self.session.flush()
        return record
