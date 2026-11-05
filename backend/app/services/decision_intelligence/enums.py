from enum import Enum

class OverallState(str, Enum):
    ready = "ready"
    conditionally_ready = "conditionally_ready"
    blocked = "blocked"
    not_ready = "not_ready"
    unknown = "unknown"

class FreshnessState(str, Enum):
    fresh = "fresh"
    aging = "aging"
    stale = "stale"
    unknown = "unknown"
