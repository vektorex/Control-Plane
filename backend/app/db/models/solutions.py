from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.db.base import Base
import enum

class SolutionStatus(str, enum.Enum):
    draft = "draft"
    review_required = "review_required"
    approved = "approved"
    published = "published"
    deprecated = "deprecated"
    retired = "retired"

class SolutionVisibility(str, enum.Enum):
    private = "private"
    workspace = "workspace"
    organization = "organization"
    public = "public"

class Solution(Base):
    __tablename__ = "solutions"
    
    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)

    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    objective = Column(Text, nullable=True)

    status = Column(Enum(SolutionStatus), default=SolutionStatus.draft, nullable=False)
    visibility = Column(Enum(SolutionVisibility), default=SolutionVisibility.workspace, nullable=False)

    owner_type = Column(String(50), nullable=False)
    owner_id = Column(String(36), nullable=False)

    current_version_id = Column(String(36), ForeignKey("solution_versions.id", use_alter=True), nullable=True)

    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    versions = relationship("SolutionVersion", back_populates="solution", foreign_keys="[SolutionVersion.solution_id]")

class SolutionVersion(Base):
    __tablename__ = "solution_versions"

    id = Column(String(36), primary_key=True)
    solution_id = Column(String(36), ForeignKey("solutions.id"), nullable=False)
    version = Column(String(50), nullable=False)
    status = Column(Enum(SolutionStatus), default=SolutionStatus.draft, nullable=False)

    objective = Column(Text, nullable=True)
    inputs_schema = Column(JSON, nullable=True)
    outputs_schema = Column(JSON, nullable=True)

    constraints = Column(JSON, nullable=False, default={})
    requirements = Column(JSON, nullable=False, default={})

    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    published_at = Column(DateTime(timezone=True), nullable=True)
    deprecated_at = Column(DateTime(timezone=True), nullable=True)
    
    is_immutable = Column(Boolean, default=False, nullable=False)

    solution = relationship("Solution", back_populates="versions", foreign_keys=[solution_id])
    components = relationship("SolutionComponent", back_populates="solution_version", cascade="all, delete-orphan")
    connections = relationship("SolutionConnection", back_populates="solution_version", cascade="all, delete-orphan")
    inputs = relationship("SolutionInput", back_populates="solution_version", cascade="all, delete-orphan")
    outputs = relationship("SolutionOutput", back_populates="solution_version", cascade="all, delete-orphan")
    reqs = relationship("SolutionRequirement", back_populates="solution_version", cascade="all, delete-orphan")

class SolutionComponent(Base):
    __tablename__ = "solution_components"
    
    id = Column(String(36), primary_key=True)
    solution_version_id = Column(String(36), ForeignKey("solution_versions.id"), nullable=False)
    
    catalog_item_id = Column(String(36), nullable=False) # Refers to ServiceCatalogItem
    
    component_key = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=False)
    
    component_type = Column(String(50), nullable=False)
    
    configuration = Column(JSON, nullable=False, default={})
    position = Column(JSON, nullable=False, default={"x": 0, "y": 0})
    
    input_mapping = Column(JSON, nullable=False, default={})
    output_mapping = Column(JSON, nullable=False, default={})
    
    required = Column(Boolean, default=True, nullable=False)
    optional = Column(Boolean, default=False, nullable=False)
    
    condition = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    solution_version = relationship("SolutionVersion", back_populates="components")

class SolutionConnection(Base):
    __tablename__ = "solution_connections"
    
    id = Column(String(36), primary_key=True)
    solution_version_id = Column(String(36), ForeignKey("solution_versions.id"), nullable=False)
    
    source_component_id = Column(String(36), ForeignKey("solution_components.id"), nullable=False)
    source_port = Column(String(100), nullable=False)
    
    target_component_id = Column(String(36), ForeignKey("solution_components.id"), nullable=False)
    target_port = Column(String(100), nullable=False)
    
    mapping = Column(JSON, nullable=False, default={})
    condition = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    solution_version = relationship("SolutionVersion", back_populates="connections")

class SolutionInput(Base):
    __tablename__ = "solution_inputs"
    
    id = Column(String(36), primary_key=True)
    solution_version_id = Column(String(36), ForeignKey("solution_versions.id"), nullable=False)
    
    key = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    data_type = Column(String(50), nullable=False)
    schema_def = Column("schema", JSON, nullable=True)
    
    required = Column(Boolean, default=True, nullable=False)
    default_value = Column(JSON, nullable=True)
    sensitivity = Column(String(50), nullable=False, default="public")
    validation_rules = Column(JSON, nullable=False, default={})

    solution_version = relationship("SolutionVersion", back_populates="inputs")

class SolutionOutput(Base):
    __tablename__ = "solution_outputs"
    
    id = Column(String(36), primary_key=True)
    solution_version_id = Column(String(36), ForeignKey("solution_versions.id"), nullable=False)
    
    key = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    data_type = Column(String(50), nullable=False)
    schema_def = Column("schema", JSON, nullable=True)
    
    required = Column(Boolean, default=True, nullable=False)
    evidence_required = Column(Boolean, default=False, nullable=False)
    acceptance_criteria = Column(JSON, nullable=False, default=[])

    solution_version = relationship("SolutionVersion", back_populates="outputs")

class SolutionRequirement(Base):
    __tablename__ = "solution_requirements"
    
    id = Column(String(36), primary_key=True)
    solution_version_id = Column(String(36), ForeignKey("solution_versions.id"), nullable=False)
    
    requirement_type = Column(String(50), nullable=False)
    value = Column(JSON, nullable=False)
    source = Column(String(100), nullable=False)
    required = Column(Boolean, default=True, nullable=False)
    reason = Column(Text, nullable=True)

    solution_version = relationship("SolutionVersion", back_populates="reqs")
