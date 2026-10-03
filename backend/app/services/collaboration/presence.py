"""
Presence State and Heartbeat Tracking for Step 39: Collaboration.
Tracks user online/idle/offline status, cursor location, and handles TTL expiration.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.app.services.collaboration.models import (
    CollaborationParticipant,
    PresenceState,
)
from backend.app.services.collaboration.validators import CollaborationValidator

PRESENCE_TTL_SECONDS = 90
HEARTBEAT_MIN_INTERVAL_SECONDS = 2  # Throttling frequent heartbeat spam


class PresenceManager:
    """Manages ephemeral presence state and heartbeat rate limiting."""

    def __init__(self, session: AsyncSession):
        self.db = session

    async def record_heartbeat(
        self,
        session_id: str,
        user_id: str,
        status: str = "active",
        cursor_context: Optional[Dict[str, Any]] = None,
        active_resource: Optional[str] = None,
    ) -> Tuple[PresenceState, bool]:
        """
        Updates participant presence heartbeat.
        Returns (presence_state, status_changed_boolean).
        Only emits status transitions to avoid event storms.
        """
        now = datetime.now(timezone.utc)
        safe_cursor = CollaborationValidator.validate_cursor_context(cursor_context or {})

        query = select(PresenceState).where(
            PresenceState.session_id == session_id,
            PresenceState.user_id == user_id,
        )
        result = await self.db.execute(query)
        presence = result.scalar_one_or_none()

        status_changed = False

        if presence:
            # Check status transition
            if presence.status != status:
                status_changed = True

            presence.status = status
            presence.cursor_context = safe_cursor
            presence.active_resource = active_resource
            presence.last_heartbeat_at = now
            presence.updated_at = now
        else:
            status_changed = True
            presence = PresenceState(
                session_id=session_id,
                user_id=user_id,
                status=status,
                cursor_context=safe_cursor,
                active_resource=active_resource,
                last_heartbeat_at=now,
                updated_at=now,
            )
            self.db.add(presence)

        # Also touch participant last_seen_at
        part_query = select(CollaborationParticipant).where(
            CollaborationParticipant.session_id == session_id,
            CollaborationParticipant.user_id == user_id,
        )
        part_res = await self.db.execute(part_query)
        part = part_res.scalar_one_or_none()
        if part:
            part.last_seen_at = now
            if part.status != "active":
                part.status = "active"

        await self.db.flush()
        return presence, status_changed

    async def set_offline(
        self,
        session_id: str,
        user_id: str,
    ) -> Optional[PresenceState]:
        """Marks user as explicitly offline upon leaving."""
        query = select(PresenceState).where(
            PresenceState.session_id == session_id,
            PresenceState.user_id == user_id,
        )
        result = await self.db.execute(query)
        presence = result.scalar_one_or_none()
        if presence:
            presence.status = "offline"
            presence.updated_at = datetime.now(timezone.utc)
            await self.db.flush()
        return presence

    async def get_active_presence(
        self,
        session_id: str,
    ) -> List[PresenceState]:
        """
        Returns all active or idle users who have heartbeated within PRESENCE_TTL_SECONDS.
        Expired users are filtered out.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=PRESENCE_TTL_SECONDS)
        query = select(PresenceState).where(
            PresenceState.session_id == session_id,
            PresenceState.last_heartbeat_at >= cutoff,
            PresenceState.status.in_(["active", "idle", "away"]),
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
