"""
Collaboration Assignments Service for Step 39: Collaboration.
Manages actionable human review, approval, and investigation tasks.
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.services.collaboration.exceptions import AssignmentNotFoundError
from backend.app.services.collaboration.models import CollaborationAssignment


class CollaborationAssignmentService:
    """Manages assignment lifecycle within a collaboration session."""

    def __init__(self, session: AsyncSession):
        self.db = session

    async def create_assignment(
        self,
        session_id: str,
        resource_type: str,
        resource_id: str,
        assigned_to: str,
        assigned_by: str,
        assignment_type: str,
        due_at: Optional[datetime] = None,
    ) -> CollaborationAssignment:
        """Creates a new actionable assignment."""
        now = datetime.now(timezone.utc)
        assignment = CollaborationAssignment(
            session_id=session_id,
            resource_type=resource_type,
            resource_id=resource_id,
            assigned_to=assigned_to,
            assigned_by=assigned_by,
            assignment_type=assignment_type,
            status="pending",
            due_at=due_at,
            created_at=now,
            updated_at=now,
        )
        self.db.add(assignment)
        await self.db.flush()
        return assignment

    async def get_assignment(self, assignment_id: str) -> CollaborationAssignment:
        """Retrieves assignment by ID."""
        query = select(CollaborationAssignment).where(CollaborationAssignment.id == assignment_id)
        result = await self.db.execute(query)
        assignment = result.scalar_one_or_none()
        if not assignment:
            raise AssignmentNotFoundError(assignment_id)
        return assignment

    async def update_assignment(
        self,
        assignment_id: str,
        status: Optional[str] = None,
        due_at: Optional[datetime] = None,
    ) -> CollaborationAssignment:
        """Updates assignment status (accepted, completed, cancelled) or due date."""
        assignment = await self.get_assignment(assignment_id)
        if status is not None:
            assignment.status = status
        if due_at is not None:
            assignment.due_at = due_at
        assignment.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return assignment

    async def list_assignments(
        self,
        session_id: str,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[CollaborationAssignment]:
        """Lists assignments for a session."""
        query = select(CollaborationAssignment).where(CollaborationAssignment.session_id == session_id)
        if status:
            query = query.where(CollaborationAssignment.status == status)
        if assigned_to:
            query = query.where(CollaborationAssignment.assigned_to == assigned_to)

        query = query.order_by(desc(CollaborationAssignment.created_at)).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
