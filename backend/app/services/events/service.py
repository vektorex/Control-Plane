"""
EventBus service for asynchronous and synchronous event routing.
"""
from typing import Any, Callable, Dict, List, Optional
import logging

logger = logging.getLogger("events.service")


class EventBus:
    """
    In-memory and unified EventBus interface supporting publishing events by topic
    and dispatching to registered subscribers.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[str, Any], None]]] = {}

    def subscribe(self, topic: str, handler: Callable[[str, Any], None]) -> None:
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(handler)

    def publish(self, topic: str, payload: Any = None) -> None:
        logger.debug(f"[EventBus] Publishing event on topic: {topic}")
        handlers = self._subscribers.get(topic, [])
        wildcard_handlers = self._subscribers.get("*", [])
        for handler in handlers + wildcard_handlers:
            try:
                handler(topic, payload)
            except Exception as e:
                logger.error(f"[EventBus] Error executing subscriber for topic {topic}: {e}", exc_info=True)


default_event_bus = EventBus()

