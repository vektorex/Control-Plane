"""
Persistence Repository for Agents, Versions, Runs, Delegations, Teams, Messages, and Conflicts.
Step 40: Governed AI Agent Runtime and Multi-Agent Teams.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.services.agents.errors import (
    AgentNotFoundError,
    AgentTeamNotFoundError,
    AgentVersionImmutableError,
    AgentVersionNotFoundError,
)
from backend.app.services.agents.models import (
    Agent,
    AgentConflict,
    AgentDelegation,
    AgentMessage,
    AgentRun,
    AgentTeam,
    AgentTeamMember,
    AgentTeamRun,
    AgentTeamVersion,
    AgentVersion,
)
from backend.app.services.agents.schemas import AgentStatus, AgentTeamStatus


class AgentRepository:
    """Async repository providing full transactional access to agent and team entities."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # =========================================================================
    # AGENTS
    # =========================================================================

    async def create_agent(
        self,
        workspace_id: str,
        name: str,
        slug: str,
        purpose: str,
        created_by: str,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Agent:
        agent = Agent(
            workspace_id=workspace_id,
            project_id=project_id,
            name=name,
            slug=slug,
            description=description,
            purpose=purpose,
            status=AgentStatus.DRAFT.value,
            created_by=created_by,
        )
        self.session.add(agent)
        await self.session.flush()
        return agent

    async def get_agent(self, agent_id: str, workspace_id: Optional[str] = None) -> Optional[Agent]:
        stmt = select(Agent).where(Agent.id == agent_id)
        if workspace_id:
            stmt = stmt.where(Agent.workspace_id == workspace_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_agent_by_slug(self, workspace_id: str, slug: str) -> Optional[Agent]:
        stmt = select(Agent).where(Agent.workspace_id == workspace_id, Agent.slug == slug)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_agents(
        self,
        workspace_id: str,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Agent], int]:
        stmt = select(Agent).where(Agent.workspace_id == workspace_id)
        if project_id:
            stmt = stmt.where(Agent.project_id == project_id)
        if status:
            stmt = stmt.where(Agent.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(Agent.created_at.desc()).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return list(res.scalars().all()), total

    async def update_agent(self, agent: Agent, updates: Dict[str, Any]) -> Agent:
        for k, v in updates.items():
            if hasattr(agent, k) and v is not None:
                setattr(agent, k, v)
        agent.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return agent

    async def delete_agent(self, agent: Agent) -> None:
        await self.session.delete(agent)
        await self.session.flush()

    # =========================================================================
    # AGENT VERSIONS
    # =========================================================================

    async def create_version(
        self,
        agent_id: str,
        instructions: str,
        created_by: str,
        model_policy: Dict[str, Any],
        capability_policy: List[str],
        memory_policy: Dict[str, Any],
        knowledge_policy: Dict[str, Any],
        execution_policy: Dict[str, Any],
        evaluation_policy: Dict[str, Any],
        approval_policy: Dict[str, Any],
        budget_policy: Dict[str, Any],
        configuration: Dict[str, Any],
    ) -> AgentVersion:
        # Determine next version number
        stmt = select(func.coalesce(func.max(AgentVersion.version), 0)).where(AgentVersion.agent_id == agent_id)
        curr_max = (await self.session.execute(stmt)).scalar() or 0
        new_version_num = curr_max + 1

        version = AgentVersion(
            agent_id=agent_id,
            version=new_version_num,
            instructions=instructions,
            model_policy=model_policy,
            capability_policy=capability_policy,
            memory_policy=memory_policy,
            knowledge_policy=knowledge_policy,
            execution_policy=execution_policy,
            evaluation_policy=evaluation_policy,
            approval_policy=approval_policy,
            budget_policy=budget_policy,
            configuration=configuration,
            created_by=created_by,
        )
        self.session.add(version)
        await self.session.flush()
        return version

    async def get_version(self, version_id: str) -> Optional[AgentVersion]:
        return await self.session.get(AgentVersion, version_id)

    async def get_latest_version(self, agent_id: str) -> Optional[AgentVersion]:
        stmt = (
            select(AgentVersion)
            .where(AgentVersion.agent_id == agent_id)
            .order_by(AgentVersion.version.desc())
            .limit(1)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_versions(self, agent_id: str) -> List[AgentVersion]:
        stmt = (
            select(AgentVersion)
            .where(AgentVersion.agent_id == agent_id)
            .order_by(AgentVersion.version.desc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def publish_version(self, version: AgentVersion) -> AgentVersion:
        version.published_at = datetime.now(timezone.utc)
        await self.session.flush()
        return version

    # =========================================================================
    # AGENT RUNS & TRACES
    # =========================================================================

    async def get_run(self, run_id: str, workspace_id: Optional[str] = None) -> Optional[AgentRun]:
        stmt = select(AgentRun).where(AgentRun.id == run_id)
        if workspace_id:
            stmt = stmt.where(AgentRun.workspace_id == workspace_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_runs(
        self,
        workspace_id: str,
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[AgentRun], int]:
        stmt = select(AgentRun).where(AgentRun.workspace_id == workspace_id)
        if agent_id:
            stmt = stmt.where(AgentRun.agent_id == agent_id)
        if project_id:
            stmt = stmt.where(AgentRun.project_id == project_id)
        if status:
            stmt = stmt.where(AgentRun.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(AgentRun.created_at.desc()).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return list(res.scalars().all()), total

    # =========================================================================
    # DELEGATIONS
    # =========================================================================

    async def get_delegation(self, delegation_id: str) -> Optional[AgentDelegation]:
        return await self.session.get(AgentDelegation, delegation_id)

    async def list_delegations_for_run(self, run_id: str) -> List[AgentDelegation]:
        stmt = (
            select(AgentDelegation)
            .where(AgentDelegation.parent_agent_run_id == run_id)
            .order_by(AgentDelegation.created_at.asc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    # =========================================================================
    # AGENT TEAMS
    # =========================================================================

    async def create_team(
        self,
        workspace_id: str,
        name: str,
        slug: str,
        created_by: str,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> AgentTeam:
        team = AgentTeam(
            workspace_id=workspace_id,
            project_id=project_id,
            name=name,
            slug=slug,
            description=description,
            status=AgentTeamStatus.DRAFT.value,
            created_by=created_by,
        )
        self.session.add(team)
        await self.session.flush()
        return team

    async def get_team(self, team_id: str, workspace_id: Optional[str] = None) -> Optional[AgentTeam]:
        stmt = select(AgentTeam).where(AgentTeam.id == team_id)
        if workspace_id:
            stmt = stmt.where(AgentTeam.workspace_id == workspace_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_teams(
        self,
        workspace_id: str,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[AgentTeam], int]:
        stmt = select(AgentTeam).where(AgentTeam.workspace_id == workspace_id)
        if project_id:
            stmt = stmt.where(AgentTeam.project_id == project_id)
        if status:
            stmt = stmt.where(AgentTeam.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(AgentTeam.created_at.desc()).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return list(res.scalars().all()), total

    async def create_team_version(
        self,
        team_id: str,
        objective: str,
        created_by: str,
        coordination_policy: Dict[str, Any],
        shared_context_policy: Dict[str, Any],
        approval_policy: Dict[str, Any],
    ) -> AgentTeamVersion:
        stmt = select(func.coalesce(func.max(AgentTeamVersion.version), 0)).where(AgentTeamVersion.team_id == team_id)
        curr_max = (await self.session.execute(stmt)).scalar() or 0
        new_version_num = curr_max + 1

        version = AgentTeamVersion(
            team_id=team_id,
            version=new_version_num,
            objective=objective,
            coordination_policy=coordination_policy,
            shared_context_policy=shared_context_policy,
            approval_policy=approval_policy,
            created_by=created_by,
        )
        self.session.add(version)
        await self.session.flush()
        return version

    async def get_team_version(self, version_id: str) -> Optional[AgentTeamVersion]:
        stmt = (
            select(AgentTeamVersion)
            .options(selectinload(AgentTeamVersion.members))
            .where(AgentTeamVersion.id == version_id)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def add_team_member(
        self,
        team_version_id: str,
        agent_id: str,
        agent_version_id: str,
        role: str,
        capabilities: List[str],
        responsibilities: str,
        limits: Dict[str, Any],
    ) -> AgentTeamMember:
        member = AgentTeamMember(
            team_version_id=team_version_id,
            agent_id=agent_id,
            agent_version_id=agent_version_id,
            role=role,
            capabilities=capabilities,
            responsibilities=responsibilities,
            limits=limits,
        )
        self.session.add(member)
        await self.session.flush()
        return member

    # =========================================================================
    # TEAM RUNS, MESSAGES, CONFLICTS
    # =========================================================================

    async def get_team_run(self, run_id: str, workspace_id: Optional[str] = None) -> Optional[AgentTeamRun]:
        stmt = (
            select(AgentTeamRun)
            .options(selectinload(AgentTeamRun.messages), selectinload(AgentTeamRun.conflicts))
            .where(AgentTeamRun.id == run_id)
        )
        if workspace_id:
            stmt = stmt.where(AgentTeamRun.workspace_id == workspace_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_team_runs(
        self,
        workspace_id: str,
        team_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[AgentTeamRun], int]:
        stmt = select(AgentTeamRun).where(AgentTeamRun.workspace_id == workspace_id)
        if team_id:
            stmt = stmt.where(AgentTeamRun.team_id == team_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(AgentTeamRun.created_at.desc()).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return list(res.scalars().all()), total

    async def get_conflict(self, conflict_id: str) -> Optional[AgentConflict]:
        return await self.session.get(AgentConflict, conflict_id)
