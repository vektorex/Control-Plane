"""
Constants and Enums for Step 31: Production-Grade Semantic Cache and Intelligent Reuse Layer.
"""
from enum import Enum


class CacheMode(str, Enum):
    AUTO = "auto"
    ENABLED = "enabled"
    DISABLED = "disabled"
    REFRESH = "refresh"


class WorkflowCachePolicy(str, Enum):
    DISABLED = "disabled"
    SAFE = "safe"
    AGGRESSIVE = "aggressive"


class CacheStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"
    BLOCKED = "blocked"


class CacheNamespace(str, Enum):
    WORKSPACE = "workspace"
    PROJECT = "project"
    USER = "user"
    GLOBAL = "global"


class MatchMode(str, Enum):
    EXACT = "exact"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class FreshnessPolicy(str, Enum):
    STRICT = "strict"
    NORMAL = "normal"
    RELAXED = "relaxed"


class InvalidationMode(str, Enum):
    ENTRY = "entry"
    NAMESPACE = "namespace"
    PROMPT = "prompt"
    ARTIFACT = "artifact"
    DOCUMENT = "document"
    GRAPH = "graph"
    MEMORY = "memory"
    MODEL = "model"
    WORKSPACE = "workspace"
    PROJECT = "project"


# Numerical & Operational Thresholds
CACHE_DEFAULT_SEMANTIC_THRESHOLD: float = 0.88
CACHE_MIN_SEMANTIC_THRESHOLD: float = 0.70
CACHE_MAX_SEMANTIC_THRESHOLD: float = 0.99

CACHE_DEFAULT_TTL_SECONDS: int = 86400  # 24 hours
CACHE_STRICT_TTL_SECONDS: int = 3600    # 1 hour
CACHE_RELAXED_TTL_SECONDS: int = 604800 # 7 days

CACHE_MAX_RESPONSE_BYTES: int = 500_000  # 500 KB limit to prevent unbounded storage
CACHE_MAX_ENTRIES_PER_WORKSPACE: int = 10_000
CACHE_STAMPEDE_LOCK_TIMEOUT_SECONDS: int = 30
STALE_REVALIDATE_GRACE_PERIOD_SECONDS: int = 3600  # 1 hour grace period
