"""
Repository persistence layer for Step 39: Collaboration.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from backend.app.services.collaboration.models import (
    CoExecutionSession,
    CollaborationActivity,
    CollaborationAnnotation,
    CollaborationAssignment,
    CollaborationChange,
    CollaborationComment,
    CollaborationConflict,
    CollaborationDecision,
    CollaborationLock,
    CollaborationParticipant,
    CollaborationSession,
    CollaborationSnapshot,
    CollaborativeState,
    CommentMention,
    PresenceState,
)


class CollaborationRepository:
    """Async repository for collaboration database entities."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_session(self, session_id: str) -> Optional[CollaborationSession]:
        query = (
            select(CollaborationSession)
            .options(selectinload(CollaborationSession.participants))
            .where(CollaborationSession.id == session_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_participant(self, session_id: str, user_id: str) -> Optional[CollaborationParticipant]:
        query = select(CollaborationParticipant).where(
            CollaborationParticipant.session_id == session_id,
            CollaborationParticipant.user_id == user_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_participants(self, session_id: str) -> List[CollaborationParticipant]:
        query = select(CollaborationParticipant).where(CollaborationParticipant.session_id == session_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_conflicts(self, session_id: str, status: Optional[str] = None) -> List[CollaborationConflict]:
        query = select(CollaborationConflict).where(CollaborationConflict.session_id == session_id)
        if status:
            query = query.where(CollaborationConflict.status == status)
        query = query.order_by(desc(CollaborationConflict.created_at))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_co_execution(self, co_session_id: str) -> Optional[CoExecutionSession]:
        query = select(CoExecutionSession).where(CoExecutionSession.id == co_session_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
