from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from backend.app.schemas.workspace import slugify


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    slug: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Project slug unique within workspace (auto-generated from name if omitted)",
    )
    description: Optional[str] = Field(default=None, description="Project scope and context description")

    @field_validator("slug", mode="before")
    @classmethod
    def format_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and str(v).strip():
            slug_str = slugify(str(v))
            if not slug_str:
                raise ValueError("Slug must contain valid alphanumeric characters or hyphens.")
            return slug_str
        return None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    slug: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None)

    @field_validator("slug", mode="before")
    @classmethod
    def format_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and str(v).strip():
            slug_str = slugify(str(v))
            if not slug_str:
                raise ValueError("Slug must contain valid alphanumeric characters or hyphens.")
            return slug_str
        return None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    task_count: Optional[int] = 0


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int
