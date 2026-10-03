"""
Marketplace Package Version Management.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.marketplace.exceptions import (
    PackageNotFoundError,
    PackageVersionNotFoundError,
    MarketplaceException,
)
from backend.app.services.marketplace.models import (
    MarketplacePackage,
    MarketplacePackageVersion,
    MarketplaceDependency,
)
from backend.app.services.marketplace.repository import MarketplaceRepository
from backend.app.services.marketplace.schemas import MarketplacePackageVersionCreate
from backend.app.services.marketplace.validator import PackageValidator
from backend.app.services.marketplace.builder import MarketplacePackageBuilder


class PackageVersionService:
    """Manages immutable package versions, SemVer validation, and dependencies."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = MarketplaceRepository(session)

    async def create_version(
        self,
        package_id: str,
        data: MarketplacePackageVersionCreate,
        creator_user_id: Optional[str] = None,
    ) -> MarketplacePackageVersion:
        """
        Creates a new draft version for a package.
        Validates SemVer, validates manifest, and computes hashes.
        """
        pkg = await self.repo.get_package_by_id(package_id)
        if not pkg:
            raise PackageNotFoundError(package_id)

        PackageValidator.validate_version(data.version)

        # Check existing version
        existing = await self.repo.get_version_by_number(package_id, data.version)
        if existing:
            raise MarketplaceException(f"Version '{data.version}' already exists for package '{package_id}'.")

        manifest_dict = data.manifest.model_dump()
        PackageValidator.validate_manifest(manifest_dict)

        content_hash = MarketplacePackageBuilder.compute_content_hash(manifest_dict.get("components", []))
        manifest_hash = MarketplacePackageBuilder.compute_manifest_hash(manifest_dict)

        now = datetime.now(timezone.utc)
        ver = MarketplacePackageVersion(
            package_id=package_id,
            version=data.version,
            manifest=manifest_dict,
            content_hash=content_hash,
            manifest_hash=manifest_hash,
            compatibility=manifest_dict.get("compatibility"),
            security_status="not_scanned",
            validation_status="valid",
            publication_status="draft",
            created_by=creator_user_id,
            created_at=now,
        )
        created_ver = await self.repo.create_version(ver)

        # Store dependencies
        for dep in manifest_dict.get("dependencies", []):
            d_type = dep.get("type", "package")
            d_type_val = d_type.value if hasattr(d_type, "value") else str(d_type)
            dep_record = MarketplaceDependency(
                package_version_id=created_ver.id,
                dependency_type=d_type_val,
                dependency_identifier=dep.get("identifier"),
                version_constraint=dep.get("version_constraint", "*"),
                optional=dep.get("optional", False),
                created_at=now,
            )
            self.session.add(dep_record)
        await self.session.commit()

        return created_ver

    async def deprecate_version(self, package_id: str, version_id: str) -> MarketplacePackageVersion:
        """Marks a version as deprecated without deleting historical references."""
        ver = await self.repo.get_version_by_id(version_id)
        if not ver or ver.package_id != package_id:
            raise PackageVersionNotFoundError(package_id, version_id)

        ver.publication_status = "deprecated"
        ver.deprecated_at = datetime.now(timezone.utc)
        return await self.repo.update_version(ver)

    async def revoke_version(self, package_id: str, version_id: str, reason: str = "") -> MarketplacePackageVersion:
        """Revokes a published version for security or policy violation."""
        ver = await self.repo.get_version_by_id(version_id)
        if not ver or ver.package_id != package_id:
            raise PackageVersionNotFoundError(package_id, version_id)

        ver.publication_status = "revoked"
        ver.security_status = "revoked"
        return await self.repo.update_version(ver)
