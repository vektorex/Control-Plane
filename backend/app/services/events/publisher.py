"""
EventPublisher for Step 26: Unified Event Bus.
Atomically validates, sanitizes, persists, and dispatches system events.
"""
from typing import Any, Dict, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.events.consumer import consumer_registry
from backend.app.services.events.dispatcher import EventDispatcher
from backend.app.services.events.policies import EventPolicyEngine
from backend.app.services.events.repository import EventRepository
from backend.app.services.events.sanitizer import EventSanitizer
from backend.app.services.events.schemas import EventContract, EventPublishRequest


class EventPublisher:
    """
    Primary interface for publishing system events.
    Guarantees:
    1. Schema validation & actor validation
    2. Payload & metadata secret scrubbing
    3. Transactional persistence in PostgreSQL event store BEFORE consumer dispatch
    4. Monotonic sequence numbering per aggregate
    5. Deduplication via idempotency keys
    6. Consumer routing with failure isolation
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = EventRepository(session)

    async def publish(self, request: EventPublishRequest) -> EventContract:
        # 1. Validate actor type
        actor_type = EventPolicyEngine.validate_actor_type(request.actor_type)

        # 2. Sanitize payload and metadata
        clean_payload = EventSanitizer.validate_and_sanitize_payload(request.payload)
        clean_metadata = EventSanitizer.validate_and_sanitize_metadata(request.metadata or {})

        # 3. Transactionally persist into Event Store
        event, is_new = await self.repository.create_event(
            workspace_id=request.workspace_id,
            event_type=request.event_type,
            aggregate_type=request.aggregate_type,
            aggregate_id=request.aggregate_id,
            payload=clean_payload,
            metadata=clean_metadata,
            project_id=request.project_id,
            actor_type=actor_type,
            actor_id=request.actor_id,
            parent_event_id=request.parent_event_id,
            correlation_id=request.correlation_id,
            causation_id=request.causation_id,
            idempotency_key=request.idempotency_key,
        )

        contract = EventSanitizer.to_contract(event)

        # If duplicate detected, do not re-dispatch to consumers
        if not is_new:
            logger.info(f"[EventPublisher] Duplicate event detected for idempotency key '{request.idempotency_key}'. Returning existing.")
            return contract

        # 4. Create delivery tracking for interested consumers
        matching_consumers = consumer_registry.get_matching_consumers(request.event_type)
        if matching_consumers:
            consumer_names = [c.consumer_name for c in matching_consumers]
            await self.repository.create_deliveries_for_consumers(event.id, consumer_names)

        # 5. Dispatch to consumers (failure-isolated)
        await EventDispatcher.dispatch(contract, self.repository)

        logger.info(
            f"[EventPublisher] Published event {contract.id} ({contract.type}) for aggregate "
            f"{contract.aggregate.type}:{contract.aggregate.id} [seq={contract.sequence_number}]"
        )
        return contract

    async def publish_event(
        self,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        workspace_id: UUID,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        project_id: Optional[UUID] = None,
        actor_type: str = "system",
        actor_id: Optional[str] = None,
        parent_event_id: Optional[UUID] = None,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> EventContract:
        req = EventPublishRequest(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            workspace_id=workspace_id,
            project_id=project_id,
            actor_type=actor_type,
            actor_id=actor_id,
            payload=payload,
            metadata=metadata or {},
            parent_event_id=parent_event_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
            idempotency_key=idempotency_key,
        )
        return await self.publish(req)
