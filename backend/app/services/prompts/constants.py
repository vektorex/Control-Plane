"""
Constants and Enums for Step 28: Prompt Management, Versioning, Release, and Experimentation.
"""
from enum import Enum
from typing import Set


class PromptType(str, Enum):
    SYSTEM = "system"
    INSTRUCTION = "instruction"
    TASK = "task"
    PLANNER = "planner"
    EVALUATOR = "evaluator"
    TRANSFORM = "transform"
    WORKFLOW = "workflow"


class PromptStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class PromptVersionStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


class PromptEnvironment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ReleaseStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ROLLED_BACK = "rolled_back"


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AllocationKey(str, Enum):
    USER_ID = "user_id"
    TASK_ID = "task_id"
    WORKFLOW_RUN_ID = "workflow_run_id"


# Allowed variable types in variable_schema
SUPPORTED_VARIABLE_TYPES: Set[str] = {
    "string",
    "number",
    "boolean",
    "string_array",
    "json",
}

# Allowed root variable namespaces
ALLOWED_VARIABLE_NAMESPACES: Set[str] = {
    "input",
    "task",
    "project",
    "context",
    "workflow",
    "memory",
    "system",
}

# Default environments for promotion ordering
ENVIRONMENT_PROMOTION_ORDER = [
    PromptEnvironment.DEVELOPMENT.value,
    PromptEnvironment.STAGING.value,
    PromptEnvironment.PRODUCTION.value,
]
