import re
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


def slugify(text: str) -> str:
    """Convert a name into a URL-safe lowercase slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


class WorkspaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Human-readable workspace name")
    slug: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Unique URL-friendly slug (auto-generated from name if omitted)",
    )

    @field_validator("slug", mode="before")
    @classmethod
    def format_slug(cls, v: Optional[str], info) -> Optional[str]:
        if v is not None and str(v).strip():
            slug_str = slugify(str(v))
            if not slug_str:
                raise ValueError("Slug must contain valid alphanumeric characters or hyphens.")
            return slug_str
        return None


from typing import Dict, List, Optional


class WorkspaceCreate(WorkspaceBase):
    organization_id: Optional[UUID] = Field(default=None, description="Parent organization ID")


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    slug: Optional[str] = Field(default=None, min_length=1, max_length=255)

    @field_validator("slug", mode="before")
    @classmethod
    def format_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and str(v).strip():
            slug_str = slugify(str(v))
            if not slug_str:
                raise ValueError("Slug must contain valid alphanumeric characters or hyphens.")
            return slug_str
        return None


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_user_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    name: str
    slug: str
    status: Optional[str] = "active"
    created_at: datetime
    updated_at: datetime
    project_count: Optional[int] = 0
    capabilities: Dict[str, bool] = Field(default_factory=dict)


class WorkspaceListResponse(BaseModel):
    workspaces: List[WorkspaceResponse]
    total: int
