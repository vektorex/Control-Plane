from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class DocumentResponse(BaseModel):
    """API schema for a document entity."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    project_id: Optional[UUID] = None
    filename: str
    original_filename: str
    mime_type: str
    file_size: int
    checksum: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    chunk_count: int = 0
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    """API schema for a paginated / filtered list of documents."""
    items: List[DocumentResponse]
    total: int


class DocumentChunkResponse(BaseModel):
    """API schema for an extracted and indexed document chunk."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    workspace_id: UUID
    project_id: Optional[UUID] = None
    chunk_index: int
    content: str
    token_count: int
    page_number: Optional[int] = None
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime


class DocumentChunkListResponse(BaseModel):
    """API schema for a list of chunks within a document."""
    items: List[DocumentChunkResponse]
    total: int
