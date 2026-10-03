"""
Marketplace Database Models.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from backend.app.db.base import Base


class MarketplacePackage(Base):
    """Represents a reusable AI Work Layer package entity belonging to an organization."""

    __tablename__ = "marketplace_packages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_organization_id = Column(String(36), nullable=False, index=True)
    slug = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, index=True)
    package_type = Column(String(50), nullable=False, index=True)  # workflow, prompt, evaluation, tool, connector_template, task_template, work_pack
    visibility = Column(String(50), nullable=False, default="private", index=True)  # private, organization, unlisted, public
    status = Column(String(50), nullable=False, default="draft", index=True)  # draft, review, published, suspended, deprecated, revoked
    current_version_id = Column(String(36), nullable=True)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("owner_organization_id", "slug", name="uq_marketplace_org_slug"),
        Index("ix_marketplace_packages_owner_status", "owner_organization_id", "status"),
        Index("ix_marketplace_packages_vis_status", "visibility", "status"),
    )

    # Relationships
    versions = relationship("MarketplacePackageVersion", back_populates="package", cascade="all, delete-orphan", foreign_keys="MarketplacePackageVersion.package_id")
    installations = relationship("PackageInstallation", back_populates="package", cascade="all, delete-orphan")
    reviews = relationship("MarketplaceReview", back_populates="package", cascade="all, delete-orphan")


class MarketplacePackageVersion(Base):
    """Immutable version of a marketplace package containing verified manifest and content hashes."""

    __tablename__ = "marketplace_package_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    package_id = Column(String(36), ForeignKey("marketplace_packages.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(String(50), nullable=False)  # SemVer (e.g. 1.0.0)
    manifest = Column(JSON, nullable=False)  # Strict JSON manifest of components, inputs, outputs, etc.
    content_hash = Column(String(64), nullable=False)  # Deterministic SHA-256 hash of all components
    manifest_hash = Column(String(64), nullable=False)  # Deterministic SHA-256 hash of manifest JSON
    compatibility = Column(JSON, nullable=True)  # Platform min/max versions, required capabilities
    security_status = Column(String(50), nullable=False, default="not_scanned", index=True)  # not_scanned, scanned, warning, blocked, revoked
    validation_status = Column(String(50), nullable=False, default="pending", index=True)  # pending, valid, invalid
    publication_status = Column(String(50), nullable=False, default="draft", index=True)  # draft, review, published, deprecated, revoked
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    published_at = Column(DateTime, nullable=True)
    deprecated_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("package_id", "version", name="uq_package_version"),
        Index("ix_package_versions_pkg_sec", "package_id", "security_status"),
    )

    # Relationships
    package = relationship("MarketplacePackage", back_populates="versions", foreign_keys=[package_id])
    dependencies = relationship("MarketplaceDependency", back_populates="package_version", cascade="all, delete-orphan")
    provenance = relationship("PackageProvenance", back_populates="package_version", uselist=False, cascade="all, delete-orphan")


class MarketplaceDependency(Base):
    """Declares explicit platform or package dependencies for a package version."""

    __tablename__ = "marketplace_dependencies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    package_version_id = Column(String(36), ForeignKey("marketplace_package_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    dependency_type = Column(String(50), nullable=False)  # package, workflow, prompt, tool, connector, model_capability, platform_capability
    dependency_identifier = Column(String(255), nullable=False)
    version_constraint = Column(String(100), nullable=False, default="*")
    optional = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    package_version = relationship("MarketplacePackageVersion", back_populates="dependencies")


class PackageInstallation(Base):
    """Tenant-scoped installation record of a marketplace package into a workspace or project."""

    __tablename__ = "marketplace_installations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    package_id = Column(String(36), ForeignKey("marketplace_packages.id", ondelete="CASCADE"), nullable=False, index=True)
    package_version_id = Column(String(36), ForeignKey("marketplace_package_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=True, index=True)
    project_id = Column(String(36), nullable=True, index=True)
    installed_by = Column(String(36), nullable=True)
    status = Column(String(50), nullable=False, default="installed", index=True)  # pending, installed, suspended, update_available, uninstalled, blocked
    configuration = Column(JSON, nullable=False, default=dict)
    installed_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    uninstalled_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_installations_org_status", "organization_id", "status"),
        Index("ix_installations_pkg_scope", "package_id", "organization_id", "workspace_id"),
    )

    package = relationship("MarketplacePackage", back_populates="installations")
    package_version = relationship("MarketplacePackageVersion")


class MarketplaceReview(Base):
    """User-submitted factual review and optional 1-5 rating."""

    __tablename__ = "marketplace_reviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    package_id = Column(String(36), ForeignKey("marketplace_packages.id", ondelete="CASCADE"), nullable=False, index=True)
    package_version_id = Column(String(36), nullable=True)
    organization_id = Column(String(36), nullable=False)
    user_id = Column(String(36), nullable=False)
    rating = Column(Integer, nullable=True)  # 1 to 5
    review = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="published", index=True)  # published, pending_moderation, flagged, hidden
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("package_id", "organization_id", "user_id", name="uq_package_user_review"),
    )

    package = relationship("MarketplacePackage", back_populates="reviews")


class MarketplaceUsageRecord(Base):
    """Telemetry record tracking lifecycle events and operations on marketplace packages."""

    __tablename__ = "marketplace_usage_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    package_id = Column(String(36), nullable=False, index=True)
    package_version_id = Column(String(36), nullable=False)
    organization_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=True)
    installation_id = Column(String(36), nullable=True, index=True)
    run_id = Column(String(36), nullable=True)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    operation = Column(String(50), nullable=False)  # install, run, update, uninstall, fork
    status = Column(String(50), nullable=False, default="success")


class PackageProvenance(Base):
    """Records verifiable origin, creator identity, and lineage of a package version."""

    __tablename__ = "marketplace_provenance"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    package_version_id = Column(String(36), ForeignKey("marketplace_package_versions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    source_type = Column(String(50), nullable=False, default="native")  # native, imported, forked, derived
    source_reference = Column(String(500), nullable=True)
    creator_organization_id = Column(String(36), nullable=False)
    creator_user_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    content_hash = Column(String(64), nullable=False)
    parent_version_id = Column(String(36), nullable=True)

    package_version = relationship("MarketplacePackageVersion", back_populates="provenance")


class MarketplaceTag(Base):
    """Search and discovery tags for marketplace packages."""

    __tablename__ = "marketplace_tags"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class MarketplacePackageTag(Base):
    """Association between packages and tags."""

    __tablename__ = "marketplace_package_tags"

    package_id = Column(String(36), ForeignKey("marketplace_packages.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(String(36), ForeignKey("marketplace_tags.id", ondelete="CASCADE"), primary_key=True)


class MarketplaceApproval(Base):
    """Human-in-the-loop and governance approval request for sensitive marketplace actions."""

    __tablename__ = "marketplace_approvals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    package_id = Column(String(36), ForeignKey("marketplace_packages.id", ondelete="CASCADE"), nullable=False, index=True)
    package_version_id = Column(String(36), nullable=True)
    organization_id = Column(String(36), nullable=False, index=True)
    action_type = Column(String(50), nullable=False)  # publish_public, install_sensitive, update_high_risk
    status = Column(String(50), nullable=False, default="pending", index=True)  # pending, approved, rejected, revoked
    requested_by = Column(String(36), nullable=True)
    reviewed_by = Column(String(36), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    reviewed_at = Column(DateTime, nullable=True)
