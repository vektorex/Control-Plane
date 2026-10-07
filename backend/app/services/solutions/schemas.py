from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class SolutionComponentBase(BaseModel):
    catalog_item_id: str
    component_key: str
    display_name: str
    component_type: str
    configuration: Dict[str, Any] = {}
    position: Dict[str, Any] = {"x": 0, "y": 0}
    input_mapping: Dict[str, Any] = {}
    output_mapping: Dict[str, Any] = {}
    required: bool = True
    optional: bool = False
    condition: Optional[Dict[str, Any]] = None

class SolutionComponentResponse(SolutionComponentBase):
    id: str
    solution_version_id: str
    created_at: datetime
    class Config:
        from_attributes = True

class SolutionConnectionBase(BaseModel):
    source_component_id: str
    source_port: str
    target_component_id: str
    target_port: str
    mapping: Dict[str, Any] = {}
    condition: Optional[Dict[str, Any]] = None

class SolutionConnectionResponse(SolutionConnectionBase):
    id: str
    solution_version_id: str
    created_at: datetime
    class Config:
        from_attributes = True

class SolutionBase(BaseModel):
    organization_id: str
    workspace_id: str
    project_id: Optional[str] = None
    name: str
    slug: str
    description: Optional[str] = None
    objective: Optional[str] = None
    status: str = "draft"
    visibility: str = "workspace"
    owner_type: str
    owner_id: str

class SolutionCreate(SolutionBase):
    created_by: str

class SolutionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    objective: Optional[str] = None
    status: Optional[str] = None
    visibility: Optional[str] = None

class SolutionVersionBase(BaseModel):
    version: str
    status: str = "draft"
    objective: Optional[str] = None
    inputs_schema: Optional[Dict[str, Any]] = None
    outputs_schema: Optional[Dict[str, Any]] = None
    constraints: Dict[str, Any] = {}
    requirements: Dict[str, Any] = {}
    created_by: str

class SolutionVersionResponse(SolutionVersionBase):
    id: str
    solution_id: str
    created_at: datetime
    published_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None
    is_immutable: bool
    components: List[SolutionComponentResponse] = []
    connections: List[SolutionConnectionResponse] = []

    class Config:
        from_attributes = True

class SolutionResponse(SolutionBase):
    id: str
    current_version_id: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ValidationFinding(BaseModel):
    code: str
    message: str
    component_id: Optional[str] = None
    source: str
    severity: str # error, warning, info
    remediation: Optional[str] = None

class ValidationResponse(BaseModel):
    is_valid: bool
    findings: List[ValidationFinding]
