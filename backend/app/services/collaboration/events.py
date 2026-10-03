"""
Real-time Collaboration Event Publisher for Step 39: Collaboration.
Integrates directly with Step 26 Unified Event Bus and SSE delivery layer.
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.events.constants import ActorType, AggregateType
from backend.app.services.events.publisher import EventPublisher
from backend.app.services.events.schemas import EventPublishRequest

logger = logging.getLogger(__name__)


class CollaborationEventBroadcaster:
    """Publishes tenant-scoped collaboration events to the Unified Event Bus."""

    def __init__(self, session: AsyncSession):
        self.db = session
        self.publisher = EventPublisher(session)

    async def emit_collaboration_event(
        self,
        event_type: str,
        organization_id: str,
        workspace_id: str,
        session_id: str,
        actor_id: Optional[str] = None,
        actor_type: str = "user",
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Publishes a collaboration event with sanitized payload.
        Ensures tenant boundaries (organization_id and workspace_id) are attached.
        """
        try:
            ws_uuid = UUID(workspace_id) if isinstance(workspace_id, str) else workspace_id
            act_uuid = UUID(actor_id) if actor_id and isinstance(actor_id, str) else None

            meta = dict(metadata or {})
            meta["organization_id"] = organization_id
            meta["session_id"] = session_id
            meta["timestamp"] = datetime.now(timezone.utc).isoformat()

            request = EventPublishRequest(
                workspace_id=ws_uuid,
                event_type=event_type,
                aggregate_type=AggregateType.COLLABORATION.value if hasattr(AggregateType, "COLLABORATION") else "collaboration",
                aggregate_id=UUID(session_id) if isinstance(session_id, str) else session_id,
                payload=payload or {},
                metadata=meta,
                actor_type=ActorType.USER.value if actor_type == "user" else ActorType.SYSTEM.value,
                actor_id=act_uuid,
                correlation_id=UUID(correlation_id) if correlation_id and isinstance(correlation_id, str) else None,
            )
            await self.publisher.publish(request)
        except Exception as e:
            logger.warning("Failed to publish collaboration event '%s': %s", event_type, e)
