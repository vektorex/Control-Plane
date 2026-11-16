from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class ServiceCatalogItemBase(BaseModel):
    organization_id: str
    workspace_id: str
    project_id: Optional[str] = None
    
    name: str
    slug: str
    description: Optional[str] = None
    
    resource_type: str
    resource_id: str
    
    category: str
    subcategory: Optional[str] = None
    
    status: str = "draft"
    visibility: str = "workspace"
    
    owner_type: str
    owner_id: str
    
    version_reference: Optional[str] = None
    
    capability_summary: Dict[str, Any] = {}
    
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    
    requirements: Dict[str, Any] = {}
    
    supported_modes: List[str] = []
    supported_modalities: List[str] = []
    supported_data_classes: List[str] = []
    
    required_permissions: List[str] = []
    required_tools: List[str] = []
    required_connectors: List[str] = []
    required_models: List[str] = []
    
    dependency_summary: List[Dict[str, Any]] = []
    
    availability_status: str = "unknown"
    eligibility_status: str = "unknown"
    
    quality_evidence_summary: Dict[str, Any] = {}
    
    sla_reference: Optional[Dict[str, Any]] = None
    documentation_reference: Optional[Dict[str, Any]] = None
    
    provenance: Dict[str, Any] = {}
    freshness_status: str = "unknown"

class ServiceCatalogItemCreate(ServiceCatalogItemBase):
    pass

class ServiceCatalogItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    visibility: Optional[str] = None

class ServiceCatalogItemResponse(ServiceCatalogItemBase):
    id: str
    last_verified_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CompatibilityRequest(BaseModel):
    input_requirements: Optional[List[str]] = None
    output_requirements: Optional[List[str]] = None
    required_capabilities: Optional[List[str]] = None
    required_tools: Optional[List[str]] = None
    data_classes: Optional[List[str]] = None

class CompatibilityResponse(BaseModel):
    status: str # compatible, conditionally_compatible, incompatible, unknown
    reasons: List[str]
    missing_requirements: List[str]
    incompatible_requirements: List[str]

class EligibilityRequest(BaseModel):
    user_id: str
    workspace_id: str

class EligibilityResponse(BaseModel):
    status: str # eligible, conditionally_eligible, ineligible, unknown
    reasons: List[str]
