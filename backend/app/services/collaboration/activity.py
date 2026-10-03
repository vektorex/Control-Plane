"""
Shared Collaboration Activity Feed Service for Step 39: Collaboration.
Records human, AI, and system timeline actions for full session visibility.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.services.collaboration.models import CollaborationActivity


class CollaborationActivityLogger:
    """Records sanitized activity entries and queries the activity timeline."""

    def __init__(self, session: AsyncSession):
        self.db = session

    async def log_activity(
        self,
        session_id: str,
        actor_type: str,  # user, ai, system
        activity_type: str,
        resource_type: str,
        resource_id: str,
        summary: str,
        actor_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CollaborationActivity:
        """Appends a new activity item to the shared timeline."""
        clean_summary = summary[:500]
        activity = CollaborationActivity(
            session_id=session_id,
            actor_type=actor_type,
            actor_id=actor_id,
            activity_type=activity_type,
            resource_type=resource_type,
            resource_id=resource_id,
            summary=clean_summary,
            activity_metadata=metadata or {},
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(activity)
        await self.db.flush()
        return activity

    async def list_activity(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
        activity_type: Optional[str] = None,
    ) -> List[CollaborationActivity]:
        """Lists activity items ordered chronologically descending."""
        query = select(CollaborationActivity).where(CollaborationActivity.session_id == session_id)
        if activity_type:
            query = query.where(CollaborationActivity.activity_type == activity_type)
        query = query.order_by(desc(CollaborationActivity.created_at)).offset(offset).limit(min(limit, 100))
        result = await self.db.execute(query)
        return list(result.scalars().all())
