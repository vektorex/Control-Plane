import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.core.logging import logger
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.multimodal.artifact_service import ArtifactService
from backend.app.services.multimodal.constants import ArtifactPartType, ArtifactStatus, ArtifactType
from backend.app.services.multimodal.errors import (
    ArtifactAccessDeniedError,
    ArtifactNotFoundError,
    DecompressionBombError,
    FileLimitExceededError,
    MimeSpoofingError,
    MultimodalError,
    UnsupportedMimeTypeError,
)
from backend.app.services.multimodal.schemas import (
    ArtifactAnalysisRequest,
    ArtifactAnalysisResponse,
    ArtifactEvidenceResponse,
    ArtifactPartResponse,
    ArtifactResponse,
)
from backend.app.services.multimodal.service import MultimodalService

router = APIRouter(prefix="/artifacts", tags=["Artifacts"])


@router.post("", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
async def upload_artifact(
    file: UploadFile = File(...),
    workspace_id: uuid.UUID = Form(...),
    project_id: Optional[uuid.UUID] = Form(None),
    auto_process: bool = Form(True),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ArtifactResponse:
    """
    Upload a new multimodal artifact (PDF, image, audio, video, table/CSV/XLSX).
    Enforces MIME validation, magic-byte checks, decompression limits, and tenant scoping.
    """
    try:
        service = ArtifactService(session)
        data = await file.read()
        filename = file.filename or "uploaded_file"
        claimed_mime = file.content_type

        artifact = await service.upload_artifact(
            file_data=data,
            filename=filename,
            claimed_mime=claimed_mime,
            workspace_id=workspace_id,
            project_id=project_id,
            user=current_user,
            auto_process=auto_process,
        )

        return ArtifactResponse.model_validate(artifact)
    except (UnsupportedMimeTypeError, MimeSpoofingError, FileLimitExceededError, DecompressionBombError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except ArtifactAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except Exception as exc:
        logger.error(f"[ArtifactUpload] Failed: {exc}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload failed: {str(exc)}")


@router.get("", response_model=List[ArtifactResponse])
async def list_artifacts(
    workspace_id: uuid.UUID = Query(...),
    project_id: Optional[uuid.UUID] = Query(None),
    artifact_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[ArtifactResponse]:
    """
    List artifacts in a workspace/project with tenant isolation and metadata filtering.
    """
    try:
        service = ArtifactService(session)
        art_type = ArtifactType(artifact_type) if artifact_type else None
        art_status = ArtifactStatus(status_filter) if status_filter else None

        artifacts = await service.list_artifacts(
            workspace_id=workspace_id,
            user=current_user,
            project_id=project_id,
            artifact_type=art_type,
            status=art_status,
            limit=limit,
            offset=offset,
        )
        return [ArtifactResponse.model_validate(a) for a in artifacts]
    except ArtifactAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except Exception as exc:
        logger.error(f"[ArtifactList] Failed: {exc}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ArtifactResponse:
    """
    Retrieve single artifact details and metadata.
    """
    try:
        service = ArtifactService(session)
        artifact = await service.get_artifact(artifact_id, current_user)
        return ArtifactResponse.model_validate(artifact)
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ArtifactAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.delete("/{artifact_id}")
async def delete_artifact(
    artifact_id: uuid.UUID,
    hard_delete: bool = Query(False),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Delete or archive an artifact, checking retention rules and active replay/graph references.
    """
    try:
        service = ArtifactService(session)
        success = await service.delete_artifact(artifact_id, current_user, hard_delete=hard_delete)
        return {"success": success, "id": str(artifact_id)}
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ArtifactAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.post("/{artifact_id}/process", response_model=ArtifactResponse)
async def process_artifact(
    artifact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ArtifactResponse:
    """
    Trigger media extraction and part normalization for an uploaded artifact.
    """
    try:
        service = ArtifactService(session)
        artifact = await service.process_artifact(artifact_id, current_user)
        return ArtifactResponse.model_validate(artifact)
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ArtifactAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except Exception as exc:
        logger.error(f"[ArtifactProcess] Failed: {exc}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/{artifact_id}/parts", response_model=List[ArtifactPartResponse])
async def list_artifact_parts(
    artifact_id: uuid.UUID,
    part_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[ArtifactPartResponse]:
    """
    List extracted parts (text, image, table, audio segment, video frame) of an artifact.
    """
    try:
        service = ArtifactService(session)
        p_type = ArtifactPartType(part_type) if part_type else None
        parts = await service.list_parts(artifact_id, current_user, part_type=p_type)
        return [ArtifactPartResponse.model_validate(p) for p in parts]
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ArtifactAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.get("/{artifact_id}/status")
async def get_artifact_status(
    artifact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Returns lightweight processing status and parts count.
    """
    try:
        service = ArtifactService(session)
        artifact = await service.get_artifact(artifact_id, current_user)
        return {
            "id": str(artifact.id),
            "status": artifact.status.value,
            "parts_count": len(artifact.parts) if artifact.parts else 0,
            "artifact_type": artifact.artifact_type.value,
            "updated_at": artifact.updated_at.isoformat() if artifact.updated_at else None,
        }
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ArtifactAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.post("/{artifact_id}/analyze", response_model=ArtifactAnalysisResponse)
async def analyze_artifact(
    artifact_id: uuid.UUID,
    request: ArtifactAnalysisRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ArtifactAnalysisResponse:
    """
    Perform multimodal reasoning over the artifact.
    Routes to vision/audio/table capable model via AI Gateway, returning grounded evidence.
    """
    try:
        mm_service = MultimodalService(session)
        return await mm_service.analyze_artifact(
            artifact_id=artifact_id,
            user=current_user,
            request=request,
        )
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ArtifactAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except Exception as exc:
        logger.error(f"[ArtifactAnalyze] Error: {exc}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/{artifact_id}/extract", response_model=List[ArtifactPartResponse])
async def extract_artifact(
    artifact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[ArtifactPartResponse]:
    """
    Trigger part extraction or re-extraction on the artifact.
    """
    try:
        service = ArtifactService(session)
        artifact = await service.process_artifact(artifact_id, current_user)
        return [ArtifactPartResponse.model_validate(p) for p in (artifact.parts or [])]
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ArtifactAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
