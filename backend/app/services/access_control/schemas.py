"""
Pydantic schemas for Step 27: Multi-Tenant Organizations, Teams, Roles & Access Control.
Includes UI hint capabilities dictionary in responses.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator


# -----------------------------------------------------------------------------
# 1. Organization Schemas
# -----------------------------------------------------------------------------

class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Human readable organization name")
    slug: Optional[str] = Field(None, min_length=2, max_length=255, description="Unique organization slug")


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    slug: Optional[str] = Field(None, min_length=2, max_length=255)


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    owner_user_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    workspace_count: Optional[int] = 0
    member_count: Optional[int] = 0
    capabilities: Dict[str, bool] = Field(default_factory=dict)


class OrganizationListResponse(BaseModel):
    organizations: List[OrganizationResponse]
    total: int


# -----------------------------------------------------------------------------
# 2. Member Schemas
# -----------------------------------------------------------------------------

class OrganizationMemberUpdate(BaseModel):
    role: Optional[str] = Field(None, description="Updated role: admin, member, or viewer")
    status: Optional[str] = Field(None, description="Updated status: active, suspended, or removed")


class OrganizationMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    user_id: UUID
    email: Optional[str] = None
    role: str
    status: str
    joined_at: Optional[datetime] = None
    created_at: datetime
    capabilities: Dict[str, bool] = Field(default_factory=dict)


class OrganizationMemberListResponse(BaseModel):
    members: List[OrganizationMemberResponse]
    total: int


# -----------------------------------------------------------------------------
# 3. Invitation Schemas
# -----------------------------------------------------------------------------

class OrganizationInvitationCreate(BaseModel):
    email: str = Field(..., min_length=3, max_length=255, description="Recipient email address")
    role: str = Field("member", description="Assigned role: admin, member, or viewer")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean):
            raise ValueError("Invalid email address format.")
        return clean


class OrganizationInvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    email: str
    role: str
    invited_by: UUID
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime
    invite_token: Optional[str] = None  # Returned only upon creation for link generation


class OrganizationInvitationListResponse(BaseModel):
    invitations: List[OrganizationInvitationResponse]
    total: int


# -----------------------------------------------------------------------------
# 4. Workspace Member Schemas
# -----------------------------------------------------------------------------

class WorkspaceMemberCreate(BaseModel):
    user_id: UUID
    role: str = Field("member", description="Workspace role: admin, member, or viewer")


class WorkspaceMemberUpdate(BaseModel):
    role: Optional[str] = Field(None, description="Workspace role: admin, member, or viewer")
    status: Optional[str] = Field(None, description="Status: active, suspended, or removed")


class WorkspaceMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    user_id: UUID
    email: Optional[str] = None
    role: str
    status: str
    created_at: datetime


class WorkspaceMemberListResponse(BaseModel):
    members: List[WorkspaceMemberResponse]
    total: int


# -----------------------------------------------------------------------------
# 5. Project Member & Access Schemas
# -----------------------------------------------------------------------------

class ProjectMemberCreate(BaseModel):
    user_id: UUID
    role: str = Field("editor", description="Project role: editor or viewer")


class ProjectMemberUpdate(BaseModel):
    role: str = Field(..., description="Project role: editor or viewer")


class ProjectMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    user_id: UUID
    email: Optional[str] = None
    role: str
    created_at: datetime


class ProjectMemberListResponse(BaseModel):
    members: List[ProjectMemberResponse]
    total: int


class ProjectAccessModeUpdate(BaseModel):
    access_mode: str = Field(..., description="Access mode: 'workspace' or 'restricted'")


# -----------------------------------------------------------------------------
# 6. Ownership Transfer Schemas
# -----------------------------------------------------------------------------

class OwnershipTransferRequest(BaseModel):
    target_user_id: UUID = Field(..., description="Target active organization member user ID")
    confirmation: bool = Field(True, description="Explicit confirmation requirement")


# -----------------------------------------------------------------------------
# 7. Authorization Context & UI Hints
# -----------------------------------------------------------------------------

class AuthorizationContextResponse(BaseModel):
    user_id: UUID
    organization_id: UUID
    organization_role: str
    workspace_id: Optional[UUID] = None
    workspace_role: Optional[str] = None
    project_id: Optional[UUID] = None
    project_access: Optional[str] = None
    project_role: Optional[str] = None
    permissions: List[str]
    capabilities: Dict[str, bool]
