from enum import Enum

class RolloutStatus(str, Enum):
    draft = "draft"
    validation_required = "validation_required"
    approval_required = "approval_required"
    ready = "ready"
    scheduled = "scheduled"
    running = "running"
    paused = "paused"
    blocked = "blocked"
    aborting = "aborting"
    rolling_back = "rolling_back"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"

class StrategyType(str, Enum):
    canary = "canary"
    percentage = "percentage"
    cohort = "cohort"
    workspace = "workspace"
    project = "project"
    organization = "organization"
    environment = "environment"
    time_window = "time_window"

class StageStatus(str, Enum):
    pending = "pending"
    ready = "ready"
    running = "running"
    observing = "observing"
    passed = "passed"
    failed = "failed"
    paused = "paused"
    skipped = "skipped"
    rolled_back = "rolled_back"\n