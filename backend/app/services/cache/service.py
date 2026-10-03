"""
Cache Service Facade for Step 31: Production-Grade Semantic Cache and Intelligent Reuse Layer.

Unifies lookup, admission, surgical invalidation, preview probes, policy management,
and telemetry into a single production-grade interface.
"""
import uuid
from typing import Any, Dict, List, Optional, Tuple
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.cache.admission import CacheAdmissionService
from backend.app.services.cache.constants import (
    CacheMode,
    CacheNamespace,
    MatchMode,
)
from backend.app.services.cache.eligibility import CacheEligibilityService
from backend.app.services.cache.embeddings import CacheEmbeddingService
from backend.app.services.cache.freshness import FreshnessService
from backend.app.services.cache.invalidation import CacheInvalidationService
from backend.app.services.cache.lookup import CacheLookupService, compute_request_fingerprint
from backend.app.services.cache.matcher import CacheMatcher
from backend.app.services.cache.models import CacheEntry
from backend.app.services.cache.namespaces import NamespaceResolver
from backend.app.services.cache.policies import CachePolicyEngine
from backend.app.services.cache.repository import CacheRepository
from backend.app.services.cache.sanitizer import CacheSanitizer
from backend.app.services.cache.schemas import (
    CacheAdmissionCandidate,
    CacheInvalidationRequest,
    CacheInvalidationResult,
    CacheLookupRequest,
    CacheLookupResult,
    CachePolicyConfig,
    CachePreviewRequest,
    CachePreviewResponse,
    CacheStatsResponse,
)
from backend.app.services.cache.statistics import CacheStatisticsService

logger = logging.getLogger(__name__)


class CacheService:
    """Production facade for the Semantic Cache and Intelligent Reuse Layer."""

    def __init__(
        self,
        repository: Optional[CacheRepository] = None,
        eligibility: Optional[CacheEligibilityService] = None,
        lookup_svc: Optional[CacheLookupService] = None,
        admission_svc: Optional[CacheAdmissionService] = None,
        invalidation_svc: Optional[CacheInvalidationService] = None,
        policy_engine: Optional[CachePolicyEngine] = None,
        embedding_svc: Optional[CacheEmbeddingService] = None,
        stats_svc: Optional[CacheStatisticsService] = None,
        freshness_svc: Optional[FreshnessService] = None,
    ):
        self.repository = repository or CacheRepository()
        self.eligibility = eligibility or CacheEligibilityService()
        self.stats = stats_svc or CacheStatisticsService()
        self.policy_engine = policy_engine or CachePolicyEngine()
        self.embedding = embedding_svc or CacheEmbeddingService()
        self.freshness = freshness_svc or FreshnessService()
        self.lookup_svc = lookup_svc or CacheLookupService(
            repository=self.repository,
            policy_engine=self.policy_engine,
            embedding_service=self.embedding,
            freshness_service=self.freshness,
            stats_service=self.stats,
        )
        self.admission_svc = admission_svc or CacheAdmissionService(
            repository=self.repository,
            eligibility_service=self.eligibility,
            policy_engine=self.policy_engine,
            embedding_service=self.embedding,
            stats_service=self.stats,
        )
        self.invalidation_svc = invalidation_svc or CacheInvalidationService(
            repository=self.repository,
            stats_service=self.stats,
        )

    async def lookup(
        self,
        db: AsyncSession,
        request: CacheLookupRequest,
    ) -> CacheLookupResult:
        """Query cache for an exact or semantic reusable result."""
        return await self.lookup_svc.lookup(db, request)

    async def admit(
        self,
        db: AsyncSession,
        candidate: CacheAdmissionCandidate,
        task_type: Optional[str] = None,
        execution_success: bool = True,
        evaluation_passed: bool = True,
        strict_evaluation: bool = False,
    ) -> Tuple[Optional[CacheEntry], Optional[str]]:
        """Admit a newly executed AI response into the cache."""
        return await self.admission_svc.admit(
            db=db,
            candidate=candidate,
            task_type=task_type,
            execution_success=execution_success,
            evaluation_passed=evaluation_passed,
            strict_evaluation=strict_evaluation,
        )

    async def invalidate(
        self,
        db: AsyncSession,
        request: CacheInvalidationRequest,
    ) -> CacheInvalidationResult:
        """Invalidate entries matching specified mode and criteria."""
        return await self.invalidation_svc.invalidate(db, request)

    async def preview(
        self,
        db: AsyncSession,
        request: CachePreviewRequest,
    ) -> CachePreviewResponse:
        """
        Evaluate cache eligibility and candidate match without executing any task.
        """
        workspace_id = request.workspace_id or uuid.uuid4()
        policy = await self.policy_engine.get_workspace_policy(db, workspace_id)

        # 1. Eligibility Check
        eligible, reason = self.eligibility.is_cacheable(
            task_type=request.task_type,
            parameters={"prompt": request.prompt_text},
            cache_mode=request.cache_mode,
        )

        if not eligible:
            return CachePreviewResponse(
                eligible=False,
                reason=reason,
                exact_match_available=False,
                semantic_candidate_available=False,
                expected_behavior="Bypass cache and execute directly via AI Gateway",
            )

        # 2. Check for exact match availability
        exact_fp = compute_request_fingerprint(
            normalized_request=request.prompt_text,
            model_id=request.model_id,
        )
        exact_match = await self.repository.find_exact_match(
            db=db,
            workspace_id=workspace_id,
            namespace=CacheNamespace.WORKSPACE.value,
            cache_key=exact_fp,
            project_id=request.project_id,
        )

        exact_available = exact_match is not None
        semantic_available = False
        candidate_sim = None
        freshness_label = "fresh" if exact_match else None

        # 3. Check for semantic candidate if no exact match
        if not exact_available and policy.semantic_enabled:
            query_embedding = await self.embedding.get_embedding(request.prompt_text)
            if query_embedding:
                candidates = await self.repository.find_semantic_candidates(
                    db=db,
                    workspace_id=workspace_id,
                    namespace=CacheNamespace.WORKSPACE.value,
                    query_embedding=query_embedding,
                    project_id=request.project_id,
                    limit=1,
                )
                if candidates:
                    top_entry, sim = candidates[0]
                    candidate_sim = round(sim, 4)
                    if sim >= policy.semantic_threshold:
                        semantic_available = True
                        freshness_label = "fresh"

        # 4. Formulate expected behavior
        if exact_available:
            expected = "Instant exact cache hit; AI execution skipped"
        elif semantic_available:
            expected = f"Semantic cache hit (similarity: {candidate_sim}); AI execution skipped"
        else:
            expected = "Cache miss; will execute via AI Gateway and evaluate for admission"

        return CachePreviewResponse(
            eligible=True,
            reason="Operation is deterministic and eligible for reuse",
            exact_match_available=exact_available,
            semantic_candidate_available=semantic_available,
            candidate_similarity=candidate_sim,
            freshness=freshness_label,
            expected_behavior=expected,
        )

    async def get_stats(
        self,
        db: AsyncSession,
        workspace_id: uuid.UUID,
    ) -> CacheStatsResponse:
        """Fetch factual metrics for workspace cache operations."""
        return await self.stats.get_stats(db, workspace_id, self.repository)

    async def list_entries(
        self,
        db: AsyncSession,
        workspace_id: uuid.UUID,
        namespace: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[CacheEntry], int]:
        """List cache entries with pagination."""
        return await self.repository.list_entries(
            db, workspace_id, namespace=namespace, status=status, limit=limit, offset=offset
        )

    async def get_entry(
        self,
        db: AsyncSession,
        entry_id: uuid.UUID,
    ) -> Optional[CacheEntry]:
        """Fetch a single entry by ID."""
        return await self.repository.get_by_id(db, entry_id)

    async def delete_entry(
        self,
        db: AsyncSession,
        entry_id: uuid.UUID,
        reason: str = "administrative_deletion",
    ) -> bool:
        """Invalidate/delete a specific cache entry."""
        count = await self.repository.invalidate_by_ids(db, [entry_id], reason)
        return count > 0

    async def handle_cleanup_job(
        self,
        db: AsyncSession,
        workspace_id: Optional[uuid.UUID] = None,
    ) -> int:
        """STEP 24 cleanup job handler: purge expired and stale entries."""
        return await self.repository.evict_expired(db, workspace_id=workspace_id)
