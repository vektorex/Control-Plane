from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class IntentRequestCreate(BaseModel):
    organization_id: str
    workspace_id: str
    project_id: Optional[str] = None
    submitted_by: str
    raw_intent: str

class IntentRequirementSchema(BaseModel):
    req_type: str
    description: str
    value: Optional[Dict[str, Any]] = None
    source: str
    mandatory: bool = True
    confidence: Optional[float] = None
    status: str = "active"

class IntentRequirementResponse(IntentRequirementSchema):
    id: str
    intent_request_id: str
    model_config = ConfigDict(from_attributes=True)

class IntentClarificationSchema(BaseModel):
    question: str
    reason: str
    options: List[str] = []
    required: bool = True

class IntentClarificationResponse(IntentClarificationSchema):
    id: str
    intent_request_id: str
    answer: Optional[str] = None
    answered_by: Optional[str] = None
    answered_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class CandidateSolutionSchema(BaseModel):
    name: str
    objective: str
    source: str
    solution_blueprint: Dict[str, Any] = {}
    requirements: Dict[str, Any] = {}
    assumptions: Dict[str, Any] = {}
    validation_summary: Dict[str, Any] = {}
    simulation_summary: Dict[str, Any] = {}
    provenance: Dict[str, Any] = {}

class CandidateSolutionResponse(CandidateSolutionSchema):
    id: str
    intent_request_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IntentRequestResponse(BaseModel):
    id: str
    organization_id: str
    workspace_id: str
    project_id: Optional[str] = None
    submitted_by: str
    raw_intent: str
    normalized_intent: Optional[str] = None
    status: str
    complexity: str
    confidence: Optional[float] = None
    analysis: Dict[str, Any] = {}
    constraints: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    requirements: List[IntentRequirementResponse] = []
    clarifications: List[IntentClarificationResponse] = []
    candidates: List[CandidateSolutionResponse] = []

    model_config = ConfigDict(from_attributes=True)

class ValidationResponse(BaseModel):
    is_valid: bool
    findings: List[Dict[str, Any]]
