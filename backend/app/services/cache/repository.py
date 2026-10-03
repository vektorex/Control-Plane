"""
Cache Repository for Step 31: Production-Grade Semantic Cache and Intelligent Reuse Layer.

Handles database persistence, exact index lookups, vector-based semantic retrieval,
hit counters, invalidation sweeps, and deterministic LRU/TTL evictions.
"""
import math
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import logging

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.cache.constants import (
    CacheNamespace,
    CacheStatus,
)
from backend.app.services.cache.models import CacheEntry
from backend.app.services.cache.schemas import (
    CacheAdmissionCandidate,
    CacheStatsResponse,
)

logger = logging.getLogger(__name__)


def compute_cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes exact cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return max(-1.0, min(1.0, dot / (norm1 * norm2)))


class CacheRepository:
    """Data access layer for CacheEntry records."""

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        entry_id: uuid.UUID,
    ) -> Optional[CacheEntry]:
        """Fetch a single cache entry by primary key."""
        stmt = select(CacheEntry).where(CacheEntry.id == entry_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def find_exact_match(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        namespace: str,
        cache_key: str,
        organization_id: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> Optional[CacheEntry]:
        """
        Exact cache key lookup against active and non-expired records.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(CacheEntry)
            .where(
                CacheEntry.workspace_id == workspace_id,
                CacheEntry.namespace == namespace,
                CacheEntry.cache_key == cache_key,
                CacheEntry.status == CacheStatus.ACTIVE.value,
            )
        )
        if organization_id:
            stmt = stmt.where(CacheEntry.organization_id == organization_id)
        if namespace == CacheNamespace.PROJECT.value and project_id:
            stmt = stmt.where(CacheEntry.project_id == project_id)
        if namespace == CacheNamespace.USER.value and user_id:
            stmt = stmt.where(CacheEntry.user_id == user_id)

        result = await db.execute(stmt)
        entries = result.scalars().all()
        for entry in entries:
            # Check if active and not hard expired
            if entry.expires_at and entry.expires_at.tzinfo is None:
                entry_expires = entry.expires_at.replace(tzinfo=timezone.utc)
            else:
                entry_expires = entry.expires_at

            if entry_expires > now:
                return entry
            else:
                # Mark as expired lazily
                entry.status = CacheStatus.EXPIRED.value
                await db.flush()

        return None

    @staticmethod
    async def find_semantic_candidates(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        namespace: str,
        query_embedding: List[float],
        organization_id: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        limit: int = 15,
    ) -> List[Tuple[CacheEntry, float]]:
        """
        Find candidates in the authorized scope with computed cosine similarity.
        Works seamlessly across both PostgreSQL + pgvector and SQLite.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(CacheEntry)
            .where(
                CacheEntry.workspace_id == workspace_id,
                CacheEntry.namespace == namespace,
                CacheEntry.status == CacheStatus.ACTIVE.value,
                CacheEntry.semantic_embedding.isnot(None),
            )
        )
        if organization_id:
            stmt = stmt.where(CacheEntry.organization_id == organization_id)
        if namespace == CacheNamespace.PROJECT.value and project_id:
            stmt = stmt.where(CacheEntry.project_id == project_id)
        if namespace == CacheNamespace.USER.value and user_id:
            stmt = stmt.where(CacheEntry.user_id == user_id)

        result = await db.execute(stmt)
        entries = result.scalars().all()

        scored: List[Tuple[CacheEntry, float]] = []
        for entry in entries:
            # Check expiration
            if entry.expires_at and entry.expires_at.tzinfo is None:
                entry_expires = entry.expires_at.replace(tzinfo=timezone.utc)
            else:
                entry_expires = entry.expires_at

            if entry_expires <= now:
                entry.status = CacheStatus.EXPIRED.value
                continue

            if entry.semantic_embedding:
                sim = compute_cosine_similarity(query_embedding, entry.semantic_embedding)
                scored.append((entry, sim))

        # Sort descending by similarity
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]

    @staticmethod
    async def create_entry(
        db: AsyncSession,
        candidate: CacheAdmissionCandidate,
        embedding: Optional[List[float]],
        expires_at: datetime,
    ) -> CacheEntry:
        """Persist a new reusable CacheEntry."""
        now = datetime.now(timezone.utc)
        entry = CacheEntry(
            id=uuid.uuid4(),
            organization_id=candidate.organization_id,
            workspace_id=candidate.workspace_id,
            project_id=candidate.project_id,
            user_id=candidate.user_id,
            namespace=candidate.namespace.value,
            cache_key=candidate.cache_key,
            semantic_embedding=embedding,
            normalized_request=candidate.normalized_request,
            request_fingerprint=candidate.request_fingerprint,
            response_content=candidate.response_content,
            response_metadata=candidate.response_metadata or {},
            source_snapshot=candidate.source_snapshot or {},
            prompt_id=candidate.prompt_id,
            prompt_version_id=candidate.prompt_version_id,
            model_id=candidate.model_id,
            model_provider=candidate.model_provider,
            execution_config_hash=candidate.execution_config_hash,
            context_hash=candidate.context_hash,
            artifact_hash=candidate.artifact_hash,
            graph_snapshot_hash=candidate.graph_snapshot_hash,
            memory_snapshot_hash=candidate.memory_snapshot_hash,
            status=CacheStatus.ACTIVE.value,
            expires_at=expires_at,
            created_at=now,
            accessed_at=now,
            hit_count=0,
        )
        db.add(entry)
        await db.flush()
        return entry

    @staticmethod
    async def record_hit(
        db: AsyncSession,
        entry_id: uuid.UUID,
    ) -> None:
        """Increment hit count and update accessed timestamp."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(CacheEntry)
            .where(CacheEntry.id == entry_id)
            .values(
                hit_count=CacheEntry.hit_count + 1,
                last_hit_at=now,
                accessed_at=now,
            )
        )
        await db.execute(stmt)
        await db.flush()

    @staticmethod
    async def invalidate_by_ids(
        db: AsyncSession,
        entry_ids: List[uuid.UUID],
        reason: str,
    ) -> int:
        """Mark specific entries as invalidated."""
        if not entry_ids:
            return 0
        now = datetime.now(timezone.utc)
        stmt = (
            update(CacheEntry)
            .where(
                CacheEntry.id.in_(entry_ids),
                CacheEntry.status == CacheStatus.ACTIVE.value,
            )
            .values(
                status=CacheStatus.INVALIDATED.value,
                invalidated_at=now,
                invalidation_reason=reason,
            )
        )
        result = await db.execute(stmt)
        await db.flush()
        return result.rowcount

    @staticmethod
    async def invalidate_by_filter(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        reason: str,
        namespace: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        prompt_version_id: Optional[uuid.UUID] = None,
        artifact_hash: Optional[str] = None,
        graph_snapshot_hash: Optional[str] = None,
        memory_snapshot_hash: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> int:
        """Invalidate entries matching given criteria within a workspace."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(CacheEntry)
            .where(
                CacheEntry.workspace_id == workspace_id,
                CacheEntry.status == CacheStatus.ACTIVE.value,
            )
        )
        if namespace:
            stmt = stmt.where(CacheEntry.namespace == namespace)
        if project_id:
            stmt = stmt.where(CacheEntry.project_id == project_id)
        if prompt_version_id:
            stmt = stmt.where(CacheEntry.prompt_version_id == prompt_version_id)
        if artifact_hash:
            stmt = stmt.where(CacheEntry.artifact_hash == artifact_hash)
        if graph_snapshot_hash:
            stmt = stmt.where(CacheEntry.graph_snapshot_hash == graph_snapshot_hash)
        if memory_snapshot_hash:
            stmt = stmt.where(CacheEntry.memory_snapshot_hash == memory_snapshot_hash)
        if model_id:
            stmt = stmt.where(CacheEntry.model_id == model_id)

        stmt = stmt.values(
            status=CacheStatus.INVALIDATED.value,
            invalidated_at=now,
            invalidation_reason=reason,
        )
        result = await db.execute(stmt)
        await db.flush()
        return result.rowcount

    @staticmethod
    async def evict_expired(
        db: AsyncSession,
        workspace_id: Optional[uuid.UUID] = None,
    ) -> int:
        """Mark all expired active entries as EXPIRED."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(CacheEntry)
            .where(
                CacheEntry.status == CacheStatus.ACTIVE.value,
                CacheEntry.expires_at <= now,
            )
        )
        if workspace_id:
            stmt = stmt.where(CacheEntry.workspace_id == workspace_id)

        stmt = stmt.values(status=CacheStatus.EXPIRED.value)
        result = await db.execute(stmt)
        await db.flush()
        return result.rowcount

    @staticmethod
    async def evict_lru_in_namespace(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        namespace: str,
        max_entries: int,
    ) -> int:
        """Evict least recently accessed entries if count exceeds max_entries."""
        count_stmt = (
            select(func.count())
            .select_from(CacheEntry)
            .where(
                CacheEntry.workspace_id == workspace_id,
                CacheEntry.namespace == namespace,
                CacheEntry.status == CacheStatus.ACTIVE.value,
            )
        )
        total = (await db.execute(count_stmt)).scalar() or 0
        if total <= max_entries:
            return 0

        excess = total - max_entries
        # Find oldest accessed entries
        subq = (
            select(CacheEntry.id)
            .where(
                CacheEntry.workspace_id == workspace_id,
                CacheEntry.namespace == namespace,
                CacheEntry.status == CacheStatus.ACTIVE.value,
            )
            .order_by(CacheEntry.accessed_at.asc())
            .limit(excess)
        )
        subq_res = await db.execute(subq)
        ids_to_evict = [row[0] for row in subq_res.all()]

        if ids_to_evict:
            now = datetime.now(timezone.utc)
            update_stmt = (
                update(CacheEntry)
                .where(CacheEntry.id.in_(ids_to_evict))
                .values(
                    status=CacheStatus.EXPIRED.value,
                    invalidated_at=now,
                    invalidation_reason="lru_capacity_eviction",
                )
            )
            await db.execute(update_stmt)
            await db.flush()
            return len(ids_to_evict)
        return 0

    @staticmethod
    async def list_entries(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        namespace: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[CacheEntry], int]:
        """List cache entries with pagination."""
        base_stmt = select(CacheEntry).where(CacheEntry.workspace_id == workspace_id)
        count_stmt = select(func.count()).select_from(CacheEntry).where(CacheEntry.workspace_id == workspace_id)

        if namespace:
            base_stmt = base_stmt.where(CacheEntry.namespace == namespace)
            count_stmt = count_stmt.where(CacheEntry.namespace == namespace)
        if status:
            base_stmt = base_stmt.where(CacheEntry.status == status)
            count_stmt = count_stmt.where(CacheEntry.status == status)

        total = (await db.execute(count_stmt)).scalar() or 0
        query = base_stmt.order_by(CacheEntry.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return result.scalars().all(), total

    @staticmethod
    async def get_storage_bytes(
        db: AsyncSession,
        workspace_id: uuid.UUID,
    ) -> int:
        """Estimate total storage consumed by cached response content in bytes."""
        stmt = (
            select(
                func.coalesce(
                    func.sum(func.length(CacheEntry.response_content) + func.length(CacheEntry.normalized_request)),
                    0,
                )
            )
            .where(
                CacheEntry.workspace_id == workspace_id,
                CacheEntry.status == CacheStatus.ACTIVE.value,
            )
        )
        res = await db.execute(stmt)
        return int(res.scalar() or 0)
