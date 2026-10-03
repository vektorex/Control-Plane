"""
Marketplace Pydantic Schemas.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class PackageType(str, Enum):
    WORKFLOW = "workflow"
    PROMPT = "prompt"
    EVALUATION = "evaluation"
    TOOL = "tool"
    CONNECTOR_TEMPLATE = "connector_template"
    TASK_TEMPLATE = "task_template"
    WORK_PACK = "work_pack"
    AGENT_TEMPLATE = "agent_template"
    AGENT_TEAM_TEMPLATE = "agent_team_template"


class PackageVisibility(str, Enum):
    PRIVATE = "private"
    ORGANIZATION = "organization"
    UNLISTED = "unlisted"
    PUBLIC = "public"


class PackageStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    SUSPENDED = "suspended"
    DEPRECATED = "deprecated"
    REVOKED = "revoked"


class SecurityStatus(str, Enum):
    NOT_SCANNED = "not_scanned"
    SCANNED = "scanned"
    WARNING = "warning"
    BLOCKED = "blocked"
    REVOKED = "revoked"


class InstallationStatus(str, Enum):
    PENDING = "pending"
    INSTALLED = "installed"
    SUSPENDED = "suspended"
    UPDATE_AVAILABLE = "update_available"
    UNINSTALLED = "uninstalled"
    BLOCKED = "blocked"


class DependencyType(str, Enum):
    PACKAGE = "package"
    WORKFLOW = "workflow"
    PROMPT = "prompt"
    TOOL = "tool"
    CONNECTOR = "connector"
    MODEL_CAPABILITY = "model_capability"
    PLATFORM_CAPABILITY = "platform_capability"


# ----------------------------------------------------
# Manifest Schemas
# ----------------------------------------------------

class ManifestComponent(BaseModel):
    id: str = Field(..., description="Unique component identifier inside package")
    name: str = Field(..., max_length=255)
    type: str = Field(..., description="workflow, prompt, evaluation_dataset, tool_definition, etc.")
    description: Optional[str] = None
    version: Optional[str] = None
    definition: Dict[str, Any] = Field(default_factory=dict, description="Component structure/configuration")


class ManifestPermission(BaseModel):
    scope: str = Field(..., description="Target scope e.g. workflow, task, document")
    permissions: List[str] = Field(default_factory=list, description="Requested permissions e.g. tasks:read, documents:read")


class ManifestDependency(BaseModel):
    type: DependencyType
    identifier: str = Field(..., description="Package slug or capability identifier")
    version_constraint: str = Field(default="*", description="SemVer range e.g. ^1.0.0, >=2.1.0")
    optional: bool = False


class ManifestVariable(BaseModel):
    type: str = Field(..., description="string, integer, number, boolean, enum, object")
    description: Optional[str] = None
    default: Optional[Any] = None
    enum_values: Optional[List[Any]] = None
    required: bool = False


class PackageManifest(BaseModel):
    schema_version: str = Field(default="1.0", description="Manifest schema version")
    package: Dict[str, Any] = Field(..., description="Package identity (name, version, type)")
    compatibility: Dict[str, Any] = Field(default_factory=dict, description="Platform version and required model capabilities")
    components: List[ManifestComponent] = Field(default_factory=list)
    permissions: List[ManifestPermission] = Field(default_factory=list)
    dependencies: List[ManifestDependency] = Field(default_factory=list)
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Declared variables configuration")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Input payload schema")
    outputs: Dict[str, Any] = Field(default_factory=dict, description="Output payload schema")


# ----------------------------------------------------
# Package Schemas
# ----------------------------------------------------

class MarketplacePackageCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: Optional[str] = None
    category: str = Field(..., max_length=50)
    package_type: PackageType
    visibility: PackageVisibility = PackageVisibility.PRIVATE
    tags: List[str] = Field(default_factory=list)


class MarketplacePackageUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    visibility: Optional[PackageVisibility] = None
    status: Optional[PackageStatus] = None
    tags: Optional[List[str]] = None


class MarketplacePackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_organization_id: str
    slug: str
    name: str
    description: Optional[str] = None
    category: str
    package_type: PackageType
    visibility: PackageVisibility
    status: PackageStatus
    current_version_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    latest_version: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class MarketplacePackageVersionCreate(BaseModel):
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
    manifest: PackageManifest
    source_type: Optional[str] = "native"
    source_reference: Optional[str] = None
    parent_version_id: Optional[str] = None


class MarketplacePackageVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    package_id: str
    version: str
    manifest: Dict[str, Any]
    content_hash: str
    manifest_hash: str
    compatibility: Optional[Dict[str, Any]] = None
    security_status: SecurityStatus
    validation_status: str
    publication_status: str
    created_by: Optional[str] = None
    created_at: datetime
    published_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None


class MarketplacePackageDetailResponse(MarketplacePackageResponse):
    versions: List[MarketplacePackageVersionResponse] = Field(default_factory=list)
    average_rating: Optional[float] = None
    total_reviews: int = 0
    total_installations: int = 0


# ----------------------------------------------------
# Installation Schemas
# ----------------------------------------------------

class PackageInstallationCreate(BaseModel):
    package_id: str
    package_version_id: Optional[str] = None  # If omitted, installs latest published version
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)


class PackageInstallationUpdate(BaseModel):
    configuration: Optional[Dict[str, Any]] = None
    status: Optional[InstallationStatus] = None


class PackageInstallationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    package_id: str
    package_version_id: str
    organization_id: str
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    installed_by: Optional[str] = None
    status: InstallationStatus
    configuration: Dict[str, Any]
    installed_at: datetime
    updated_at: datetime
    uninstalled_at: Optional[datetime] = None
    package_name: Optional[str] = None
    package_slug: Optional[str] = None
    installed_version: Optional[str] = None
    latest_available_version: Optional[str] = None


# ----------------------------------------------------
# Review Schemas
# ----------------------------------------------------

class MarketplaceReviewCreate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5, description="Factual user rating 1 to 5")
    review: Optional[str] = Field(None, max_length=2000)


class MarketplaceReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    package_id: str
    package_version_id: Optional[str] = None
    organization_id: str
    user_id: str
    rating: Optional[int] = None
    review: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


# ----------------------------------------------------
# Approval & Governance Schemas
# ----------------------------------------------------

class PackageApprovalReviewRequest(BaseModel):
    approved: bool
    notes: Optional[str] = None


class PackageApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    package_id: str
    package_version_id: Optional[str] = None
    organization_id: str
    action_type: str
    status: str
    requested_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None


# ----------------------------------------------------
# Telemetry & Search Schemas
# ----------------------------------------------------

class PackageUsageResponse(BaseModel):
    package_id: str
    total_installations: int
    active_installations: int
    total_runs: int
    total_updates: int
    total_uninstalls: int
    version_distribution: Dict[str, int] = Field(default_factory=dict)


class PackageForkRequest(BaseModel):
    new_slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    new_name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    target_organization_id: Optional[str] = None


class MarketplaceSearchQuery(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    package_type: Optional[PackageType] = None
    visibility: Optional[PackageVisibility] = None
    status: Optional[PackageStatus] = None
    required_capability: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
