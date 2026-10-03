"""
Cache Statistics Service for Step 31: Production-Grade Semantic Cache and Intelligent Reuse Layer.

Tracks non-subjective, factual telemetry regarding lookups, exact hits, semantic hits,
misses, bypasses, admission decisions, and storage footprints.
"""
import uuid
from typing import Dict, Optional
from collections import defaultdict
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.cache.repository import CacheRepository
from backend.app.services.cache.schemas import CacheStatsResponse

logger = logging.getLogger(__name__)


class CacheStatisticsService:
    """In-memory telemetry counters paired with database aggregations."""

    _counters: Dict[uuid.UUID, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    @classmethod
    def record_lookup(cls, workspace_id: uuid.UUID) -> None:
        cls._counters[workspace_id]["lookups"] += 1

    @classmethod
    def record_exact_hit(cls, workspace_id: uuid.UUID) -> None:
        cls._counters[workspace_id]["exact_hits"] += 1

    @classmethod
    def record_semantic_hit(cls, workspace_id: uuid.UUID) -> None:
        cls._counters[workspace_id]["semantic_hits"] += 1

    @classmethod
    def record_miss(cls, workspace_id: uuid.UUID) -> None:
        cls._counters[workspace_id]["misses"] += 1

    @classmethod
    def record_bypass(cls, workspace_id: uuid.UUID) -> None:
        cls._counters[workspace_id]["bypasses"] += 1

    @classmethod
    def record_invalidation(cls, workspace_id: uuid.UUID, count: int = 1) -> None:
        cls._counters[workspace_id]["invalidations"] += count

    @classmethod
    def record_refresh(cls, workspace_id: uuid.UUID) -> None:
        cls._counters[workspace_id]["refreshes"] += 1

    @classmethod
    def record_admitted(cls, workspace_id: uuid.UUID) -> None:
        cls._counters[workspace_id]["admitted_entries"] += 1

    @classmethod
    def record_rejected(cls, workspace_id: uuid.UUID) -> None:
        cls._counters[workspace_id]["rejected_entries"] += 1

    @classmethod
    async def get_stats(
        cls,
        db: AsyncSession,
        workspace_id: uuid.UUID,
        repository: Optional[CacheRepository] = None,
    ) -> CacheStatsResponse:
        """
        Aggregate in-memory counters with database counts and storage footprint.
        """
        repo = repository or CacheRepository()
        c = cls._counters[workspace_id]

        lookups = c["lookups"]
        exact_hits = c["exact_hits"]
        semantic_hits = c["semantic_hits"]
        total_hits = exact_hits + semantic_hits
        hit_ratio = round(total_hits / max(1, lookups), 4) if lookups > 0 else 0.0

        # Query DB for active entries count and estimated storage
        _, active_count = await repo.list_entries(db, workspace_id=workspace_id, status="active", limit=1)
        storage_bytes = await repo.get_storage_bytes(db, workspace_id=workspace_id)

        return CacheStatsResponse(
            lookups=lookups,
            exact_hits=exact_hits,
            semantic_hits=semantic_hits,
            misses=c["misses"],
            bypasses=c["bypasses"],
            invalidations=c["invalidations"],
            refreshes=c["refreshes"],
            admitted_entries=c["admitted_entries"],
            rejected_entries=c["rejected_entries"],
            active_entries=active_count,
            storage_bytes=storage_bytes,
            hit_ratio=hit_ratio,
        )
