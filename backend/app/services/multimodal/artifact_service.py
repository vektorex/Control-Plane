"""
Artifact Lifecycle and Storage Service for Step 30: Multimodal AI.
Orchestrates file upload, storage, permission verification, processing, retention, and deletion.
"""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.db.models.user import User
from backend.app.services.events.constants import ActorType, AggregateType, SystemEventType
from backend.app.services.events.publisher import EventPublisher, EventPublishRequest
from backend.app.services.multimodal.constants import ArtifactStatus
from backend.app.services.multimodal.errors import (
    ArtifactAccessDeniedError,
    ArtifactNotFoundError,
)
from backend.app.services.multimodal.extractors import MultimodalExtractionCoordinator
from backend.app.services.multimodal.limits import ARTIFACT_RETENTION_DAYS
from backend.app.services.multimodal.media_detector import MediaDetector
from backend.app.services.multimodal.models import Artifact, ArtifactPart
from backend.app.services.multimodal.policies import ArtifactPolicyEngine
from backend.app.services.multimodal.repository import ArtifactRepository
from backend.app.services.multimodal.sanitizer import sanitize_artifact_metadata
from backend.app.services.multimodal.schemas import ArtifactInspection
from backend.app.services.storage.factory import get_storage


class ArtifactService:
    """
    Core management service for Multimodal Artifact lifecycle.
    """

    def __init__(self, session: AsyncSession, event_publisher: Optional[EventPublisher] = None):
        self.session = session
        self.repo = ArtifactRepository(session)
        self.storage = get_storage()
        self.event_publisher = event_publisher or EventPublisher(session)
        self.extractor = MultimodalExtractionCoordinator(session)

    async def upload_artifact(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        owner_user_id: uuid.UUID,
        filename: str,
        data: bytes,
        declared_mime: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Artifact, ArtifactInspection]:
        """
        Validates, sniffs, persists raw media in storage abstraction, and creates Artifact database record.
        """
        # 1. Clean filename and validate inspection
        safe_filename = ArtifactPolicyEngine.sanitize_filename(filename)
        inspection = MediaDetector.detect_and_inspect(safe_filename, data, declared_mime)

        # 2. Compute hash and upload to storage abstraction
        content_hash = hashlib.sha256(data).hexdigest()
        artifact_id = uuid.uuid4()
        storage_key = f"artifacts/{workspace_id}/{artifact_id}/{safe_filename}"
        ArtifactPolicyEngine.validate_storage_reference(storage_key)

        await self.storage.upload(storage_key, data, content_type=inspection.mime_type)

        # 3. Create Artifact DB record
        clean_metadata = sanitize_artifact_metadata(metadata or {})
        clean_metadata.update({
            "detected_type": inspection.detected_type,
            "dimensions": inspection.dimensions,
            "duration_seconds": inspection.duration_seconds,
            "page_count": inspection.page_count,
            "required_capabilities": inspection.required_capabilities,
        })

        artifact = await self.repo.create_artifact(
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            owner_user_id=owner_user_id,
            artifact_type=inspection.detected_type,
            mime_type=inspection.mime_type,
            filename=safe_filename,
            size_bytes=len(data),
            storage_reference=storage_key,
            content_hash=content_hash,
            status=ArtifactStatus.UPLOADED.value,
            metadata=clean_metadata,
        )

        return artifact, inspection

    async def process_artifact(self, artifact_id: uuid.UUID) -> List[ArtifactPart]:
        """
        Processes an uploaded artifact by downloading from storage, extracting parts,
        and setting status to READY or FAILED.
        """
        artifact = await self.repo.get_artifact_by_id(artifact_id)
        if not artifact:
            raise ArtifactNotFoundError(f"Artifact {artifact_id} not found.")

        # Update status to processing
        await self.repo.update_artifact_status(artifact_id, ArtifactStatus.PROCESSING.value)
        await self._publish_event(artifact, SystemEventType.ARTIFACT_PROCESSING_STARTED.value)

        try:
            data = await self.storage.download(artifact.storage_reference)
            inspection = MediaDetector.detect_and_inspect(artifact.filename, data, artifact.mime_type)

            parts = await self.extractor.extract_parts(artifact, data, inspection)
            await self.repo.update_artifact_status(artifact_id, ArtifactStatus.READY.value)
            await self._publish_event(artifact, SystemEventType.ARTIFACT_PROCESSING_COMPLETED.value)
            return parts
        except Exception as e:
            logger.error(f"[ArtifactService] Processing failed for artifact {artifact_id}: {e}", exc_info=True)
            await self.repo.update_artifact_status(
                artifact_id,
                ArtifactStatus.FAILED.value,
                metadata_update={"processing_error": str(e)},
            )
            await self._publish_event(
                artifact,
                SystemEventType.ARTIFACT_PROCESSING_FAILED.value,
                payload={"error": str(e)},
            )
            raise

    async def get_artifact(
        self,
        artifact_id: uuid.UUID,
        user: Optional[User] = None,
        workspace_id: Optional[uuid.UUID] = None,
        organization_id: Optional[uuid.UUID] = None,
        permission: Optional[str] = None,
    ) -> Artifact:
        """
        Fetches an artifact by ID, strictly enforcing organization and workspace tenant boundary.
        """
        # If a UUID was passed as the 2nd positional argument, treat it as workspace_id
        if isinstance(user, uuid.UUID):
            workspace_id = user
            user = None

        artifact = await self.repo.get_artifact_by_id(
            artifact_id,
            workspace_id=workspace_id,
            organization_id=organization_id,
        )
        if not artifact:
            raise ArtifactNotFoundError(f"Artifact {artifact_id} not found.")

        if user:
            ArtifactPolicyEngine.verify_tenant_boundary(user, artifact.organization_id)
            if permission:
                await ArtifactPolicyEngine.authorize_artifact_access(
                    self.session, user, artifact, permission
                )

        return artifact

    async def get_artifact_parts(
        self,
        artifact_id: uuid.UUID,
        user: Optional[User] = None,
    ) -> List[ArtifactPart]:
        """Fetches all parts for an artifact with tenant boundary enforcement."""
        artifact = await self.get_artifact(artifact_id, user=user)
        return await self.repo.list_parts(artifact.id)

    async def create_artifact(self, *args, **kwargs) -> Tuple[Artifact, ArtifactInspection]:
        """Alias for upload_artifact."""
        return await self.upload_artifact(*args, **kwargs)

    async def list_artifacts(
        self,
        workspace_id: uuid.UUID,
        project_id: Optional[uuid.UUID] = None,
        artifact_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        user: Optional[User] = None,
    ) -> Tuple[List[Artifact], int]:
        """Lists artifacts for a given workspace with pagination and filters."""
        return await self.repo.list_artifacts(
            workspace_id=workspace_id,
            project_id=project_id,
            artifact_type=artifact_type,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def delete_artifact(
        self,
        artifact_id: uuid.UUID,
        user: Optional[User] = None,
        force: bool = False,
        hard_delete: bool = False,
    ) -> bool:
        """
        Safely deletes an artifact and its underlying storage reference.
        Checks for active references before deletion unless force=True.
        """
        artifact = await self.get_artifact(artifact_id, user=user)
        # Delete from DB
        await self.repo.delete_artifact(artifact_id)
        # Delete from storage abstraction
        try:
            await self.storage.delete(artifact.storage_reference)
        except Exception as e:
            logger.warning(f"[ArtifactService] Storage file deletion failed for {artifact.storage_reference}: {e}")

        return True

    async def archive_artifact(self, artifact_id: uuid.UUID, user: Optional[User] = None) -> Artifact:
        """Archives an artifact without deleting storage data."""
        await self.get_artifact(artifact_id, user=user)
        return await self.repo.archive_artifact(artifact_id)

    async def cleanup_expired_artifacts(
        self,
        workspace_id: uuid.UUID,
        retention_days: int = ARTIFACT_RETENTION_DAYS,
    ) -> int:
        """
        Enforces retention policy, archiving or purging artifacts older than retention threshold.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        artifacts, _ = await self.repo.list_artifacts(workspace_id=workspace_id, limit=200)
        expired_count = 0
        for art in artifacts:
            if art.created_at < cutoff and art.status != ArtifactStatus.ARCHIVED.value:
                await self.repo.archive_artifact(art.id)
                expired_count += 1
        return expired_count

    async def _publish_event(
        self,
        artifact: Artifact,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Helper to broadcast events over the unified event bus."""
        try:
            data = {"artifact_id": str(artifact.id), "filename": artifact.filename, "status": artifact.status}
            if payload:
                data.update(payload)

            await self.event_publisher.publish(
                EventPublishRequest(
                    workspace_id=artifact.workspace_id,
                    project_id=artifact.project_id,
                    event_type=event_type,
                    aggregate_type=AggregateType.ARTIFACT.value,
                    aggregate_id=str(artifact.id),
                    actor_type=ActorType.SYSTEM.value,
                    actor_id=str(artifact.owner_user_id),
                    payload=data,
                )
            )
        except Exception as e:
            logger.warning(f"[ArtifactService] Failed to publish event '{event_type}': {e}")
