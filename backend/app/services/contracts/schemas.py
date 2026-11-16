from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class WorkContractBase(BaseModel):
    workspace_id: str
    project_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    contract_type: str
    status: str = "draft"
    priority: Optional[str] = None
    requester_type: str
    requester_id: str
    owner_user_id: Optional[str] = None
    objective_id: Optional[str] = None
    outcome_id: Optional[str] = None
    plan_id: Optional[str] = None
    effective_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

class WorkContractCreate(WorkContractBase):
    pass

class WorkContractResponse(WorkContractBase):
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ContractDeliverableBase(BaseModel):
    name: str
    description: Optional[str] = None
    deliverable_type: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    required: bool = True
    due_at: Optional[datetime] = None

class ContractDeliverableCreate(ContractDeliverableBase):
    pass

class ContractDeliverableResponse(ContractDeliverableBase):
    id: str
    contract_version_id: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ServiceLevelAgreementBase(BaseModel):
    name: str
    metric: str
    target: float
    unit: str
    measurement_window: str
    measurement_source: str
    start_condition: Dict[str, Any] = {}
    stop_condition: Dict[str, Any] = {}
    breach_threshold: Optional[float] = None

class ServiceLevelAgreementCreate(ServiceLevelAgreementBase):
    pass

class ContractAcceptanceCriterionBase(BaseModel):
    name: str
    description: Optional[str] = None
    criterion_type: str
    configuration: Dict[str, Any] = {}
    required: bool = True

class ContractAcceptanceCriterionCreate(ContractAcceptanceCriterionBase):
    pass

class SLAMeasurementResponse(BaseModel):
    id: str
    sla_id: str
    contract_id: str
    measurement_window_start: datetime
    measurement_window_end: datetime
    observed_value: Optional[float] = None
    target_value: float
    unit: str
    status: str
    source_type: str
    source_id: str
    measured_at: datetime

    model_config = ConfigDict(from_attributes=True)
