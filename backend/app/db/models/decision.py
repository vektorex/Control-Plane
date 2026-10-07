from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum

class DecisionStatus(str, enum.Enum):
    requested = "requested"
    collecting_evidence = "collecting_evidence"
    analyzing = "analyzing"
    ready = "ready"
    blocked = "blocked"
    conditional = "conditional"
    unknown = "unknown"
    expired = "expired"
    failed = "failed"

class DecisionRequest(Base):
    __tablename__ = "decision_requests"
    
    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)

    subject_type = Column(String(50), nullable=False)
    subject_id = Column(String(36), nullable=False)
    
    decision_type = Column(String(50), nullable=False)

    requested_by = Column(String(36), nullable=False)
    
    status = Column(Enum(DecisionStatus), default=DecisionStatus.requested, nullable=False)
    
    context_snapshot = Column(JSON, nullable=False, default={})

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    evidence = relationship("DecisionEvidence", back_populates="decision_request", cascade="all, delete-orphan")
    records = relationship("DecisionRecord", back_populates="decision_request", cascade="all, delete-orphan")
    required_actions = relationship("DecisionRequiredAction", back_populates="decision_request", cascade="all, delete-orphan")

class DecisionEvidence(Base):
    __tablename__ = "decision_evidence"
    
    id = Column(String(36), primary_key=True)
    decision_request_id = Column(String(36), ForeignKey("decision_requests.id"), nullable=False)
    
    source_type = Column(String(50), nullable=False)
    source_id = Column(String(36), nullable=False)
    source_version = Column(String(50), nullable=True)
    
    evidence_type = Column(String(50), nullable=False)
    claim = Column(Text, nullable=False)
    value = Column(JSON, nullable=False, default={})
    status = Column(String(50), nullable=False)
    
    observed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    provenance = Column(JSON, nullable=False, default={})
    
    decision_request = relationship("DecisionRequest", back_populates="evidence")

class DecisionRecord(Base):
    __tablename__ = "decision_records"
    
    id = Column(String(36), primary_key=True)
    decision_request_id = Column(String(36), ForeignKey("decision_requests.id"), nullable=False)
    
    decision = Column(String(50), nullable=False)
    state = Column(String(50), nullable=False)
    decision_version = Column(String(50), nullable=False)
    
    conditions = Column(JSON, nullable=False, default=[])
    blockers = Column(JSON, nullable=False, default=[])
    
    evidence_snapshot = Column(JSON, nullable=False, default={})
    policy_snapshot = Column(JSON, nullable=False, default={})
    
    explanation = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    decision_request = relationship("DecisionRequest", back_populates="records")

class DecisionRequiredAction(Base):
    __tablename__ = "decision_required_actions"
    
    id = Column(String(36), primary_key=True)
    decision_request_id = Column(String(36), ForeignKey("decision_requests.id"), nullable=False)
    
    action_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    source = Column(String(100), nullable=False)
    
    blocking = Column(Boolean, nullable=False, default=True)
    requires_user = Column(Boolean, nullable=False, default=True)
    requires_approval = Column(Boolean, nullable=False, default=False)
    
    status = Column(String(50), nullable=False, default='pending')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    decision_request = relationship("DecisionRequest", back_populates="required_actions")
