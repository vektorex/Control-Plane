"""
Constants and Enums for Step 24: Durable Background Job System.
"""
from enum import Enum


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


PRIORITY_WEIGHTS = {
    JobPriority.HIGH.value: 1,
    JobPriority.NORMAL.value: 2,
    JobPriority.LOW.value: 3,
}


class JobType(str, Enum):
    WORKFLOW_RUN = "workflow_run"
    TRIGGER_RUN = "trigger_run"
    DOCUMENT_PROCESSING = "document_processing"
    EVALUATION_EXPERIMENT = "evaluation_experiment"
    REPLAY_RUN = "replay_run"
    CONNECTOR_OPERATION = "connector_operation"


class JobEventType(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    CLAIMED = "claimed"
    STARTED = "started"
    HEARTBEAT = "heartbeat"
    PROGRESS = "progress"
    RETRY_SCHEDULED = "retry_scheduled"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERED = "recovered"
