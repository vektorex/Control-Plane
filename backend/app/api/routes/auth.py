from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.db.models.workspace import Workspace
from backend.app.schemas.user import UserProfileResponse, UserResponse
from backend.app.schemas.workspace import WorkspaceResponse

router = APIRouter(prefix="/auth", tags=["Authentication & User Profiles"])


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """
    Retrieve authenticated user's profile and default workspace context.
    """
    # Fetch first workspace for default context
    ws_stmt = (
        select(Workspace)
        .where(Workspace.owner_user_id == user.id)
        .order_by(Workspace.created_at.asc())
        .limit(1)
    )
    ws_res = await session.execute(ws_stmt)
    default_ws = ws_res.scalar_one_or_none()

    return UserProfileResponse(
        id=user.id,
        auth_user_id=user.auth_user_id,
        email=user.email,
        created_at=user.created_at,
        updated_at=user.updated_at,
        default_workspace_id=default_ws.id if default_ws else None,
    )
