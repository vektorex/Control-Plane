from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, ConfigDict

class KnowledgeProvenanceBase(BaseModel):
    source_type: str
    source_id: str
    source_version_id: Optional[str] = None
    evidence_ids: List[str] = []

class KnowledgeProvenanceCreate(KnowledgeProvenanceBase):
    pass

class KnowledgeProvenanceResponse(KnowledgeProvenanceBase):
    id: str
    knowledge_item_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class KnowledgeEvidenceBase(BaseModel):
    source_type: str
    source_id: str
    evidence_type: str
    excerpt_or_reference: str
    snapshot: Optional[Dict[str, Any]] = None
    status: str = "unreviewed"

class KnowledgeEvidenceCreate(KnowledgeEvidenceBase):
    pass

class KnowledgeEvidenceResponse(KnowledgeEvidenceBase):
    id: str
    knowledge_item_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class OrganizationalKnowledgeItemBase(BaseModel):
    workspace_id: str
    project_id: Optional[str] = None
    knowledge_type: str
    title: str
    summary: str
    content: str
    status: str = "candidate"
    confidence_state: str = "unverified"
    sensitivity: str = "internal"
    owner_user_id: Optional[str] = None
    expires_at: Optional[datetime] = None

class OrganizationalKnowledgeItemCreate(OrganizationalKnowledgeItemBase):
    pass

class OrganizationalKnowledgeItemUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    confidence_state: Optional[str] = None
    sensitivity: Optional[str] = None
    owner_user_id: Optional[str] = None
    expires_at: Optional[datetime] = None

class OrganizationalKnowledgeItemResponse(OrganizationalKnowledgeItemBase):
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    last_verified_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class KnowledgeVersionBase(BaseModel):
    version: int
    content: str
    summary: str
    classification: str
    scope: str
    provenance_snapshot: Dict[str, Any]

class KnowledgeVersionResponse(KnowledgeVersionBase):
    id: str
    knowledge_item_id: str
    created_by: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class KnowledgeCandidateBase(BaseModel):
    workspace_id: str
    project_id: Optional[str] = None
    source_type: str
    source_id: str
    candidate_type: str
    title: str
    content: str
    evidence_ids: List[str] = []
    generated_by: str
    status: str = "draft"

class KnowledgeCandidateCreate(KnowledgeCandidateBase):
    pass

class KnowledgeCandidateResponse(KnowledgeCandidateBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class KnowledgeConflictBase(BaseModel):
    workspace_id: str
    knowledge_item_a_id: str
    knowledge_item_b_id: str
    conflict_type: str
    description: str
    evidence_ids: List[str] = []
    status: str = "open"
    resolution: Optional[str] = None

class KnowledgeConflictCreate(KnowledgeConflictBase):
    pass

class KnowledgeConflictResponse(KnowledgeConflictBase):
    id: str
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
