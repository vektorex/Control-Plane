"""
Event consumer abstraction and trusted internal consumers for Step 26.
Isolates consumer failures and routes events to Notifications, Observability,
Audit, and Real-Time SSE streaming.
"""
import abc
from typing import Dict, List, Optional
from uuid import UUID

from backend.app.core.logging import logger
from backend.app.services.events.constants import AUDITABLE_EVENTS
from backend.app.services.events.filters import EventFilterValidator
from backend.app.services.events.schemas import EventContract


class EventConsumer(abc.ABC):
    """Base interface for all trusted internal event consumers."""

    @property
    @abc.abstractmethod
    def consumer_name(self) -> str:
        """Unique identifier for this consumer."""
        pass

    @property
    @abc.abstractmethod
    def supported_event_types(self) -> List[str]:
        """List of exact types or wildcards (e.g. ['workflow.*', 'job.failed'])."""
        pass

    def can_handle(self, event_type: str) -> bool:
        """Checks whether this consumer is interested in the event type."""
        for pattern in self.supported_event_types:
            if EventFilterValidator.matches(event_type, pattern):
                return True
        return False

    @abc.abstractmethod
    async def process(self, event: EventContract) -> bool:
        """
        Executes consumer logic. Returns True on success, False/raises on retryable failure.
        """
        pass


class NotificationEventConsumer(EventConsumer):
    """
    Consumes system events and routes them to the Step 25 NotificationService.
    Decouples domain engines from direct notification calls.
    """

    @property
    def consumer_name(self) -> str:
        return "notification_consumer"

    @property
    def supported_event_types(self) -> List[str]:
        return [
            "workflow.completed",
            "workflow.failed",
            "workflow.waiting_for_approval",
            "trigger.completed",
            "trigger.failed",
            "job.completed",
            "job.failed",
            "job.retrying",
            "document.processing_completed",
            "document.processing_failed",
            "evaluation.completed",
            "evaluation.regression_detected",
            "replay.completed",
            "replay.failed",
            "connector.completed",
            "connector.failed",
            "system.warning",
        ]

    async def process(self, event: EventContract) -> bool:
        try:
            from backend.app.db.database import get_session
            from backend.app.services.notifications.service import NotificationService
            from backend.app.services.notifications.registry import notification_registry
            from backend.app.services.notifications.constants import NotificationSeverity

            # Check if this event already generated a notification
            if event.metadata and event.metadata.get("notification_id"):
                return True

            # Check if this event is recognized by notification registry
            meta = notification_registry.get(event.type)
            if not meta:
                return True  # No notification configured for this event

            title = event.data.get("title") or meta.default_title_template
            body = event.data.get("body") or meta.default_body_template
            severity = event.data.get("severity") or meta.default_severity

            async for session in get_session():
                service = NotificationService(session)
                user_id = None
                if event.actor.type == "user" and event.actor.id:
                    try:
                        user_id = UUID(event.actor.id)
                    except ValueError:
                        user_id = None

                await service.create_notification(
                    workspace_id=UUID(event.workspace_id),
                    event_type=event.type,
                    title=title,
                    body=body,
                    severity=severity,
                    source_type=event.aggregate.type,
                    source_id=event.aggregate.id,
                    project_id=UUID(event.project_id) if event.project_id else None,
                    user_id=user_id,
                    metadata=event.data,
                )
                await session.commit()
                break

            return True
        except Exception as e:
            logger.error(f"[NotificationEventConsumer] Failed processing event {event.id}: {e}", exc_info=True)
            raise e


class ObservabilityEventConsumer(EventConsumer):
    """
    Connects event metadata to Step 14 observability.
    Captures event_id, event_type, aggregate, correlation_id, causation_id, timing.
    """

    @property
    def consumer_name(self) -> str:
        return "observability_consumer"

    @property
    def supported_event_types(self) -> List[str]:
        return ["*"]

    async def process(self, event: EventContract) -> bool:
        logger.info(
            f"[ObservabilityEventConsumer] event_id={event.id} type={event.type} "
            f"aggregate={event.aggregate.type}:{event.aggregate.id} "
            f"correlation_id={event.correlation_id} causation_id={event.causation_id} "
            f"workspace_id={event.workspace_id}"
        )
        return True


class AuditEventConsumer(EventConsumer):
    """
    Audits important user and system actions (approvals, triggers, security alerts).
    Never logs sensitive payloads.
    """

    @property
    def consumer_name(self) -> str:
        return "audit_consumer"

    @property
    def supported_event_types(self) -> List[str]:
        return list(AUDITABLE_EVENTS)

    async def process(self, event: EventContract) -> bool:
        logger.info(
            f"[AuditEventConsumer] AUDIT_RECORD: event_id={event.id} action={event.type} "
            f"actor={event.actor.type}:{event.actor.id} aggregate={event.aggregate.type}:{event.aggregate.id} "
            f"workspace_id={event.workspace_id} timestamp={event.timestamp}"
        )
        return True


class RealtimeEventConsumer(EventConsumer):
    """
    Pushes events to active in-process SSE client streams.
    """

    @property
    def consumer_name(self) -> str:
        return "realtime_sse_consumer"

    @property
    def supported_event_types(self) -> List[str]:
        return ["*"]

    async def process(self, event: EventContract) -> bool:
        from backend.app.services.events.stream import sse_connection_manager
        await sse_connection_manager.broadcast_event(event)
        return True


class EventConsumerRegistry:
    """
    Registry for trusted internal event consumers.
    Strictly prohibits registering arbitrary dynamic handlers from user/model inputs.
    """

    def __init__(self):
        self._consumers: Dict[str, EventConsumer] = {}
        self._register_defaults()

    def register(self, consumer: EventConsumer) -> None:
        self._consumers[consumer.consumer_name] = consumer

    def get_matching_consumers(self, event_type: str) -> List[EventConsumer]:
        return [c for c in self._consumers.values() if c.can_handle(event_type)]

    def get_consumer(self, consumer_name: str) -> Optional[EventConsumer]:
        return self._consumers.get(consumer_name)

    def list_all(self) -> List[EventConsumer]:
        return list(self._consumers.values())

    def _register_defaults(self):
        self.register(NotificationEventConsumer())
        self.register(ObservabilityEventConsumer())
        self.register(AuditEventConsumer())
        self.register(RealtimeEventConsumer())


# Global consumer registry singleton
consumer_registry = EventConsumerRegistry()
