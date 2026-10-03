"""
Cache Admission Service for Step 31: Production-Grade Semantic Cache and Intelligent Reuse Layer.

Applies strict admission gates: eligibility checks, evaluation pass validation, size limits,
deep secret & chain-of-thought sanitization, and vector embedding calculation.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.cache.constants import (
    CACHE_MAX_RESPONSE_BYTES,
    CacheNamespace,
)
from backend.app.services.cache.eligibility import CacheEligibilityService
from backend.app.services.cache.embeddings import CacheEmbeddingService
from backend.app.services.cache.models import CacheEntry
from backend.app.services.cache.policies import CachePolicyEngine
from backend.app.services.cache.repository import CacheRepository
from backend.app.services.cache.sanitizer import CacheSanitizer
from backend.app.services.cache.schemas import (
    CacheAdmissionCandidate,
    CachePolicyConfig,
)
from backend.app.services.cache.statistics import CacheStatisticsService

logger = logging.getLogger(__name__)


class CacheAdmissionService:
    """Evaluates and admits completed AI execution results into the cache."""

    def __init__(
        self,
        repository: Optional[CacheRepository] = None,
        eligibility_service: Optional[CacheEligibilityService] = None,
        policy_engine: Optional[CachePolicyEngine] = None,
        embedding_service: Optional[CacheEmbeddingService] = None,
        sanitizer: Optional[CacheSanitizer] = None,
        stats_service: Optional[CacheStatisticsService] = None,
    ):
        self.repository = repository or CacheRepository()
        self.eligibility_service = eligibility_service or CacheEligibilityService()
        self.policy_engine = policy_engine or CachePolicyEngine()
        self.embedding_service = embedding_service or CacheEmbeddingService()
        self.sanitizer = sanitizer or CacheSanitizer()
        self.stats_service = stats_service or CacheStatisticsService()

    async def admit(
        self,
        db: AsyncSession,
        candidate: CacheAdmissionCandidate,
        task_type: Optional[str] = None,
        execution_success: bool = True,
        evaluation_passed: bool = True,
        strict_evaluation: bool = False,
        policy: Optional[CachePolicyConfig] = None,
    ) -> Tuple[Optional[CacheEntry], Optional[str]]:
        """
        Admit execution output into the semantic cache if all gates pass.
        Returns (CacheEntry, None) if admitted, or (None, rejection_reason) if rejected.
        """
        # 1. Workspace Policy Check
        if not policy:
            policy = await self.policy_engine.get_workspace_policy(db, candidate.workspace_id)

        if not policy.enabled:
            self.stats_service.record_rejected(candidate.workspace_id)
            return None, "Caching disabled by workspace policy"

        # 2. Execution Success Gate
        if not execution_success:
            self.stats_service.record_rejected(candidate.workspace_id)
            return None, "Execution failed or incomplete"

        # 3. Evaluation Gate
        if strict_evaluation and not evaluation_passed:
            self.stats_service.record_rejected(candidate.workspace_id)
            return None, "Evaluation gate failed"

        # 4. Operation Eligibility Gate
        is_eligible, elig_reason = self.eligibility_service.is_cacheable(
            task_type=task_type,
            parameters=candidate.source_snapshot,
            has_side_effects=False,
            requires_hitl=False,
        )
        if not is_eligible:
            self.stats_service.record_rejected(candidate.workspace_id)
            return None, f"Operation ineligible: {elig_reason}"

        # 5. Response Size Gate
        content_bytes = len(candidate.response_content.encode("utf-8"))
        max_bytes = policy.max_entry_size or CACHE_MAX_RESPONSE_BYTES
        if content_bytes > max_bytes:
            self.stats_service.record_rejected(candidate.workspace_id)
            return None, f"Response size ({content_bytes} bytes) exceeds limit ({max_bytes} bytes)"

        # 6. Deep Sanitization (Strip credentials, bearer tokens, CoT, etc.)
        sanitized_content = self.sanitizer.sanitize_text(candidate.response_content)
        sanitized_metadata = self.sanitizer.sanitize_metadata(candidate.response_metadata or {})

        # 7. Embedding Generation for Semantic Caching
        embedding: Optional[list[float]] = None
        if policy.semantic_enabled:
            embedding = candidate.semantic_embedding
            if not embedding:
                embedding = await self.embedding_service.get_embedding(candidate.normalized_request)

        # 8. TTL and Expiration Computation
        ttl = candidate.ttl_seconds or policy.default_ttl
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl)

        # 9. Clone candidate with sanitized content
        sanitized_candidate = candidate.model_copy(
            update={
                "response_content": sanitized_content,
                "response_metadata": sanitized_metadata,
            }
        )

        # 10. Evict Oldest Entries If Namespace Capacity Exceeded
        await self.repository.evict_lru_in_namespace(
            db=db,
            workspace_id=candidate.workspace_id,
            namespace=candidate.namespace.value,
            max_entries=policy.max_namespace_entries,
        )

        # 11. Write To Repository
        try:
            entry = await self.repository.create_entry(
                db=db,
                candidate=sanitized_candidate,
                embedding=embedding,
                expires_at=expires_at,
            )
            self.stats_service.record_admitted(candidate.workspace_id)
            logger.info("Admitted cache entry %s for workspace %s", entry.id, candidate.workspace_id)
            return entry, None
        except Exception as exc:
            logger.error("Failed to persist cache entry: %s", exc, exc_info=True)
            self.stats_service.record_rejected(candidate.workspace_id)
            return None, f"Storage error: {str(exc)}"
