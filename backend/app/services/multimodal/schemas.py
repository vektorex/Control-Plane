"""
Pydantic schemas for Step 30: Multimodal AI and Unified Artifact Intelligence.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.services.multimodal.constants import (
    ArtifactPartType,
    ArtifactStatus,
    ArtifactType,
    MediaCapability,
)


class ArtifactCreate(BaseModel):
    filename: str = Field(..., max_length=255)
    mime_type: str = Field(..., max_length=128)
    size_bytes: int = Field(..., ge=0)
    storage_reference: str = Field(..., max_length=512)
    artifact_type: Optional[str] = None
    project_id: Optional[uuid.UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ArtifactPartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    artifact_id: uuid.UUID
    part_type: str
    sequence_number: int
    content_reference: Optional[str] = None
    text_content: Optional[str] = None
    metadata_: Dict[str, Any] = Field(default_factory=dict, alias="metadata")
    content_hash: Optional[str] = None
    token_estimate: Optional[int] = None
    created_at: datetime


class ArtifactEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    artifact_id: uuid.UUID
    part_id: Optional[uuid.UUID] = None
    page: Optional[int] = None
    timestamp: Optional[float] = None
    region: Optional[Dict[str, Any]] = None
    source_text: Optional[str] = None
    metadata_: Dict[str, Any] = Field(default_factory=dict, alias="metadata")
    created_at: datetime


class ArtifactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    owner_user_id: uuid.UUID
    artifact_type: str
    mime_type: str
    filename: str
    size_bytes: int
    storage_reference: str
    content_hash: str
    status: str
    metadata_: Dict[str, Any] = Field(default_factory=dict, alias="metadata")
    created_at: datetime
    updated_at: datetime
    parts: List[ArtifactPartResponse] = Field(default_factory=list)


class ArtifactInspection(BaseModel):
    detected_type: str
    mime_type: str
    dimensions: Optional[Dict[str, int]] = None  # {"width": 1920, "height": 1080}
    duration_seconds: Optional[float] = None
    page_count: Optional[int] = None
    estimated_processing_size: int = 0
    required_capabilities: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class TableArtifact(BaseModel):
    columns: List[str] = Field(default_factory=list)
    rows: List[List[Any]] = Field(default_factory=list)
    row_count: int = 0
    column_count: int = 0
    source_reference: Optional[str] = None
    sheet_name: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AudioTranscriptSegment(BaseModel):
    start_seconds: float
    end_seconds: float
    speaker: Optional[str] = None
    text: str
    artifact_id: Optional[uuid.UUID] = None
    segment_id: Optional[str] = None


class ArtifactEvidenceItem(BaseModel):
    """
    Standard evidence item representing a grounded artifact observation.
    Used across evaluation lab, citations, and responses.
    """
    artifact_id: uuid.UUID
    part_id: Optional[uuid.UUID] = None
    page: Optional[int] = None
    timestamp: Optional[float] = None
    region: Optional[Dict[str, Any]] = None
    source_text: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ArtifactAnalysisRequest(BaseModel):
    instruction: str = Field(default="Analyze this artifact and summarize its core information.")
    mode: str = Field(default="auto", description="'auto' | 'vision' | 'ocr' | 'table' | 'audio'")
    options: Dict[str, Any] = Field(default_factory=dict)


class ArtifactAnalysisResponse(BaseModel):
    artifact_id: uuid.UUID
    summary: str
    analysis: str
    extracted_parts_count: int = 0
    capabilities_used: List[str] = Field(default_factory=list)
    evidence: List[ArtifactEvidenceItem] = Field(default_factory=list)
    model_used: Optional[str] = None
    fallback_used: bool = False
