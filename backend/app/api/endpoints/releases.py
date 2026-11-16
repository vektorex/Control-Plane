from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List, Optional
from backend.app.db.database import get_db
from backend.app.services.releases.schemas import ReleaseCreate, ReleaseResponse
from backend.app.services.releases.service import ReleaseService
from backend.app.api.dependencies.auth import get_current_workspace, get_current_user

router = APIRouter()


def _get_user_id_str(user_or_id: Any) -> str:
    if hasattr(user_or_id, "id"):
        return str(user_or_id.id)
    return str(user_or_id)


@router.post("", response_model=ReleaseResponse, status_code=status.HTTP_201_CREATED)
async def create_release(
    payload: ReleaseCreate,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace),
    user_id: Any = Depends(get_current_user)
) -> Any:
    service = ReleaseService(db)
    user_id_str = _get_user_id_str(user_id)
    return await service.create_release(payload=payload, workspace_id=workspace_id, requested_by=user_id_str)


@router.get("", response_model=List[ReleaseResponse])
async def list_releases(
    status: Optional[str] = Query(None),
    workspace_id_param: Optional[str] = Query(None, alias="workspace_id"),
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ReleaseService(db)
    effective_workspace = workspace_id_param or workspace_id
    return await service.list_releases(workspace_id=effective_workspace, status=status)


@router.get("/{release_id}", response_model=ReleaseResponse)
async def get_release(
    release_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ReleaseService(db)
    release = await service.get_release(release_id=release_id, workspace_id=workspace_id)
    if not release:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    return release


@router.post("/{release_id}/build-plan", response_model=ReleaseResponse)
async def build_release_plan(
    release_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace),
    user_id: Any = Depends(get_current_user)
) -> Any:
    service = ReleaseService(db)
    user_id_str = _get_user_id_str(user_id)
    release = await service.build_release_plan(release_id=release_id, workspace_id=workspace_id, user_id=user_id_str)
    if not release:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    return release


@router.get("/{release_id}/plan")
async def get_release_plan(
    release_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ReleaseService(db)
    plan = await service.get_release_plan(release_id=release_id, workspace_id=workspace_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    return plan


@router.post("/{release_id}/validate", response_model=ReleaseResponse)
async def validate_release(
    release_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace),
    user_id: Any = Depends(get_current_user)
) -> Any:
    service = ReleaseService(db)
    user_id_str = _get_user_id_str(user_id)
    release = await service.validate_release(release_id=release_id, workspace_id=workspace_id, user_id=user_id_str)
    if not release:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    return release


@router.post("/{release_id}/submit-approval", response_model=ReleaseResponse)
async def submit_approval(
    release_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace),
    user_id: Any = Depends(get_current_user)
) -> Any:
    service = ReleaseService(db)
    user_id_str = _get_user_id_str(user_id)
    release = await service.submit_approval(release_id=release_id, workspace_id=workspace_id, user_id=user_id_str)
    if not release:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    return release


@router.post("/{release_id}/stage", response_model=ReleaseResponse)
async def stage_release(
    release_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace),
    user_id: Any = Depends(get_current_user)
) -> Any:
    service = ReleaseService(db)
    user_id_str = _get_user_id_str(user_id)
    release = await service.stage_release(release_id=release_id, workspace_id=workspace_id, user_id=user_id_str)
    if not release:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    return release


@router.post("/{release_id}/verify-staging", response_model=ReleaseResponse)
async def verify_staging(
    release_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace),
    user_id: Any = Depends(get_current_user)
) -> Any:
    service = ReleaseService(db)
    user_id_str = _get_user_id_str(user_id)
    release = await service.verify_staging(release_id=release_id, workspace_id=workspace_id, user_id=user_id_str)
    if not release:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    return release


@router.post("/{release_id}/promote", response_model=ReleaseResponse)
async def promote_release(
    release_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace),
    user_id: Any = Depends(get_current_user)
) -> Any:
    service = ReleaseService(db)
    user_id_str = _get_user_id_str(user_id)
    release = await service.promote_release(release_id=release_id, workspace_id=workspace_id, user_id=user_id_str)
    if not release:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    return release


@router.post("/{release_id}/complete", response_model=ReleaseResponse)
async def complete_release(
    release_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace),
    user_id: Any = Depends(get_current_user)
) -> Any:
    service = ReleaseService(db)
    user_id_str = _get_user_id_str(user_id)
    release = await service.complete_release(release_id=release_id, workspace_id=workspace_id, user_id=user_id_str)
    if not release:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    return release


@router.post("/{release_id}/rollback", response_model=ReleaseResponse)
async def execute_rollback(
    release_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace),
    user_id: Any = Depends(get_current_user)
) -> Any:
    service = ReleaseService(db)
    user_id_str = _get_user_id_str(user_id)
    release = await service.execute_rollback(release_id=release_id, workspace_id=workspace_id, user_id=user_id_str)
    if not release:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    return release


@router.get("/{release_id}/evidence")
async def get_evidence(
    release_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ReleaseService(db)
    return await service.get_evidence(release_id=release_id, workspace_id=workspace_id)


@router.get("/{release_id}/timeline")
async def get_timeline(
    release_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ReleaseService(db)
    return await service.get_timeline(release_id=release_id, workspace_id=workspace_id)
