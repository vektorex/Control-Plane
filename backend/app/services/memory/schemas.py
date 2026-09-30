"""
Pydantic schemas for the Memory System.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class MemoryType(str, Enum):
    PREFERENCE = "preference"
    PROJECT_CONTEXT = "project_context"
    WORKFLOW_CONTEXT = "workflow_context"
    TECHNICAL_FACT = "technical_fact"
    INSTRUCTION = "instruction"
    REFERENCE = "reference"
    DECISION = "decision"


class MemoryScope(str, Enum):
    USER = "user"
    WORKSPACE = "workspace"
    PROJECT = "project"


class MemoryStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    EXPIRED = "expired"


class MemorySourceType(str, Enum):
    EXPLICIT_USER = "explicit_user"
    TASK = "task"
    WORKFLOW = "workflow"
    DOCUMENT = "document"
    CONNECTOR = "connector"
    SYSTEM = "system"


class MemoryImportance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MemoryCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: MemoryType = Field(default=MemoryType.PREFERENCE, description="Categorization of the memory")
    scope: MemoryScope = Field(default=MemoryScope.USER, description="Scope boundary (user, workspace, project)")
    title: str = Field(..., min_length=1, max_length=255, description="Clear, descriptive title for the memory")
    content: str = Field(..., min_length=1, max_length=10000, description="Payload content of the memory")
    importance: MemoryImportance = Field(default=MemoryImportance.MEDIUM, description="Importance weighting")
    project_id: Optional[UUID] = Field(default=None, description="Project ID if scoped to a project")
    source_type: MemorySourceType = Field(default=MemorySourceType.EXPLICIT_USER, description="Source provenance")
    source_id: Optional[str] = Field(default=None, description="Optional identifier of the origin task/run/doc")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Structured attributes")
    expiration: Optional[str] = Field(default="never", description="'never', '7_days', '30_days', '90_days', 'custom'")
    expires_at: Optional[datetime] = Field(default=None, description="Explicit expiration timestamp")


class MemoryUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    content: Optional[str] = Field(default=None, min_length=1, max_length=10000)
    importance: Optional[MemoryImportance] = None
    metadata: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None


class MemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    user_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    scope: str
    type: str
    title: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="metadata_json")
    source_type: str
    source_id: Optional[str] = None
    importance: str
    status: str
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class MemoryListResponse(BaseModel):
    items: List[MemoryResponse]
    total: int
    limit: int = 50
    offset: int = 0


class CandidateMemory(BaseModel):
    """
    Extracted candidate memory that requires explicit confirmation before persistence.
    Contains only a short, user-safe reason. Chain-of-thought is never exposed.
    """
    type: MemoryType = MemoryType.PREFERENCE
    scope: MemoryScope = MemoryScope.USER
    title: str
    content: str
    reason: str = Field(..., description="Short user-safe rationale for proposing this memory")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    source_type: MemorySourceType = MemorySourceType.TASK
    source_id: Optional[str] = None
    importance: MemoryImportance = MemoryImportance.MEDIUM
    requires_confirmation: bool = True
    project_id: Optional[UUID] = None


class MemorySuggestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    user_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    type: str
    scope: str
    title: str
    content: str
    reason: str
    source_type: str
    source_id: Optional[str] = None
    importance: str
    status: str
    created_at: datetime


class MemoryConflictResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    memory_a_id: UUID
    memory_b_id: UUID
    memory_a: Optional[MemoryResponse] = None
    memory_b: Optional[MemoryResponse] = None
    status: str
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None


class ConflictResolveRequest(BaseModel):
    action: str = Field(default="keep_winner", description="'keep_winner', 'merge', 'dismiss'")
    winner_memory_id: Optional[UUID] = None
    resolution_note: Optional[str] = None
    merged_content: Optional[str] = None


class UserMemorySettingsResponse(BaseModel):
    memory_enabled: bool = True
    suggestions_enabled: bool = True
    default_retrieval_mode: str = "auto"
    default_scope: str = "user"
    retention_preference: str = "never"


class UserMemorySettingsUpdateRequest(BaseModel):
    memory_enabled: Optional[bool] = None
    suggestions_enabled: Optional[bool] = None
    default_retrieval_mode: Optional[str] = None
    default_scope: Optional[str] = None
    retention_preference: Optional[str] = None
