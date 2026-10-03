"""
Marketplace Package Management.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.marketplace.exceptions import PackageNotFoundError, MarketplaceException
from backend.app.services.marketplace.models import MarketplacePackage, MarketplaceUsageRecord
from backend.app.services.marketplace.repository import MarketplaceRepository
from backend.app.services.marketplace.schemas import MarketplacePackageCreate, MarketplacePackageUpdate
from backend.app.services.marketplace.evidence import MarketplaceEvidenceLogger
from backend.app.services.marketplace.provenance import PackageProvenanceService


class PackageManagementService:
    """Manages creation, updates, and forking of marketplace packages."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = MarketplaceRepository(session)
        self.evidence_logger = MarketplaceEvidenceLogger(session)
        self.provenance_service = PackageProvenanceService(session)

    async def create_package(
        self,
        organization_id: str,
        data: MarketplacePackageCreate,
        creator_user_id: Optional[str] = None,
    ) -> MarketplacePackage:
        """Creates a new marketplace package in draft status."""
        existing = await self.repo.get_package_by_slug(data.slug, organization_id=organization_id)
        if existing and existing.owner_organization_id == organization_id:
            raise MarketplaceException(f"Package with slug '{data.slug}' already exists in this organization.")

        now = datetime.now(timezone.utc)
        pkg = MarketplacePackage(
            owner_organization_id=organization_id,
            slug=data.slug,
            name=data.name,
            description=data.description,
            category=data.category,
            package_type=data.package_type.value,
            visibility=data.visibility.value,
            status="draft",
            created_by=creator_user_id,
            created_at=now,
            updated_at=now,
        )
        created = await self.repo.create_package(pkg)
        await self.evidence_logger.record_evidence(
            organization_id=organization_id,
            action="created",
            package_id=created.id,
            version="0.0.0",
            actor_id=creator_user_id,
            details={"name": data.name, "slug": data.slug},
        )
        return created

    async def update_package(
        self,
        package_id: str,
        data: MarketplacePackageUpdate,
        actor_id: Optional[str] = None,
    ) -> MarketplacePackage:
        """Updates package metadata."""
        pkg = await self.repo.get_package_by_id(package_id)
        if not pkg:
            raise PackageNotFoundError(package_id)

        if data.name is not None:
            pkg.name = data.name
        if data.description is not None:
            pkg.description = data.description
        if data.category is not None:
            pkg.category = data.category
        if data.visibility is not None:
            pkg.visibility = data.visibility.value
        if data.status is not None:
            pkg.status = data.status.value

        updated = await self.repo.update_package(pkg)
        return updated

    async def fork_package(
        self,
        source_package_id: str,
        target_organization_id: str,
        new_slug: str,
        new_name: str,
        description: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> MarketplacePackage:
        """
        Forks an authorized package into a target organization.
        Creates clean ownership, preserves lineage in provenance, and never copies credentials.
        """
        source_pkg = await self.repo.get_package_by_id(source_package_id)
        if not source_pkg:
            raise PackageNotFoundError(source_package_id)

        now = datetime.now(timezone.utc)
        forked = MarketplacePackage(
            owner_organization_id=target_organization_id,
            slug=new_slug,
            name=new_name,
            description=description or source_pkg.description,
            category=source_pkg.category,
            package_type=source_pkg.package_type,
            visibility="private",  # Forked packages start private
            status="draft",
            created_by=actor_id,
            created_at=now,
            updated_at=now,
        )
        created = await self.repo.create_package(forked)

        await self.evidence_logger.record_evidence(
            organization_id=target_organization_id,
            action="forked",
            package_id=created.id,
            version="0.0.0",
            actor_id=actor_id,
            details={"source_package_id": source_package_id, "source_slug": source_pkg.slug},
        )
        await self.repo.record_usage(
            MarketplaceUsageRecord(
                package_id=source_package_id,
                package_version_id=source_pkg.current_version_id or "unknown",
                organization_id=target_organization_id,
                operation="fork",
                status="success",
            )
        )

        return created
