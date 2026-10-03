"""
Agent Service Facade for Step 40.
Primary entry point for Governed AI Agent Runtime and Multi-Agent Teams.
Combines Repository, Runtime, Registry, Delegation Engine, Team Coordinator, and Event Publisher.
"""
from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.agents.delegation import AgentDelegationEngine
from backend.app.services.agents.errors import (
    AgentLifecycleError,
    AgentNotFoundError,
    AgentRunNotFoundError,
    AgentTeamNotFoundError,
    AgentTeamRunNotFoundError,
    AgentVersionImmutableError,
    AgentVersionNotFoundError,
)
from backend.app.services.agents.events import AgentEventPublisher
from backend.app.services.agents.lifecycle import validate_lifecycle_transition
from backend.app.services.agents.models import (
    Agent,
    AgentConflict,
    AgentDelegation,
    AgentRun,
    AgentTeam,
    AgentTeamRun,
    AgentTeamVersion,
    AgentVersion,
)
from backend.app.services.agents.policies import PolicyResolver
from backend.app.services.agents.repository import AgentRepository
from backend.app.services.agents.runtime import AgentRuntime
from backend.app.services.agents.schemas import (
    AgentCreate,
    AgentDelegationCreate,
    AgentRunCreate,
    AgentStatus,
    AgentTeamCreate,
    AgentTeamRunCreate,
    AgentTeamStatus,
    AgentTeamUpdate,
    AgentUpdate,
    AgentVersionCreate,
    ConflictStatus,
    EffectivePolicyPreview,
)
from backend.app.services.agents.team import TeamOrchestrationCoordinator
from backend.app.services.events.constants import SystemEventType


def _slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower().strip())
    return re.sub(r"[\s_-]+", "-", slug)[:128]


class AgentService:
    """Unified service facade for agents and multi-agent teams."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AgentRepository(session)
        self.runtime = AgentRuntime(session)
        self.delegation_engine = AgentDelegationEngine(session)
        self.team_coordinator = TeamOrchestrationCoordinator(session)
        self.event_publisher = AgentEventPublisher(session)

    # =========================================================================
    # AGENT OPERATIONS
    # =========================================================================

    async def create_agent(
        self,
        workspace_id: str,
        user_id: str,
        req: AgentCreate,
    ) -> Tuple[Agent, AgentVersion]:
        """Creates an agent and its initial draft version."""
        slug = req.slug or _slugify(req.name)
        # Check uniqueness in workspace
        existing = await self.repo.get_agent_by_slug(workspace_id, slug)
        if existing:
            slug = f"{slug}-{int(datetime.now(timezone.utc).timestamp())}"

        agent = await self.repo.create_agent(
            workspace_id=workspace_id,
            name=req.name,
            slug=slug,
            purpose=req.purpose,
            description=req.description,
            project_id=req.project_id,
            created_by=user_id,
        )

        version = await self.repo.create_version(
            agent_id=agent.id,
            instructions=req.instructions,
            created_by=user_id,
            model_policy=req.model_policy.model_dump() if req.model_policy else {},
            capability_policy=req.capability_policy or [],
            memory_policy=req.memory_policy.model_dump() if req.memory_policy else {},
            knowledge_policy=req.knowledge_policy.model_dump() if req.knowledge_policy else {},
            execution_policy=req.execution_policy.model_dump() if req.execution_policy else {},
            evaluation_policy=req.evaluation_policy.model_dump() if req.evaluation_policy else {},
            approval_policy=req.approval_policy.model_dump() if req.approval_policy else {},
            budget_policy=req.budget_policy.model_dump() if req.budget_policy else {},
            configuration=req.configuration or {},
        )

        agent.current_version_id = version.id
        await self.session.commit()

        await self.event_publisher.emit_agent_event(
            event_type=SystemEventType.AGENT_CREATED.value,
            workspace_id=workspace_id,
            agent_id=agent.id,
            payload={"name": agent.name, "slug": agent.slug},
            project_id=agent.project_id,
            actor_id=user_id,
        )

        return agent, version

    async def get_agent(self, agent_id: str, workspace_id: str) -> Agent:
        agent = await self.repo.get_agent(agent_id, workspace_id)
        if not agent:
            raise AgentNotFoundError(agent_id)
        return agent

    async def list_agents(
        self,
        workspace_id: str,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Agent], int]:
        return await self.repo.list_agents(workspace_id, project_id, status, limit, offset)

    async def update_agent(self, agent_id: str, workspace_id: str, updates: AgentUpdate) -> Agent:
        agent = await self.get_agent(agent_id, workspace_id)
        updated = await self.repo.update_agent(agent, updates.model_dump(exclude_unset=True))
        await self.session.commit()

        await self.event_publisher.emit_agent_event(
            event_type=SystemEventType.AGENT_UPDATED.value,
            workspace_id=workspace_id,
            agent_id=agent.id,
            payload={"name": agent.name},
            project_id=agent.project_id,
        )
        return updated

    async def create_agent_version(
        self,
        agent_id: str,
        workspace_id: str,
        user_id: str,
        req: AgentVersionCreate,
    ) -> AgentVersion:
        agent = await self.get_agent(agent_id, workspace_id)
        version = await self.repo.create_version(
            agent_id=agent.id,
            instructions=req.instructions,
            created_by=user_id,
            model_policy=req.model_policy.model_dump() if req.model_policy else {},
            capability_policy=req.capability_policy or [],
            memory_policy=req.memory_policy.model_dump() if req.memory_policy else {},
            knowledge_policy=req.knowledge_policy.model_dump() if req.knowledge_policy else {},
            execution_policy=req.execution_policy.model_dump() if req.execution_policy else {},
            evaluation_policy=req.evaluation_policy.model_dump() if req.evaluation_policy else {},
            approval_policy=req.approval_policy.model_dump() if req.approval_policy else {},
            budget_policy=req.budget_policy.model_dump() if req.budget_policy else {},
            configuration=req.configuration or {},
        )
        await self.session.commit()
        return version

    async def publish_version(self, agent_id: str, version_id: str, workspace_id: str, user_id: str) -> AgentVersion:
        agent = await self.get_agent(agent_id, workspace_id)
        version = await self.repo.get_version(version_id)
        if not version or version.agent_id != agent.id:
            raise AgentVersionNotFoundError(agent_id, version_id=version_id)

        published = await self.repo.publish_version(version)
        agent.current_version_id = published.id
        await self.session.commit()

        await self.event_publisher.emit_agent_event(
            event_type=SystemEventType.AGENT_VERSION_PUBLISHED.value,
            workspace_id=workspace_id,
            agent_id=agent.id,
            payload={"version_id": published.id, "version_number": published.version},
            project_id=agent.project_id,
            actor_id=user_id,
        )
        return published

    async def activate_agent(self, agent_id: str, workspace_id: str, user_id: str) -> Agent:
        agent = await self.get_agent(agent_id, workspace_id)
        validate_lifecycle_transition(agent.status, AgentStatus.ACTIVE.value, has_published_version=bool(agent.current_version_id))
        agent.status = AgentStatus.ACTIVE.value
        agent.updated_at = datetime.now(timezone.utc)
        await self.session.commit()

        await self.event_publisher.emit_agent_event(
            event_type=SystemEventType.AGENT_ACTIVATED.value,
            workspace_id=workspace_id,
            agent_id=agent.id,
            payload={"status": agent.status},
            project_id=agent.project_id,
            actor_id=user_id,
        )
        return agent

    async def pause_agent(self, agent_id: str, workspace_id: str, user_id: str) -> Agent:
        agent = await self.get_agent(agent_id, workspace_id)
        validate_lifecycle_transition(agent.status, AgentStatus.PAUSED.value)
        agent.status = AgentStatus.PAUSED.value
        agent.updated_at = datetime.now(timezone.utc)
        await self.session.commit()

        await self.event_publisher.emit_agent_event(
            event_type=SystemEventType.AGENT_PAUSED.value,
            workspace_id=workspace_id,
            agent_id=agent.id,
            payload={"status": agent.status},
            project_id=agent.project_id,
            actor_id=user_id,
        )
        return agent

    async def disable_agent(self, agent_id: str, workspace_id: str, user_id: str) -> Agent:
        agent = await self.get_agent(agent_id, workspace_id)
        validate_lifecycle_transition(agent.status, AgentStatus.DISABLED.value)
        agent.status = AgentStatus.DISABLED.value
        agent.updated_at = datetime.now(timezone.utc)
        await self.session.commit()

        await self.event_publisher.emit_agent_event(
            event_type=SystemEventType.AGENT_DISABLED.value,
            workspace_id=workspace_id,
            agent_id=agent.id,
            payload={"status": agent.status},
            project_id=agent.project_id,
            actor_id=user_id,
        )
        return agent

    # =========================================================================
    # AGENT EXECUTION & DELEGATION
    # =========================================================================

    async def run_agent(
        self,
        agent_id: str,
        workspace_id: str,
        user_id: str,
        req: AgentRunCreate,
    ) -> AgentRun:
        return await self.runtime.execute_agent_run(
            agent_id=agent_id,
            workspace_id=workspace_id,
            user_id=user_id,
            input_data=req.input,
            version_id=req.agent_version_id,
            project_id=req.project_id,
            task_id=req.task_id,
            workflow_run_id=req.workflow_run_id,
            collaboration_session_id=req.collaboration_session_id,
            dry_run=req.dry_run,
            budget_override=req.budget_override,
        )

    async def get_run(self, run_id: str, workspace_id: str) -> AgentRun:
        run = await self.repo.get_run(run_id, workspace_id)
        if not run:
            raise AgentRunNotFoundError(run_id)
        return run

    async def list_runs(
        self,
        workspace_id: str,
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[AgentRun], int]:
        return await self.repo.list_runs(workspace_id, agent_id, project_id, status, limit, offset)

    async def delegate_agent(
        self,
        agent_id: str,
        workspace_id: str,
        user_id: str,
        req: AgentDelegationCreate,
    ) -> AgentDelegation:
        """Initiates a safe delegation from an active agent execution."""
        # Find active parent run for this agent
        runs, _ = await self.repo.list_runs(workspace_id=workspace_id, agent_id=agent_id, limit=1)
        if not runs:
            raise AgentRunNotFoundError(f"No active run found for agent '{agent_id}' to delegate from.")

        parent_run = runs[0]
        parent_agent = await self.get_agent(agent_id, workspace_id)
        parent_version = await self.repo.get_version(parent_run.agent_version_id)
        if not parent_version:
            raise AgentVersionNotFoundError(agent_id)

        delegation = await self.delegation_engine.create_delegation(
            parent_run=parent_run,
            parent_agent=parent_agent,
            parent_version=parent_version,
            child_agent_id=req.child_agent_id,
            child_agent_version_id=req.child_agent_version_id,
            reason=req.reason,
            task_snapshot=req.task_snapshot,
            requested_budget=req.budget_allocation,
            requested_capabilities=req.allowed_capabilities,
        )
        await self.session.commit()

        await self.event_publisher.emit_agent_event(
            event_type=SystemEventType.AGENT_DELEGATED.value,
            workspace_id=workspace_id,
            agent_id=parent_agent.id,
            payload={
                "delegation_id": delegation.id,
                "child_agent_id": delegation.child_agent_id,
                "budget_allocation": delegation.budget_allocation,
            },
            project_id=parent_agent.project_id,
            actor_id=user_id,
        )

        return delegation

    async def replay_run(self, run_id: str, workspace_id: str, user_id: str) -> Dict[str, Any]:
        """Replays an agent run using its stored reproducibility metadata in dry-run mode."""
        orig_run = await self.get_run(run_id, workspace_id)
        meta = orig_run.reproducibility_metadata or {}

        # Re-execute in dry-run mode with original snapshot
        replay_run = await self.runtime.execute_agent_run(
            agent_id=orig_run.agent_id,
            workspace_id=workspace_id,
            user_id=user_id,
            input_data=orig_run.input_snapshot or {},
            version_id=orig_run.agent_version_id,
            project_id=orig_run.project_id,
            dry_run=True,
        )

        return {
            "original_run_id": orig_run.id,
            "replay_run_id": replay_run.id,
            "status": "completed",
            "reproducibility_match": orig_run.agent_version_id == replay_run.agent_version_id,
            "discrepancies": [],
            "metadata_snapshot": meta,
        }

    async def get_run_trace(self, run_id: str, workspace_id: str) -> Dict[str, Any]:
        run = await self.get_run(run_id, workspace_id)
        return {
            "run_id": run.id,
            "agent_id": run.agent_id,
            "steps": [
                {
                    "step_index": 1,
                    "tokens": run.tokens,
                    "cost": run.cost,
                    "status": run.status,
                    "execution_state": run.execution_state,
                }
            ],
            "tool_calls": [],
            "connector_calls": [],
            "context_sources": run.reproducibility_metadata.get("context_sources", []),
            "memory_references": [],
            "delegations": [d.id for d in await self.repo.list_delegations_for_run(run.id)],
            "approvals": [],
            "latency": run.latency,
            "cost": run.cost,
        }

    # =========================================================================
    # MULTI-AGENT TEAM OPERATIONS
    # =========================================================================

    async def create_team(
        self,
        workspace_id: str,
        user_id: str,
        req: AgentTeamCreate,
    ) -> Tuple[AgentTeam, AgentTeamVersion]:
        slug = req.slug or _slugify(req.name)
        team = await self.repo.create_team(
            workspace_id=workspace_id,
            name=req.name,
            slug=slug,
            description=req.description,
            project_id=req.project_id,
            created_by=user_id,
        )

        version = await self.repo.create_team_version(
            team_id=team.id,
            objective=req.objective,
            created_by=user_id,
            coordination_policy=req.coordination_policy,
            shared_context_policy=req.shared_context_policy,
            approval_policy=req.approval_policy,
        )

        # Add team members
        for m in req.members:
            # Resolve member agent to get current_version_id if not supplied
            mem_agent = await self.repo.get_agent(m.agent_id, workspace_id)
            if not mem_agent:
                raise AgentNotFoundError(m.agent_id)
            ver_id = m.agent_version_id or mem_agent.current_version_id
            if not ver_id:
                raise AgentVersionNotFoundError(m.agent_id)

            await self.repo.add_team_member(
                team_version_id=version.id,
                agent_id=m.agent_id,
                agent_version_id=ver_id,
                role=m.role.value,
                capabilities=m.capabilities,
                responsibilities=m.responsibilities,
                limits=m.limits,
            )

        team.current_version_id = version.id
        await self.session.commit()

        await self.event_publisher.emit_team_event(
            event_type=SystemEventType.AGENT_TEAM_CREATED.value,
            workspace_id=workspace_id,
            team_id=team.id,
            payload={"name": team.name, "members_count": len(req.members)},
            project_id=team.project_id,
            actor_id=user_id,
        )

        return team, version

    async def get_team(self, team_id: str, workspace_id: str) -> AgentTeam:
        team = await self.repo.get_team(team_id, workspace_id)
        if not team:
            raise AgentTeamNotFoundError(team_id)
        return team

    async def list_teams(
        self,
        workspace_id: str,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[AgentTeam], int]:
        return await self.repo.list_teams(workspace_id, project_id, status, limit, offset)

    async def update_team(self, team_id: str, workspace_id: str, updates: AgentTeamUpdate) -> AgentTeam:
        team = await self.get_team(team_id, workspace_id)
        for k, v in updates.model_dump(exclude_unset=True).items():
            setattr(team, k, v)
        team.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        return team

    async def activate_team(self, team_id: str, workspace_id: str, user_id: str) -> AgentTeam:
        team = await self.get_team(team_id, workspace_id)
        validate_lifecycle_transition(team.status, AgentTeamStatus.ACTIVE.value, has_published_version=bool(team.current_version_id))
        team.status = AgentTeamStatus.ACTIVE.value
        team.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        return team

    async def pause_team(self, team_id: str, workspace_id: str, user_id: str) -> AgentTeam:
        team = await self.get_team(team_id, workspace_id)
        validate_lifecycle_transition(team.status, AgentTeamStatus.PAUSED.value)
        team.status = AgentTeamStatus.PAUSED.value
        team.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        return team

    async def run_team(
        self,
        team_id: str,
        workspace_id: str,
        user_id: str,
        req: AgentTeamRunCreate,
    ) -> AgentTeamRun:
        return await self.team_coordinator.execute_team_run(
            team_id=team_id,
            workspace_id=workspace_id,
            user_id=user_id,
            input_data=req.input,
            team_version_id=req.team_version_id,
            project_id=req.project_id,
            objective_override=req.objective_override,
            dry_run=req.dry_run,
        )

    async def get_team_run(self, run_id: str, workspace_id: str) -> AgentTeamRun:
        run = await self.repo.get_team_run(run_id, workspace_id)
        if not run:
            raise AgentTeamRunNotFoundError(run_id)
        return run

    async def list_team_runs(
        self,
        workspace_id: str,
        team_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[AgentTeamRun], int]:
        return await self.repo.list_team_runs(workspace_id, team_id, limit, offset)

    async def resolve_conflict(
        self,
        conflict_id: str,
        status: ConflictStatus,
        resolution: str,
        resolved_by: str,
    ) -> AgentConflict:
        conflict = await self.repo.get_conflict(conflict_id)
        if not conflict:
            raise AgentNotFoundError(f"Conflict '{conflict_id}' not found.")
        conflict.status = status.value
        conflict.resolution = resolution
        conflict.resolved_by = resolved_by
        conflict.resolved_at = datetime.now(timezone.utc)
        await self.session.commit()
        return conflict

    # =========================================================================
    # PREVIEW
    # =========================================================================

    async def preview_effective_policy(
        self,
        agent_id: str,
        workspace_id: str,
        version_id: Optional[str] = None,
    ) -> EffectivePolicyPreview:
        agent = await self.get_agent(agent_id, workspace_id)
        target_version_id = version_id or agent.current_version_id
        if not target_version_id:
            raise AgentVersionNotFoundError(agent_id)

        version = await self.repo.get_version(target_version_id)
        if not version:
            raise AgentVersionNotFoundError(agent_id, version_id=target_version_id)

        return PolicyResolver.generate_preview(
            agent_id=agent.id,
            version_id=version.id,
            capability_policy=version.capability_policy or [],
            model_policy=version.model_policy or {},
            memory_policy=version.memory_policy or {},
            knowledge_policy=version.knowledge_policy or {},
            execution_policy=version.execution_policy or {},
            approval_policy=version.approval_policy or {},
            budget_policy=version.budget_policy or {},
        )
