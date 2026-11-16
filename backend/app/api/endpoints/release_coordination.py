from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List, Optional, Dict
from backend.app.db.database import get_db
from backend.app.services.release_coordination.schemas import (
    PortfolioCreate,
    PortfolioResponse,
    TrainCreate,
    TrainResponse,
)
from backend.app.services.release_coordination.service import ReleaseCoordinationService
from backend.app.api.dependencies.auth import get_current_workspace, get_current_user

router = APIRouter()


def _get_user_id_str(user_or_id: Any) -> str:
    if hasattr(user_or_id, "id"):
        return str(user_or_id.id)
    return str(user_or_id)


@router.post("/portfolios", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    payload: PortfolioCreate,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace),
    user_id: Any = Depends(get_current_user)
) -> Any:
    service = ReleaseCoordinationService(db)
    user_id_str = _get_user_id_str(user_id)
    return await service.create_portfolio(payload=payload, workspace_id=workspace_id, user_id=user_id_str)


@router.get("/portfolios", response_model=List[PortfolioResponse])
async def list_portfolios(
    workspace_id_param: Optional[str] = Query(None, alias="workspace_id"),
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ReleaseCoordinationService(db)
    effective_workspace = workspace_id_param or workspace_id
    return await service.list_portfolios(workspace_id=effective_workspace)


@router.get("/portfolios/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ReleaseCoordinationService(db)
    item = await service.get_portfolio(portfolio_id=portfolio_id, workspace_id=workspace_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return item


@router.post("/trains", response_model=TrainResponse, status_code=status.HTTP_201_CREATED)
async def create_train(
    payload: TrainCreate,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace),
    user_id: Any = Depends(get_current_user)
) -> Any:
    service = ReleaseCoordinationService(db)
    user_id_str = _get_user_id_str(user_id)
    return await service.create_train(payload=payload, user_id=user_id_str)


@router.get("/trains", response_model=List[TrainResponse])
async def list_trains(
    portfolio_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ReleaseCoordinationService(db)
    return await service.list_trains(portfolio_id=portfolio_id)


@router.get("/trains/{train_id}", response_model=TrainResponse)
async def get_train(
    train_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace)
) -> Any:
    service = ReleaseCoordinationService(db)
    item = await service.get_train(train_id=train_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Train not found")
    return item


@router.post("/trains/{train_id}/releases")
async def add_release_to_train(
    train_id: str,
    payload: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ReleaseCoordinationService(db)
    release_id = payload.get("release_id") if payload else None
    return await service.add_release_to_train(train_id=train_id, release_id=release_id)


@router.delete("/trains/{train_id}/releases/{release_id}")
async def remove_release_from_train(
    train_id: str,
    release_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ReleaseCoordinationService(db)
    return await service.remove_release_from_train(train_id=train_id, release_id=release_id)


@router.post("/trains/{train_id}/dependencies")
async def add_dependency(
    train_id: str,
    payload: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ReleaseCoordinationService(db)
    src = payload.get("source_release_id") if payload else None
    tgt = payload.get("target_release_id") if payload else None
    dep_type = payload.get("dependency_type", "blocks") if payload else "blocks"
    return await service.add_dependency(
        train_id=train_id, source_release_id=src, target_release_id=tgt, dependency_type=dep_type
    )


@router.delete("/trains/{train_id}/dependencies/{dependency_id}")
async def remove_dependency(
    train_id: str,
    dependency_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ReleaseCoordinationService(db)
    return await service.remove_dependency(train_id=train_id, dependency_id=dependency_id)


@router.post("/trains/{train_id}/analyze")
async def analyze_train(
    train_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ReleaseCoordinationService(db)
    return await service.analyze_train(train_id=train_id)


@router.post("/trains/{train_id}/sequence")
async def sequence_train(
    train_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ReleaseCoordinationService(db)
    return await service.sequence_train(train_id=train_id)


@router.post("/trains/{train_id}/validate")
async def validate_train(
    train_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ReleaseCoordinationService(db)
    return await service.validate_train(train_id=train_id)


@router.post("/trains/{train_id}/schedule")
async def schedule_train(
    train_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ReleaseCoordinationService(db)
    return await service.schedule_train(train_id=train_id)


@router.post("/trains/{train_id}/handoff")
async def handoff_train(
    train_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ReleaseCoordinationService(db)
    return await service.handoff_train(train_id=train_id)


@router.get("/trains/{train_id}/dependencies")
async def get_train_dependencies(
    train_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ReleaseCoordinationService(db)
    return await service.get_train_dependencies(train_id=train_id)


@router.get("/trains/{train_id}/conflicts")
async def get_train_conflicts(
    train_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ReleaseCoordinationService(db)
    return await service.get_train_conflicts(train_id=train_id)


@router.get("/trains/{train_id}/waves")
async def get_train_waves(
    train_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ReleaseCoordinationService(db)
    return await service.get_train_waves(train_id=train_id)


@router.get("/trains/{train_id}/calendar")
async def get_train_calendar(
    train_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ReleaseCoordinationService(db)
    return await service.get_train_calendar(train_id=train_id)


@router.get("/trains/{train_id}/timeline")
async def get_train_timeline(
    train_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ReleaseCoordinationService(db)
    return await service.get_train_timeline(train_id=train_id)


@router.post("/trains/{train_id}/waves")
async def create_wave(
    train_id: str,
    payload: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ReleaseCoordinationService(db)
    name = payload.get("name", "Wave 1") if payload else "Wave 1"
    seq = payload.get("sequence_number", 1) if payload else 1
    return await service.create_wave(train_id=train_id, name=name, sequence_number=seq)


@router.post("/windows")
async def create_change_window(
    payload: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_current_workspace),
    user_id: Any = Depends(get_current_user),
) -> Any:
    service = ReleaseCoordinationService(db)
    user_id_str = _get_user_id_str(user_id)
    name = payload.get("name", "Standard Maintenance Window") if payload else "Standard Maintenance Window"
    wtype = payload.get("window_type", "maintenance") if payload else "maintenance"
    return await service.create_change_window(
        workspace_id=workspace_id, name=name, window_type=wtype, user_id=user_id_str
    )


@router.get("/windows")
async def list_change_windows(
    workspace_id: str = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ReleaseCoordinationService(db)
    return await service.list_change_windows(workspace_id=workspace_id)


@router.get("/calendar")
async def get_coordination_calendar(
    workspace_id: str = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ReleaseCoordinationService(db)
    return await service.get_coordination_calendar(workspace_id=workspace_id)


@router.get("/conflicts")
async def get_coordination_conflicts(
    workspace_id: str = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ReleaseCoordinationService(db)
    return await service.get_coordination_conflicts(workspace_id=workspace_id)


@router.get("/overview")
async def get_coordination_overview(
    workspace_id: str = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ReleaseCoordinationService(db)
    return await service.get_coordination_overview(workspace_id=workspace_id)
