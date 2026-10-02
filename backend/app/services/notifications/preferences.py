"""
NotificationPreferenceService: Resolution of multi-level notification preferences.
"""
from typing import Dict, List, Optional
from uuid import UUID
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.notification import NotificationPreference
from backend.app.services.notifications.constants import (
    DeliveryChannelType,
    MANDATORY_IN_APP_EVENTS,
)


class NotificationPreferenceService:
    """
    Evaluates whether a notification should be delivered to a recipient across a given channel.
    Follows priority:
    1. Explicit User + Event preference
    2. User Global ('*') preference
    3. Workspace + Event preference
    4. Workspace Global ('*') preference
    5. System Default (in_app=True, external=False unless configured)
    """

    @classmethod
    async def is_channel_enabled(
        cls,
        session: AsyncSession,
        workspace_id: UUID,
        event_type: str,
        channel: str,
        user_id: Optional[UUID] = None,
    ) -> bool:
        # 1. Critical and HITL approval notifications are ALWAYS enabled for in-app delivery
        if channel == DeliveryChannelType.IN_APP.value and event_type in MANDATORY_IN_APP_EVENTS:
            return True

        # Query all matching preferences for workspace (and user if present)
        stmt = select(NotificationPreference).where(
            NotificationPreference.workspace_id == workspace_id,
            NotificationPreference.channel == channel,
            NotificationPreference.event_type.in_([event_type, "*"]),
        )
        if user_id:
            stmt = stmt.where(or_(NotificationPreference.user_id == user_id, NotificationPreference.user_id == None))
        else:
            stmt = stmt.where(NotificationPreference.user_id == None)

        res = await session.execute(stmt)
        prefs = list(res.scalars().all())

        if not prefs:
            # System defaults: in_app enabled, webhooks enabled if configured, email disabled by default
            if channel == DeliveryChannelType.IN_APP.value:
                return True
            if channel == DeliveryChannelType.WEBHOOK.value:
                return True
            return False

        # Sort by specificity:
        # Highest: matching user_id AND matching event_type
        # Next: matching user_id AND event_type == '*'
        # Next: user_id is None AND matching event_type
        # Lowest: user_id is None AND event_type == '*'
        def _pref_rank(p: NotificationPreference) -> int:
            score = 0
            if p.user_id == user_id and user_id is not None:
                score += 10
            if p.event_type == event_type:
                score += 5
            return score

        prefs.sort(key=_pref_rank, reverse=True)
        top_pref = prefs[0]
        return top_pref.enabled
