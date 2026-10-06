"""
Outcome Event Emitter for Step 43:
AI Outcome Intelligence & Work Impact Layer.
Integrates with Step 26 Event Bus to emit structured, auditable domain events.
"""
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.events.constants import ActorType
from backend.app.services.events.publisher import EventPublisher
from backend.app.services.events.schemas import EventContract, EventPublishRequest


class OutcomeEventPublisher:
    """Helper for emitting outcome and objective lifecycle events to the unified Event Bus."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.publisher = EventPublisher(session)

    async def emit_outcome_event(
        self,
        event_type: str,
        workspace_id: str,
        outcome_id: str,
        payload: Dict[str, Any],
        project_id: Optional[str] = None,
        actor_id: str = "system",
        actor_type: str = ActorType.SYSTEM.value,
        correlation_id: Optional[str] = None,
    ) -> Optional[EventContract]:
        """Publishes an outcome lifecycle or evidence/measurement event."""
        try:
            req = EventPublishRequest(
                event_type=event_type,
                aggregate_type="outcome",
                aggregate_id=outcome_id,
                workspace_id=workspace_id,
                project_id=project_id,
                actor_type=actor_type,
                actor_id=actor_id,
                payload=payload,
                correlation_id=correlation_id,
            )
            return await self.publisher.publish(req)
        except Exception as e:
            logger.warning(f"Failed to publish outcome event '{event_type}': {e}")
            return None

    async def emit_objective_event(
        self,
        event_type: str,
        workspace_id: str,
        objective_id: str,
        payload: Dict[str, Any],
        project_id: Optional[str] = None,
        actor_id: str = "system",
        actor_type: str = ActorType.SYSTEM.value,
        correlation_id: Optional[str] = None,
    ) -> Optional[EventContract]:
        """Publishes an objective or milestone event."""
        try:
            req = EventPublishRequest(
                event_type=event_type,
                aggregate_type="objective",
                aggregate_id=objective_id,
                workspace_id=workspace_id,
                project_id=project_id,
                actor_type=actor_type,
                actor_id=actor_id,
                payload=payload,
                correlation_id=correlation_id,
            )
            return await self.publisher.publish(req)
        except Exception as e:
            logger.warning(f"Failed to publish objective event '{event_type}': {e}")
            return None

    async def emit_decision_event(
        self,
        event_type: str,
        workspace_id: str,
        decision_id: str,
        payload: Dict[str, Any],
        project_id: Optional[str] = None,
        actor_id: str = "system",
        actor_type: str = ActorType.SYSTEM.value,
        correlation_id: Optional[str] = None,
    ) -> Optional[EventContract]:
        """Publishes a work decision event."""
        try:
            req = EventPublishRequest(
                event_type=event_type,
                aggregate_type="decision",
                aggregate_id=decision_id,
                workspace_id=workspace_id,
                project_id=project_id,
                actor_type=actor_type,
                actor_id=actor_id,
                payload=payload,
                correlation_id=correlation_id,
            )
            return await self.publisher.publish(req)
        except Exception as e:
            logger.warning(f"Failed to publish decision event '{event_type}': {e}")
            return None
