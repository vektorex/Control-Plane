"""
Controlled enums and registries for Step 44: AI Work Planning, Capacity & Resource Optimization.
"""
from enum import Enum


class WorkPlanStatus(str, Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    APPROVED = "approved"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class PlanningMode(str, Enum):
    MANUAL = "manual"
    ASSISTED = "assisted"
    OPTIMIZED = "optimized"


class PlanningItemResourceType(str, Enum):
    TASK = "task"
    WORKFLOW = "workflow"
    WORKFLOW_STEP = "workflow_step"
    AGENT_RUN = "agent_run"
    AGENT_TEAM_RUN = "agent_team_run"
    MILESTONE = "milestone"
    OUTCOME = "outcome"
    APPROVAL = "approval"
    EVALUATION = "evaluation"
    SIMULATION = "simulation"


class PlanningItemStatus(str, Enum):
    PLANNED = "planned"
    READY = "ready"
    STARTED = "started"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DependencyType(str, Enum):
    FINISH_TO_START = "finish_to_start"
    START_TO_START = "start_to_start"
    FINISH_TO_FINISH = "finish_to_finish"
    START_TO_FINISH = "start_to_finish"
    BLOCKS = "blocks"
    REQUIRES = "requires"
    OPTIONAL_AFTER = "optional_after"


class WorkResourceType(str, Enum):
    HUMAN = "human"
    AGENT = "agent"
    AGENT_TEAM = "agent_team"
    WORKFLOW = "workflow"
    TOOL = "tool"
    CONNECTOR = "connector"
    SYSTEM = "system"


class WorkResourceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    DECOMMISSIONED = "decommissioned"


class AvailabilitySource(str, Enum):
    MANUAL = "manual"
    CALENDAR = "calendar"
    SYSTEM = "system"
    POLICY = "policy"
    DERIVED = "derived"
    UNKNOWN = "unknown"


class ReservationStatus(str, Enum):
    PROPOSED = "proposed"
    RESERVED = "reserved"
    RELEASED = "released"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ConstraintType(str, Enum):
    DEADLINE = "deadline"
    DEPENDENCY = "dependency"
    CAPACITY = "capacity"
    BUDGET = "budget"
    APPROVAL = "approval"
    CAPABILITY = "capability"
    DATA_ACCESS = "data_access"
    SECURITY = "security"
    POLICY = "policy"
    CONCURRENCY = "concurrency"
    ENVIRONMENT = "environment"
    RESOURCE = "resource"
    OUTCOME = "outcome"
    MILESTONE = "milestone"


class CandidateStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    BLOCKED = "blocked"


class BlockerType(str, Enum):
    DEPENDENCY = "dependency"
    CAPACITY = "capacity"
    APPROVAL = "approval"
    PERMISSION = "permission"
    RESOURCE = "resource"
    DEADLINE = "deadline"
    TOOL = "tool"
    CONNECTOR = "connector"
    EVALUATION = "evaluation"
    SECURITY = "security"
    DATA = "data"
    POLICY = "policy"


class BlockerSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BlockerStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    IGNORED = "ignored"
    SUPERSEDED = "superseded"


class RecommendationStatus(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DISMISSED = "dismissed"


class RecommendationType(str, Enum):
    MOVE_TASK = "move_task"
    CHANGE_SEQUENCE = "change_sequence"
    USE_ANOTHER_AGENT = "use_another_agent"
    SPLIT_TASK = "split_task"
    REDUCE_SCOPE = "reduce_scope"
    REQUEST_APPROVAL = "request_approval"
    INCREASE_CAPACITY = "increase_capacity"
    RUN_SIMULATION = "run_simulation"
    RESOLVE_BLOCKER = "resolve_blocker"
    UPDATE_DEADLINE = "update_deadline"
    REASSESS_OUTCOME = "reassess_outcome"
