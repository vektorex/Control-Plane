from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, JSON, Integer, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum

class KnowledgeStatus(str, enum.Enum):
    candidate = "candidate"
    under_review = "under_review"
    verified = "verified"
    disputed = "disputed"
    deprecated = "deprecated"
    archived = "archived"

class KnowledgeConfidence(str, enum.Enum):
    unverified = "unverified"
    supported = "supported"
    strongly_supported = "strongly_supported"
    verified = "verified"
    disputed = "disputed"
    deprecated = "deprecated"

class OrganizationalKnowledgeItem(Base):
    __tablename__ = "organizational_knowledge_items"
    
    id = Column(String(36), primary_key=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    knowledge_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Enum(KnowledgeStatus), default=KnowledgeStatus.candidate, nullable=False)
    confidence_state = Column(Enum(KnowledgeConfidence), default=KnowledgeConfidence.unverified, nullable=False)
    sensitivity = Column(String(50), default="internal", nullable=False)
    owner_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    provenances = relationship("KnowledgeProvenance", back_populates="knowledge_item", cascade="all, delete-orphan")
    evidences = relationship("KnowledgeEvidence", back_populates="knowledge_item", cascade="all, delete-orphan")
    versions = relationship("KnowledgeVersion", back_populates="knowledge_item", cascade="all, delete-orphan")

class KnowledgeProvenance(Base):
    __tablename__ = "knowledge_provenance"
    
    id = Column(String(36), primary_key=True)
    knowledge_item_id = Column(String(36), ForeignKey("organizational_knowledge_items.id"), nullable=False)
    source_type = Column(String(50), nullable=False)
    source_id = Column(String(36), nullable=False)
    source_version_id = Column(String(36), nullable=True)
    evidence_ids = Column(JSON, nullable=False, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    knowledge_item = relationship("OrganizationalKnowledgeItem", back_populates="provenances")

class KnowledgeEvidence(Base):
    __tablename__ = "knowledge_evidence"
    
    id = Column(String(36), primary_key=True)
    knowledge_item_id = Column(String(36), ForeignKey("organizational_knowledge_items.id"), nullable=False)
    source_type = Column(String(50), nullable=False)
    source_id = Column(String(36), nullable=False)
    evidence_type = Column(String(50), nullable=False)
    excerpt_or_reference = Column(Text, nullable=False)
    snapshot = Column(JSON, nullable=True)
    status = Column(String(50), default="unreviewed", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    knowledge_item = relationship("OrganizationalKnowledgeItem", back_populates="evidences")

class KnowledgeVersion(Base):
    __tablename__ = "knowledge_versions"
    
    id = Column(String(36), primary_key=True)
    knowledge_item_id = Column(String(36), ForeignKey("organizational_knowledge_items.id"), nullable=False)
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    classification = Column(String(50), nullable=False)
    scope = Column(String(50), nullable=False)
    provenance_snapshot = Column(JSON, nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    knowledge_item = relationship("OrganizationalKnowledgeItem", back_populates="versions")

class KnowledgeCandidate(Base):
    __tablename__ = "knowledge_candidates"
    
    id = Column(String(36), primary_key=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    source_type = Column(String(50), nullable=False)
    source_id = Column(String(36), nullable=False)
    candidate_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    evidence_ids = Column(JSON, nullable=False, default=[])
    generated_by = Column(String(255), nullable=False)
    status = Column(String(50), default="draft", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class KnowledgeConflict(Base):
    __tablename__ = "knowledge_conflicts"
    
    id = Column(String(36), primary_key=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    knowledge_item_a_id = Column(String(36), ForeignKey("organizational_knowledge_items.id"), nullable=False)
    knowledge_item_b_id = Column(String(36), ForeignKey("organizational_knowledge_items.id"), nullable=False)
    conflict_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    evidence_ids = Column(JSON, nullable=False, default=[])
    status = Column(String(50), default="open", nullable=False)
    resolution = Column(Text, nullable=True)
    resolved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
