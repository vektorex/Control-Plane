from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum

class ChangeStatus(str, enum.Enum):
    draft = "draft"
    analyzing = "analyzing"
    impact_ready = "impact_ready"
    review_required = "review_required"
    approved = "approved"
    rejected = "rejected"
    scheduled = "scheduled"
    applied = "applied"
    rolled_back = "rolled_back"
    cancelled = "cancelled"
    failed = "failed"

class ChangeRequest(Base):
    __tablename__ = "change_requests"
    
    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    change_type = Column(String(50), nullable=False)
    subject_type = Column(String(50), nullable=False)
    subject_id = Column(String(36), nullable=False)

    requested_by = Column(String(36), nullable=False)
    
    status = Column(Enum(ChangeStatus), default=ChangeStatus.draft, nullable=False)
    
    scope = Column(JSON, nullable=False, default={})
    proposed_change = Column(JSON, nullable=False, default={})

    reason = Column(Text, nullable=True)
    expected_benefit = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    affected_resources = relationship("ChangeAffectedResource", back_populates="change_request", cascade="all, delete-orphan")
    risks = relationship("ChangeRisk", back_populates="change_request", cascade="all, delete-orphan")
    revalidation_requirements = relationship("ChangeRevalidationRequirement", back_populates="change_request", cascade="all, delete-orphan")
    evidence = relationship("ChangeEvidence", back_populates="change_request", cascade="all, delete-orphan")

class ChangeAffectedResource(Base):
    __tablename__ = "change_affected_resources"

    id = Column(String(36), primary_key=True)
    change_request_id = Column(String(36), ForeignKey("change_requests.id"), nullable=False)
    
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(36), nullable=False)
    
    relationship_type = Column(String(50), nullable=False)
    impact_state = Column(String(50), nullable=False)
    
    impact_reason = Column(Text, nullable=True)
    source_evidence = Column(JSON, nullable=False, default={})
    severity = Column(String(50), nullable=False, default="medium")
    confidence_state = Column(String(50), nullable=False, default="high")

    change_request = relationship("ChangeRequest", back_populates="affected_resources")

class ChangeRisk(Base):
    __tablename__ = "change_risks"
    
    id = Column(String(36), primary_key=True)
    change_request_id = Column(String(36), ForeignKey("change_requests.id"), nullable=False)
    
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=False, default={})
    affected_resource = Column(String(100), nullable=True)
    mitigation = Column(Text, nullable=True)
    blocking = Column(Boolean, nullable=False, default=False)
    
    change_request = relationship("ChangeRequest", back_populates="risks")

class ChangeRevalidationRequirement(Base):
    __tablename__ = "change_revalidation_requirements"
    
    id = Column(String(36), primary_key=True)
    change_request_id = Column(String(36), ForeignKey("change_requests.id"), nullable=False)
    
    requirement_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    affected_resource = Column(String(100), nullable=True)

    change_request = relationship("ChangeRequest", back_populates="revalidation_requirements")

class ChangeEvidence(Base):
    __tablename__ = "change_evidence"
    
    id = Column(String(36), primary_key=True)
    change_request_id = Column(String(36), ForeignKey("change_requests.id"), nullable=False)
    
    source_type = Column(String(50), nullable=False)
    source_id = Column(String(36), nullable=False)
    source_version = Column(String(50), nullable=True)
    
    relationship = Column(String(100), nullable=False)
    observed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    change_request = relationship("ChangeRequest", back_populates="evidence")

class ChangeAnalysisRecord(Base):
    __tablename__ = "change_analysis_records"
    
    id = Column(String(36), primary_key=True)
    change_request_id = Column(String(36), ForeignKey("change_requests.id"), nullable=False)
    
    analysis_snapshot = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class ChangeRollbackAnalysis(Base):
    __tablename__ = "change_rollback_analysis"
    
    id = Column(String(36), primary_key=True)
    change_request_id = Column(String(36), ForeignKey("change_requests.id"), nullable=False)
    
    resource = Column(String(100), nullable=False)
    current_version = Column(String(50), nullable=True)
    previous_version = Column(String(50), nullable=True)
    
    rollback_possible = Column(Boolean, nullable=False, default=False)
    rollback_dependencies = Column(JSON, nullable=False, default=[])
    rollback_constraints = Column(JSON, nullable=False, default=[])
    rollback_requirements = Column(JSON, nullable=False, default=[])
    rollback_limitations = Column(JSON, nullable=False, default=[])
