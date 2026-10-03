"""
Agent Delegation Engine for Step 40.
Enforces bounded delegation depth, cycle detection, budget subsetting, and capability inheritance.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.agents.errors import (
    AgentNotFoundError,
    AgentVersionNotFoundError,
    CapabilityNotGrantedError,
    DelegationDepthExceededError,
)
from backend.app.services.agents.models import Agent, AgentDelegation, AgentRun, AgentVersion
from backend.app.services.agents.validators import DEFAULT_MAX_DELEGATION_DEPTH, DelegationSafetyValidator


class AgentDelegationEngine:
    """Coordinates and validates sub-agent delegations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_delegation(
        self,
        parent_run: AgentRun,
        parent_agent: Agent,
        parent_version: AgentVersion,
        child_agent_id: str,
        reason: str,
        task_snapshot: Dict[str, Any],
        requested_budget: float,
        child_agent_version_id: Optional[str] = None,
        requested_capabilities: Optional[List[str]] = None,
        max_depth: int = DEFAULT_MAX_DELEGATION_DEPTH,
    ) -> AgentDelegation:
        """
        Validates and records a safe delegation request from parent_run to child_agent.
        """
        # 1. Resolve ancestor chain for cycle detection
        ancestor_chain = await self._build_ancestor_chain(parent_run)
        DelegationSafetyValidator.check_cycle(ancestor_chain, child_agent_id)

        # 2. Check depth
        current_depth = len(ancestor_chain)
        DelegationSafetyValidator.check_depth(current_depth, max_depth)

        # 3. Resolve child agent & version within same workspace (tenant boundary)
        child_agent = await self.session.get(Agent, child_agent_id)
        if not child_agent or child_agent.workspace_id != parent_run.workspace_id:
            raise AgentNotFoundError(child_agent_id)

        target_version_id = child_agent_version_id or child_agent.current_version_id
        if not target_version_id:
            raise AgentVersionNotFoundError(child_agent_id)

        child_version = await self.session.get(AgentVersion, target_version_id)
        if not child_version or child_version.agent_id != child_agent.id:
            raise AgentVersionNotFoundError(child_agent_id, version_id=target_version_id)

        # 4. Check budget inheritance: child cannot exceed parent's available budget
        parent_budget_limit = float(parent_version.budget_policy.get("max_budget_per_run", 5.0))
        remaining_parent_budget = max(0.0, parent_budget_limit - parent_run.cost)
        allocated_budget = min(requested_budget, remaining_parent_budget)
        DelegationSafetyValidator.check_budget_inheritance(requested_budget, remaining_parent_budget)

        # 5. Compute inherited capabilities: child can NEVER exceed parent capabilities
        parent_caps = parent_version.capability_policy or []
        allowed_caps = DelegationSafetyValidator.compute_inherited_capabilities(
            parent_capabilities=parent_caps,
            requested_capabilities=requested_capabilities or child_version.capability_policy,
        )

        # 6. Create AgentDelegation record
        delegation = AgentDelegation(
            parent_agent_run_id=parent_run.id,
            parent_agent_id=parent_agent.id,
            child_agent_id=child_agent.id,
            child_agent_version_id=child_version.id,
            reason=reason,
            task_snapshot=task_snapshot,
            allowed_capabilities=allowed_caps,
            budget_allocation=allocated_budget,
            depth=current_depth,
            status="pending",
        )
        self.session.add(delegation)

        # Increment parent delegation counter
        parent_run.delegations_count += 1
        await self.session.flush()

        return delegation

    async def _build_ancestor_chain(self, run: AgentRun) -> List[str]:
        """Traverses parent run hierarchy to build list of ancestor agent IDs."""
        chain = [run.agent_id]
        curr = run
        while curr.parent_agent_run_id:
            parent = await self.session.get(AgentRun, curr.parent_agent_run_id)
            if not parent:
                break
            chain.append(parent.agent_id)
            curr = parent
            if len(chain) > 10:  # Circuit breaker
                break
        return list(reversed(chain))
