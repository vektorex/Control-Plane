"""
Repository Layer for Step 30: Multimodal AI and Unified Artifact Intelligence.
Handles multi-tenant persistence and querying for Artifacts, ArtifactParts, and ArtifactEvidence.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.services.multimodal.constants import ArtifactStatus
from backend.app.services.multimodal.errors import ArtifactNotFoundError
from backend.app.services.multimodal.models import Artifact, ArtifactEvidence, ArtifactPart


class ArtifactRepository:
    """
    Data access layer for multimodal artifacts with tenant and workspace isolation.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_artifact(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        owner_user_id: uuid.UUID,
        artifact_type: str,
        mime_type: str,
        filename: str,
        size_bytes: int,
        storage_reference: str,
        content_hash: str,
        project_id: Optional[uuid.UUID] = None,
        status: str = ArtifactStatus.UPLOADED.value,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Artifact:
        artifact = Artifact(
            id=uuid.uuid4(),
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            owner_user_id=owner_user_id,
            artifact_type=artifact_type,
            mime_type=mime_type,
            filename=filename,
            size_bytes=size_bytes,
            storage_reference=storage_reference,
            content_hash=content_hash,
            status=status,
            metadata_=metadata or {},
        )
        self.session.add(artifact)
        await self.session.flush()
        return artifact

    async def get_artifact_by_id(
        self,
        artifact_id: uuid.UUID,
        workspace_id: Optional[uuid.UUID] = None,
        organization_id: Optional[uuid.UUID] = None,
        include_parts: bool = True,
    ) -> Optional[Artifact]:
        query = select(Artifact).where(Artifact.id == artifact_id)
        if workspace_id:
            query = query.where(Artifact.workspace_id == workspace_id)
        if organization_id:
            query = query.where(Artifact.organization_id == organization_id)
        if include_parts:
            query = query.options(
                selectinload(Artifact.parts),
                selectinload(Artifact.evidence),
            )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def list_artifacts(
        self,
        workspace_id: uuid.UUID,
        project_id: Optional[uuid.UUID] = None,
        artifact_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Artifact], int]:
        base_query = select(Artifact).where(Artifact.workspace_id == workspace_id)
        count_query = select(func.count(Artifact.id)).where(Artifact.workspace_id == workspace_id)

        if project_id:
            base_query = base_query.where(or_(Artifact.project_id == project_id, Artifact.project_id.is_(None)))
            count_query = count_query.where(or_(Artifact.project_id == project_id, Artifact.project_id.is_(None)))
        if artifact_type:
            base_query = base_query.where(Artifact.artifact_type == artifact_type)
            count_query = count_query.where(Artifact.artifact_type == artifact_type)
        if status:
            base_query = base_query.where(Artifact.status == status)
            count_query = count_query.where(Artifact.status == status)

        total_res = await self.session.execute(count_query)
        total = total_res.scalar() or 0

        query = (
            base_query.options(selectinload(Artifact.parts))
            .order_by(desc(Artifact.created_at))
            .offset(offset)
            .limit(limit)
        )
        res = await self.session.execute(query)
        return list(res.scalars().all()), total

    async def update_artifact_status(
        self,
        artifact_id: uuid.UUID,
        status: str,
        metadata_update: Optional[Dict[str, Any]] = None,
    ) -> Artifact:
        artifact = await self.get_artifact_by_id(artifact_id, include_parts=False)
        if not artifact:
            raise ArtifactNotFoundError(f"Artifact {artifact_id} not found.")

        artifact.status = status
        artifact.updated_at = datetime.now(timezone.utc)
        if metadata_update:
            updated_meta = dict(artifact.metadata_ or {})
            updated_meta.update(metadata_update)
            artifact.metadata_ = updated_meta

        await self.session.flush()
        return artifact

    async def archive_artifact(self, artifact_id: uuid.UUID) -> Artifact:
        return await self.update_artifact_status(artifact_id, ArtifactStatus.ARCHIVED.value)

    async def delete_artifact(self, artifact_id: uuid.UUID) -> bool:
        artifact = await self.get_artifact_by_id(artifact_id, include_parts=False)
        if not artifact:
            return False
        await self.session.delete(artifact)
        await self.session.flush()
        return True

    # -------------------------------------------------------------------------
    # Artifact Parts
    # -------------------------------------------------------------------------

    async def create_part(
        self,
        artifact_id: uuid.UUID,
        part_type: str,
        sequence_number: int = 0,
        content_reference: Optional[str] = None,
        text_content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        content_hash: Optional[str] = None,
        token_estimate: Optional[int] = None,
    ) -> ArtifactPart:
        part = ArtifactPart(
            id=uuid.uuid4(),
            artifact_id=artifact_id,
            part_type=part_type,
            sequence_number=sequence_number,
            content_reference=content_reference,
            text_content=text_content,
            metadata_=metadata or {},
            content_hash=content_hash,
            token_estimate=token_estimate,
        )
        self.session.add(part)
        await self.session.flush()
        return part

    async def list_parts(self, artifact_id: uuid.UUID) -> List[ArtifactPart]:
        query = (
            select(ArtifactPart)
            .where(ArtifactPart.artifact_id == artifact_id)
            .order_by(ArtifactPart.sequence_number)
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    # -------------------------------------------------------------------------
    # Artifact Evidence
    # -------------------------------------------------------------------------

    async def create_evidence(
        self,
        artifact_id: uuid.UUID,
        part_id: Optional[uuid.UUID] = None,
        page: Optional[int] = None,
        timestamp: Optional[float] = None,
        region: Optional[Dict[str, Any]] = None,
        source_text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ArtifactEvidence:
        evidence = ArtifactEvidence(
            id=uuid.uuid4(),
            artifact_id=artifact_id,
            part_id=part_id,
            page=page,
            timestamp=timestamp,
            region=region,
            source_text=source_text,
            metadata_=metadata or {},
        )
        self.session.add(evidence)
        await self.session.flush()
        return evidence

    async def list_evidence(
        self,
        artifact_id: uuid.UUID,
        part_id: Optional[uuid.UUID] = None,
    ) -> List[ArtifactEvidence]:
        query = select(ArtifactEvidence).where(ArtifactEvidence.artifact_id == artifact_id)
        if part_id:
            query = query.where(ArtifactEvidence.part_id == part_id)
        query = query.order_by(ArtifactEvidence.created_at)
        res = await self.session.execute(query)
        return list(res.scalars().all())
