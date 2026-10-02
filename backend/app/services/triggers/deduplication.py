"""
Idempotency, deduplication, and debouncing service for workflow triggers.
"""
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Tuple
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.db.models.trigger import TriggerRun, WorkflowTrigger


class TriggerDeduplicationService:
    """
    Guarantees deterministic idempotency and debouncing across triggers.
    """

    # In-memory hot-path cache: key -> timestamp (float)
    _memory_cache: Dict[str, float] = {}

    @classmethod
    def _clean_cache(cls) -> None:
        """Prunes cache entries older than window."""
        now = time.time()
        window = getattr(settings, "TRIGGER_DEDUPLICATION_WINDOW_SECONDS", 3600)
        expired = [k for k, ts in cls._memory_cache.items() if now - ts > window]
        for k in expired:
            cls._memory_cache.pop(k, None)

    @classmethod
    async def check_and_record_idempotency(
        cls,
        session: AsyncSession,
        trigger_id: uuid.UUID,
        idempotency_key: Optional[str] = None,
        event_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Checks whether an event or idempotency key has already been received within window.
        Returns (is_duplicate: bool, reason: Optional[str]).
        """
        cls._clean_cache()
        key = idempotency_key or event_id
        if not key:
            return False, None

        cache_key = f"{trigger_id}:{key}"
        now_ts = time.time()
        window_seconds = getattr(settings, "TRIGGER_DEDUPLICATION_WINDOW_SECONDS", 3600)

        # 1. Hot-path check
        if cache_key in cls._memory_cache:
            if now_ts - cls._memory_cache[cache_key] < window_seconds:
                return True, f"Duplicate key '{key}' detected in deduplication window."

        # 2. Database verification within window
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)

        stmt = (
            select(TriggerRun.id)
            .where(
                TriggerRun.trigger_id == trigger_id,
                TriggerRun.created_at >= cutoff,
                (TriggerRun.idempotency_key == key) | (TriggerRun.event_id == key),
            )
            .limit(1)
        )
        result = await session.execute(stmt)
        existing_run_id = result.scalar_one_or_none()

        if existing_run_id:
            cls._memory_cache[cache_key] = now_ts
            return True, f"Existing trigger run {existing_run_id} matched key '{key}' within {window_seconds}s window."

        # Mark in cache
        cls._memory_cache[cache_key] = now_ts
        return False, None

    @classmethod
    async def check_debounce(
        cls,
        session: AsyncSession,
        trigger_id: uuid.UUID,
        debounce_seconds: Optional[int],
    ) -> Tuple[bool, Optional[int]]:
        """
        Checks if trigger execution should be debounced.
        Returns (is_debounced: bool, remaining_seconds: Optional[int]).
        """
        if not debounce_seconds or debounce_seconds <= 0:
            return False, None

        # Bounded to max 3600 seconds
        effective_debounce = min(debounce_seconds, 3600)
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=effective_debounce)

        stmt = (
            select(TriggerRun.created_at)
            .where(
                TriggerRun.trigger_id == trigger_id,
                TriggerRun.created_at >= cutoff,
                TriggerRun.status.not_in(["skipped", "cancelled"]),
            )
            .order_by(desc(TriggerRun.created_at))
            .limit(1)
        )
        result = await session.execute(stmt)
        last_created_at = result.scalar_one_or_none()

        if last_created_at:
            # Normalize timezone
            if last_created_at.tzinfo is None:
                last_created_at = last_created_at.replace(tzinfo=timezone.utc)
            elapsed = (datetime.now(timezone.utc) - last_created_at).total_seconds()
            if elapsed < effective_debounce:
                remaining = int(effective_debounce - elapsed)
                return True, remaining

        return False, None
