"""
Constants and Enums for Step 25: Notifications & External Delivery Layer.
"""
from enum import Enum


class NotificationSeverity(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationStatus(str, Enum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"


class DeliveryChannelType(str, Enum):
    IN_APP = "in_app"
    WEBHOOK = "webhook"
    EMAIL = "email"


class DeliveryStatus(str, Enum):
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    RETRYING = "retrying"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationEventType(str, Enum):
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_WAITING_APPROVAL = "workflow.waiting_for_approval"
    TRIGGER_COMPLETED = "trigger.completed"
    TRIGGER_FAILED = "trigger.failed"
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    JOB_RETRYING = "job.retrying"
    DOCUMENT_COMPLETED = "document.processing_completed"
    DOCUMENT_FAILED = "document.processing_failed"
    EVALUATION_COMPLETED = "evaluation.completed"
    EVALUATION_REGRESSION = "evaluation.regression_detected"
    REPLAY_COMPLETED = "replay.completed"
    REPLAY_FAILED = "replay.failed"
    CONNECTOR_COMPLETED = "connector.completed"
    CONNECTOR_FAILED = "connector.failed"
    SYSTEM_WARNING = "system.warning"


# Webhook HMAC Signing Headers
WEBHOOK_HEADER_EVENT = "X-AI-Work-Event"
WEBHOOK_HEADER_TIMESTAMP = "X-AI-Work-Timestamp"
WEBHOOK_HEADER_SIGNATURE = "X-AI-Work-Signature"

# Default Severity per Event Type
DEFAULT_EVENT_SEVERITY = {
    NotificationEventType.WORKFLOW_COMPLETED.value: NotificationSeverity.SUCCESS.value,
    NotificationEventType.WORKFLOW_FAILED.value: NotificationSeverity.ERROR.value,
    NotificationEventType.WORKFLOW_WAITING_APPROVAL.value: NotificationSeverity.WARNING.value,
    NotificationEventType.TRIGGER_COMPLETED.value: NotificationSeverity.INFO.value,
    NotificationEventType.TRIGGER_FAILED.value: NotificationSeverity.ERROR.value,
    NotificationEventType.JOB_COMPLETED.value: NotificationSeverity.INFO.value,
    NotificationEventType.JOB_FAILED.value: NotificationSeverity.ERROR.value,
    NotificationEventType.JOB_RETRYING.value: NotificationSeverity.WARNING.value,
    NotificationEventType.DOCUMENT_COMPLETED.value: NotificationSeverity.SUCCESS.value,
    NotificationEventType.DOCUMENT_FAILED.value: NotificationSeverity.ERROR.value,
    NotificationEventType.EVALUATION_COMPLETED.value: NotificationSeverity.INFO.value,
    NotificationEventType.EVALUATION_REGRESSION.value: NotificationSeverity.ERROR.value,
    NotificationEventType.REPLAY_COMPLETED.value: NotificationSeverity.INFO.value,
    NotificationEventType.REPLAY_FAILED.value: NotificationSeverity.ERROR.value,
    NotificationEventType.CONNECTOR_COMPLETED.value: NotificationSeverity.INFO.value,
    NotificationEventType.CONNECTOR_FAILED.value: NotificationSeverity.ERROR.value,
    NotificationEventType.SYSTEM_WARNING.value: NotificationSeverity.WARNING.value,
}

# Events that cannot be disabled or suppressed via preferences (must deliver at least in-app)
MANDATORY_IN_APP_EVENTS = {
    NotificationEventType.WORKFLOW_WAITING_APPROVAL.value,
    NotificationEventType.SYSTEM_WARNING.value,
}
