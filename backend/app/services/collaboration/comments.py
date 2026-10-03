"""
Threaded Comments Service for Step 39: Collaboration.
Manages sanitization, @mentions processing, threaded replies, and soft-deletion.
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from backend.app.services.collaboration.exceptions import CommentNotFoundError
from backend.app.services.collaboration.models import CollaborationComment
from backend.app.services.collaboration.mentions import MentionService
from backend.app.services.collaboration.validators import CollaborationValidator


class CollaborationCommentService:
    """Manages creation, updates, threaded retrieval, and deletion of collaboration comments."""

    def __init__(self, session: AsyncSession):
        self.db = session
        self.mention_service = MentionService(session)

    async def add_comment(
        self,
        session_id: str,
        organization_id: str,
        workspace_id: str,
        author_id: str,
        resource_type: str,
        resource_id: str,
        body: str,
        author_type: str = "user",
        parent_comment_id: Optional[str] = None,
    ) -> CollaborationComment:
        """Creates a sanitized comment, processes @mentions, and persists."""
        clean_body = CollaborationValidator.sanitize_text(body)
        now = datetime.now(timezone.utc)

        comment = CollaborationComment(
            session_id=session_id,
            resource_type=resource_type,
            resource_id=resource_id,
            author_id=author_id,
            author_type=author_type,
            body=clean_body,
            status="active",
            parent_comment_id=parent_comment_id,
            created_at=now,
            updated_at=now,
        )
        self.db.add(comment)
        await self.db.flush()

        # Extract and save mentions
        await self.mention_service.process_mentions(
            comment_id=comment.id,
            comment_body=body,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )

        return comment

    async def get_comment(self, comment_id: str) -> CollaborationComment:
        """Retrieves comment with loaded mentions."""
        query = (
            select(CollaborationComment)
            .options(selectinload(CollaborationComment.mentions))
            .where(CollaborationComment.id == comment_id)
        )
        result = await self.db.execute(query)
        comment = result.scalar_one_or_none()
        if not comment:
            raise CommentNotFoundError(comment_id)
        return comment

    async def update_comment(
        self,
        comment_id: str,
        body: Optional[str] = None,
        status: Optional[str] = None,
    ) -> CollaborationComment:
        """Updates comment text or status (active, resolved)."""
        comment = await self.get_comment(comment_id)
        if body is not None:
            comment.body = CollaborationValidator.sanitize_text(body)
        if status is not None:
            comment.status = status
        comment.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return comment

    async def soft_delete_comment(self, comment_id: str) -> CollaborationComment:
        """Soft-deletes comment preserving audit history."""
        comment = await self.get_comment(comment_id)
        now = datetime.now(timezone.utc)
        comment.status = "deleted"
        comment.body = "[This comment has been deleted]"
        comment.deleted_at = now
        comment.updated_at = now
        await self.db.flush()
        return comment

    async def list_comments(
        self,
        session_id: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        include_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CollaborationComment]:
        """Lists session comments ordered chronologically."""
        query = (
            select(CollaborationComment)
            .options(selectinload(CollaborationComment.mentions))
            .where(CollaborationComment.session_id == session_id)
        )
        if resource_type:
            query = query.where(CollaborationComment.resource_type == resource_type)
        if resource_id:
            query = query.where(CollaborationComment.resource_id == resource_id)
        if not include_deleted:
            query = query.where(CollaborationComment.status != "deleted")

        query = query.order_by(CollaborationComment.created_at.asc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
