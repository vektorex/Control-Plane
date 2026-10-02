"""
Step 26: Unified Event Bus and Real-Time Execution Updates.
"""
from backend.app.services.events.constants import (
    ActorType,
    AggregateType,
    EventDeliveryStatus,
    EventVisibility,
    SystemEventType,
)
from backend.app.services.events.consumer import (
    EventConsumer,
    EventConsumerRegistry,
    NotificationEventConsumer,
    ObservabilityEventConsumer,
    AuditEventConsumer,
    RealtimeEventConsumer,
    consumer_registry,
)
from backend.app.services.events.dispatcher import EventDispatcher
from backend.app.services.events.errors import (
    ConsumerExecutionError,
    EventAuthorizationError,
    EventDuplicateError,
    EventError,
    EventNotFoundError,
    EventPayloadTooLargeError,
    EventValidationError,
    InvalidFilterError,
    SlowClientError,
)
from backend.app.services.events.filters import EventFilterValidator
from backend.app.services.events.policies import EventPolicyEngine
from backend.app.services.events.publisher import EventPublisher
from backend.app.services.events.registry import (
    EventRegistry,
    EventTypeDefinition,
    event_registry,
)
from backend.app.services.events.repository import EventRepository
from backend.app.services.events.sanitizer import EventSanitizer
from backend.app.services.events.schemas import (
    ActorSchema,
    AggregateSchema,
    EventContract,
    EventFilterParams,
    EventPublishRequest,
    EventReplayResponse,
)
from backend.app.services.events.stream import (
    EventStreamService,
    SSEClientConnection,
    SSEConnectionManager,
    sse_connection_manager,
)

__all__ = [
    "ActorType",
    "AggregateType",
    "EventDeliveryStatus",
    "EventVisibility",
    "SystemEventType",
    "EventConsumer",
    "EventConsumerRegistry",
    "NotificationEventConsumer",
    "ObservabilityEventConsumer",
    "AuditEventConsumer",
    "RealtimeEventConsumer",
    "consumer_registry",
    "EventDispatcher",
    "EventError",
    "EventNotFoundError",
    "EventValidationError",
    "EventAuthorizationError",
    "EventPayloadTooLargeError",
    "InvalidFilterError",
    "SlowClientError",
    "ConsumerExecutionError",
    "EventDuplicateError",
    "EventFilterValidator",
    "EventPolicyEngine",
    "EventPublisher",
    "EventRegistry",
    "EventTypeDefinition",
    "event_registry",
    "EventRepository",
    "EventSanitizer",
    "ActorSchema",
    "AggregateSchema",
    "EventContract",
    "EventFilterParams",
    "EventPublishRequest",
    "EventReplayResponse",
    "EventStreamService",
    "SSEClientConnection",
    "SSEConnectionManager",
    "sse_connection_manager",
]
