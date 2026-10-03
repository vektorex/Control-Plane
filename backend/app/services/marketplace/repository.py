"""
Marketplace Repository Layer.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, or_, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.services.marketplace.models import (
    MarketplacePackage,
    MarketplacePackageVersion,
    MarketplaceDependency,
    PackageInstallation,
    MarketplaceReview,
    MarketplaceUsageRecord,
    PackageProvenance,
    MarketplaceTag,
    MarketplacePackageTag,
    MarketplaceApproval,
)


class MarketplaceRepository:
    """Database interactions for marketplace packages, versions, installations, and reviews."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ----------------------------------------------------
    # Package Operations
    # ----------------------------------------------------

    async def get_package_by_id(self, package_id: str) -> Optional[MarketplacePackage]:
        query = select(MarketplacePackage).where(MarketplacePackage.id == package_id).options(
            selectinload(MarketplacePackage.versions),
            selectinload(MarketplacePackage.installations),
            selectinload(MarketplacePackage.reviews),
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_package_by_slug(self, slug: str, organization_id: Optional[str] = None) -> Optional[MarketplacePackage]:
        conditions = [MarketplacePackage.slug == slug]
        if organization_id:
            conditions.append(
                or_(
                    MarketplacePackage.owner_organization_id == organization_id,
                    MarketplacePackage.visibility.in_(["public", "unlisted"]),
                )
            )
        else:
            conditions.append(MarketplacePackage.visibility == "public")

        query = select(MarketplacePackage).where(and_(*conditions)).options(
            selectinload(MarketplacePackage.versions),
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_packages(
        self,
        organization_id: Optional[str] = None,
        category: Optional[str] = None,
        package_type: Optional[str] = None,
        visibility: Optional[str] = None,
        status: Optional[str] = None,
        search_query: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[MarketplacePackage], int]:
        conditions = []

        # Visibility filter
        if organization_id:
            conditions.append(
                or_(
                    MarketplacePackage.owner_organization_id == organization_id,
                    MarketplacePackage.visibility.in_(["public", "unlisted", "organization"]),
                )
            )
        else:
            conditions.append(MarketplacePackage.visibility == "public")

        if category:
            conditions.append(MarketplacePackage.category == category)
        if package_type:
            conditions.append(MarketplacePackage.package_type == package_type)
        if visibility:
            conditions.append(MarketplacePackage.visibility == visibility)
        if status:
            conditions.append(MarketplacePackage.status == status)

        # Search query matching name, slug, description
        if search_query:
            term = f"%{search_query.strip()}%"
            conditions.append(
                or_(
                    MarketplacePackage.name.ilike(term),
                    MarketplacePackage.slug.ilike(term),
                    MarketplacePackage.description.ilike(term),
                )
            )

        query = select(MarketplacePackage).where(and_(*conditions)).order_by(MarketplacePackage.created_at.desc())
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_res = await self.session.execute(count_query)
        total = count_res.scalar_one()

        paginated = query.limit(limit).offset(offset).options(
            selectinload(MarketplacePackage.versions)
        )
        result = await self.session.execute(paginated)
        return list(result.scalars().all()), total

    async def create_package(self, package: MarketplacePackage) -> MarketplacePackage:
        self.session.add(package)
        await self.session.commit()
        await self.session.refresh(package)
        return package

    async def update_package(self, package: MarketplacePackage) -> MarketplacePackage:
        package.updated_at = datetime.now(timezone.utc)
        self.session.add(package)
        await self.session.commit()
        await self.session.refresh(package)
        return package

    # ----------------------------------------------------
    # Version Operations
    # ----------------------------------------------------

    async def get_version_by_id(self, version_id: str) -> Optional[MarketplacePackageVersion]:
        query = select(MarketplacePackageVersion).where(MarketplacePackageVersion.id == version_id).options(
            selectinload(MarketplacePackageVersion.dependencies),
            selectinload(MarketplacePackageVersion.provenance),
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_version_by_number(self, package_id: str, version: str) -> Optional[MarketplacePackageVersion]:
        query = select(MarketplacePackageVersion).where(
            MarketplacePackageVersion.package_id == package_id,
            MarketplacePackageVersion.version == version,
        ).options(
            selectinload(MarketplacePackageVersion.dependencies),
            selectinload(MarketplacePackageVersion.provenance),
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def create_version(self, version: MarketplacePackageVersion) -> MarketplacePackageVersion:
        self.session.add(version)
        await self.session.commit()
        await self.session.refresh(version)
        return version

    async def update_version(self, version: MarketplacePackageVersion) -> MarketplacePackageVersion:
        self.session.add(version)
        await self.session.commit()
        await self.session.refresh(version)
        return version

    # ----------------------------------------------------
    # Installation Operations
    # ----------------------------------------------------

    async def get_installation_by_id(self, installation_id: str) -> Optional[PackageInstallation]:
        query = select(PackageInstallation).where(PackageInstallation.id == installation_id).options(
            selectinload(PackageInstallation.package),
            selectinload(PackageInstallation.package_version),
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_installation_by_scope(
        self,
        package_id: str,
        organization_id: str,
        workspace_id: Optional[str] = None,
    ) -> Optional[PackageInstallation]:
        query = select(PackageInstallation).where(
            PackageInstallation.package_id == package_id,
            PackageInstallation.organization_id == organization_id,
            PackageInstallation.workspace_id == workspace_id,
            PackageInstallation.status != "uninstalled",
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_installations(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[PackageInstallation], int]:
        conditions = [PackageInstallation.organization_id == organization_id]
        if workspace_id:
            conditions.append(PackageInstallation.workspace_id == workspace_id)
        if status:
            conditions.append(PackageInstallation.status == status)

        query = select(PackageInstallation).where(and_(*conditions)).order_by(PackageInstallation.installed_at.desc())
        count_res = await self.session.execute(select(func.count()).select_from(query.subquery()))
        total = count_res.scalar_one()

        paginated = query.limit(limit).offset(offset).options(
            selectinload(PackageInstallation.package),
            selectinload(PackageInstallation.package_version),
        )
        res = await self.session.execute(paginated)
        return list(res.scalars().all()), total

    async def create_installation(self, installation: PackageInstallation) -> PackageInstallation:
        self.session.add(installation)
        await self.session.commit()
        await self.session.refresh(installation)
        return installation

    async def update_installation(self, installation: PackageInstallation) -> PackageInstallation:
        installation.updated_at = datetime.now(timezone.utc)
        self.session.add(installation)
        await self.session.commit()
        await self.session.refresh(installation)
        return installation

    # ----------------------------------------------------
    # Reviews & Usage Telemetry
    # ----------------------------------------------------

    async def list_reviews(self, package_id: str, limit: int = 50, offset: int = 0) -> List[MarketplaceReview]:
        query = select(MarketplaceReview).where(
            MarketplaceReview.package_id == package_id,
            MarketplaceReview.status == "published",
        ).order_by(MarketplaceReview.created_at.desc()).limit(limit).offset(offset)
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def create_review(self, review: MarketplaceReview) -> MarketplaceReview:
        self.session.add(review)
        await self.session.commit()
        await self.session.refresh(review)
        return review

    async def record_usage(self, record: MarketplaceUsageRecord) -> None:
        self.session.add(record)
        await self.session.commit()

    async def get_package_usage_stats(self, package_id: str) -> Dict[str, Any]:
        """Calculates factual installation and operation counts for a package."""
        inst_query = select(func.count()).where(PackageInstallation.package_id == package_id)
        total_inst = (await self.session.execute(inst_query)).scalar_one()

        active_inst_query = select(func.count()).where(
            PackageInstallation.package_id == package_id,
            PackageInstallation.status == "installed",
        )
        active_inst = (await self.session.execute(active_inst_query)).scalar_one()

        # Operations count
        ops_query = select(
            MarketplaceUsageRecord.operation,
            func.count(MarketplaceUsageRecord.id),
        ).where(MarketplaceUsageRecord.package_id == package_id).group_by(MarketplaceUsageRecord.operation)
        ops_res = await self.session.execute(ops_query)
        ops_map = {op: cnt for op, cnt in ops_res.all()}

        return {
            "package_id": package_id,
            "total_installations": total_inst,
            "active_installations": active_inst,
            "total_runs": ops_map.get("run", 0),
            "total_updates": ops_map.get("update", 0),
            "total_uninstalls": ops_map.get("uninstall", 0),
            "version_distribution": {},
        }
