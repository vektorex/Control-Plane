from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.app.schemas.workspace import WorkspaceResponse


class UserBase(BaseModel):
    email: str
    auth_user_id: str


class UserCreate(UserBase):
    pass


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    auth_user_id: str
    email: str
    created_at: datetime
    updated_at: datetime
    workspaces: Optional[List[WorkspaceResponse]] = None


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    auth_user_id: str
    email: str
    created_at: datetime
    updated_at: datetime
    default_workspace_id: Optional[UUID] = None
