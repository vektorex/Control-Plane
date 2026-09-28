import enum


class TaskStatus(str, enum.Enum):
    """Centralized lifecycle statuses for Tasks."""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class RunStatus(str, enum.Enum):
    """Centralized execution statuses for Task Runs."""
    QUEUED = "queued"
    RUNNING = "running"
    PLANNING = "planning"
    EXECUTING = "executing"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"



class DocumentStatus(str, enum.Enum):
    """Lifecycle statuses for document ingestion and indexing."""
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"

