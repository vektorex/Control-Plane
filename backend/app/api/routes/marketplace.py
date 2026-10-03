"""
Marketplace Management API Routes.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.models.user import User
from backend.app.db.database import get_db
from backend.app.services.marketplace.exceptions import (
    MarketplaceException,
    PackageNotFoundError,
    PackageVersionNotFoundError,
    PackageValidationError,
    PackageSecurityBlockedError,
    PackageIncompatibleError,
    DependencyResolutionError,
    PackageAlreadyInstalledError,
    PackageInstallationNotFoundError,
    RollbackNotAllowedError,
    PackageRevokedError,
    MarketplaceGovernanceDeniedError,
)
from backend.app.services.marketplace.schemas import (
    MarketplacePackageCreate,
    MarketplacePackageUpdate,
    MarketplacePackageResponse,
    MarketplacePackageDetailResponse,
    MarketplacePackageVersionCreate,
    MarketplacePackageVersionResponse,
    PackageInstallationCreate,
    PackageInstallationResponse,
    MarketplaceReviewCreate,
    MarketplaceReviewResponse,
    MarketplaceSearchQuery,
    PackageType,
    PackageVisibility,
    PackageStatus,
    PackageForkRequest,
)
from backend.app.services.marketplace.service import MarketplaceService

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])


@router.get("/categories", response_model=List[str])
async def list_categories():
    """List standard package categories."""
    return MarketplaceService.get_categories()


@router.get("/tags", response_model=List[str])
async def list_tags():
    """List standard package taxonomy tags."""
    return MarketplaceService.get_tags()


@router.get("/packages", response_model=Dict[str, Any])
async def list_packages(
    query: Optional[str] = None,
    category: Optional[str] = None,
    package_type: Optional[PackageType] = None,
    visibility: Optional[PackageVisibility] = None,
    package_status: Optional[PackageStatus] = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search and browse marketplace packages."""
    search_q = MarketplaceSearchQuery(
        query=query,
        category=category,
        package_type=package_type,
        visibility=visibility,
        status=package_status,
        limit=limit,
        offset=offset,
    )
    svc = MarketplaceService(db)
    items, total = await svc.list_packages(search_q, organization_id=current_user.organization_id)
    return {
        "items": [MarketplacePackageResponse.model_validate(p) for p in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/packages", response_model=MarketplacePackageResponse, status_code=status.HTTP_201_CREATED)
async def create_package(
    data: MarketplacePackageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new package in draft status."""
    svc = MarketplaceService(db)
    pkg = await svc.create_package(
        organization_id=current_user.organization_id,
        data=data,
        user_id=current_user.id,
    )
    return MarketplacePackageResponse.model_validate(pkg)


@router.get("/packages/{package_id}", response_model=MarketplacePackageDetailResponse)
async def get_package(
    package_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get package details including versions, average rating, and total installations."""
    svc = MarketplaceService(db)
    pkg = await svc.get_package(package_id)
    if not pkg:
        # Also check by slug
        pkg = await svc.get_package_by_slug(package_id, organization_id=current_user.organization_id)
    if not pkg:
        raise PackageNotFoundError(package_id)

    # Compute stats
    avg_rating = await svc.get_average_rating(pkg.id)
    usage = await svc.get_package_usage(pkg.id)

    resp = MarketplacePackageDetailResponse.model_validate(pkg)
    resp.average_rating = avg_rating
    resp.total_installations = usage.get("total_installations", 0)
    resp.versions = [MarketplacePackageVersionResponse.model_validate(v) for v in (pkg.versions or [])]
    return resp


@router.patch("/packages/{package_id}", response_model=MarketplacePackageResponse)
async def update_package(
    package_id: str,
    data: MarketplacePackageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update package metadata."""
    svc = MarketplaceService(db)
    pkg = await svc.update_package(package_id, data, user_id=current_user.id)
    return MarketplacePackageResponse.model_validate(pkg)


@router.post("/packages/{package_id}/fork", response_model=MarketplacePackageResponse, status_code=status.HTTP_201_CREATED)
async def fork_package(
    package_id: str,
    data: PackageForkRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fork a package into target organization with fresh validation and clean ownership."""
    svc = MarketplaceService(db)
    target_org = data.target_organization_id or current_user.organization_id
    forked = await svc.fork_package(
        source_package_id=package_id,
        target_org_id=target_org,
        new_slug=data.new_slug,
        new_name=data.new_name,
        description=data.description,
        user_id=current_user.id,
    )
    return MarketplacePackageResponse.model_validate(forked)


@router.get("/packages/{package_id}/usage", response_model=Dict[str, Any])
async def get_package_usage(
    package_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get factual usage analytics for a package."""
    svc = MarketplaceService(db)
    return await svc.get_package_usage(package_id)


# ----------------------------------------------------
# Versions
# ----------------------------------------------------

@router.post("/packages/{package_id}/versions", response_model=MarketplacePackageVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    package_id: str,
    data: MarketplacePackageVersionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new immutable draft version of a package."""
    svc = MarketplaceService(db)
    ver = await svc.create_version(package_id, data, user_id=current_user.id)
    return MarketplacePackageVersionResponse.model_validate(ver)


@router.post("/packages/{package_id}/versions/{version_id}/publish", response_model=MarketplacePackageVersionResponse)
async def publish_version(
    package_id: str,
    version_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute validation, security scanning, compatibility check, and publish package version."""
    svc = MarketplaceService(db)
    is_admin = getattr(current_user, "role", "") in ("admin", "owner")
    ver = await svc.publish_version(package_id, version_id, user_id=current_user.id, is_org_admin=is_admin)
    return MarketplacePackageVersionResponse.model_validate(ver)


@router.post("/packages/{package_id}/versions/{version_id}/deprecate", response_model=MarketplacePackageVersionResponse)
async def deprecate_version(
    package_id: str,
    version_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark version as deprecated."""
    svc = MarketplaceService(db)
    ver = await svc.deprecate_version(package_id, version_id)
    return MarketplacePackageVersionResponse.model_validate(ver)


# ----------------------------------------------------
# Installations
# ----------------------------------------------------

@router.post("/installations", response_model=PackageInstallationResponse, status_code=status.HTTP_201_CREATED)
async def install_package(
    data: PackageInstallationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Install package into organization or workspace."""
    svc = MarketplaceService(db)
    inst = await svc.install_package(
        package_id=data.package_id,
        organization_id=current_user.organization_id,
        workspace_id=data.workspace_id,
        project_id=data.project_id,
        version_id=data.package_version_id,
        configuration=data.configuration,
        user_id=current_user.id,
    )
    return PackageInstallationResponse.model_validate(inst)


@router.get("/installations", response_model=Dict[str, Any])
async def list_installations(
    workspace_id: Optional[str] = None,
    installation_status: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List package installations in tenant scope."""
    svc = MarketplaceService(db)
    items, total = await svc.list_installations(
        organization_id=current_user.organization_id,
        workspace_id=workspace_id,
        status=installation_status,
        limit=limit,
        offset=offset,
    )
    res_items = []
    for item in items:
        resp = PackageInstallationResponse.model_validate(item)
        if item.package:
            resp.package_name = item.package.name
            resp.package_slug = item.package.slug
        if item.package_version:
            resp.installed_version = item.package_version.version
        res_items.append(resp)

    return {"items": res_items, "total": total, "limit": limit, "offset": offset}


@router.get("/installations/{installation_id}", response_model=PackageInstallationResponse)
async def get_installation(
    installation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get installation details."""
    svc = MarketplaceService(db)
    inst = await svc.get_installation(installation_id)
    if not inst or inst.organization_id != current_user.organization_id:
        raise PackageInstallationNotFoundError(installation_id)

    resp = PackageInstallationResponse.model_validate(inst)
    if inst.package:
        resp.package_name = inst.package.name
        resp.package_slug = inst.package.slug
    if inst.package_version:
        resp.installed_version = inst.package_version.version
    return resp


@router.post("/installations/{installation_id}/check-updates", response_model=Dict[str, Any])
async def check_updates(
    installation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if newer compatible version is available."""
    svc = MarketplaceService(db)
    has_update, cur_v, latest_v = await svc.check_for_updates(installation_id)
    return {"has_update": has_update, "current_version": cur_v, "latest_version": latest_v}


@router.post("/installations/{installation_id}/update", response_model=PackageInstallationResponse)
async def update_installation(
    installation_id: str,
    target_version_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Safely update package installation."""
    svc = MarketplaceService(db)
    updated = await svc.update_installation(
        installation_id=installation_id,
        target_version_id=target_version_id,
        user_id=current_user.id,
    )
    return PackageInstallationResponse.model_validate(updated)


@router.post("/installations/{installation_id}/rollback", response_model=PackageInstallationResponse)
async def rollback_installation(
    installation_id: str,
    target_version_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Safely roll back package installation to previous valid version."""
    svc = MarketplaceService(db)
    rolled_back = await svc.rollback_installation(
        installation_id=installation_id,
        target_version_id=target_version_id,
        user_id=current_user.id,
    )
    return PackageInstallationResponse.model_validate(rolled_back)


@router.delete("/installations/{installation_id}", response_model=PackageInstallationResponse)
async def uninstall_package(
    installation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Uninstall a package installation."""
    svc = MarketplaceService(db)
    uninstalled = await svc.uninstall_installation(installation_id, user_id=current_user.id)
    return PackageInstallationResponse.model_validate(uninstalled)


# ----------------------------------------------------
# Reviews
# ----------------------------------------------------

@router.get("/packages/{package_id}/reviews", response_model=List[MarketplaceReviewResponse])
async def list_reviews(
    package_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List reviews for a package."""
    svc = MarketplaceService(db)
    reviews = await svc.list_reviews(package_id, limit=limit, offset=offset)
    return [MarketplaceReviewResponse.model_validate(r) for r in reviews]


@router.post("/packages/{package_id}/reviews", response_model=MarketplaceReviewResponse, status_code=status.HTTP_201_CREATED)
async def add_review(
    package_id: str,
    data: MarketplaceReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a factual user review with optional 1-5 rating."""
    svc = MarketplaceService(db)
    rev = await svc.add_review(
        package_id=package_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        data=data,
    )
    return MarketplaceReviewResponse.model_validate(rev)
