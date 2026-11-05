from fastapi import Header, Depends, HTTPException, status
from typing import Union
from backend.app.core.auth import get_current_user
from backend.app.db.models.user import User


async def get_current_workspace(
    x_workspace_id: str = Header(default="default-workspace", alias="X-Workspace-Id")
) -> str:
    return x_workspace_id


__all__ = ["get_current_workspace", "get_current_user"]

