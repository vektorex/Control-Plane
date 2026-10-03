"""
Annotations Service for Step 39: Collaboration.
Supports targeted highlights, evidence, questions, and warnings across platform resources.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.services.collaboration.exceptions import AnnotationNotFoundError
from backend.app.services.collaboration.models import CollaborationAnnotation
from backend.app.services.collaboration.validators import CollaborationValidator


class CollaborationAnnotationService:
    """Manages multi-target annotations across documents, artifacts, workflow steps, and graph entities."""

    def __init__(self, session: AsyncSession):
        self.db = session

    async def create_annotation(
        self,
        session_id: str,
        resource_type: str,
        resource_id: str,
        author_id: str,
        annotation_type: str,
        target: Dict[str, Any],
        content: str,
    ) -> CollaborationAnnotation:
        """Creates a targeted annotation."""
        clean_content = CollaborationValidator.sanitize_text(content)
        now = datetime.now(timezone.utc)

        annotation = CollaborationAnnotation(
            session_id=session_id,
            resource_type=resource_type,
            resource_id=resource_id,
            author_id=author_id,
            annotation_type=annotation_type,
            target=target or {},
            content=clean_content,
            status="active",
            created_at=now,
            updated_at=now,
        )
        self.db.add(annotation)
        await self.db.flush()
        return annotation

    async def get_annotation(self, annotation_id: str) -> CollaborationAnnotation:
        """Retrieves annotation by ID."""
        query = select(CollaborationAnnotation).where(CollaborationAnnotation.id == annotation_id)
        result = await self.db.execute(query)
        ann = result.scalar_one_or_none()
        if not ann:
            raise AnnotationNotFoundError(annotation_id)
        return ann

    async def update_annotation(
        self,
        annotation_id: str,
        content: Optional[str] = None,
        status: Optional[str] = None,
    ) -> CollaborationAnnotation:
        """Updates annotation content or status."""
        annotation = await self.get_annotation(annotation_id)
        if content is not None:
            annotation.content = CollaborationValidator.sanitize_text(content)
        if status is not None:
            annotation.status = status
        annotation.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return annotation

    async def list_annotations(
        self,
        session_id: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        annotation_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CollaborationAnnotation]:
        """Lists annotations for a session."""
        query = select(CollaborationAnnotation).where(CollaborationAnnotation.session_id == session_id)
        if resource_type:
            query = query.where(CollaborationAnnotation.resource_type == resource_type)
        if resource_id:
            query = query.where(CollaborationAnnotation.resource_id == resource_id)
        if annotation_type:
            query = query.where(CollaborationAnnotation.annotation_type == annotation_type)

        query = query.order_by(desc(CollaborationAnnotation.created_at)).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
