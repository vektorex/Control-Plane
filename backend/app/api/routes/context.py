from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.repositories.context import ContextRepository
from backend.app.schemas.context import (
    TaskContextResponse,
    TaskContextUpdate,
)
from backend.app.services.context.token_estimator import estimate_tokens

router = APIRouter(prefix="/context", tags=["Context"])


@router.get("/{context_id}", response_model=TaskContextResponse)
async def get_context_item(
    context_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TaskContextResponse:
    """
    Retrieve a single TaskContext item by ID with ownership enforcement.
    """
    repo = ContextRepository(session)
    ctx = await repo.get_by_id_and_owner_or_raise(context_id, user.id)
    resp = TaskContextResponse.model_validate(ctx)
    resp.estimated_tokens = estimate_tokens(ctx.content) + estimate_tokens(ctx.title) + 4
    return resp


@router.patch("/{context_id}", response_model=TaskContextResponse)
async def update_context_item(
    context_id: UUID,
    data: TaskContextUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TaskContextResponse:
    """
    Update title, content, priority, source_type, or metadata for an owned TaskContext item.
    """
    repo = ContextRepository(session)
    ctx = await repo.update(context_id, user.id, data)
    resp = TaskContextResponse.model_validate(ctx)
    resp.estimated_tokens = estimate_tokens(ctx.content) + estimate_tokens(ctx.title) + 4
    return resp


@router.delete("/{context_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_context_item(
    context_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Delete an owned TaskContext item.
    """
    repo = ContextRepository(session)
    await repo.delete(context_id, user.id)
    return None
