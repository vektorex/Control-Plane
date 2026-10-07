from enum import Enum

class PortfolioStatus(str, Enum):
    draft = "draft"
    active = "active"
    paused = "paused"
    completed = "completed"
    cancelled = "cancelled"

class TrainStatus(str, Enum):
    draft = "draft"
    planning = "planning"
    validation_required = "validation_required"
    blocked = "blocked"
    scheduled = "scheduled"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"

class DependencyType(str, Enum):
    requires = "requires"
    blocks = "blocks"
    must_precede = "must_precede"
    must_follow = "must_follow"
    same_window = "same_window"
    different_window = "different_window"

class ConflictSeverity(str, Enum):
    informational = "informational"
    warning = "warning"
    blocking = "blocking"

class ChangeWindowType(str, Enum):
    preferred = "preferred"
    maintenance = "maintenance"
    blackout = "blackout"
    security_freeze = "security_freeze"
    contract_restricted = "contract_restricted"
    availability_restricted = "availability_restricted"
    emergency = "emergency"
