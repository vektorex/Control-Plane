"""
Collaboration Session Lifecycle and Participant Management for Step 39: Collaboration.
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from backend.app.services.collaboration.exceptions import (
    ParticipantNotFoundError,
    SessionNotFoundError,
)
from backend.app.services.collaboration.models import (
    CollaborationDecision,
    CollaborationParticipant,
    CollaborationSession,
    PresenceState,
)


class CollaborationSessionManager:
    """Manages creation, membership, role assignment, and closure of collaboration sessions."""

    def __init__(self, session: AsyncSession):
        self.db = session

    async def create_session(
        self,
        organization_id: str,
        workspace_id: str,
        resource_type: str,
        resource_id: str,
        created_by: str,
        project_id: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> CollaborationSession:
        """Creates a new collaboration session and registers the creator as owner participant."""
        now = datetime.now(timezone.utc)
        session = CollaborationSession(
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            resource_type=resource_type,
            resource_id=resource_id,
            created_by=created_by,
            status="active",
            created_at=now,
            last_activity_at=now,
            expires_at=expires_at,
        )
        self.db.add(session)
        await self.db.flush()

        # Add creator as owner participant
        owner = CollaborationParticipant(
            session_id=session.id,
            user_id=created_by,
            role="owner",
            status="active",
            joined_at=now,
            last_seen_at=now,
        )
        self.db.add(owner)
        await self.db.flush()
        return session

    async def get_session(self, session_id: str) -> CollaborationSession:
        """Retrieves session with participants."""
        query = (
            select(CollaborationSession)
            .options(selectinload(CollaborationSession.participants))
            .where(CollaborationSession.id == session_id)
        )
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()
        if not session:
            raise SessionNotFoundError(session_id)
        return session

    async def list_sessions(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[CollaborationSession]:
        """Lists tenant-scoped collaboration sessions."""
        query = select(CollaborationSession).where(CollaborationSession.organization_id == organization_id)
        if workspace_id:
            query = query.where(CollaborationSession.workspace_id == workspace_id)
        if resource_type:
            query = query.where(CollaborationSession.resource_type == resource_type)
        if resource_id:
            query = query.where(CollaborationSession.resource_id == resource_id)
        if status:
            query = query.where(CollaborationSession.status == status)

        query = query.order_by(desc(CollaborationSession.last_activity_at)).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def join_session(
        self,
        session_id: str,
        user_id: str,
        role: str = "editor",
    ) -> CollaborationParticipant:
        """Adds a user to a session or activates existing participation."""
        session = await self.get_session(session_id)
        now = datetime.now(timezone.utc)

        query = select(CollaborationParticipant).where(
            CollaborationParticipant.session_id == session_id,
            CollaborationParticipant.user_id == user_id,
        )
        result = await self.db.execute(query)
        participant = result.scalar_one_or_none()

        if participant:
            participant.status = "active"
            participant.last_seen_at = now
            participant.left_at = None
        else:
            participant = CollaborationParticipant(
                session_id=session_id,
                user_id=user_id,
                role=role,
                status="active",
                joined_at=now,
                last_seen_at=now,
            )
            self.db.add(participant)

        session.last_activity_at = now
        await self.db.flush()
        return participant

    async def leave_session(
        self,
        session_id: str,
        user_id: str,
    ) -> CollaborationParticipant:
        """Marks a participant as offline/left."""
        query = select(CollaborationParticipant).where(
            CollaborationParticipant.session_id == session_id,
            CollaborationParticipant.user_id == user_id,
        )
        result = await self.db.execute(query)
        participant = result.scalar_one_or_none()
        if not participant:
            raise ParticipantNotFoundError(user_id, session_id)

        now = datetime.now(timezone.utc)
        participant.status = "offline"
        participant.left_at = now

        # Update presence state
        pres_query = select(PresenceState).where(
            PresenceState.session_id == session_id,
            PresenceState.user_id == user_id,
        )
        pres_res = await self.db.execute(pres_query)
        presence = pres_res.scalar_one_or_none()
        if presence:
            presence.status = "offline"
            presence.updated_at = now

        await self.db.flush()
        return participant

    async def close_session(self, session_id: str, closed_by: str) -> CollaborationSession:
        """Closes session: presence expires, realtime ends, history preserved."""
        session = await self.get_session(session_id)
        now = datetime.now(timezone.utc)
        session.status = "closed"
        session.last_activity_at = now

        # Set all presence to offline
        query = select(PresenceState).where(PresenceState.session_id == session_id)
        result = await self.db.execute(query)
        for pres in result.scalars().all():
            pres.status = "offline"
            pres.updated_at = now

        await self.db.flush()
        return session

    async def record_decision(
        self,
        session_id: str,
        resource_type: str,
        resource_id: str,
        decision_type: str,
        decision_data: dict,
        created_by: str,
        supersedes_id: Optional[str] = None,
    ) -> CollaborationDecision:
        """Records a collaborative decision/review outcome."""
        now = datetime.now(timezone.utc)
        decision = CollaborationDecision(
            session_id=session_id,
            resource_type=resource_type,
            resource_id=resource_id,
            decision_type=decision_type,
            decision=decision_data,
            created_by=created_by,
            created_at=now,
            supersedes_id=supersedes_id,
        )
        self.db.add(decision)
        await self.db.flush()
        return decision

    async def list_decisions(
        self,
        session_id: str,
        limit: int = 50,
    ) -> List[CollaborationDecision]:
        """Lists decisions recorded in a session."""
        query = (
            select(CollaborationDecision)
            .where(CollaborationDecision.session_id == session_id)
            .order_by(desc(CollaborationDecision.created_at))
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
