from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.db.base import Base
import enum

class CatalogResourceType(str, enum.Enum):
    agent = "agent"
    agent_team = "agent_team"
    workflow = "workflow"
    work_pack = "work_pack"
    prompt = "prompt"
    tool = "tool"
    connector = "connector"
    model_capability = "model_capability"
    knowledge_service = "knowledge_service"
    document_capability = "document_capability"
    evaluation_capability = "evaluation_capability"
    automation = "automation"
    other = "other"

class CatalogStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    deprecated = "deprecated"
    retired = "retired"

class CatalogVisibility(str, enum.Enum):
    private = "private"
    workspace = "workspace"
    organization = "organization"
    public = "public"

class AvailabilityStatus(str, enum.Enum):
    available = "available"
    limited = "limited"
    unavailable = "unavailable"
    unknown = "unknown"

class EligibilityStatus(str, enum.Enum):
    eligible = "eligible"
    conditionally_eligible = "conditionally_eligible"
    ineligible = "ineligible"
    unknown = "unknown"

class FreshnessStatus(str, enum.Enum):
    fresh = "fresh"
    aging = "aging"
    stale = "stale"
    unknown = "unknown"

class ServiceCatalogItem(Base):
    __tablename__ = "service_catalog_items"
    
    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)

    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    resource_type = Column(Enum(CatalogResourceType), nullable=False)
    resource_id = Column(String(36), nullable=False)

    category = Column(String(100), nullable=False)
    subcategory = Column(String(100), nullable=True)

    status = Column(Enum(CatalogStatus), default=CatalogStatus.draft, nullable=False)
    visibility = Column(Enum(CatalogVisibility), default=CatalogVisibility.workspace, nullable=False)

    owner_type = Column(String(50), nullable=False)
    owner_id = Column(String(36), nullable=False)

    version_reference = Column(String(50), nullable=True)

    capability_summary = Column(JSON, nullable=False, default={})
    
    input_schema = Column(JSON, nullable=True)
    output_schema = Column(JSON, nullable=True)

    requirements = Column(JSON, nullable=False, default={})

    supported_modes = Column(JSON, nullable=False, default=[])
    supported_modalities = Column(JSON, nullable=False, default=[])
    supported_data_classes = Column(JSON, nullable=False, default=[])

    required_permissions = Column(JSON, nullable=False, default=[])
    required_tools = Column(JSON, nullable=False, default=[])
    required_connectors = Column(JSON, nullable=False, default=[])
    required_models = Column(JSON, nullable=False, default=[])

    dependency_summary = Column(JSON, nullable=False, default=[])

    availability_status = Column(Enum(AvailabilityStatus), default=AvailabilityStatus.unknown, nullable=False)
    eligibility_status = Column(Enum(EligibilityStatus), default=EligibilityStatus.unknown, nullable=False)

    quality_evidence_summary = Column(JSON, nullable=False, default={})
    
    sla_reference = Column(JSON, nullable=True)
    documentation_reference = Column(JSON, nullable=True)
    provenance = Column(JSON, nullable=False, default={})

    freshness_status = Column(Enum(FreshnessStatus), default=FreshnessStatus.unknown, nullable=False)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

