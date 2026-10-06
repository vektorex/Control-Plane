"""
Repository for Step 41: AI Agent Simulation, Sandbox & Scenario Testing Layer.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.services.simulation.models import (
    FaultInjection,
    FaultProfile,
    Simulation,
    SimulationAssertion,
    SimulationComparison,
    SimulationEnvironment,
    SimulationRun,
    SimulationScenario,
    SimulationSideEffect,
    SimulationSuite,
    SimulationSuiteScenario,
    SimulationVersion,
)


class SimulationRepository:
    """Handles CRUD persistence for simulation entities with tenant isolation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # =========================================================================
    # SIMULATIONS
    # =========================================================================

    async def create_simulation(self, simulation: Simulation) -> Simulation:
        self.session.add(simulation)
        await self.session.flush()
        return simulation

    async def get_simulation(self, simulation_id: str, workspace_id: Optional[str] = None) -> Optional[Simulation]:
        stmt = select(Simulation).where(Simulation.id == simulation_id)
        if workspace_id:
            stmt = stmt.where(Simulation.workspace_id == workspace_id)
        stmt = stmt.options(selectinload(Simulation.versions))
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_simulation_by_slug(self, workspace_id: str, slug: str) -> Optional[Simulation]:
        stmt = select(Simulation).where(
            Simulation.workspace_id == workspace_id,
            Simulation.slug == slug,
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

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
        stmt = select(Simulation).where(Simulation.workspace_id == workspace_id)
        if project_id:
            stmt = stmt.where(Simulation.project_id == project_id)
        if target_type:
            stmt = stmt.where(Simulation.target_type == target_type)
        if target_id:
            stmt = stmt.where(Simulation.target_id == target_id)
        if status:
            stmt = stmt.where(Simulation.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(desc(Simulation.created_at)).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return list(res.scalars().all()), total

    # =========================================================================
    # SIMULATION VERSIONS
    # =========================================================================

    async def create_version(self, version: SimulationVersion) -> SimulationVersion:
        self.session.add(version)
        await self.session.flush()
        return version

    async def get_version(self, simulation_id: str, version_number: int) -> Optional[SimulationVersion]:
        stmt = select(SimulationVersion).where(
            SimulationVersion.simulation_id == simulation_id,
            SimulationVersion.version == version_number,
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_version_by_id(self, version_id: str) -> Optional[SimulationVersion]:
        stmt = select(SimulationVersion).where(SimulationVersion.id == version_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_latest_version(self, simulation_id: str) -> Optional[SimulationVersion]:
        stmt = (
            select(SimulationVersion)
            .where(SimulationVersion.simulation_id == simulation_id)
            .order_by(desc(SimulationVersion.version))
            .limit(1)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    # =========================================================================
    # ENVIRONMENTS
    # =========================================================================

    async def create_environment(self, env: SimulationEnvironment) -> SimulationEnvironment:
        self.session.add(env)
        await self.session.flush()
        return env

    async def get_environment(self, env_id: str, workspace_id: Optional[str] = None) -> Optional[SimulationEnvironment]:
        stmt = select(SimulationEnvironment).where(SimulationEnvironment.id == env_id)
        if workspace_id:
            stmt = stmt.where(SimulationEnvironment.workspace_id == workspace_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    # =========================================================================
    # SCENARIOS
    # =========================================================================

    async def create_scenario(self, scenario: SimulationScenario) -> SimulationScenario:
        self.session.add(scenario)
        await self.session.flush()
        return scenario

    async def get_scenario(self, scenario_id: str, workspace_id: Optional[str] = None) -> Optional[SimulationScenario]:
        stmt = select(SimulationScenario).where(SimulationScenario.id == scenario_id)
        if workspace_id:
            stmt = stmt.where(SimulationScenario.workspace_id == workspace_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_scenarios(
        self,
        workspace_id: str,
        scenario_type: Optional[str] = None,
        simulation_version_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[SimulationScenario], int]:
        stmt = select(SimulationScenario).where(SimulationScenario.workspace_id == workspace_id)
        if scenario_type:
            stmt = stmt.where(SimulationScenario.scenario_type == scenario_type)
        if simulation_version_id:
            stmt = stmt.where(SimulationScenario.simulation_version_id == simulation_version_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(desc(SimulationScenario.created_at)).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return list(res.scalars().all()), total

    # =========================================================================
    # SIMULATION RUNS
    # =========================================================================

    async def create_run(self, run: SimulationRun) -> SimulationRun:
        self.session.add(run)
        await self.session.flush()
        return run

    async def get_run(self, run_id: str) -> Optional[SimulationRun]:
        stmt = (
            select(SimulationRun)
            .where(SimulationRun.id == run_id)
            .options(
                selectinload(SimulationRun.assertions_rel),
                selectinload(SimulationRun.side_effects_rel),
                selectinload(SimulationRun.fault_injections_rel),
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_runs(
        self,
        simulation_id: Optional[str] = None,
        target_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[SimulationRun], int]:
        stmt = select(SimulationRun)
        if simulation_id:
            stmt = stmt.where(SimulationRun.simulation_id == simulation_id)
        if target_id:
            stmt = stmt.where(SimulationRun.target_id == target_id)
        if status:
            stmt = stmt.where(SimulationRun.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(desc(SimulationRun.created_at)).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return list(res.scalars().all()), total

    # =========================================================================
    # SUITES
    # =========================================================================

    async def create_suite(self, suite: SimulationSuite) -> SimulationSuite:
        self.session.add(suite)
        await self.session.flush()
        return suite

    async def get_suite(self, suite_id: str, workspace_id: Optional[str] = None) -> Optional[SimulationSuite]:
        stmt = (
            select(SimulationSuite)
            .where(SimulationSuite.id == suite_id)
            .options(selectinload(SimulationSuite.scenarios))
        )
        if workspace_id:
            stmt = stmt.where(SimulationSuite.workspace_id == workspace_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_suites(
        self,
        workspace_id: str,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[SimulationSuite], int]:
        stmt = select(SimulationSuite).where(SimulationSuite.workspace_id == workspace_id)
        if target_type:
            stmt = stmt.where(SimulationSuite.target_type == target_type)
        if target_id:
            stmt = stmt.where(SimulationSuite.target_id == target_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(desc(SimulationSuite.created_at)).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return list(res.scalars().all()), total

    # =========================================================================
    # COMPARISONS
    # =========================================================================

    async def create_comparison(self, comp: SimulationComparison) -> SimulationComparison:
        self.session.add(comp)
        await self.session.flush()
        return comp
