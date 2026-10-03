"""
Agent Registry for Step 40.
Resolves immutable agent version configurations, validates scopes, and ensures runtime safety.
Never loads arbitrary mutable configurations during active execution.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.agents.capabilities import validate_capabilities
from backend.app.services.agents.errors import (
    AgentLifecycleError,
    AgentNotFoundError,
    AgentVersionNotFoundError,
)
from backend.app.services.agents.models import Agent, AgentVersion
from backend.app.services.agents.policies import PolicyResolver
from backend.app.services.agents.schemas import AgentStatus


@dataclass(frozen=True)
class ResolvedAgentConfig:
    """Immutable runtime configuration container resolved by AgentRegistry."""

    agent_id: str
    version_id: str
    version_number: int
    workspace_id: str
    project_id: Optional[str]
    name: str
    slug: str
    purpose: str
    instructions: str
    capabilities: List[str]
    model_policy: Dict[str, Any]
    memory_policy: Dict[str, Any]
    knowledge_policy: Dict[str, Any]
    execution_policy: Dict[str, Any]
    evaluation_policy: Dict[str, Any]
    approval_policy: Dict[str, Any]
    budget_policy: Dict[str, Any]
    configuration: Dict[str, Any]


class AgentRegistry:
    """Provides validated, tenant-scoped resolution of immutable Agent versions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def resolve_agent_for_execution(
        self,
        agent_id: str,
        workspace_id: str,
        version_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> ResolvedAgentConfig:
        """
        Resolves the agent, confirms status is active, resolves the immutable version,
        and constructs the ResolvedAgentConfig.
        """
        # 1. Fetch Agent within workspace boundary
        agent = await self.session.get(Agent, agent_id)
        if not agent or agent.workspace_id != workspace_id:
            raise AgentNotFoundError(agent_id)

        # 2. Check lifecycle status: must be active for execution
        if agent.status != AgentStatus.ACTIVE.value:
            raise AgentLifecycleError(
                current_status=agent.status,
                target_status="executing",
                reason=f"Agent '{agent_id}' is '{agent.status}'. Only active agents can execute tasks.",
            )

        # 3. Resolve version (either specified or current_version_id)
        target_version_id = version_id or agent.current_version_id
        if not target_version_id:
            raise AgentVersionNotFoundError(agent_id)

        version = await self.session.get(AgentVersion, target_version_id)
        if not version or version.agent_id != agent.id:
            raise AgentVersionNotFoundError(agent_id, version_id=target_version_id)

        # 4. Resolve effective policy
        effective = PolicyResolver.resolve_effective_policy(
            agent_id=agent.id,
            version_id=version.id,
            capability_policy=version.capability_policy or [],
            model_policy=version.model_policy or {},
            memory_policy=version.memory_policy or {},
            knowledge_policy=version.knowledge_policy or {},
            execution_policy=version.execution_policy or {},
            approval_policy=version.approval_policy or {},
            budget_policy=version.budget_policy or {},
            evaluation_policy=version.evaluation_policy or {},
        )

        return ResolvedAgentConfig(
            agent_id=agent.id,
            version_id=version.id,
            version_number=version.version,
            workspace_id=agent.workspace_id,
            project_id=project_id or agent.project_id,
            name=agent.name,
            slug=agent.slug,
            purpose=agent.purpose,
            instructions=version.instructions,
            capabilities=effective["capabilities"],
            model_policy=effective["model_policy"],
            memory_policy=effective["memory_policy"],
            knowledge_policy=effective["knowledge_policy"],
            execution_policy=effective["execution_policy"],
            evaluation_policy=effective["evaluation_policy"],
            approval_policy=effective["approval_policy"],
            budget_policy=effective["budget_policy"],
            configuration=version.configuration or {},
        )
