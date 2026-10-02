"""
Database Repository for Step 26: Unified Event Bus.
Provides transactional event store persistence, sequence numbering,
idempotency checks, consumer delivery tracking, and stream querying.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import and_, delete, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.event import Event, EventDelivery
from backend.app.services.events.constants import (
    AUDITABLE_EVENTS,
    EventDeliveryStatus,
)
from backend.app.services.events.errors import EventNotFoundError
from backend.app.services.events.filters import EventFilterValidator


class EventRepository:
    """
    Data access layer for durable events and consumer deliveries.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_event(
        self,
        workspace_id: uuid.UUID,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        project_id: Optional[uuid.UUID] = None,
        actor_type: str = "system",
        actor_id: Optional[str] = None,
        parent_event_id: Optional[uuid.UUID] = None,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Tuple[Event, bool]:
        """
        Atomically persists an event.
        Returns (Event, is_new: bool). If idempotency_key already exists for workspace,
        returns the existing event with is_new=False without duplicating.
        """
        # 1. Idempotency check
        if idempotency_key:
            stmt = select(Event).where(
                Event.workspace_id == workspace_id,
                Event.idempotency_key == idempotency_key,
            )
            res = await self.session.execute(stmt)
            existing = res.scalar_one_or_none()
            if existing:
                return existing, False

        # 2. Compute next monotonic sequence number for the aggregate within workspace
        seq_stmt = select(func.coalesce(func.max(Event.sequence_number), 0) + 1).where(
            Event.workspace_id == workspace_id,
            Event.aggregate_type == aggregate_type,
            Event.aggregate_id == aggregate_id,
        )
        seq_res = await self.session.execute(seq_stmt)
        next_seq = seq_res.scalar_one()

        # 3. Create Event instance
        event = Event(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            project_id=project_id,
            actor_type=actor_type,
            actor_id=actor_id,
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            parent_event_id=parent_event_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
            sequence_number=next_seq,
            idempotency_key=idempotency_key,
            payload=payload,
            metadata_json=metadata or {},
        )
        self.session.add(event)
        await self.session.flush()
        return event, True

    async def get_by_id(
        self,
        event_id: uuid.UUID,
        workspace_id: Optional[uuid.UUID] = None,
    ) -> Optional[Event]:
        stmt = select(Event).where(Event.id == event_id)
        if workspace_id:
            stmt = stmt.where(Event.workspace_id == workspace_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_events(
        self,
        workspace_id: uuid.UUID,
        project_id: Optional[uuid.UUID] = None,
        event_type_pattern: Optional[str] = None,
        aggregate_type: Optional[str] = None,
        aggregate_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        after_id: Optional[uuid.UUID] = None,
        limit: int = 50,
    ) -> List[Event]:
        """
        Lists events ordered by created_at ascending or descending.
        """
        stmt = select(Event).where(Event.workspace_id == workspace_id)

        if project_id:
            stmt = stmt.where(Event.project_id == project_id)

        if aggregate_type:
            stmt = stmt.where(Event.aggregate_type == aggregate_type)

        if aggregate_id:
            stmt = stmt.where(Event.aggregate_id == aggregate_id)

        if correlation_id:
            stmt = stmt.where(Event.correlation_id == correlation_id)

        if event_type_pattern and event_type_pattern != "*":
            if event_type_pattern.endswith(".*"):
                prefix = event_type_pattern[:-1]  # e.g. "workflow."
                stmt = stmt.where(Event.event_type.like(f"{prefix}%"))
            else:
                stmt = stmt.where(Event.event_type == event_type_pattern)

        if after_id:
            # Subquery to find after event's created_at
            sub_stmt = select(Event.created_at).where(Event.id == after_id)
            sub_res = await self.session.execute(sub_stmt)
            after_created = sub_res.scalar_one_or_none()
            if after_created:
                stmt = stmt.where(Event.created_at > after_created)

        stmt = stmt.order_by(Event.created_at.desc()).limit(min(limit, 100))
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def replay_events(
        self,
        workspace_id: uuid.UUID,
        after_id: Optional[uuid.UUID] = None,
        event_type_pattern: Optional[str] = None,
        limit: int = 50,
    ) -> List[Event]:
        """
        Replays events chronologically (ASC) after a given cursor event ID.
        Used for SSE reconnection with Last-Event-ID.
        """
        stmt = select(Event).where(Event.workspace_id == workspace_id)

        if event_type_pattern and event_type_pattern != "*":
            if event_type_pattern.endswith(".*"):
                prefix = event_type_pattern[:-1]
                stmt = stmt.where(Event.event_type.like(f"{prefix}%"))
            else:
                stmt = stmt.where(Event.event_type == event_type_pattern)

        if after_id:
            sub_stmt = select(Event.created_at).where(Event.id == after_id)
            sub_res = await self.session.execute(sub_stmt)
            after_created = sub_res.scalar_one_or_none()
            if after_created:
                stmt = stmt.where(Event.created_at > after_created)

        stmt = stmt.order_by(Event.created_at.asc()).limit(min(limit, 100))
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def create_deliveries_for_consumers(
        self,
        event_id: uuid.UUID,
        consumer_names: List[str],
    ) -> List[EventDelivery]:
        """
        Initializes pending EventDelivery records for registered consumers.
        """
        deliveries = []
        for name in consumer_names:
            delivery = EventDelivery(
                id=uuid.uuid4(),
                event_id=event_id,
                consumer_name=name,
                status=EventDeliveryStatus.PENDING.value,
                attempt_count=0,
                available_at=datetime.now(timezone.utc),
            )
            self.session.add(delivery)
            deliveries.append(delivery)
        await self.session.flush()
        return deliveries

    async def update_delivery_status(
        self,
        delivery_id: uuid.UUID,
        status: str,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        stmt = (
            update(EventDelivery)
            .where(EventDelivery.id == delivery_id)
            .values(
                status=status,
                attempt_count=EventDelivery.attempt_count + 1,
                processed_at=datetime.now(timezone.utc) if status == EventDeliveryStatus.COMPLETED.value else None,
                error_code=error_code,
                error_message=error_message,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def cleanup_old_events(self, retention_days: int = 30) -> int:
        """
        Removes non-auditable events older than retention_days.
        Preserves auditable records indefinitely.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        stmt = (
            delete(Event)
            .where(
                Event.created_at < cutoff,
                Event.event_type.not_in(list(AUDITABLE_EVENTS)),
            )
        )
        res = await self.session.execute(stmt)
        return res.rowcount or 0
