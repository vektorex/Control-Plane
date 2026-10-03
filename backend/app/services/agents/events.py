"""
Agent Event Emitter for Step 40.
Integrates with Step 26 Event Bus to emit structured, sanitized events for agent lifecycle,
runs, delegations, teams, and conflicts.
"""
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.events.constants import ActorType, AggregateType, SystemEventType
from backend.app.services.events.publisher import EventPublisher
from backend.app.services.events.schemas import EventContract, EventPublishRequest


class AgentEventPublisher:
    """Helper for emitting standardized Agent and Agent Team events to the Event Bus."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.publisher = EventPublisher(session)

    async def emit_agent_event(
        self,
        event_type: str,
        workspace_id: str,
        agent_id: str,
        payload: Dict[str, Any],
        project_id: Optional[str] = None,
        actor_id: str = "system",
        actor_type: str = ActorType.SYSTEM.value,
        correlation_id: Optional[str] = None,
    ) -> Optional[EventContract]:
        """Publishes an agent aggregate event."""
        try:
            req = EventPublishRequest(
                event_type=event_type,
                aggregate_type=AggregateType.AGENT.value,
                aggregate_id=agent_id,
                workspace_id=workspace_id,
                project_id=project_id,
                actor_type=actor_type,
                actor_id=actor_id,
                payload=payload,
                correlation_id=correlation_id,
            )
            return await self.publisher.publish(req)
        except Exception as e:
            logger.warning(f"Failed to publish agent event '{event_type}': {e}")
            return None

    async def emit_agent_run_event(
        self,
        event_type: str,
        workspace_id: str,
        run_id: str,
        agent_id: str,
        payload: Dict[str, Any],
        project_id: Optional[str] = None,
        actor_id: str = "system",
        actor_type: str = ActorType.AGENT.value,
        correlation_id: Optional[str] = None,
    ) -> Optional[EventContract]:
        """Publishes an agent run event."""
        try:
            meta = {"agent_id": agent_id}
            req = EventPublishRequest(
                event_type=event_type,
                aggregate_type=AggregateType.AGENT_RUN.value,
                aggregate_id=run_id,
                workspace_id=workspace_id,
                project_id=project_id,
                actor_type=actor_type,
                actor_id=actor_id,
                payload=payload,
                metadata=meta,
                correlation_id=correlation_id,
            )
            return await self.publisher.publish(req)
        except Exception as e:
            logger.warning(f"Failed to publish agent run event '{event_type}': {e}")
            return None

    async def emit_team_event(
        self,
        event_type: str,
        workspace_id: str,
        team_id: str,
        payload: Dict[str, Any],
        project_id: Optional[str] = None,
        actor_id: str = "system",
        actor_type: str = ActorType.SYSTEM.value,
        correlation_id: Optional[str] = None,
    ) -> Optional[EventContract]:
        """Publishes an agent team aggregate event."""
        try:
            req = EventPublishRequest(
                event_type=event_type,
                aggregate_type=AggregateType.AGENT_TEAM.value,
                aggregate_id=team_id,
                workspace_id=workspace_id,
                project_id=project_id,
                actor_type=actor_type,
                actor_id=actor_id,
                payload=payload,
                correlation_id=correlation_id,
            )
            return await self.publisher.publish(req)
        except Exception as e:
            logger.warning(f"Failed to publish agent team event '{event_type}': {e}")
            return None

    async def emit_team_run_event(
        self,
        event_type: str,
        workspace_id: str,
        team_run_id: str,
        team_id: str,
        payload: Dict[str, Any],
        project_id: Optional[str] = None,
        actor_id: str = "system",
        actor_type: str = ActorType.AGENT.value,
        correlation_id: Optional[str] = None,
    ) -> Optional[EventContract]:
        """Publishes an agent team run event."""
        try:
            meta = {"team_id": team_id}
            req = EventPublishRequest(
                event_type=event_type,
                aggregate_type=AggregateType.AGENT_TEAM_RUN.value,
                aggregate_id=team_run_id,
                workspace_id=workspace_id,
                project_id=project_id,
                actor_type=actor_type,
                actor_id=actor_id,
                payload=payload,
                metadata=meta,
                correlation_id=correlation_id,
            )
            return await self.publisher.publish(req)
        except Exception as e:
            logger.warning(f"Failed to publish agent team run event '{event_type}': {e}")
            return None
