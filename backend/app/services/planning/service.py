"""
Master Planning Service Orchestrator for Step 44:
AI Work Planning, Capacity & Resource Optimization Layer.
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.planning.capacity import CapacityManager
from backend.app.services.planning.errors import (
    PlanNotFoundError,
    PlanStaleError,
    PlanVersionNotFoundError,
    ResourceNotFoundError,
)
from backend.app.services.planning.events import PlanningEventPublisher
from backend.app.services.planning.lifecycle import PlanLifecycleManager
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
from backend.app.services.planning.planner import HybridPlanningEngine
from backend.app.services.planning.policies import PlanningPolicyEngine
from backend.app.services.planning.repository import PlanningRepository
from backend.app.services.planning.schemas import (
    CapacityReservationCreate,
    PlanGenerationRequest,
    PlanGenerationResult,
    PlanValidationResult,
    PlanningConstraintCreate,
    PlanningDependencyCreate,
    PlanningItemCreate,
    PlanningScenarioCreate,
    ResourceAvailabilityCreate,
    WorkPlanCreate,
    WorkPlanUpdate,
    WorkResourceCreate,
)
from backend.app.services.planning.scenarios import ScenarioEngine
from backend.app.services.planning.validators import PlanValidator


class PlanningService:
    """Master service for work planning, capacity evaluation, and resource optimization."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PlanningRepository(session)
        self.events = PlanningEventPublisher(session)

    # -----------------------------------------------------------------------
    # Work Plans
    # -----------------------------------------------------------------------

    async def create_plan(
        self,
        workspace_id: str,
        user_id: str,
        data: WorkPlanCreate,
    ) -> WorkPlan:
        PlanningPolicyEngine.validate_no_subjective_rankings(data.description)
        plan = WorkPlan(
            workspace_id=workspace_id,
            project_id=data.project_id,
            objective_id=data.objective_id,
            name=data.name,
            description=data.description,
            status="draft",
            planning_mode=data.planning_mode or "assisted",
            planning_horizon_start=data.planning_horizon_start or datetime.now(timezone.utc),
            planning_horizon_end=data.planning_horizon_end,
            created_by=user_id,
        )
        created = await self.repo.create_plan(plan)

        # Create initial Version 1
        initial_version = WorkPlanVersion(
            work_plan_id=created.id,
            version=1,
            created_by=user_id,
        )
        await self.repo.create_version(initial_version)
        await self.session.commit()

        await self.events.emit_plan_event(
            event_type="work_plan.created",
            workspace_id=workspace_id,
            plan_id=created.id,
            payload={"name": created.name, "status": created.status},
            project_id=created.project_id,
            actor_id=user_id,
        )
        return created

    async def get_plan(self, plan_id: str, workspace_id: str) -> WorkPlan:
        plan = await self.repo.get_plan(plan_id, workspace_id)
        if not plan:
            raise PlanNotFoundError(plan_id)
        return plan

    async def list_plans(
        self,
        workspace_id: str,
        project_id: Optional[str] = None,
        objective_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[WorkPlan]:
        return await self.repo.list_plans(workspace_id, project_id, objective_id, status, limit, offset)

    async def update_plan(
        self,
        plan_id: str,
        workspace_id: str,
        data: WorkPlanUpdate,
    ) -> WorkPlan:
        plan = await self.get_plan(plan_id, workspace_id)
        if data.name is not None:
            plan.name = data.name
        if data.description is not None:
            PlanningPolicyEngine.validate_no_subjective_rankings(data.description)
            plan.description = data.description
        if data.planning_mode is not None:
            plan.planning_mode = data.planning_mode
        if data.planning_horizon_start is not None:
            plan.planning_horizon_start = data.planning_horizon_start
        if data.planning_horizon_end is not None:
            plan.planning_horizon_end = data.planning_horizon_end
        if data.status is not None:
            PlanLifecycleManager.validate_transition(plan.status, data.status)
            plan.status = data.status

        plan.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        return plan

    # -----------------------------------------------------------------------
    # Planning Items & Dependencies
    # -----------------------------------------------------------------------

    async def add_item(
        self,
        plan_id: str,
        workspace_id: str,
        data: PlanningItemCreate,
    ) -> PlanningItem:
        plan = await self.get_plan(plan_id, workspace_id)
        latest_ver = await self.repo.get_latest_version(plan.id)
        if not latest_ver:
            raise PlanVersionNotFoundError(plan.id)

        PlanLifecycleManager.enforce_version_immutability(latest_ver)
        PlanningPolicyEngine.validate_no_subjective_rankings(data.description)

        item = PlanningItem(
            work_plan_version_id=latest_ver.id,
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            name=data.name,
            description=data.description,
            priority=data.priority,
            estimated_duration=data.estimated_duration,
            estimated_cost=data.estimated_cost,
            required_capabilities=data.required_capabilities,
            status=data.status or "planned",
            planned_start=data.planned_start,
            planned_end=data.planned_end,
        )
        created = await self.repo.create_item(item)
        await self.session.commit()
        return created

    async def add_dependency(
        self,
        plan_id: str,
        workspace_id: str,
        data: PlanningDependencyCreate,
    ) -> PlanningDependency:
        plan = await self.get_plan(plan_id, workspace_id)
        latest_ver = await self.repo.get_latest_version(plan.id)
        if not latest_ver:
            raise PlanVersionNotFoundError(plan.id)

        PlanLifecycleManager.enforce_version_immutability(latest_ver)

        dep = PlanningDependency(
            work_plan_version_id=latest_ver.id,
            predecessor_item_id=data.predecessor_item_id,
            successor_item_id=data.successor_item_id,
            dependency_type=data.dependency_type,
            lag=data.lag,
        )
        created = await self.repo.create_dependency(dep)
        await self.session.commit()
        return created

    # -----------------------------------------------------------------------
    # Work Resources & Availability
    # -----------------------------------------------------------------------

    async def register_resource(
        self,
        workspace_id: str,
        data: WorkResourceCreate,
    ) -> WorkResource:
        PlanningPolicyEngine.validate_no_subjective_rankings(data.description)
        res = WorkResource(
            workspace_id=workspace_id,
            project_id=data.project_id,
            resource_type=data.resource_type,
            resource_ref=data.resource_ref,
            name=data.name,
            description=data.description,
            status=data.status,
            capabilities=data.capabilities,
            availability_policy=data.availability_policy,
        )
        created = await self.repo.create_resource(res)
        await self.session.commit()
        return created

    async def get_resource(self, resource_id: str, workspace_id: str) -> WorkResource:
        res = await self.repo.get_resource(resource_id, workspace_id)
        if not res:
            raise ResourceNotFoundError(resource_id)
        return res

    async def list_resources(
        self,
        workspace_id: str,
        resource_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[WorkResource]:
        return await self.repo.list_resources(workspace_id, resource_type, status)

    async def add_availability(
        self,
        resource_id: str,
        workspace_id: str,
        data: ResourceAvailabilityCreate,
    ) -> ResourceAvailability:
        res = await self.get_resource(resource_id, workspace_id)
        PlanningPolicyEngine.validate_no_fabricated_capacity(data.source, data.capacity_units)

        avail = ResourceAvailability(
            resource_id=res.id,
            start_at=data.start_at,
            end_at=data.end_at,
            capacity_units=data.capacity_units,
            reserved_units=data.reserved_units,
            source=data.source,
        )
        created = await self.repo.create_availability(avail)
        await self.session.commit()
        return created

    async def get_resource_capacity(
        self,
        resource_id: str,
        workspace_id: str,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        res = await self.get_resource(resource_id, workspace_id)
        start = window_start or datetime.now(timezone.utc)
        end = window_end or (start + timedelta(days=7))

        avails = await self.repo.list_availabilities_for_resource(res.id)
        reserves = await self.repo.list_reservations_for_resource(res.id)

        return CapacityManager.calculate_resource_capacity(
            resource=res,
            availabilities=avails,
            reservations=reserves,
            window_start=start,
            window_end=end,
        )

    # -----------------------------------------------------------------------
    # Capacity Reservations
    # -----------------------------------------------------------------------

    async def create_reservation(
        self,
        workspace_id: str,
        user_id: str,
        data: CapacityReservationCreate,
    ) -> CapacityReservation:
        res = await self.get_resource(data.resource_id, workspace_id)
        cap = await self.get_resource_capacity(res.id, workspace_id, data.start_at, data.end_at)

        CapacityManager.evaluate_reservation_request(
            resource_id=res.id,
            available_units=cap["available_units"],
            current_reserved=cap["reserved_units"],
            requested_units=data.units,
            is_authorized=True,
        )

        reservation = CapacityReservation(
            resource_id=res.id,
            planning_item_id=data.planning_item_id,
            start_at=data.start_at,
            end_at=data.end_at,
            units=data.units,
            status="reserved",
            created_by=user_id,
        )
        created = await self.repo.create_reservation(reservation)
        await self.session.commit()

        await self.events.emit_capacity_event(
            event_type="capacity.reservation_created",
            workspace_id=workspace_id,
            resource_id=res.id,
            payload={"reservation_id": created.id, "units": created.units},
            actor_id=user_id,
        )
        return created

    # -----------------------------------------------------------------------
    # Planning Generation, Validation & Lifecycle
    # -----------------------------------------------------------------------

    async def generate_plan(
        self,
        plan_id: str,
        workspace_id: str,
        req: PlanGenerationRequest,
    ) -> Dict[str, Any]:
        plan = await self.get_plan(plan_id, workspace_id)
        latest_ver = await self.repo.get_latest_version(plan.id)
        if not latest_ver:
            raise PlanVersionNotFoundError(plan.id)

        items = await self.repo.list_items_for_version(latest_ver.id)
        deps = await self.repo.list_dependencies_for_version(latest_ver.id)
        resources = await self.repo.list_resources(workspace_id)
        constraints = await self.repo.list_constraints_for_version(latest_ver.id)

        pipeline_result = await HybridPlanningEngine.execute_planning_pipeline(
            plan=plan,
            items=items,
            dependencies=deps,
            resources=resources,
            constraints=constraints,
            mode=req.planning_mode or plan.planning_mode,
            preferences=req.preferences,
        )

        # Persist candidate schedules
        saved_candidates = []
        for cand in pipeline_result["candidates"]:
            cand_obj = ScheduleCandidate(
                work_plan_version_id=latest_ver.id,
                name=cand["name"],
                schedule=cand["schedule"],
                assumptions=cand["assumptions"],
                constraint_results=cand["constraint_results"],
                resource_allocations=cand["resource_allocations"],
                estimated_duration=cand["estimated_duration"],
                estimated_cost=cand["estimated_cost"],
            )
            saved = await self.repo.create_candidate(cand_obj)
            saved_candidates.append(saved)

        # Persist recommendations
        for rec in pipeline_result["recommendations"]:
            rec_obj = PlanningRecommendation(
                workspace_id=workspace_id,
                work_plan_id=plan.id,
                recommendation_type=rec["recommendation_type"],
                description=rec["description"],
                reason=rec["reason"],
                evidence_ids=rec.get("evidence_ids", []),
                affected_resources=rec.get("affected_resources", []),
                affected_items=rec.get("affected_items", []),
                risk=rec.get("risk"),
                assumptions=rec.get("assumptions", []),
            )
            await self.repo.create_recommendation(rec_obj)

        plan.status = "proposed"
        await self.session.commit()

        await self.events.emit_plan_event(
            event_type="work_plan.generated",
            workspace_id=workspace_id,
            plan_id=plan.id,
            payload={"candidates_count": len(saved_candidates)},
        )

        return {
            "work_plan_id": plan.id,
            "version": latest_ver.version,
            "items_count": len(items),
            "dependencies_count": len(deps),
            "candidates_count": len(saved_candidates),
            "blockers_count": 0,
            "recommendations_count": len(pipeline_result["recommendations"]),
            "candidates": saved_candidates,
        }

    async def validate_plan(
        self,
        plan_id: str,
        workspace_id: str,
    ) -> Dict[str, Any]:
        plan = await self.get_plan(plan_id, workspace_id)
        latest_ver = await self.repo.get_latest_version(plan.id)
        if not latest_ver:
            raise PlanVersionNotFoundError(plan.id)

        items = await self.repo.list_items_for_version(latest_ver.id)
        deps = await self.repo.list_dependencies_for_version(latest_ver.id)
        resources = await self.repo.list_resources(workspace_id)
        constraints = await self.repo.list_constraints_for_version(latest_ver.id)

        val_result = PlanValidator.validate_plan_version(
            items=items,
            dependencies=deps,
            resources=resources,
            constraints=constraints,
        )

        is_stale, stale_reasons = PlanLifecycleManager.check_staleness(
            plan=plan,
            latest_version=latest_ver,
            staleness_records=plan.staleness_records,
        )
        val_result["is_stale"] = is_stale
        val_result["stale_reasons"] = stale_reasons

        await self.events.emit_plan_event(
            event_type="work_plan.validated",
            workspace_id=workspace_id,
            plan_id=plan.id,
            payload={"is_valid": val_result["is_valid"], "is_stale": is_stale},
        )
        return val_result

    async def activate_plan(
        self,
        plan_id: str,
        workspace_id: str,
    ) -> WorkPlan:
        plan = await self.get_plan(plan_id, workspace_id)
        val = await self.validate_plan(plan_id, workspace_id)

        # Safety check: Cannot activate stale or invalid plans
        PlanningPolicyEngine.validate_activation_safety(val["is_stale"], val.get("stale_reasons"))
        if not val["is_valid"]:
            raise PlanStaleError("Plan contains hard constraint violations or cycles and cannot be activated.")

        PlanLifecycleManager.validate_transition(plan.status, "active")
        plan.status = "active"
        await self.session.commit()

        await self.events.emit_plan_event(
            event_type="work_plan.activated",
            workspace_id=workspace_id,
            plan_id=plan.id,
            payload={"status": "active"},
        )
        return plan

    async def pause_plan(
        self,
        plan_id: str,
        workspace_id: str,
    ) -> WorkPlan:
        plan = await self.get_plan(plan_id, workspace_id)
        PlanLifecycleManager.validate_transition(plan.status, "paused")
        plan.status = "paused"
        await self.session.commit()

        await self.events.emit_plan_event(
            event_type="work_plan.paused",
            workspace_id=workspace_id,
            plan_id=plan.id,
            payload={"status": "paused"},
        )
        return plan

    # -----------------------------------------------------------------------
    # Scenarios
    # -----------------------------------------------------------------------

    async def create_scenario(
        self,
        workspace_id: str,
        user_id: str,
        data: PlanningScenarioCreate,
    ) -> PlanningScenario:
        plan = await self.get_plan(data.work_plan_id, workspace_id)
        scenario = PlanningScenario(
            workspace_id=workspace_id,
            work_plan_id=plan.id,
            name=data.name,
            description=data.description,
            modifications=data.modifications,
            simulation_results={},
            comparison={},
            created_by=user_id,
        )
        created = await self.repo.create_scenario(scenario)
        await self.session.commit()
        return created

    async def run_scenario(
        self,
        scenario_id: str,
        workspace_id: str,
    ) -> PlanningScenario:
        scenario = await self.repo.get_scenario(scenario_id, workspace_id)
        if not scenario:
            raise PlanNotFoundError(scenario_id)

        plan = await self.get_plan(scenario.work_plan_id, workspace_id)
        latest_ver = await self.repo.get_latest_version(plan.id)
        items = await self.repo.list_items_for_version(latest_ver.id)
        deps = await self.repo.list_dependencies_for_version(latest_ver.id)
        resources = await self.repo.list_resources(workspace_id)
        constraints = await self.repo.list_constraints_for_version(latest_ver.id)

        sim_output = ScenarioEngine.run_scenario(
            base_items=items,
            base_dependencies=deps,
            base_resources=resources,
            base_constraints=constraints,
            modifications=scenario.modifications,
        )

        scenario.simulation_results = {
            "candidates_count": sim_output["simulated_candidates_count"],
            "candidates": [c.get("name") for c in sim_output["candidates"]],
        }
        scenario.comparison = {"comparison": sim_output["comparison"]}
        await self.session.commit()
        return scenario

    # -----------------------------------------------------------------------
    # Forecast & Workload Views
    # -----------------------------------------------------------------------

    async def get_forecast(
        self,
        workspace_id: str,
        horizon_days: int = 14,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=horizon_days)
        resources = await self.repo.list_resources(workspace_id)

        all_avails = []
        all_reserves = []
        for r in resources:
            all_avails.extend(await self.repo.list_availabilities_for_resource(r.id))
            all_reserves.extend(await self.repo.list_reservations_for_resource(r.id))

        plans = await self.repo.list_plans(workspace_id, status="active")
        demands = []
        for p in plans:
            v = await self.repo.get_latest_version(p.id)
            if v:
                its = await self.repo.list_items_for_version(v.id)
                for it in its:
                    demands.append({"estimated_units": 1.0, "item_id": it.id})

        return CapacityManager.generate_capacity_forecast(
            resources=resources,
            availabilities=all_avails,
            reservations=all_reserves,
            planned_demands=demands,
            period_start=now,
            period_end=end,
        )

    async def get_workload(self, workspace_id: str) -> List[Dict[str, Any]]:
        resources = await self.repo.list_resources(workspace_id)
        workloads = []
        for r in resources:
            cap = await self.get_resource_capacity(r.id, workspace_id)
            workloads.append({
                "workspace_id": workspace_id,
                "resource_id": r.id,
                "resource_name": r.name,
                "resource_type": r.resource_type,
                "scheduled_workload": cap["reserved_units"] + cap["proposed_units"],
                "reserved_capacity": cap["reserved_units"],
                "remaining_capacity": cap["remaining_capacity"],
                "blocked_items_count": 0,
                "overlapping_items_count": 0,
            })
        return workloads

    async def list_recommendations(
        self,
        workspace_id: str,
        work_plan_id: Optional[str] = None,
    ) -> List[PlanningRecommendation]:
        if work_plan_id:
            return await self.repo.list_recommendations_for_plan(work_plan_id, workspace_id)
        plans = await self.repo.list_plans(workspace_id)
        all_recs = []
        for p in plans:
            recs = await self.repo.list_recommendations_for_plan(p.id, workspace_id)
            all_recs.extend(recs)
        return all_recs
