"""
Pydantic Schemas for Step 31: Production-Grade Semantic Cache and Intelligent Reuse Layer.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.services.cache.constants import (
    CACHE_DEFAULT_SEMANTIC_THRESHOLD,
    CACHE_DEFAULT_TTL_SECONDS,
    CACHE_MAX_RESPONSE_BYTES,
    CACHE_MAX_SEMANTIC_THRESHOLD,
    CACHE_MIN_SEMANTIC_THRESHOLD,
    CacheMode,
    CacheNamespace,
    CacheStatus,
    FreshnessPolicy,
    InvalidationMode,
    MatchMode,
)


class CachePolicyConfig(BaseModel):
    """Workspace-level Cache Policy Configuration."""
    model_config = ConfigDict(extra="ignore")

    enabled: bool = Field(default=True, description="Master enable switch for caching in workspace")
    default_mode: CacheMode = Field(default=CacheMode.AUTO, description="Default cache mode (auto, enabled, disabled, refresh)")
    semantic_enabled: bool = Field(default=True, description="Whether to allow semantic similarity lookups on exact misses")
    semantic_threshold: float = Field(
        default=CACHE_DEFAULT_SEMANTIC_THRESHOLD,
        ge=CACHE_MIN_SEMANTIC_THRESHOLD,
        le=CACHE_MAX_SEMANTIC_THRESHOLD,
        description="Cosine similarity cutoff threshold (0.70 to 0.99)",
    )
    default_ttl: int = Field(default=CACHE_DEFAULT_TTL_SECONDS, ge=60, description="Default time-to-live in seconds")
    max_entry_size: int = Field(default=CACHE_MAX_RESPONSE_BYTES, ge=1024, description="Max response size in bytes for cache admission")
    allow_cross_model_cache: bool = Field(default=False, description="Whether responses from compatible models may be reused")
    stale_while_revalidate: bool = Field(default=True, description="Whether to return slightly stale results while refreshing asynchronously")
    max_namespace_entries: int = Field(default=10_000, ge=100, description="Max cache entries per namespace before eviction")


class CacheLookupRequest(BaseModel):
    """Specification for cache lookup."""
    model_config = ConfigDict(extra="ignore")

    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    prompt_text: str = Field(..., min_length=1)
    task_type: Optional[str] = None
    model_id: Optional[str] = None
    model_provider: Optional[str] = None
    execution_config: Optional[Dict[str, Any]] = None
    context_fingerprint: Optional[str] = None
    artifact_fingerprint: Optional[str] = None
    graph_fingerprint: Optional[str] = None
    memory_fingerprint: Optional[str] = None
    prompt_id: Optional[uuid.UUID] = None
    prompt_version_id: Optional[uuid.UUID] = None
    cache_mode: CacheMode = CacheMode.AUTO
    match_mode: MatchMode = MatchMode.HYBRID
    namespace: CacheNamespace = CacheNamespace.WORKSPACE


class CacheLookupResult(BaseModel):
    """Normalized response of a cache query."""
    model_config = ConfigDict(extra="ignore")

    hit: bool = False
    source: str = "cache"
    cache_entry_id: Optional[str] = None
    match_type: Optional[str] = None  # "exact", "semantic", None
    fresh: bool = True
    stale_while_revalidate_candidate: bool = False
    response_content: Optional[str] = None
    response_metadata: Optional[Dict[str, Any]] = None
    similarity_score: Optional[float] = None
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    revalidation_job_id: Optional[str] = None


class CacheAdmissionCandidate(BaseModel):
    """Data payload submitted for admission into the semantic cache."""
    model_config = ConfigDict(extra="ignore")

    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    namespace: CacheNamespace = CacheNamespace.WORKSPACE
    normalized_request: str
    request_fingerprint: str
    cache_key: str
    response_content: str
    response_metadata: Optional[Dict[str, Any]] = None
    source_snapshot: Optional[Dict[str, Any]] = None
    prompt_id: Optional[uuid.UUID] = None
    prompt_version_id: Optional[uuid.UUID] = None
    model_id: Optional[str] = None
    model_provider: Optional[str] = None
    execution_config_hash: Optional[str] = None
    context_hash: Optional[str] = None
    artifact_hash: Optional[str] = None
    graph_snapshot_hash: Optional[str] = None
    memory_snapshot_hash: Optional[str] = None
    ttl_seconds: Optional[int] = None
    semantic_embedding: Optional[List[float]] = None


class CacheInvalidationRequest(BaseModel):
    """Administrative or automated cache invalidation request."""
    model_config = ConfigDict(extra="ignore")

    workspace_id: uuid.UUID
    mode: InvalidationMode
    target_id: Optional[str] = None
    reason: Optional[str] = Field(default="administrative_invalidation")


class CacheInvalidationResult(BaseModel):
    """Result of invalidating cache entries."""
    model_config = ConfigDict(extra="ignore")

    invalidated_count: int
    mode: str
    reason: str


class CacheStatsResponse(BaseModel):
    """Factual, non-subjective metrics reflecting cache health and activity."""
    model_config = ConfigDict(extra="ignore")

    lookups: int = 0
    exact_hits: int = 0
    semantic_hits: int = 0
    misses: int = 0
    bypasses: int = 0
    invalidations: int = 0
    refreshes: int = 0
    admitted_entries: int = 0
    rejected_entries: int = 0
    active_entries: int = 0
    storage_bytes: int = 0
    hit_ratio: float = 0.0


class CacheEntryResponse(BaseModel):
    """Public, sanitized representation of a CacheEntry for UI and APIs."""
    model_config = ConfigDict(extra="ignore", from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    namespace: str
    cache_key: Optional[str] = None
    normalized_request: str
    request_fingerprint: str
    response_content: str
    response_metadata: Dict[str, Any] = Field(default_factory=dict)
    prompt_id: Optional[uuid.UUID] = None
    prompt_version_id: Optional[uuid.UUID] = None
    model_id: Optional[str] = None
    model_provider: Optional[str] = None
    status: str
    hit_count: int
    created_at: datetime
    accessed_at: datetime
    expires_at: datetime
    last_hit_at: Optional[datetime] = None
    invalidated_at: Optional[datetime] = None
    invalidation_reason: Optional[str] = None


class CachePreviewRequest(BaseModel):
    """Request to preview cache eligibility and candidate match without executing task."""
    model_config = ConfigDict(extra="ignore")

    prompt_text: str = Field(..., min_length=1)
    task_type: Optional[str] = None
    model_id: Optional[str] = None
    workspace_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    cache_mode: CacheMode = CacheMode.AUTO


class CachePreviewResponse(BaseModel):
    """Result of cache preview probe."""
    model_config = ConfigDict(extra="ignore")

    eligible: bool
    reason: str
    exact_match_available: bool
    semantic_candidate_available: bool
    candidate_similarity: Optional[float] = None
    freshness: Optional[str] = None
    invalidation_reason: Optional[str] = None
    expected_behavior: str
