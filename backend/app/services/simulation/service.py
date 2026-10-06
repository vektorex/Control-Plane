"""
Service layer for Step 41: AI Agent Simulation, Sandbox & Scenario Testing Layer.
Coordinates simulation lifecycle, execution, suite regression testing, replay, and factual comparisons.
"""
from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.simulation.artifacts import SimulationReportGenerator
from backend.app.services.simulation.comparator import SimulationComparator
from backend.app.services.simulation.errors import (
    SimulationNotFoundError,
    SimulationRunNotFoundError,
    SimulationScenarioNotFoundError,
    SimulationSuiteNotFoundError,
    SimulationVersionImmutableError,
    SimulationVersionNotFoundError,
)
from backend.app.services.simulation.events import SimulationEventPublisher
from backend.app.services.simulation.lifecycle import SimulationLifecycle
from backend.app.services.simulation.models import (
    Simulation,
    SimulationComparison,
    SimulationEnvironment,
    SimulationRun,
    SimulationScenario,
    SimulationSuite,
    SimulationSuiteScenario,
    SimulationVersion,
)
from backend.app.services.simulation.repository import SimulationRepository
from backend.app.services.simulation.runner import SimulationRunner
from backend.app.services.simulation.safety import SimulationSafetyEnforcer
from backend.app.services.simulation.schemas import (
    SimulationCreate,
    SimulationRunCreate,
    SimulationScenarioCreate,
    SimulationScenarioUpdate,
    SimulationStatus,
    SimulationSuiteCreate,
    SimulationSuiteRunRequest,
    SimulationSuiteRunResult,
    SimulationUpdate,
    SimulationVersionCreate,
)
from backend.app.services.simulation.validators import SimulationValidator


def _slugify(name: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", name).strip().lower()
    return re.sub(r"[-\s]+", "-", cleaned)[:120] or "sim"


class SimulationCreationResult(tuple):
    """Result tuple supporting both (simulation, version) unpacking and direct attribute access to simulation."""
    def __new__(cls, simulation, version):
        return super().__new__(cls, (simulation, version))

    def __getattr__(self, name):
        return getattr(self[0], name)


class SimulationService:
    """High-level service orchestrating AI Agent Simulation."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SimulationRepository(session)
        self.runner = SimulationRunner(session)
        self.event_publisher = SimulationEventPublisher(session)

    # =========================================================================
    # SIMULATION CRUD & VERSIONS
    # =========================================================================

    async def create_simulation(
        self,
        workspace_id: str,
        user_id: Optional[str] = None,
        req: Optional[SimulationCreate] = None,
        data: Optional[SimulationCreate] = None,
        **kwargs,
    ) -> SimulationCreationResult:
        actual_req = req or data
        actual_user_id = user_id or kwargs.get("user_id") or "user-default"
        # Validate configuration
        ttype = actual_req.target_type.value if hasattr(actual_req.target_type, "value") else str(actual_req.target_type)
        stype = actual_req.simulation_type.value if hasattr(actual_req.simulation_type, "value") else str(actual_req.simulation_type)
        SimulationValidator.validate_simulation_config(
            target_type=ttype,
            target_id=actual_req.target_id,
            assertions=actual_req.assertions,
            fault_config=actual_req.fault_config,
            policy_overrides=actual_req.policy_overrides,
        )

        sim_id = str(uuid.uuid4())
        version_id = str(uuid.uuid4())
        slug_base = actual_req.slug or _slugify(actual_req.name)
        slug = slug_base

        # Check existing slug uniqueness within workspace
        existing = await self.repo.get_simulation_by_slug(workspace_id, slug)
        if existing:
            slug = f"{slug_base}-{uuid.uuid4().hex[:6]}"

        sim = Simulation(
            id=sim_id,
            workspace_id=workspace_id,
            project_id=actual_req.project_id,
            name=actual_req.name,
            slug=slug,
            description=actual_req.description,
            status=SimulationStatus.DRAFT.value,
            simulation_type=stype,
            target_type=ttype,
            target_id=actual_req.target_id,
            target_version_id=actual_req.target_version_id,
            current_version_id=version_id,
            created_by=actual_user_id,
        )
        await self.repo.create_simulation(sim)

        version = SimulationVersion(
            id=version_id,
            simulation_id=sim_id,
            version=1,
            configuration=actual_req.configuration or {},
            environment_config=actual_req.environment_config or {},
            scenario_config=actual_req.scenario_config or {},
            fault_config=actual_req.fault_config or {},
            policy_overrides=actual_req.policy_overrides or {},
            assertions=actual_req.assertions or [],
            created_by=actual_user_id,
            published_at=None,  # initial version is draft
        )
        await self.repo.create_version(version)
        await self.session.commit()

        await self.event_publisher.emit_simulation_event(
            event_type="simulation.created",
            workspace_id=workspace_id,
            simulation_id=sim_id,
            payload={"name": sim.name, "target_type": sim.target_type, "target_id": sim.target_id},
            actor_id=actual_user_id,
        )

        return SimulationCreationResult(sim, version)


    async def get_simulation(self, simulation_id: str, workspace_id: str) -> Simulation:
        sim = await self.repo.get_simulation(simulation_id, workspace_id)
        if not sim:
            raise SimulationNotFoundError(simulation_id)
        return sim

    async def list_simulations(
        self,
        workspace_id: str,
        project_id: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Simulation], int]:
        return await self.repo.list_simulations(
            workspace_id=workspace_id,
            project_id=project_id,
            target_type=target_type,
            target_id=target_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def update_simulation(
        self,
        simulation_id: str,
        workspace_id: str,
        req: SimulationUpdate,
    ) -> Simulation:
        sim = await self.get_simulation(simulation_id, workspace_id)
        if req.name is not None:
            sim.name = req.name
        if req.description is not None:
            sim.description = req.description
        if req.target_version_id is not None:
            sim.target_version_id = req.target_version_id
        if req.status is not None:
            SimulationLifecycle.validate_simulation_transition(sim.status, req.status.value)
            sim.status = req.status.value

        await self.session.commit()
        return sim

    async def create_version(
        self,
        simulation_id: str,
        workspace_id: Optional[str] = None,
        user_id: Optional[str] = None,
        req: Optional[SimulationVersionCreate] = None,
        data: Optional[SimulationVersionCreate] = None,
        **kwargs,
    ) -> SimulationVersion:
        actual_req = req or data or SimulationVersionCreate()
        actual_user_id = user_id or kwargs.get("user_id") or "user-default"
        sim = await self.repo.get_simulation(simulation_id)
        if not sim:
            raise SimulationNotFoundError(simulation_id)
        actual_ws = workspace_id or sim.workspace_id
        latest = await self.repo.get_latest_version(simulation_id)
        next_ver_num = (latest.version + 1) if latest else 1

        new_version = SimulationVersion(
            id=str(uuid.uuid4()),
            simulation_id=simulation_id,
            version=next_ver_num,
            configuration=actual_req.configuration or {},
            environment_config=actual_req.environment_config or {},
            scenario_config=actual_req.scenario_config or {},
            fault_config=actual_req.fault_config or {},
            policy_overrides=actual_req.policy_overrides or {},
            assertions=actual_req.assertions or [],
            created_by=actual_user_id,
            published_at=datetime.now(timezone.utc) if actual_req.publish_immediately else None,
        )
        await self.repo.create_version(new_version)
        sim.current_version_id = new_version.id
        await self.session.commit()

        await self.event_publisher.emit_simulation_event(
            event_type="simulation.version.created",
            workspace_id=actual_ws,
            simulation_id=simulation_id,
            payload={"version": next_ver_num, "version_id": new_version.id},
            actor_id=actual_user_id,
        )

        return new_version

    async def publish_version(self, version_id: str, user_id: Optional[str] = None) -> SimulationVersion:
        version = await self.repo.get_version_by_id(version_id)
        if not version:
            raise SimulationVersionNotFoundError(simulation_id="unknown", version_id=version_id)
        if version.published_at is None:
            version.published_at = datetime.now(timezone.utc)
            await self.session.commit()
        return version

    async def update_version(self, version_id: str, updates: Dict[str, Any], user_id: Optional[str] = None) -> SimulationVersion:
        version = await self.repo.get_version_by_id(version_id)
        if not version:
            raise SimulationVersionNotFoundError(simulation_id="unknown", version_id=version_id)
        if version.published_at is not None:
            raise SimulationVersionImmutableError(version_id)
        for k, v in updates.items():
            if hasattr(version, k):
                setattr(version, k, v)
        await self.session.commit()
        return version


    # =========================================================================
    # RUN SIMULATION
    # =========================================================================

    async def run_simulation(
        self,
        simulation_id: str,
        workspace_id: Optional[str] = None,
        user_id: Optional[str] = None,
        req: Optional[SimulationRunCreate] = None,
        data: Optional[SimulationRunCreate] = None,
        version_id: Optional[str] = None,
        scenario_id: Optional[str] = None,
        seed: Optional[int] = None,
        **kwargs,
    ) -> SimulationRun:
        sim = await self.repo.get_simulation(simulation_id)
        if not sim:
            raise SimulationNotFoundError(simulation_id)
        actual_ws = workspace_id or sim.workspace_id
        actual_user_id = user_id or kwargs.get("user_id") or "user-default"
        actual_req = req or data or SimulationRunCreate(
            simulation_version_id=version_id,
            scenario_id=scenario_id,
            seed=seed or 42,
        )

        # Resolve version
        version = None
        target_v_id = actual_req.simulation_version_id or version_id or sim.current_version_id
        if target_v_id:
            version = await self.repo.get_version_by_id(target_v_id)
        else:
            version = await self.repo.get_latest_version(simulation_id)

        if not version:
            raise SimulationVersionNotFoundError(simulation_id)

        # Resolve scenario if specified
        target_scen_id = actual_req.scenario_id or scenario_id
        scenario = None
        if target_scen_id:
            scenario = await self.repo.get_scenario(target_scen_id)
            if not scenario:
                raise SimulationScenarioNotFoundError(target_scen_id)

        target_version_id = actual_req.target_version_id or sim.target_version_id

        # Execute deterministically via runner
        run = await self.runner.run_simulation(
            simulation=sim,
            version=version,
            user_id=actual_user_id,
            scenario=scenario,
            scenario_override=actual_req.scenario_override,
            seed=actual_req.seed or seed or 42,
            target_version_id=target_version_id,
            policy_overrides=actual_req.policy_overrides,
            fault_overrides=actual_req.fault_overrides,
            budget_limit=actual_req.budget_limit,
        )
        return run

    # =========================================================================
    # SCENARIOS
    # =========================================================================

    async def create_scenario(
        self,
        workspace_id: Optional[str] = None,
        user_id: Optional[str] = None,
        req: Optional[SimulationScenarioCreate] = None,
        data: Optional[SimulationScenarioCreate] = None,
        version_id: Optional[str] = None,
        **kwargs,
    ) -> SimulationScenario:
        actual_req = req or data
        if not actual_req:
            raise SimulationNotFoundError("Scenario payload missing.")

        actual_ws = workspace_id or kwargs.get("workspace_id")
        if not actual_ws and version_id:
            v = await self.repo.get_version_by_id(version_id)
            if v:
                sim = await self.repo.get_simulation(v.simulation_id)
                if sim:
                    actual_ws = sim.workspace_id
        actual_ws = actual_ws or "ws-default"

        SimulationValidator.validate_scenario(actual_req.model_dump())

        stype = actual_req.scenario_type.value if hasattr(actual_req.scenario_type, "value") else str(actual_req.scenario_type)
        scenario = SimulationScenario(
            id=str(uuid.uuid4()),
            workspace_id=actual_ws,
            simulation_version_id=actual_req.simulation_version_id or version_id,
            suite_id=actual_req.suite_id,
            name=actual_req.name,
            description=actual_req.description,
            scenario_type=stype,
            input=actual_req.input or {},
            context=actual_req.context or {},
            environment_state=actual_req.environment_state or {},
            expected_behavior=actual_req.expected_behavior or {},
            fault_configuration=actual_req.fault_configuration or {},
            assertions=actual_req.assertions or [],
        )
        await self.repo.create_scenario(scenario)
        await self.session.commit()
        return scenario

    async def get_scenario(self, scenario_id: str, workspace_id: Optional[str] = None) -> SimulationScenario:
        scen = await self.repo.get_scenario(scenario_id, workspace_id)
        if not scen:
            raise SimulationScenarioNotFoundError(scenario_id)
        return scen

    async def list_scenarios(
        self,
        workspace_id: str,
        scenario_type: Optional[str] = None,
        simulation_version_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[SimulationScenario], int]:
        return await self.repo.list_scenarios(
            workspace_id=workspace_id,
            scenario_type=scenario_type,
            simulation_version_id=simulation_version_id,
            limit=limit,
            offset=offset,
        )

    # =========================================================================
    # SUITES & REGRESSION TESTING
    # =========================================================================

    async def create_suite(
        self,
        workspace_id: str,
        user_id: Optional[str] = None,
        req: Optional[SimulationSuiteCreate] = None,
        data: Optional[SimulationSuiteCreate] = None,
        **kwargs,
    ) -> SimulationSuite:
        actual_req = req or data
        actual_user_id = user_id or kwargs.get("user_id") or "user-default"
        suite_id = str(uuid.uuid4())
        ttype = actual_req.target_type.value if hasattr(actual_req.target_type, "value") else str(actual_req.target_type)
        suite = SimulationSuite(
            id=suite_id,
            workspace_id=workspace_id,
            project_id=actual_req.project_id,
            name=actual_req.name,
            description=actual_req.description,
            target_type=ttype,
            target_id=actual_req.target_id,
            created_by=actual_user_id,
        )
        await self.repo.create_suite(suite)

        if actual_req.scenario_ids:
            for idx, sc_id in enumerate(actual_req.scenario_ids):
                link = SimulationSuiteScenario(
                    id=str(uuid.uuid4()),
                    suite_id=suite_id,
                    scenario_id=sc_id,
                    order_index=idx,
                )
                self.session.add(link)

        await self.session.commit()
        return suite

    async def get_suite(self, suite_id: str, workspace_id: str) -> SimulationSuite:
        suite = await self.repo.get_suite(suite_id, workspace_id)
        if not suite:
            raise SimulationSuiteNotFoundError(suite_id)
        return suite

    async def list_suites(
        self,
        workspace_id: str,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[SimulationSuite], int]:
        return await self.repo.list_suites(workspace_id, target_type, target_id, limit, offset)

    async def run_suite(
        self,
        suite_id: str,
        workspace_id: str,
        user_id: str,
        req: SimulationSuiteRunRequest,
    ) -> SimulationSuiteRunResult:
        suite = await self.get_suite(suite_id, workspace_id)
        # Find simulation targeting this target_id
        sims, _ = await self.repo.list_simulations(workspace_id=workspace_id, target_id=suite.target_id, limit=1)
        if not sims:
            # Create a quick default simulation container for suite execution
            sim, version = await self.create_simulation(
                workspace_id=workspace_id,
                user_id=user_id,
                req=SimulationCreate(
                    name=f"Suite Sim: {suite.name}",
                    target_type=suite.target_type,
                    target_id=suite.target_id,
                    target_version_id=req.target_version_id,
                ),
            )
        else:
            sim = sims[0]
            version = await self.repo.get_latest_version(sim.id)

        runs = []
        run_ids = []
        regressions = []

        for link in suite.scenarios:
            scenario = await self.repo.get_scenario(link.scenario_id, workspace_id)
            if not scenario:
                continue

            run = await self.runner.run_simulation(
                simulation=sim,
                version=version,
                user_id=user_id,
                scenario=scenario,
                seed=req.seed or 42,
                target_version_id=req.target_version_id,
                suite_id=suite.id,
            )
            runs.append(run)
            run_ids.append(run.id)

            # Check if any assertions failed (regression detected)
            failed_asserts = [a for a in run.assertion_results if not a.get("passed")]
            if failed_asserts:
                reg = {
                    "scenario_id": scenario.id,
                    "scenario_name": scenario.name,
                    "run_id": run.id,
                    "failed_assertions": failed_asserts,
                }
                regressions.append(reg)
                await self.event_publisher.emit_simulation_event(
                    event_type="simulation.regression.detected",
                    workspace_id=workspace_id,
                    simulation_id=sim.id,
                    payload=reg,
                )

        completed_count = sum(1 for r in runs if r.status == "completed")
        failed_count = sum(1 for r in runs if r.status == "failed")

        return SimulationSuiteRunResult(
            suite_id=suite.id,
            total_scenarios=len(runs),
            completed_scenarios=completed_count,
            failed_scenarios=failed_count,
            run_ids=run_ids,
            runs=runs,
            regressions_detected=regressions,
        )

    # =========================================================================
    # RUN METRICS & REPORTS
    # =========================================================================

    async def get_run(self, run_id: str) -> SimulationRun:
        run = await self.repo.get_run(run_id)
        if not run:
            raise SimulationRunNotFoundError(run_id)
        return run

    async def list_runs(
        self,
        simulation_id: Optional[str] = None,
        target_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[SimulationRun], int]:
        return await self.repo.list_runs(simulation_id, target_id, status, limit, offset)

    async def get_run_report(self, run_id: str, workspace_id: str) -> Dict[str, Any]:
        run = await self.get_run(run_id)
        sim = await self.get_simulation(run.simulation_id, workspace_id)
        scenario_dict = {}
        if run.scenario_id:
            scen = await self.repo.get_scenario(run.scenario_id)
            if scen:
                scenario_dict = {
                    "id": scen.id,
                    "name": scen.name,
                    "scenario_type": scen.scenario_type,
                    "input": scen.input,
                }

        report = SimulationReportGenerator.generate_report(
            simulation={
                "id": sim.id,
                "name": sim.name,
                "target_type": sim.target_type,
                "target_id": sim.target_id,
                "target_version_id": run.target_version_id,
            },
            run={
                "id": run.id,
                "status": run.status,
                "cost": run.cost,
                "latency": run.latency,
                "tokens": run.tokens,
                "output": run.output,
                "seed": run.seed,
                "tool_calls": run.tool_calls,
                "connector_calls": run.connector_calls,
                "reproducibility_metadata": run.reproducibility_metadata,
            },
            scenario=scenario_dict,
            trace_events=[],
            side_effects=run.side_effects,
            assertions=run.assertion_results,
            faults_injected=[{"fault_type": fi.fault_type, "target": fi.target} for fi in (run.fault_injections_rel or [])],
            policy_decisions=run.policy_snapshot.get("decisions", []),
            security_findings=[],
        )
        return report

    async def compare_runs(self, baseline_run_id: str, comparison_run_id: str, workspace_id: str) -> SimulationComparison:
        b_run = await self.get_run(baseline_run_id)
        c_run = await self.get_run(comparison_run_id)

        diffs = SimulationComparator.compare_runs(
            baseline_run={
                "id": b_run.id,
                "status": b_run.status,
                "target_version_id": b_run.target_version_id,
                "seed": b_run.seed,
                "cost": b_run.cost,
                "latency": b_run.latency,
                "tokens": b_run.tokens,
                "tool_calls": b_run.tool_calls,
                "connector_calls": b_run.connector_calls,
                "side_effects": b_run.side_effects,
                "assertion_results": b_run.assertion_results,
            },
            comparison_run={
                "id": c_run.id,
                "status": c_run.status,
                "target_version_id": c_run.target_version_id,
                "seed": c_run.seed,
                "cost": c_run.cost,
                "latency": c_run.latency,
                "tokens": c_run.tokens,
                "tool_calls": c_run.tool_calls,
                "connector_calls": c_run.connector_calls,
                "side_effects": c_run.side_effects,
                "assertion_results": c_run.assertion_results,
            },
        )

        comp = SimulationComparison(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            baseline_run_id=baseline_run_id,
            comparison_run_id=comparison_run_id,
            factual_differences=diffs,
        )
        await self.repo.create_comparison(comp)
        await self.session.commit()
        return comp

    # =========================================================================
    # PRODUCTION REPLAY INTEGRATION (Section 30)
    # =========================================================================

    async def create_simulation_from_replay(
        self,
        production_run_id: str,
        workspace_id: str,
        user_id: str,
    ) -> Tuple[Simulation, SimulationRun]:
        """
        Creates a sandboxed simulation seeded with a sanitized snapshot of a production run.
        Original production run is NEVER modified. Side effects disabled.
        """
        # Fetch target run snapshot (from runs table or agents run)
        sim_name = f"Replay Sim: Run {production_run_id[:8]}"
        sim, version = await self.create_simulation(
            workspace_id=workspace_id,
            user_id=user_id,
            req=SimulationCreate(
                name=sim_name,
                simulation_type="replay",
                target_type="replay",
                target_id=production_run_id,
                environment_config={"mode": "snapshot", "replayed_from_run_id": production_run_id},
            ),
        )

        # Run in sandbox
        sim_run = await self.run_simulation(
            simulation_id=sim.id,
            workspace_id=workspace_id,
            user_id=user_id,
            req=SimulationRunCreate(
                seed=42,
                scenario_override={"input": {"replayed_run_id": production_run_id}},
            ),
        )

        return sim, sim_run
