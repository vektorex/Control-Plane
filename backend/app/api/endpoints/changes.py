from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List, Optional
from backend.app.db.database import get_db
from backend.app.services.change_intelligence.schemas import ChangeRequestCreate, ChangeRequestResponse, ImpactSummary
from backend.app.services.change_intelligence.service import ChangeIntelligenceService
from backend.app.api.dependencies.auth import get_current_workspace, get_current_user

router = APIRouter()


def _get_user_id_str(user_or_id: Any) -> str:
    if hasattr(user_or_id, "id"):
        return str(user_or_id.id)
    return str(user_or_id)


@router.post("", response_model=ChangeRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_change_request(
    payload: ChangeRequestCreate,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace),
    user_id: Any = Depends(get_current_user)
) -> Any:
    service = ChangeIntelligenceService(db)
    user_id_str = _get_user_id_str(user_id)
    return await service.create_change_request(workspace_id=workspace_id, payload=payload, requested_by=user_id_str)


@router.get("", response_model=List[ChangeRequestResponse])
async def list_change_requests(
    workspace_id_param: Optional[str] = Query(None, alias="workspace_id"),
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ChangeIntelligenceService(db)
    effective_workspace = workspace_id_param or workspace_id
    return await service.list_change_requests(workspace_id=effective_workspace)


@router.get("/{change_id}", response_model=ChangeRequestResponse)
async def get_change_request(
    change_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ChangeIntelligenceService(db)
    change_req = await service.get_change_request(change_id=change_id, workspace_id=workspace_id)
    if not change_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")
    return change_req


@router.post("/{change_id}/parse")
async def parse_change(
    change_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ChangeIntelligenceService(db)
    change_req = await service.get_change_request(change_id=change_id, workspace_id=workspace_id)
    if not change_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")
    return {"status": "parsed", "change_id": change_id}


@router.post("/{change_id}/analyze", response_model=ImpactSummary)
async def analyze_change(
    change_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ChangeIntelligenceService(db)
    change_req = await service.get_change_request(change_id=change_id, workspace_id=workspace_id)
    if not change_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")
    return await service.analyze_impact(change_id)


@router.get("/{change_id}/impact")
async def get_change_impact(
    change_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ChangeIntelligenceService(db)
    change_req = await service.get_change_request(change_id=change_id, workspace_id=workspace_id)
    if not change_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")
    return await service.get_impact(change_id)


@router.get("/{change_id}/dependencies")
async def get_change_dependencies(
    change_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ChangeIntelligenceService(db)
    change_req = await service.get_change_request(change_id=change_id, workspace_id=workspace_id)
    if not change_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")
    return await service.get_dependencies(change_id)


@router.get("/{change_id}/risks")
async def get_change_risks(
    change_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ChangeIntelligenceService(db)
    change_req = await service.get_change_request(change_id=change_id, workspace_id=workspace_id)
    if not change_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")
    return await service.get_risks(change_id)


@router.get("/{change_id}/evidence")
async def get_change_evidence(
    change_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ChangeIntelligenceService(db)
    change_req = await service.get_change_request(change_id=change_id, workspace_id=workspace_id)
    if not change_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")
    return await service.get_evidence(change_id)


@router.get("/{change_id}/rollback")
async def get_change_rollback(
    change_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ChangeIntelligenceService(db)
    change_req = await service.get_change_request(change_id=change_id, workspace_id=workspace_id)
    if not change_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")
    return await service.get_rollback(change_id)
