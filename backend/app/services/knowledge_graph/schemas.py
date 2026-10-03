"""
Pydantic contracts and schemas for Step 29 Knowledge Graph and Structured Context Layer.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.services.knowledge_graph.constants import (
    GRAPH_DEFAULT_HOPS,
    GRAPH_MAX_ENTITIES,
    GRAPH_MAX_HOPS,
    GRAPH_MAX_RELATIONSHIPS,
)


# -----------------------------------------------------------------------------
# Entity Aliases and Sources
# -----------------------------------------------------------------------------

class EntityAliasResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_id: uuid.UUID
    alias: str
    normalized_alias: str
    source_type: str
    created_at: datetime


class EntitySourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_id: uuid.UUID
    source_type: str
    source_id: str
    source_location: Optional[str] = None
    content_hash: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="meta")
    created_at: datetime


# -----------------------------------------------------------------------------
# Entity Schemas
# -----------------------------------------------------------------------------

class EntityCreateRequest(BaseModel):
    canonical_name: str = Field(..., min_length=1, max_length=255)
    entity_type: str = Field(..., min_length=1, max_length=64)
    description: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    aliases: List[str] = Field(default_factory=list)
    source_type: str = Field(default="manual")
    source_id: Optional[str] = None
    source_metadata: Dict[str, Any] = Field(default_factory=dict)
    project_id: Optional[uuid.UUID] = None


class EntityUpdateRequest(BaseModel):
    canonical_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    status: Optional[str] = None


class EntityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    entity_type: str
    canonical_name: str
    description: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    source_count: int = 1
    confidence: Optional[float] = None
    status: str
    created_at: datetime
    updated_at: datetime
    aliases: List[EntityAliasResponse] = Field(default_factory=list)
    sources: List[EntitySourceResponse] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Relationship Schemas
# -----------------------------------------------------------------------------

class RelationshipCreateRequest(BaseModel):
    source_entity_id: uuid.UUID
    relationship_type: str = Field(..., min_length=1, max_length=64)
    target_entity_id: uuid.UUID
    properties: Dict[str, Any] = Field(default_factory=dict)
    source_reference: Dict[str, Any] = Field(default_factory=dict)
    confidence: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    project_id: Optional[uuid.UUID] = None


class RelationshipUpdateRequest(BaseModel):
    properties: Optional[Dict[str, Any]] = None
    source_reference: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    status: Optional[str] = None


class RelationshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    source_entity_id: uuid.UUID
    relationship_type: str
    target_entity_id: uuid.UUID
    properties: Dict[str, Any] = Field(default_factory=dict)
    source_reference: Dict[str, Any] = Field(default_factory=dict)
    confidence: Optional[float] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: datetime
    source_entity_name: Optional[str] = None
    target_entity_name: Optional[str] = None


# -----------------------------------------------------------------------------
# Graph Traversal and Query Schemas
# -----------------------------------------------------------------------------

class GraphQueryRequest(BaseModel):
    seed_entities: List[uuid.UUID] = Field(default_factory=list, description="Seed entity UUIDs to begin traversal")
    seed_names: List[str] = Field(default_factory=list, description="Optional entity canonical names or aliases to link")
    entity_types: List[str] = Field(default_factory=list, description="Filter for returned entity types")
    relationship_types: List[str] = Field(default_factory=list, description="Filter for traversal edge types")
    max_hops: int = Field(default=GRAPH_DEFAULT_HOPS, ge=1, le=GRAPH_MAX_HOPS, description="Bounded expansion depth (1-3)")
    max_entities: int = Field(default=50, ge=1, le=GRAPH_MAX_ENTITIES, description="Upper ceiling on visited nodes")
    max_relationships: int = Field(default=100, ge=1, le=GRAPH_MAX_RELATIONSHIPS, description="Upper ceiling on collected edges")
    include_temporal_expired: bool = Field(default=False, description="Whether to include relationships where valid_to < now")
    project_id: Optional[uuid.UUID] = None


class GraphNeighborResponse(BaseModel):
    entity: EntityResponse
    neighbors: List[EntityResponse] = Field(default_factory=list)
    relationships: List[RelationshipResponse] = Field(default_factory=list)


class GraphContextResult(BaseModel):
    """
    Standardized payload consumed by GraphContextProvider to synthesize ContextItems.
    """
    entities: List[EntityResponse] = Field(default_factory=list)
    relationships: List[RelationshipResponse] = Field(default_factory=list)
    source_references: List[Dict[str, Any]] = Field(default_factory=list)
    retrieval_metadata: Dict[str, Any] = Field(default_factory=dict)
    token_estimate: int = 0


# -----------------------------------------------------------------------------
# Change Proposals and Reviews
# -----------------------------------------------------------------------------

class GraphChangeProposalCreate(BaseModel):
    source_id: str
    source_type: str = "extraction"
    proposed_entities: List[Dict[str, Any]] = Field(default_factory=list)
    proposed_relationships: List[Dict[str, Any]] = Field(default_factory=list)
    project_id: Optional[uuid.UUID] = None


class GraphChangeProposalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    source_id: str
    source_type: str
    proposed_entities: List[Dict[str, Any]] = Field(default_factory=list)
    proposed_relationships: List[Dict[str, Any]] = Field(default_factory=list)
    status: str
    created_by: Optional[uuid.UUID] = None
    reviewed_by: Optional[uuid.UUID] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime


class ProposalActionRequest(BaseModel):
    rejection_reason: Optional[str] = None


# -----------------------------------------------------------------------------
# Conflicts
# -----------------------------------------------------------------------------

class GraphConflictResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    entity_id: Optional[uuid.UUID] = None
    relationship_id: Optional[uuid.UUID] = None
    conflict_type: str
    details: Dict[str, Any] = Field(default_factory=dict)
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[uuid.UUID] = None


class ConflictResolveRequest(BaseModel):
    resolution_action: str = Field(..., description="resolve, dismiss, or merge")
    notes: Optional[str] = None


# -----------------------------------------------------------------------------
# Entity Merge
# -----------------------------------------------------------------------------

class EntityMergeRequest(BaseModel):
    primary_entity_id: uuid.UUID = Field(..., description="Canonical entity to absorb relationships and aliases")
    duplicate_entity_id: uuid.UUID = Field(..., description="Duplicate entity to be archived")
    merge_reason: Optional[str] = Field(default=None, description="Human-readable justification for the merge")


class EntityMergeResponse(BaseModel):
    canonical_entity: "EntityResponse"
    archived_entity_id: uuid.UUID
    transferred_relationships_count: int
    transferred_aliases_count: int


# -----------------------------------------------------------------------------
# Extraction Schemas
# -----------------------------------------------------------------------------

class ExtractedEntity(BaseModel):
    canonical_name: str
    entity_type: str
    description: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    aliases: List[str] = Field(default_factory=list)
    confidence: float = 1.0

    @field_validator("entity_type", mode="before")
    @classmethod
    def _validate_entity_type(cls, v: Any) -> str:
        from backend.app.services.knowledge_graph.constants import ALLOWED_ENTITY_TYPES  # noqa: PLC0415
        raw = str(v).strip().lower().replace(" ", "_").replace("-", "_")
        if raw not in ALLOWED_ENTITY_TYPES:
            raise ValueError(
                f"entity_type '{v}' is not in the controlled entity type registry. "
                f"Allowed values: {sorted(ALLOWED_ENTITY_TYPES)}"
            )
        return raw


class ExtractedRelationship(BaseModel):
    source_name: str
    relationship_type: str
    target_name: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0


class GraphExtractionPayload(BaseModel):
    """
    Strict Pydantic structure enforced upon AI Gateway extraction outputs.
    """
    entities: List[ExtractedEntity] = Field(default_factory=list)
    relationships: List[ExtractedRelationship] = Field(default_factory=list)


class GraphExtractRequest(BaseModel):
    source_id: str
    source_type: str = "document"
    content: Optional[str] = None
    project_id: Optional[uuid.UUID] = None
    run_async: bool = False


class GraphExtractResponse(BaseModel):
    proposal_id: Optional[uuid.UUID] = None
    entities_created: int = 0
    relationships_created: int = 0
    is_async: bool = False
    job_id: Optional[uuid.UUID] = None
    message: str = "Extraction completed"


# -----------------------------------------------------------------------------
# Task Preview and Project Knowledge Map
# -----------------------------------------------------------------------------

class GraphPreviewRequest(BaseModel):
    text: str = Field(..., description="Task instructions or query to analyze for graph relevance")
    project_id: Optional[uuid.UUID] = None


class GraphPreviewResponse(BaseModel):
    is_graph_recommended: bool
    detected_entities: List[str] = Field(default_factory=list)
    candidate_relationships: List[Dict[str, str]] = Field(default_factory=list)
    estimated_tokens: int = 0
    retrieval_scope: str = "workspace"


class ProjectKnowledgeSummary(BaseModel):
    entity_count: int = 0
    relationship_count: int = 0
    pending_proposals_count: int = 0
    open_conflicts_count: int = 0
    entity_type_counts: Dict[str, int] = Field(default_factory=dict)
    relationship_type_counts: Dict[str, int] = Field(default_factory=dict)
