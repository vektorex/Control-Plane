"""
Planning Event Emitter for Step 44:
AI Work Planning, Capacity & Resource Optimization Layer.
Integrates with Step 26 Event Bus to emit structured, auditable domain events.
"""
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.events.constants import ActorType
from backend.app.services.events.publisher import EventPublisher
from backend.app.services.events.schemas import EventContract, EventPublishRequest


class PlanningEventPublisher:
    """Helper for emitting planning and capacity lifecycle events to the unified Event Bus."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.publisher = EventPublisher(session)

    async def emit_plan_event(
        self,
        event_type: str,
        workspace_id: str,
        plan_id: str,
        payload: Dict[str, Any],
        project_id: Optional[str] = None,
        actor_id: str = "system",
        actor_type: str = ActorType.SYSTEM.value,
        correlation_id: Optional[str] = None,
    ) -> Optional[EventContract]:
        """Publishes a work plan lifecycle event."""
        try:
            req = EventPublishRequest(
                event_type=event_type,
                aggregate_type="work_plan",
                aggregate_id=plan_id,
                workspace_id=workspace_id,
                project_id=project_id,
                actor_type=actor_type,
                actor_id=actor_id,
                payload=payload,
                correlation_id=correlation_id,
            )
            return await self.publisher.publish(req)
        except Exception as e:
            logger.warning(f"Failed to publish planning event '{event_type}': {e}")
            return None

    async def emit_capacity_event(
        self,
        event_type: str,
        workspace_id: str,
        resource_id: str,
        payload: Dict[str, Any],
        project_id: Optional[str] = None,
        actor_id: str = "system",
        actor_type: str = ActorType.SYSTEM.value,
        correlation_id: Optional[str] = None,
    ) -> Optional[EventContract]:
        """Publishes a capacity or reservation event."""
        try:
            req = EventPublishRequest(
                event_type=event_type,
                aggregate_type="work_resource",
                aggregate_id=resource_id,
                workspace_id=workspace_id,
                project_id=project_id,
                actor_type=actor_type,
                actor_id=actor_id,
                payload=payload,
                correlation_id=correlation_id,
            )
            return await self.publisher.publish(req)
        except Exception as e:
            logger.warning(f"Failed to publish capacity event '{event_type}': {e}")
            return None
