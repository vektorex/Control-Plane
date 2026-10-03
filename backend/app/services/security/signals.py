"""
Security Signal Management Service for Step 34.
Ingests normalized events, executes deterministic detectors, and records signals.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.security.detectors import SecurityDetectionEngine
from backend.app.services.security.exceptions import SecuritySignalNotFoundError
from backend.app.services.security.models import SecuritySignal
from backend.app.services.security.schemas import (
    SecurityEventNormalized,
    SecuritySignalCreate,
    SecuritySignalResponse,
)


class SecuritySignalService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.detection_engine = SecurityDetectionEngine()

    async def ingest_event(self, event: SecurityEventNormalized) -> List[SecuritySignal]:
        """
        Normalizes incoming operational events, executes all 16 deterministic detectors,
        and persists detected security signals.
        """
        detected_creates = self.detection_engine.detect_signals(event)
        created_signals: List[SecuritySignal] = []

        now = datetime.now(timezone.utc)
        for create_data in detected_creates:
            sig = SecuritySignal(
                organization_id=create_data.organization_id,
                workspace_id=create_data.workspace_id,
                project_id=create_data.project_id,
                signal_type=create_data.signal_type,
                source_type=create_data.source_type,
                source_id=create_data.source_id,
                actor_type=create_data.actor_type,
                actor_id=create_data.actor_id,
                resource_type=create_data.resource_type,
                resource_id=create_data.resource_id,
                severity=create_data.severity,
                confidence=create_data.confidence,
                timestamp=create_data.timestamp or now,
                request_id=create_data.request_id,
                correlation_id=create_data.correlation_id,
                causation_id=create_data.causation_id,
                metadata_payload=create_data.metadata_payload,
                status="new",
                created_at=now,
            )
            self.session.add(sig)
            created_signals.append(sig)

        if created_signals:
            await self.session.flush()

        return created_signals

    async def list_signals(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        signal_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[SecuritySignal]:
        """
        Lists tenant-scoped security signals with filters.
        """
        query = select(SecuritySignal).where(SecuritySignal.organization_id == organization_id)

        if workspace_id:
            query = query.where(SecuritySignal.workspace_id == workspace_id)
        if severity:
            query = query.where(SecuritySignal.severity == severity)
        if status:
            query = query.where(SecuritySignal.status == status)
        if signal_type:
            query = query.where(SecuritySignal.signal_type == signal_type)
        if actor_id:
            query = query.where(SecuritySignal.actor_id == actor_id)

        query = query.order_by(desc(SecuritySignal.timestamp)).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_signal_by_id(
        self,
        signal_id: str,
        organization_id: str,
    ) -> SecuritySignal:
        """
        Retrieves a single security signal within the tenant boundary.
        """
        query = select(SecuritySignal).where(
            SecuritySignal.id == signal_id,
            SecuritySignal.organization_id == organization_id,
        )
        res = await self.session.execute(query)
        sig = res.scalar_one_or_none()
        if not sig:
            raise SecuritySignalNotFoundError(f"Security signal '{signal_id}' not found.")
        return sig

    async def update_status(
        self,
        signal_id: str,
        organization_id: str,
        status: str,
        notes: Optional[str] = None,
    ) -> SecuritySignal:
        """
        Updates signal status (new, triaged, correlated, resolved, dismissed).
        """
        sig = await self.get_signal_by_id(signal_id, organization_id)
        sig.status = status
        if notes:
            meta = dict(sig.metadata_payload or {})
            meta["status_notes"] = notes
            meta["status_updated_at"] = datetime.now(timezone.utc).isoformat()
            sig.metadata_payload = meta
        await self.session.flush()
        return sig
