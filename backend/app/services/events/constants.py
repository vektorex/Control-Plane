"""
Constants and Enums for Step 26: Unified Event Bus and Real-Time Execution Updates.
"""
from enum import Enum


class ActorType(str, Enum):
    USER = "user"
    SYSTEM = "system"
    WORKER = "worker"
    CONNECTOR = "connector"
    SCHEDULER = "scheduler"


class AggregateType(str, Enum):
    WORKFLOW = "workflow"
    JOB = "job"
    TRIGGER = "trigger"
    DOCUMENT = "document"
    EVALUATION = "evaluation"
    REPLAY = "replay"
    CONNECTOR = "connector"
    APPROVAL = "approval"
    NOTIFICATION = "notification"
    SYSTEM = "system"


class EventDeliveryStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    RETRYING = "retrying"
    FAILED = "failed"


class EventVisibility(str, Enum):
    WORKSPACE = "workspace"
    PROJECT = "project"
    USER = "user"
    SYSTEM = "system"


class SystemEventType(str, Enum):
    # Job events
    JOB_CREATED = "job.created"
    JOB_QUEUED = "job.queued"
    JOB_STARTED = "job.started"
    JOB_PROGRESS = "job.progress"
    JOB_RETRYING = "job.retrying"
    JOB_CANCEL_REQUESTED = "job.cancel_requested"
    JOB_CANCELLED = "job.cancelled"
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    JOB_RECOVERED = "job.recovered"

    # Workflow events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_STEP_STARTED = "workflow.step_started"
    WORKFLOW_STEP_COMPLETED = "workflow.step_completed"
    WORKFLOW_WAITING_FOR_APPROVAL = "workflow.waiting_for_approval"
    WORKFLOW_RESUMED = "workflow.resumed"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"

    # Trigger events
    TRIGGER_CREATED = "trigger.created"
    TRIGGER_UPDATED = "trigger.updated"
    TRIGGER_PAUSED = "trigger.paused"
    TRIGGER_RESUMED = "trigger.resumed"
    TRIGGER_FIRED = "trigger.fired"
    TRIGGER_COMPLETED = "trigger.completed"
    TRIGGER_FAILED = "trigger.failed"

    # Document events
    DOCUMENT_PROCESSING_STARTED = "document.processing_started"
    DOCUMENT_PROCESSING_PROGRESS = "document.processing_progress"
    DOCUMENT_PROCESSING_COMPLETED = "document.processing_completed"
    DOCUMENT_PROCESSING_FAILED = "document.processing_failed"

    # Evaluation events
    EVALUATION_STARTED = "evaluation.started"
    EVALUATION_COMPLETED = "evaluation.completed"
    EVALUATION_REGRESSION_DETECTED = "evaluation.regression_detected"
    EVALUATION_FAILED = "evaluation.failed"

    # Replay events
    REPLAY_STARTED = "replay.started"
    REPLAY_PROGRESS = "replay.progress"
    REPLAY_COMPLETED = "replay.completed"
    REPLAY_FAILED = "replay.failed"

    # Connector events
    CONNECTOR_STARTED = "connector.started"
    CONNECTOR_COMPLETED = "connector.completed"
    CONNECTOR_FAILED = "connector.failed"

    # HITL events
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_APPROVED = "approval.approved"
    APPROVAL_REJECTED = "approval.rejected"
    APPROVAL_EXPIRED = "approval.expired"

    # Notification events
    NOTIFICATION_CREATED = "notification.created"
    NOTIFICATION_DELIVERY_STARTED = "notification.delivery_started"
    NOTIFICATION_DELIVERY_COMPLETED = "notification.delivery_completed"
    NOTIFICATION_DELIVERY_FAILED = "notification.delivery_failed"

    # System events
    SYSTEM_WARNING = "system.warning"
    SYSTEM_ERROR = "system.error"


# Auditable event types
AUDITABLE_EVENTS = {
    SystemEventType.APPROVAL_APPROVED.value,
    SystemEventType.APPROVAL_REJECTED.value,
    SystemEventType.TRIGGER_UPDATED.value,
    SystemEventType.TRIGGER_PAUSED.value,
    SystemEventType.TRIGGER_RESUMED.value,
    SystemEventType.WORKFLOW_STARTED.value,
    SystemEventType.WORKFLOW_COMPLETED.value,
    SystemEventType.WORKFLOW_FAILED.value,
    SystemEventType.SYSTEM_WARNING.value,
    SystemEventType.SYSTEM_ERROR.value,
}

# Sensitive keys scrubbed from all payloads
SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "secret",
    "secret_key",
    "password",
    "passwd",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "auth",
    "cookie",
    "cookies",
    "private_key",
    "credential",
    "credentials",
    "database_url",
    "connection_string",
    "prompt",
    "hidden_prompt",
    "system_prompt",
    "chain_of_thought",
    "internal_reasoning",
    "raw_thought",
}

SSE_HEARTBEAT_EVENT = "heartbeat"
SSE_HEADER_LAST_EVENT_ID = "last-event-id"
