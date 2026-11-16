from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List, Optional
from backend.app.db.database import get_db
from backend.app.services.progressive_delivery.schemas import RolloutCreate, RolloutResponse
from backend.app.services.progressive_delivery.service import ProgressiveDeliveryService
from backend.app.api.dependencies.auth import get_current_workspace, get_current_user

router = APIRouter()


def _get_user_id_str(user_or_id: Any) -> str:
    if hasattr(user_or_id, "id"):
        return str(user_or_id.id)
    return str(user_or_id)


@router.post("", response_model=RolloutResponse, status_code=status.HTTP_201_CREATED)
async def create_rollout(
    payload: RolloutCreate,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace),
    user_id: Any = Depends(get_current_user)
) -> Any:
    service = ProgressiveDeliveryService(db)
    user_id_str = _get_user_id_str(user_id)
    return await service.create_rollout(payload=payload, workspace_id=workspace_id, user_id=user_id_str)


@router.get("", response_model=List[RolloutResponse])
async def list_rollouts(
    status: Optional[str] = Query(None),
    release_id: Optional[str] = Query(None),
    workspace_id_param: Optional[str] = Query(None, alias="workspace_id"),
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ProgressiveDeliveryService(db)
    effective_workspace = workspace_id_param or workspace_id
    return await service.list_rollouts(workspace_id=effective_workspace, release_id=release_id, status=status)


@router.get("/{rollout_id}", response_model=RolloutResponse)
async def get_rollout(
    rollout_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ProgressiveDeliveryService(db)
    rollout = await service.get_rollout(rollout_id=rollout_id, workspace_id=workspace_id)
    if not rollout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rollout not found")
    return rollout


@router.post("/{rollout_id}/validate", response_model=RolloutResponse)
async def validate_rollout(
    rollout_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace),
    user_id: Any = Depends(get_current_user)
) -> Any:
    service = ProgressiveDeliveryService(db)
    user_id_str = _get_user_id_str(user_id)
    rollout = await service.validate_rollout(rollout_id=rollout_id, workspace_id=workspace_id, user_id=user_id_str)
    if not rollout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rollout not found")
    return rollout


@router.post("/{rollout_id}/start", response_model=RolloutResponse)
async def start_rollout(
    rollout_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace),
    user_id: Any = Depends(get_current_user)
) -> Any:
    service = ProgressiveDeliveryService(db)
    user_id_str = _get_user_id_str(user_id)
    rollout = await service.start_rollout(rollout_id=rollout_id, workspace_id=workspace_id, user_id=user_id_str)
    if not rollout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rollout not found")
    return rollout


@router.post("/{rollout_id}/pause", response_model=RolloutResponse)
async def pause_rollout(
    rollout_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace),
    user_id: Any = Depends(get_current_user)
) -> Any:
    service = ProgressiveDeliveryService(db)
    user_id_str = _get_user_id_str(user_id)
    rollout = await service.pause_rollout(rollout_id=rollout_id, workspace_id=workspace_id, user_id=user_id_str)
    if not rollout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rollout not found")
    return rollout


@router.post("/{rollout_id}/resume", response_model=RolloutResponse)
async def resume_rollout(
    rollout_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace),
    user_id: Any = Depends(get_current_user)
) -> Any:
    service = ProgressiveDeliveryService(db)
    user_id_str = _get_user_id_str(user_id)
    rollout = await service.resume_rollout(rollout_id=rollout_id, workspace_id=workspace_id, user_id=user_id_str)
    if not rollout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rollout not found")
    return rollout


@router.post("/{rollout_id}/abort", response_model=RolloutResponse)
async def abort_rollout(
    rollout_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace),
    user_id: Any = Depends(get_current_user)
) -> Any:
    service = ProgressiveDeliveryService(db)
    user_id_str = _get_user_id_str(user_id)
    rollout = await service.abort_rollout(rollout_id=rollout_id, workspace_id=workspace_id, user_id=user_id_str)
    if not rollout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rollout not found")
    return rollout


@router.get("/{rollout_id}/stages")
async def get_rollout_stages(
    rollout_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ProgressiveDeliveryService(db)
    return await service.get_stages(rollout_id=rollout_id, workspace_id=workspace_id)


@router.get("/{rollout_id}/health")
async def get_rollout_health(
    rollout_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ProgressiveDeliveryService(db)
    return await service.get_health(rollout_id=rollout_id, workspace_id=workspace_id)


@router.get("/{rollout_id}/evidence")
async def get_rollout_evidence(
    rollout_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ProgressiveDeliveryService(db)
    return await service.get_evidence(rollout_id=rollout_id, workspace_id=workspace_id)
