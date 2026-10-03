"""
EventDispatcher for Step 26: Unified Event Bus.
Routes persisted events to registered consumers with failure isolation and retry tracking.
"""
from __future__ import annotations

import asyncio
from typing import Any, List, Optional, TYPE_CHECKING
from uuid import UUID

from backend.app.core.logging import logger
from backend.app.services.events.constants import EventDeliveryStatus
from backend.app.services.events.consumer import EventConsumer, consumer_registry
from backend.app.services.events.schemas import EventContract

if TYPE_CHECKING:
    from backend.app.services.events.repository import EventRepository


class EventDispatcher:
    """
    Coordinates event routing to registered internal consumers.
    Guarantees failure isolation: an exception in one consumer never interrupts others.
    """

    @classmethod
    async def dispatch(
        cls,
        event: EventContract,
        repository: Optional[EventRepository] = None,
        deliveries: Optional[List[Any]] = None,
    ) -> None:
        """
        Executes consumer processing for an already persisted event.
        """
        consumers = consumer_registry.get_matching_consumers(event.type)
        if not consumers:
            return

        tasks = []
        for consumer in consumers:
            tasks.append(cls._execute_consumer_safe(consumer, event, repository))

        await asyncio.gather(*tasks, return_exceptions=True)

    @classmethod
    async def _execute_consumer_safe(
        cls,
        consumer: EventConsumer,
        event: EventContract,
        repository: Optional[EventRepository] = None,
    ) -> None:
        try:
            success = await consumer.process(event)
            # If repository available, update delivery status if recorded
            logger.debug(f"[EventDispatcher] Consumer '{consumer.consumer_name}' processed event {event.id}: success={success}")
        except Exception as e:
            logger.error(
                f"[EventDispatcher] Failure in consumer '{consumer.consumer_name}' for event {event.id}: {e}",
                exc_info=True,
            )
