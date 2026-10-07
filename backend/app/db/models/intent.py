from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, JSON, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum

class IntentStatus(str, enum.Enum):
    received = "received"
    analyzing = "analyzing"
    requirements_ready = "requirements_ready"
    discovering = "discovering"
    composing = "composing"
    validating = "validating"
    simulation_ready = "simulation_ready"
    review_required = "review_required"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"

class IntentComplexity(str, enum.Enum):
    simple = "simple"
    moderate = "moderate"
    complex = "complex"
    unknown = "unknown"

class CandidateStatus(str, enum.Enum):
    draft = "draft"
    validation_required = "validation_required"
    simulation_required = "simulation_required"
    review_required = "review_required"
    accepted = "accepted"
    rejected = "rejected"
    converted = "converted"

class IntentRequest(Base):
    __tablename__ = "intent_requests"
    
    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)

    submitted_by = Column(String(36), nullable=False)

    raw_intent = Column(Text, nullable=False)
    normalized_intent = Column(Text, nullable=True)

    status = Column(Enum(IntentStatus), default=IntentStatus.received, nullable=False)
    complexity = Column(Enum(IntentComplexity), default=IntentComplexity.unknown, nullable=False)
    confidence = Column(Float, nullable=True)

    analysis = Column(JSON, nullable=False, default={})
    constraints = Column(JSON, nullable=False, default={})

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    requirements = relationship("IntentRequirement", back_populates="intent_request", cascade="all, delete-orphan")
    clarifications = relationship("IntentClarification", back_populates="intent_request", cascade="all, delete-orphan")
    candidates = relationship("CandidateSolution", back_populates="intent_request", cascade="all, delete-orphan")

class IntentRequirement(Base):
    __tablename__ = "intent_requirements"
    
    id = Column(String(36), primary_key=True)
    intent_request_id = Column(String(36), ForeignKey("intent_requests.id"), nullable=False)
    
    req_type = Column("type", String(50), nullable=False)
    description = Column(Text, nullable=False)
    value = Column(JSON, nullable=True)
    source = Column(String(50), nullable=False) # user, policy, catalog, system, inferred
    mandatory = Column(Boolean, default=True, nullable=False)
    confidence = Column(Float, nullable=True)
    status = Column(String(50), default="active", nullable=False)
    
    intent_request = relationship("IntentRequest", back_populates="requirements")

class IntentClarification(Base):
    __tablename__ = "intent_clarifications"
    
    id = Column(String(36), primary_key=True)
    intent_request_id = Column(String(36), ForeignKey("intent_requests.id"), nullable=False)
    
    question = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    options = Column(JSON, nullable=False, default=[])
    required = Column(Boolean, default=True, nullable=False)
    
    answer = Column(Text, nullable=True)
    answered_by = Column(String(36), nullable=True)
    answered_at = Column(DateTime(timezone=True), nullable=True)

    intent_request = relationship("IntentRequest", back_populates="clarifications")

class CapabilityMatch(Base):
    __tablename__ = "intent_capability_matches"
    
    id = Column(String(36), primary_key=True)
    intent_request_id = Column(String(36), ForeignKey("intent_requests.id"), nullable=False)
    catalog_item_id = Column(String(36), nullable=False)
    
    requirement_ids = Column(JSON, nullable=False, default=[])
    compatibility = Column(String(50), nullable=False) # compatible, conditionally_compatible, incompatible, unknown
    eligibility = Column(String(50), nullable=False)
    availability = Column(String(50), nullable=False)
    
    matched_capabilities = Column(JSON, nullable=False, default=[])
    missing_requirements = Column(JSON, nullable=False, default=[])
    incompatibilities = Column(JSON, nullable=False, default=[])
    evidence = Column(JSON, nullable=False, default={})

class CandidateSolution(Base):
    __tablename__ = "candidate_solutions"
    
    id = Column(String(36), primary_key=True)
    intent_request_id = Column(String(36), ForeignKey("intent_requests.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    objective = Column(Text, nullable=False)
    
    source = Column(String(50), nullable=False) # generated, template, user_composed
    status = Column(Enum(CandidateStatus), default=CandidateStatus.draft, nullable=False)
    
    solution_blueprint = Column(JSON, nullable=False, default={})
    requirements = Column(JSON, nullable=False, default={})
    assumptions = Column(JSON, nullable=False, default={})
    
    validation_summary = Column(JSON, nullable=False, default={})
    simulation_summary = Column(JSON, nullable=False, default={})
    provenance = Column(JSON, nullable=False, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    intent_request = relationship("IntentRequest", back_populates="candidates")

class CandidateSolutionEvidence(Base):
    __tablename__ = "candidate_solution_evidence"
    
    id = Column(String(36), primary_key=True)
    candidate_id = Column(String(36), ForeignKey("candidate_solutions.id"), nullable=False)
    
    evidence_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    data = Column(JSON, nullable=False, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
