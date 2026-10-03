"""
Marketplace Service Facade.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.marketplace.models import (
    MarketplacePackage,
    MarketplacePackageVersion,
    PackageInstallation,
    MarketplaceReview,
)
from backend.app.services.marketplace.repository import MarketplaceRepository
from backend.app.services.marketplace.packages import PackageManagementService
from backend.app.services.marketplace.versions import PackageVersionService
from backend.app.services.marketplace.publishing import PackagePublishingService
from backend.app.services.marketplace.installation import PackageInstallationService
from backend.app.services.marketplace.updates import PackageUpdateService
from backend.app.services.marketplace.rollback import PackageRollbackService
from backend.app.services.marketplace.search import MarketplaceSearchService
from backend.app.services.marketplace.registry import MarketplaceRegistryService
from backend.app.services.marketplace.reviews import MarketplaceReviewService
from backend.app.services.marketplace.ratings import MarketplaceRatingCalculator
from backend.app.services.marketplace.schemas import (
    MarketplacePackageCreate,
    MarketplacePackageUpdate,
    MarketplacePackageVersionCreate,
    MarketplaceReviewCreate,
    MarketplaceSearchQuery,
)


class MarketplaceService:
    """Master facade for all marketplace catalog, package versioning, installation, and review operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = MarketplaceRepository(session)
        self.pkg_service = PackageManagementService(session)
        self.ver_service = PackageVersionService(session)
        self.pub_service = PackagePublishingService(session)
        self.inst_service = PackageInstallationService(session)
        self.upd_service = PackageUpdateService(session)
        self.rb_service = PackageRollbackService(session)
        self.search_service = MarketplaceSearchService(session)
        self.review_service = MarketplaceReviewService(session)

    # Packages
    async def create_package(self, organization_id: str, data: MarketplacePackageCreate, user_id: Optional[str] = None) -> MarketplacePackage:
        return await self.pkg_service.create_package(organization_id, data, creator_user_id=user_id)

    async def get_package(self, package_id: str) -> Optional[MarketplacePackage]:
        return await self.repo.get_package_by_id(package_id)

    async def get_package_by_slug(self, slug: str, organization_id: Optional[str] = None) -> Optional[MarketplacePackage]:
        return await self.repo.get_package_by_slug(slug, organization_id=organization_id)

    async def list_packages(self, query: MarketplaceSearchQuery, organization_id: Optional[str] = None) -> Tuple[List[MarketplacePackage], int]:
        return await self.search_service.search(query, organization_id=organization_id)

    async def update_package(self, package_id: str, data: MarketplacePackageUpdate, user_id: Optional[str] = None) -> MarketplacePackage:
        return await self.pkg_service.update_package(package_id, data, actor_id=user_id)

    async def fork_package(
        self,
        source_package_id: str,
        target_org_id: str,
        new_slug: str,
        new_name: str,
        description: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> MarketplacePackage:
        return await self.pkg_service.fork_package(source_package_id, target_org_id, new_slug, new_name, description, actor_id=user_id)

    # Versions
    async def create_version(self, package_id: str, data: MarketplacePackageVersionCreate, user_id: Optional[str] = None) -> MarketplacePackageVersion:
        return await self.ver_service.create_version(package_id, data, creator_user_id=user_id)

    async def get_version(self, version_id: str) -> Optional[MarketplacePackageVersion]:
        return await self.repo.get_version_by_id(version_id)

    async def publish_version(self, package_id: str, version_id: str, user_id: Optional[str] = None, is_org_admin: bool = False) -> MarketplacePackageVersion:
        return await self.pub_service.publish_version(package_id, version_id, actor_id=user_id, is_org_admin=is_org_admin)

    async def deprecate_version(self, package_id: str, version_id: str) -> MarketplacePackageVersion:
        return await self.ver_service.deprecate_version(package_id, version_id)

    async def revoke_version(self, package_id: str, version_id: str, reason: str = "") -> MarketplacePackageVersion:
        return await self.ver_service.revoke_version(package_id, version_id, reason=reason)

    # Installations
    async def install_package(
        self,
        package_id: str,
        organization_id: str,
        workspace_id: Optional[str] = None,
        project_id: Optional[str] = None,
        version_id: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> PackageInstallation:
        return await self.inst_service.install_package(
            package_id=package_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            package_version_id=version_id,
            configuration=configuration,
            installed_by=user_id,
        )

    async def uninstall_installation(self, installation_id: str, user_id: Optional[str] = None) -> PackageInstallation:
        return await self.inst_service.uninstall_package(installation_id, actor_id=user_id)

    async def check_for_updates(self, installation_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
        return await self.upd_service.check_for_updates(installation_id)

    async def update_installation(self, installation_id: str, target_version_id: Optional[str] = None, user_id: Optional[str] = None) -> PackageInstallation:
        return await self.upd_service.update_installation(installation_id, target_version_id=target_version_id, actor_id=user_id)

    async def rollback_installation(self, installation_id: str, target_version_id: str, user_id: Optional[str] = None) -> PackageInstallation:
        return await self.rb_service.rollback_installation(installation_id, target_version_id=target_version_id, actor_id=user_id)

    async def get_installation(self, installation_id: str) -> Optional[PackageInstallation]:
        return await self.repo.get_installation_by_id(installation_id)

    async def list_installations(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[PackageInstallation], int]:
        return await self.repo.list_installations(organization_id, workspace_id=workspace_id, status=status, limit=limit, offset=offset)

    # Reviews & Ratings
    async def add_review(self, package_id: str, organization_id: str, user_id: str, data: MarketplaceReviewCreate) -> MarketplaceReview:
        return await self.review_service.add_review(package_id, organization_id, user_id, data)

    async def list_reviews(self, package_id: str, limit: int = 50, offset: int = 0) -> List[MarketplaceReview]:
        return await self.review_service.list_reviews(package_id, limit=limit, offset=offset)

    async def get_average_rating(self, package_id: str) -> Optional[float]:
        reviews = await self.review_service.list_reviews(package_id, limit=200)
        return MarketplaceRatingCalculator.calculate_average(reviews)

    # Usage & Taxonomy
    async def get_package_usage(self, package_id: str) -> Dict[str, Any]:
        return await self.repo.get_package_usage_stats(package_id)

    @classmethod
    def get_categories(cls) -> List[str]:
        return MarketplaceRegistryService.get_categories()

    @classmethod
    def get_tags(cls) -> List[str]:
        return MarketplaceRegistryService.get_tags()
