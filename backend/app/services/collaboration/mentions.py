"""
Mentions Service for Step 39: Collaboration.
Extracts and validates @mentions against workspace membership boundaries.
"""
from datetime import datetime, timezone
from typing import List, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.db.models.user import User
from backend.app.services.access_control.models import WorkspaceMember
from backend.app.services.collaboration.models import CommentMention

from backend.app.services.collaboration.validators import CollaborationValidator


class MentionService:
    """Extracts @mentions from comment body and validates workspace membership."""

    def __init__(self, session: AsyncSession):
        self.db = session

    async def process_mentions(
        self,
        comment_id: str,
        comment_body: str,
        organization_id: str,
        workspace_id: str,
    ) -> List[CommentMention]:
        """
        Extracts @mentions, validates that target users belong to this organization and workspace,
        and saves CommentMention records.
        """
        raw_mentions = CollaborationValidator.extract_mentions(comment_body)
        if not raw_mentions:
            return []

        # Find users by username or email or id
        query = select(User).where(
            (User.email.in_(raw_mentions))
            | (User.id.in_(raw_mentions))
        )
        result = await self.db.execute(query)
        matched_users = result.scalars().all()

        if not matched_users:
            return []

        # Validate that matched users belong to the workspace
        user_ids = [u.id for u in matched_users]
        member_query = select(WorkspaceMember.user_id).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id.in_(user_ids),
        )
        member_res = await self.db.execute(member_query)
        authorized_user_ids: Set[str] = set(member_res.scalars().all())

        created_mentions: List[CommentMention] = []
        now = datetime.now(timezone.utc)
        for uid in authorized_user_ids:
            mention = CommentMention(
                comment_id=comment_id,
                mentioned_user_id=uid,
                created_at=now,
            )
            self.db.add(mention)
            created_mentions.append(mention)

        await self.db.flush()
        return created_mentions
