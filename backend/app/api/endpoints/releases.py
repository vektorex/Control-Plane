from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from backend.app.db.database import get_db
from backend.app.services.releases.schemas import ReleaseCreate, ReleaseResponse
from backend.app.services.releases.service import ReleaseService
from backend.app.api.dependencies.auth import get_current_workspace, get_current_user

router = APIRouter()

@router.post("", response_model=ReleaseResponse, status_code=status.HTTP_201_CREATED)
async def create_release(
    payload: ReleaseCreate,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace),
    user_id: str = Depends(get_current_user)
) -> Any:
    service = ReleaseService(db)
    return await service.create_release(payload=payload, workspace_id=workspace_id, requested_by=user_id)

@router.get("", response_model=list[ReleaseResponse])
async def list_releases(
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    return []

@router.get("/{release_id}", response_model=ReleaseResponse)
async def get_release(
    release_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    pass

@router.post("/{release_id}/build-plan")
async def build_release_plan(release_id: str) -> Any:
    return {"status": "plan_built"}

@router.get("/{release_id}/plan")
async def get_release_plan(release_id: str) -> Any:
    return {"stages": []}

@router.post("/{release_id}/validate")
async def validate_release(release_id: str) -> Any:
    return {"status": "validated"}

@router.post("/{release_id}/submit-approval")
async def submit_approval(release_id: str) -> Any:
    return {"status": "approval_submitted"}

@router.post("/{release_id}/stage")
async def stage_release(release_id: str) -> Any:
    return {"status": "staged"}

@router.post("/{release_id}/verify-staging")
async def verify_staging(release_id: str) -> Any:
    return {"status": "staging_verified"}

@router.post("/{release_id}/promote")
async def promote_release(release_id: str) -> Any:
    return {"status": "promoted"}

@router.post("/{release_id}/verify-production")
async def verify_production(release_id: str) -> Any:
    return {"status": "production_verified"}

@router.post("/{release_id}/observe")
async def observe_release(release_id: str) -> Any:
    return {"status": "observation_started"}

@router.get("/{release_id}/observations")
async def get_observations(release_id: str) -> Any:
    return []

@router.post("/{release_id}/complete")
async def complete_release(release_id: str) -> Any:
    return {"status": "completed"}

@router.post("/{release_id}/cancel")
async def cancel_release(release_id: str) -> Any:
    return {"status": "cancelled"}

@router.post("/{release_id}/rollback-request")
async def request_rollback(release_id: str) -> Any:
    return {"status": "rollback_requested"}

@router.post("/{release_id}/rollback")
async def execute_rollback(release_id: str) -> Any:
    return {"status": "rolled_back"}

@router.get("/{release_id}/evidence")
async def get_evidence(release_id: str) -> Any:
    return []

@router.get("/{release_id}/timeline")
async def get_timeline(release_id: str) -> Any:
    return []
