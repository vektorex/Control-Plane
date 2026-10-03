"""
Cache Lookup Service for Step 31: Production-Grade Semantic Cache and Intelligent Reuse Layer.

Performs deterministic fingerprinting, stampede prevention (request coalescing),
exact matching first, semantic matching fallback, and freshness/authorization verification.
"""
import asyncio
import hashlib
import json
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.cache.constants import (
    CacheMode,
    CacheNamespace,
    MatchMode,
)
from backend.app.services.cache.embeddings import CacheEmbeddingService
from backend.app.services.cache.freshness import FreshnessService
from backend.app.services.cache.matcher import CacheMatcher
from backend.app.services.cache.models import CacheEntry
from backend.app.services.cache.namespaces import NamespaceResolver
from backend.app.services.cache.policies import CachePolicyEngine
from backend.app.services.cache.repository import CacheRepository
from backend.app.services.cache.schemas import (
    CacheLookupRequest,
    CacheLookupResult,
    CachePolicyConfig,
)
from backend.app.services.cache.statistics import CacheStatisticsService

logger = logging.getLogger(__name__)

# Request coalescing registry to prevent cache stampedes
_COALESCE_LOCKS: Dict[str, asyncio.Lock] = {}
_COALESCE_REGISTRY_LOCK = asyncio.Lock()


def canonical_hash(data: Any) -> str:
    """Computes deterministic SHA-256 hash over canonical JSON or string representations."""
    if data is None:
        return ""
    if isinstance(data, (dict, list)):
        serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
    else:
        serialized = str(data)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def compute_request_fingerprint(
    normalized_request: str,
    prompt_version_id: Optional[uuid.UUID] = None,
    model_id: Optional[str] = None,
    execution_config_hash: Optional[str] = None,
    context_hash: Optional[str] = None,
    artifact_hash: Optional[str] = None,
    graph_hash: Optional[str] = None,
    memory_hash: Optional[str] = None,
) -> str:
    """
    Computes deterministic SHA-256 fingerprint encompassing all execution requirements.
    Never hashes raw secret credentials into logs or fingerprints.
    """
    elements = [
        normalized_request.strip(),
        str(prompt_version_id or ""),
        str(model_id or ""),
        str(execution_config_hash or ""),
        str(context_hash or ""),
        str(artifact_hash or ""),
        str(graph_hash or ""),
        str(memory_hash or ""),
    ]
    combined = "||".join(elements)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


class CacheLookupService:
    """Coordinates cache lookups with stampede prevention and strict validation."""

    def __init__(
        self,
        repository: Optional[CacheRepository] = None,
        policy_engine: Optional[CachePolicyEngine] = None,
        embedding_service: Optional[CacheEmbeddingService] = None,
        freshness_service: Optional[FreshnessService] = None,
        matcher: Optional[CacheMatcher] = None,
        stats_service: Optional[CacheStatisticsService] = None,
    ):
        self.repository = repository or CacheRepository()
        self.policy_engine = policy_engine or CachePolicyEngine()
        self.embedding_service = embedding_service or CacheEmbeddingService()
        self.freshness_service = freshness_service or FreshnessService()
        self.matcher = matcher or CacheMatcher()
        self.stats_service = stats_service or CacheStatisticsService()

    async def get_coalesce_lock(self, lock_key: str) -> asyncio.Lock:
        """Get or initialize an in-memory lock for a specific cache key."""
        async with _COALESCE_REGISTRY_LOCK:
            if lock_key not in _COALESCE_LOCKS:
                _COALESCE_LOCKS[lock_key] = asyncio.Lock()
            return _COALESCE_LOCKS[lock_key]

    async def release_coalesce_lock(self, lock_key: str) -> None:
        """Clean up coalesce lock when computation completes."""
        async with _COALESCE_REGISTRY_LOCK:
            _COALESCE_LOCKS.pop(lock_key, None)

    async def lookup(
        self,
        db: AsyncSession,
        request: CacheLookupRequest,
        policy: Optional[CachePolicyConfig] = None,
    ) -> CacheLookupResult:
        """
        Execute full cache lookup flow.
        1. Resolve namespace & permissions.
        2. Evaluate bypass/mode.
        3. Exact match.
        4. Semantic match if exact miss.
        5. Validate freshness & scope compatibility.
        """
        start_time = time.perf_counter()

        # 1. Fetch workspace policy if not supplied
        if not policy:
            policy = await self.policy_engine.get_workspace_policy(db, request.workspace_id)

        # 2. Check if caching is globally/workspace disabled or request is bypass
        if not policy.enabled or request.cache_mode in (CacheMode.DISABLED, CacheMode.REFRESH):
            self.stats_service.record_bypass(request.workspace_id)
            return CacheLookupResult(
                hit=False,
                source="cache",
                fresh=True,
            )

        self.stats_service.record_lookup(request.workspace_id)

        # 3. Resolve normalized namespace string
        namespace_str = request.namespace.value

        # 4. Compute deterministic hashes
        exec_config_hash = canonical_hash(request.execution_config) if request.execution_config else None
        context_hash = request.context_fingerprint
        artifact_hash = request.artifact_fingerprint
        graph_hash = request.graph_fingerprint
        memory_hash = request.memory_fingerprint

        request_fp = compute_request_fingerprint(
            normalized_request=request.prompt_text,
            prompt_version_id=request.prompt_version_id,
            model_id=request.model_id,
            execution_config_hash=exec_config_hash,
            context_hash=context_hash,
            artifact_hash=artifact_hash,
            graph_hash=graph_hash,
            memory_hash=memory_hash,
        )
        exact_cache_key = request_fp

        # 5. Exact Match Lookup (always attempted first)
        exact_entry = await self.repository.find_exact_match(
            db=db,
            workspace_id=request.workspace_id,
            namespace=namespace_str,
            cache_key=exact_cache_key,
            organization_id=request.organization_id,
            project_id=request.project_id,
            user_id=request.user_id,
        )

        if exact_entry:
            is_compat, reason = self.matcher.validate_compatibility(
                candidate=exact_entry,
                request=request,
                policy=policy,
                execution_config_hash=exec_config_hash,
                context_hash=context_hash,
                artifact_hash=artifact_hash,
                graph_hash=graph_hash,
                memory_hash=memory_hash,
            )
            if is_compat:
                is_fresh, allow_swr = self.freshness_service.is_fresh(
                    entry=exact_entry,
                    allow_stale_while_revalidate=policy.stale_while_revalidate,
                )
                if is_fresh:
                    await self.repository.record_hit(db, exact_entry.id)
                    self.stats_service.record_exact_hit(request.workspace_id)
                    return CacheLookupResult(
                        hit=True,
                        source="cache",
                        cache_entry_id=str(exact_entry.id),
                        match_type="exact",
                        fresh=True,
                        response_content=exact_entry.response_content,
                        response_metadata=exact_entry.response_metadata,
                        similarity_score=1.0,
                        created_at=exact_entry.created_at,
                        expires_at=exact_entry.expires_at,
                    )
                elif allow_swr:
                    # Return stale result but mark as candidate for background revalidation
                    await self.repository.record_hit(db, exact_entry.id)
                    self.stats_service.record_exact_hit(request.workspace_id)
                    return CacheLookupResult(
                        hit=True,
                        source="cache",
                        cache_entry_id=str(exact_entry.id),
                        match_type="exact",
                        fresh=False,
                        stale_while_revalidate_candidate=True,
                        response_content=exact_entry.response_content,
                        response_metadata=exact_entry.response_metadata,
                        similarity_score=1.0,
                        created_at=exact_entry.created_at,
                        expires_at=exact_entry.expires_at,
                    )

        # 6. Semantic Match Lookup (if mode permits and semantic enabled)
        if (
            request.match_mode in (MatchMode.SEMANTIC, MatchMode.HYBRID)
            and policy.semantic_enabled
        ):
            # Compute embedding for prompt text using existing embedding provider
            query_embedding = await self.embedding_service.get_embedding(request.prompt_text)
            if query_embedding:
                candidates = await self.repository.find_semantic_candidates(
                    db=db,
                    workspace_id=request.workspace_id,
                    namespace=namespace_str,
                    query_embedding=query_embedding,
                    organization_id=request.organization_id,
                    project_id=request.project_id,
                    user_id=request.user_id,
                    limit=10,
                )

                for candidate_entry, similarity in candidates:
                    if similarity < policy.semantic_threshold:
                        # Since sorted descending, subsequent candidates will also be below cutoff
                        break

                    is_compat, reason = self.matcher.validate_compatibility(
                        candidate=candidate_entry,
                        request=request,
                        policy=policy,
                        execution_config_hash=exec_config_hash,
                        context_hash=context_hash,
                        artifact_hash=artifact_hash,
                        graph_hash=graph_hash,
                        memory_hash=memory_hash,
                    )
                    if not is_compat:
                        continue

                    is_fresh, allow_swr = self.freshness_service.is_fresh(
                        entry=candidate_entry,
                        allow_stale_while_revalidate=policy.stale_while_revalidate,
                    )
                    if is_fresh or allow_swr:
                        await self.repository.record_hit(db, candidate_entry.id)
                        self.stats_service.record_semantic_hit(request.workspace_id)
                        return CacheLookupResult(
                            hit=True,
                            source="cache",
                            cache_entry_id=str(candidate_entry.id),
                            match_type="semantic",
                            fresh=is_fresh,
                            stale_while_revalidate_candidate=(not is_fresh and allow_swr),
                            response_content=candidate_entry.response_content,
                            response_metadata=candidate_entry.response_metadata,
                            similarity_score=round(similarity, 4),
                            created_at=candidate_entry.created_at,
                            expires_at=candidate_entry.expires_at,
                        )

        # 7. Cache Miss
        self.stats_service.record_miss(request.workspace_id)
        return CacheLookupResult(
            hit=False,
            source="cache",
            fresh=True,
        )
