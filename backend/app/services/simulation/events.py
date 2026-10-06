"""
Simulation Event Emitter for Step 41: AI Agent Simulation.
Integrates with Step 26 Event Bus to emit structured, sanitized simulation lifecycle and telemetry events.
"""
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.events.constants import ActorType, AggregateType, SystemEventType
from backend.app.services.events.publisher import EventPublisher
from backend.app.services.events.schemas import EventContract, EventPublishRequest


class SimulationEventPublisher:
    """Helper for emitting simulation events to the unified Event Bus."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.publisher = EventPublisher(session)

    async def emit_simulation_event(
        self,
        event_type: str,
        workspace_id: str,
        simulation_id: str,
        payload: Dict[str, Any],
        project_id: Optional[str] = None,
        actor_id: str = "system",
        actor_type: str = ActorType.SYSTEM.value,
        correlation_id: Optional[str] = None,
    ) -> Optional[EventContract]:
        """Publishes a simulation lifecycle event."""
        try:
            req = EventPublishRequest(
                event_type=event_type,
                aggregate_type="simulation",
                aggregate_id=simulation_id,
                workspace_id=workspace_id,
                project_id=project_id,
                actor_type=actor_type,
                actor_id=actor_id,
                payload=payload,
                correlation_id=correlation_id,
            )
            return await self.publisher.publish(req)
        except Exception as e:
            logger.warning(f"Failed to publish simulation event '{event_type}': {e}")
            return None

    async def emit_run_event(
        self,
        event_type: str,
        workspace_id: str,
        run_id: str,
        simulation_id: str,
        payload: Dict[str, Any],
        project_id: Optional[str] = None,
        actor_id: str = "simulation_runner",
        actor_type: str = ActorType.SYSTEM.value,
        correlation_id: Optional[str] = None,
    ) -> Optional[EventContract]:
        """Publishes an event during a simulation run."""
        try:
            req = EventPublishRequest(
                event_type=event_type,
                aggregate_type="simulation_run",
                aggregate_id=run_id,
                workspace_id=workspace_id,
                project_id=project_id,
                actor_type=actor_type,
                actor_id=actor_id,
                payload={**payload, "simulation_id": simulation_id},
                correlation_id=correlation_id,
            )
            return await self.publisher.publish(req)
        except Exception as e:
            logger.warning(f"Failed to publish simulation run event '{event_type}': {e}")
            return None
