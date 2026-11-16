from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class DecisionRequestCreate(BaseModel):
    organization_id: str
    workspace_id: str
    project_id: Optional[str] = None
    subject_type: str
    subject_id: str
    decision_type: str
    requested_by: str
    context_snapshot: Dict[str, Any] = {}

class DecisionEvidenceSchema(BaseModel):
    source_type: str
    source_id: str
    source_version: Optional[str] = None
    evidence_type: str
    claim: str
    value: Dict[str, Any] = {}
    status: str
    expires_at: Optional[datetime] = None
    provenance: Dict[str, Any] = {}

class DecisionEvidenceResponse(DecisionEvidenceSchema):
    id: str
    decision_request_id: str
    observed_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DecisionRequiredActionResponse(BaseModel):
    id: str
    action_type: str
    description: str
    source: str
    blocking: bool
    requires_user: bool
    requires_approval: bool
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DecisionRecordResponse(BaseModel):
    id: str
    decision: str
    state: str
    decision_version: str
    conditions: List[Dict[str, Any]] = []
    blockers: List[Dict[str, Any]] = []
    evidence_snapshot: Dict[str, Any] = {}
    policy_snapshot: Dict[str, Any] = {}
    explanation: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DecisionRequestResponse(BaseModel):
    id: str
    organization_id: str
    workspace_id: str
    project_id: Optional[str] = None
    subject_type: str
    subject_id: str
    decision_type: str
    requested_by: str
    status: str
    context_snapshot: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    evidence: List[DecisionEvidenceResponse] = []
    records: List[DecisionRecordResponse] = []
    required_actions: List[DecisionRequiredActionResponse] = []
    
    model_config = ConfigDict(from_attributes=True)
