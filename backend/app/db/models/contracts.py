from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, JSON, Integer, Float, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum

class ContractStatus(str, enum.Enum):
    draft = "draft"
    proposed = "proposed"
    review_required = "review_required"
    approved = "approved"
    active = "active"
    paused = "paused"
    at_risk = "at_risk"
    breached = "breached"
    completed = "completed"
    cancelled = "cancelled"
    expired = "expired"
    superseded = "superseded"

class WorkContract(Base):
    __tablename__ = "work_contracts"
    
    id = Column(String(36), primary_key=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    contract_type = Column(String(50), nullable=False)
    status = Column(Enum(ContractStatus), default=ContractStatus.draft, nullable=False)
    priority = Column(String(50), nullable=True)
    requester_type = Column(String(50), nullable=False)
    requester_id = Column(String(36), nullable=False)
    owner_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    objective_id = Column(String(36), ForeignKey("objectives.id"), nullable=True)
    outcome_id = Column(String(36), ForeignKey("outcomes.id"), nullable=True)
    plan_id = Column(String(36), ForeignKey("work_plans.id"), nullable=True)
    
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    effective_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

class WorkContractVersion(Base):
    __tablename__ = "work_contract_versions"
    
    id = Column(String(36), primary_key=True)
    contract_id = Column(String(36), ForeignKey("work_contracts.id"), nullable=False)
    version = Column(Integer, nullable=False)
    scope_snapshot = Column(JSON, nullable=False)
    deliverables_snapshot = Column(JSON, nullable=False)
    acceptance_snapshot = Column(JSON, nullable=False)
    sla_snapshot = Column(JSON, nullable=False)
    resource_snapshot = Column(JSON, nullable=False)
    policy_snapshot = Column(JSON, nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)

class ContractParty(Base):
    __tablename__ = "contract_parties"
    
    id = Column(String(36), primary_key=True)
    contract_id = Column(String(36), ForeignKey("work_contracts.id"), nullable=False)
    party_type = Column(String(50), nullable=False)
    party_id = Column(String(36), nullable=False)
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class ContractScope(Base):
    __tablename__ = "contract_scopes"
    
    id = Column(String(36), primary_key=True)
    contract_version_id = Column(String(36), ForeignKey("work_contract_versions.id"), nullable=False)
    scope_type = Column(String(50), nullable=False)
    configuration = Column(JSON, nullable=False, default={})
    included_resources = Column(JSON, nullable=False, default=[])
    excluded_resources = Column(JSON, nullable=False, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class ContractDeliverable(Base):
    __tablename__ = "contract_deliverables"
    
    id = Column(String(36), primary_key=True)
    contract_version_id = Column(String(36), ForeignKey("work_contract_versions.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    deliverable_type = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(36), nullable=True)
    required = Column(Integer, default=1, nullable=False) # sqlite boolean
    status = Column(String(50), default="pending", nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

class ContractAcceptanceCriterion(Base):
    __tablename__ = "contract_acceptance_criteria"
    
    id = Column(String(36), primary_key=True)
    contract_version_id = Column(String(36), ForeignKey("work_contract_versions.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    criterion_type = Column(String(50), nullable=False)
    configuration = Column(JSON, nullable=False, default={})
    required = Column(Integer, default=1, nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    evidence_ids = Column(JSON, nullable=False, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)

class ServiceLevelAgreement(Base):
    __tablename__ = "service_level_agreements"
    
    id = Column(String(36), primary_key=True)
    contract_version_id = Column(String(36), ForeignKey("work_contract_versions.id"), nullable=False)
    name = Column(String(255), nullable=False)
    metric = Column(String(50), nullable=False)
    target = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    measurement_window = Column(String(50), nullable=False)
    measurement_source = Column(String(50), nullable=False)
    start_condition = Column(JSON, nullable=False, default={})
    stop_condition = Column(JSON, nullable=False, default={})
    breach_threshold = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class SLAMeasurement(Base):
    __tablename__ = "sla_measurements"
    
    id = Column(String(36), primary_key=True)
    sla_id = Column(String(36), ForeignKey("service_level_agreements.id"), nullable=False)
    contract_id = Column(String(36), ForeignKey("work_contracts.id"), nullable=False)
    measurement_window_start = Column(DateTime(timezone=True), nullable=False)
    measurement_window_end = Column(DateTime(timezone=True), nullable=False)
    observed_value = Column(Float, nullable=True)
    target_value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False) # met, at_risk, breached, unknown
    source_type = Column(String(50), nullable=False)
    source_id = Column(String(36), nullable=False)
    evidence_ids = Column(JSON, nullable=False, default=[])
    measured_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class SLAClock(Base):
    __tablename__ = "sla_clocks"
    
    id = Column(String(36), primary_key=True)
    contract_id = Column(String(36), ForeignKey("work_contracts.id"), nullable=False)
    clock_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False) # running, paused, stopped
    accumulated_ms = Column(Integer, default=0, nullable=False)
    last_started_at = Column(DateTime(timezone=True), nullable=True)
    last_paused_at = Column(DateTime(timezone=True), nullable=True)

class ContractBreach(Base):
    __tablename__ = "contract_breaches"
    
    id = Column(String(36), primary_key=True)
    contract_id = Column(String(36), ForeignKey("work_contracts.id"), nullable=False)
    contract_version_id = Column(String(36), ForeignKey("work_contract_versions.id"), nullable=False)
    sla_id = Column(String(36), ForeignKey("service_level_agreements.id"), nullable=True)
    breach_type = Column(String(50), nullable=False)
    severity = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    observed_value = Column(String(255), nullable=True)
    expected_value = Column(String(255), nullable=True)
    evidence_ids = Column(JSON, nullable=False, default=[])
    status = Column(String(50), default="open", nullable=False)
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

class ContractEscalationPolicy(Base):
    __tablename__ = "contract_escalation_policies"
    
    id = Column(String(36), primary_key=True)
    contract_version_id = Column(String(36), ForeignKey("work_contract_versions.id"), nullable=False)
    trigger = Column(String(50), nullable=False)
    delay = Column(Integer, nullable=False) # milliseconds or seconds
    severity = Column(String(50), nullable=False)
    recipient_type = Column(String(50), nullable=False)
    recipient_id = Column(String(36), nullable=False)
    action = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class ContractWaiver(Base):
    __tablename__ = "contract_waivers"
    
    id = Column(String(36), primary_key=True)
    contract_id = Column(String(36), ForeignKey("work_contracts.id"), nullable=False)
    criterion_or_sla_id = Column(String(36), nullable=False)
    reason = Column(Text, nullable=False)
    evidence_ids = Column(JSON, nullable=False, default=[])
    requested_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="requested", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
