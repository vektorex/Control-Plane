from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime


class ChangeRequestCreate(BaseModel):
    title: str
    description: Optional[str] = None
    change_type: str = "prompt_update"
    subject_type: str = "prompt"
    subject_id: str
    organization_id: Optional[str] = "default-org"
    project_id: Optional[str] = None
    scope: Optional[Dict[str, Any]] = Field(default_factory=dict)
    proposed_change: Optional[Dict[str, Any]] = Field(default_factory=dict)
    reason: Optional[str] = None
    expected_benefit: Optional[str] = None


class ChangeRequestResponse(BaseModel):
    id: str
    organization_id: str
    workspace_id: str
    project_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    change_type: str
    subject_type: str
    subject_id: str
    requested_by: str
    status: str
    scope: Dict[str, Any] = Field(default_factory=dict)
    proposed_change: Dict[str, Any] = Field(default_factory=dict)
    reason: Optional[str] = None
    expected_benefit: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ImpactSummary(BaseModel):
    direct_impacts: int = 0
    indirect_impacts: int = 0
    unknown_impacts: int = 0
    revalidation_reqs: int = 0
