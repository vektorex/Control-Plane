from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.repositories.run import RunRepository
from backend.app.schemas.run import RunResponse

router = APIRouter(prefix="/runs", tags=["Execution Runs"])


@router.get("/{run_id}", response_model=RunResponse)
async def get_run_detail(
    run_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> RunResponse:
    """
    Retrieve run execution detail, input snapshot, token metrics, and output.
    Enforces multi-tenant ownership: returns 404 if the run belongs to another user.
    """
    repo = RunRepository(session)
    run = await repo.get_by_id_and_owner_or_raise(run_id, user.id)
    return RunResponse.model_validate(run)
