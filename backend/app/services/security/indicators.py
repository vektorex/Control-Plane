"""
Security Indicators Service for Step 34.
Manages tenant-scoped threat indicators, request/session fingerprints, and suspicious artifact hashes.
Never stores raw secrets or plaintext tokens.
"""
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.security.models import SecurityIndicator
from backend.app.services.security.schemas import SecurityIndicatorCreate


def compute_indicator_hash(value: str) -> str:
    """Computes deterministic SHA-256 hash for indicator value matching."""
    return hashlib.sha256(value.strip().encode("utf-8")).hexdigest()


class SecurityIndicatorService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_indicator(
        self,
        organization_id: str,
        data: SecurityIndicatorCreate,
    ) -> SecurityIndicator:
        """
        Creates or updates a security indicator using deterministic hash matching.
        """
        val_hash = compute_indicator_hash(data.value_display)
        now = datetime.now(timezone.utc)

        # Check existing indicator by hash in tenant
        q = select(SecurityIndicator).where(
            SecurityIndicator.organization_id == organization_id,
            SecurityIndicator.indicator_type == data.indicator_type,
            SecurityIndicator.value_hash == val_hash,
        )
        res = await self.session.execute(q)
        existing = res.scalar_one_or_none()

        if existing:
            existing.last_seen_at = now
            existing.confidence = max(existing.confidence, data.confidence)
            existing.status = data.status
            if data.metadata:
                meta = dict(existing.metadata_payload or {})
                meta.update(data.metadata)
                existing.metadata_payload = meta
            await self.session.flush()
            return existing

        # Create new indicator
        ind = SecurityIndicator(
            organization_id=organization_id,
            indicator_type=data.indicator_type,
            value_hash=val_hash,
            value_display=data.value_display,
            source=data.source,
            confidence=data.confidence,
            first_seen_at=now,
            last_seen_at=now,
            status=data.status,
            metadata_payload=data.metadata or {},
        )
        self.session.add(ind)
        await self.session.flush()
        return ind

    async def list_indicators(
        self,
        organization_id: str,
        indicator_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[SecurityIndicator]:
        """
        Lists tenant-scoped threat indicators with filtering.
        """
        query = select(SecurityIndicator).where(SecurityIndicator.organization_id == organization_id)
        if indicator_type:
            query = query.where(SecurityIndicator.indicator_type == indicator_type)
        if status:
            query = query.where(SecurityIndicator.status == status)

        query = query.order_by(desc(SecurityIndicator.last_seen_at)).limit(limit).offset(offset)
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def is_indicator_flagged(
        self,
        organization_id: str,
        indicator_type: str,
        value: str,
    ) -> bool:
        """
        Checks if a given value's SHA-256 fingerprint is currently flagged as an active threat indicator.
        """
        val_hash = compute_indicator_hash(value)
        query = select(SecurityIndicator.id).where(
            SecurityIndicator.organization_id == organization_id,
            SecurityIndicator.indicator_type == indicator_type,
            SecurityIndicator.value_hash == val_hash,
            SecurityIndicator.status == "active",
        )
        res = await self.session.execute(query)
        return res.scalar_one_or_none() is not None
