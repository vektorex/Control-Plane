"""
Step 25: Notifications & External Delivery Layer.
"""
from backend.app.services.notifications.constants import (
    DEFAULT_EVENT_SEVERITY,
    MANDATORY_IN_APP_EVENTS,
    DeliveryChannelType,
    DeliveryStatus,
    NotificationEventType,
    NotificationSeverity,
    NotificationStatus,
    WEBHOOK_HEADER_EVENT,
    WEBHOOK_HEADER_SIGNATURE,
    WEBHOOK_HEADER_TIMESTAMP,
)
from backend.app.services.notifications.errors import (
    DeliveryError,
    DeliveryPermanentError,
    DeliveryTransientError,
    InvalidDestinationError,
    NotificationError,
    NotificationNotFoundError,
    NotificationRateLimitError,
    NotificationValidationError,
    SSRFSecurityError,
    WebhookEndpointNotFoundError,
)
from backend.app.services.notifications.channels import (
    DeliveryChannel,
    EmailDeliveryChannel,
    InAppDeliveryChannel,
    WebhookDeliveryChannel,
    channel_registry,
)
from backend.app.services.notifications.delivery import DeliveryDispatcher
from backend.app.services.notifications.dispatcher import (
    NotificationEvent,
    NotificationEventBus,
    event_bus,
)
from backend.app.services.notifications.policies import (
    NotificationRateLimiter,
    RecipientResolver,
    SSRFValidator,
)
from backend.app.services.notifications.preferences import NotificationPreferenceService
from backend.app.services.notifications.registry import (
    NotificationRegistry,
    notification_registry,
)
from backend.app.services.notifications.repository import NotificationRepository
from backend.app.services.notifications.retry import DeliveryRetryPolicy
from backend.app.services.notifications.sanitizer import NotificationSanitizer
from backend.app.services.notifications.schemas import (
    NotificationDeliveryResponse,
    NotificationFilterParams,
    NotificationPreferenceItem,
    NotificationPreferenceUpdate,
    NotificationResponse,
    UnreadCountResponse,
    WebhookEndpointCreate,
    WebhookEndpointResponse,
    WebhookEndpointUpdate,
    WebhookTestResponse,
)
from backend.app.services.notifications.service import NotificationService
from backend.app.services.notifications.templates import NotificationTemplateEngine

__all__ = [
    "DEFAULT_EVENT_SEVERITY",
    "MANDATORY_IN_APP_EVENTS",
    "DeliveryChannelType",
    "DeliveryStatus",
    "NotificationEventType",
    "NotificationSeverity",
    "NotificationStatus",
    "WEBHOOK_HEADER_EVENT",
    "WEBHOOK_HEADER_SIGNATURE",
    "WEBHOOK_HEADER_TIMESTAMP",
    "NotificationError",
    "NotificationNotFoundError",
    "NotificationValidationError",
    "NotificationRateLimitError",
    "WebhookEndpointNotFoundError",
    "DeliveryError",
    "DeliveryTransientError",
    "DeliveryPermanentError",
    "InvalidDestinationError",
    "SSRFSecurityError",
    "DeliveryChannel",
    "InAppDeliveryChannel",
    "WebhookDeliveryChannel",
    "EmailDeliveryChannel",
    "channel_registry",
    "DeliveryDispatcher",
    "NotificationEvent",
    "NotificationEventBus",
    "event_bus",
    "NotificationRateLimiter",
    "RecipientResolver",
    "SSRFValidator",
    "NotificationPreferenceService",
    "NotificationRegistry",
    "notification_registry",
    "NotificationRepository",
    "DeliveryRetryPolicy",
    "NotificationSanitizer",
    "NotificationTemplateEngine",
    "NotificationService",
    "NotificationResponse",
    "NotificationFilterParams",
    "UnreadCountResponse",
    "WebhookEndpointCreate",
    "WebhookEndpointUpdate",
    "WebhookEndpointResponse",
    "WebhookTestResponse",
    "NotificationPreferenceItem",
    "NotificationPreferenceUpdate",
    "NotificationDeliveryResponse",
]
