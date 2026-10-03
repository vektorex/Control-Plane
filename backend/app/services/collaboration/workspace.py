"""
Shared AI Workspace Aggregator for Step 39: Collaboration.
Aggregates heterogeneous resource state, presence, and activity across the unified collaboration layer.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.services.collaboration.models import (
    CollaborationActivity,
    CollaborationAssignment,
    CollaborationComment,
    CollaborationParticipant,
    CollaborationSession,
    PresenceState,
)
from backend.app.services.collaboration.presence import PresenceManager


class SharedWorkspaceService:
    """Aggregates real-time workspace context for collaborative task, document, and workflow execution."""

    def __init__(self, session: AsyncSession):
        self.db = session
        self.presence_mgr = PresenceManager(session)

    async def get_workspace_collaboration_summary(
        self,
        session_id: str,
    ) -> Dict[str, Any]:
        """
        Gathers high-level summary of active participants, presence, comments count,
        pending assignments, and recent activity for the session's resource.
        """
        # 1. Fetch active presence
        active_presence = await self.presence_mgr.get_active_presence(session_id)

        # 2. Count comments
        comment_count_q = select(func.count(CollaborationComment.id)).where(
            CollaborationComment.session_id == session_id,
            CollaborationComment.status != "deleted",
        )
        comm_res = await self.db.execute(comment_count_q)
        total_comments = comm_res.scalar() or 0

        # 3. Pending assignments
        assign_q = select(func.count(CollaborationAssignment.id)).where(
            CollaborationAssignment.session_id == session_id,
            CollaborationAssignment.status == "pending",
        )
        assign_res = await self.db.execute(assign_q)
        pending_assignments = assign_res.scalar() or 0

        return {
            "session_id": session_id,
            "active_participants_count": len(active_presence),
            "active_users": [p.user_id for p in active_presence],
            "total_comments": total_comments,
            "pending_assignments": pending_assignments,
        }
