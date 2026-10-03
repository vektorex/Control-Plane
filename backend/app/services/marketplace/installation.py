"""
Marketplace Package Installation Service.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.marketplace.exceptions import (
    PackageNotFoundError,
    PackageVersionNotFoundError,
    PackageAlreadyInstalledError,
    PackageSecurityBlockedError,
    PackageRevokedError,
    MarketplaceGovernanceDeniedError,
)
from backend.app.services.marketplace.models import PackageInstallation, MarketplaceUsageRecord
from backend.app.services.marketplace.repository import MarketplaceRepository
from backend.app.services.marketplace.policies import MarketplaceGovernanceEvaluator
from backend.app.services.marketplace.evidence import MarketplaceEvidenceLogger


class PackageInstallationService:
    """Manages tenant-scoped package installations into workspaces or organizations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = MarketplaceRepository(session)
        self.gov_evaluator = MarketplaceGovernanceEvaluator(session)
        self.evidence_logger = MarketplaceEvidenceLogger(session)

    async def install_package(
        self,
        package_id: str,
        organization_id: str,
        workspace_id: Optional[str] = None,
        project_id: Optional[str] = None,
        package_version_id: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        installed_by: Optional[str] = None,
    ) -> PackageInstallation:
        """
        Installs a published package version into target organization/workspace.
        Enforces that installation does NOT automatically grant permissions or secrets.
        """
        pkg = await self.repo.get_package_by_id(package_id)
        if not pkg:
            raise PackageNotFoundError(package_id)

        # Resolve version: specific version or latest published
        if package_version_id:
            ver = await self.repo.get_version_by_id(package_version_id)
        elif pkg.current_version_id:
            ver = await self.repo.get_version_by_id(pkg.current_version_id)
        else:
            raise PackageVersionNotFoundError(package_id, "latest")

        if not ver or ver.package_id != package_id:
            raise PackageVersionNotFoundError(package_id, str(package_version_id or "latest"))

        # Safety checks: blocked or revoked packages cannot be installed
        if ver.security_status == "blocked":
            raise PackageSecurityBlockedError("Cannot install package: flagged as security blocked.")
        if ver.publication_status == "revoked" or ver.security_status == "revoked":
            raise PackageRevokedError(package_id, ver.version)

        # Check existing installation in scope
        existing = await self.repo.get_installation_by_scope(
            package_id=package_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
        if existing:
            raise PackageAlreadyInstalledError(package_id, workspace_id or organization_id)

        # Evaluate Governance
        manifest = ver.manifest
        perms = manifest.get("permissions", [])
        await self.gov_evaluator.evaluate_action(
            organization_id=organization_id,
            action="install",
            package_id=package_id,
            package_version=ver.version,
            security_status=ver.security_status,
            requested_permissions=[p for entry in perms for p in entry.get("permissions", [])],
        )

        now = datetime.now(timezone.utc)
        installation = PackageInstallation(
            package_id=package_id,
            package_version_id=ver.id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            installed_by=installed_by,
            status="installed",
            configuration=configuration or {},
            installed_at=now,
            updated_at=now,
        )
        created = await self.repo.create_installation(installation)

        # Record evidence & telemetry
        await self.evidence_logger.record_evidence(
            organization_id=organization_id,
            action="installed",
            package_id=package_id,
            version=ver.version,
            actor_id=installed_by,
            details={"installation_id": created.id, "workspace_id": workspace_id},
        )
        await self.repo.record_usage(
            MarketplaceUsageRecord(
                package_id=package_id,
                package_version_id=ver.id,
                organization_id=organization_id,
                workspace_id=workspace_id,
                installation_id=created.id,
                operation="install",
                status="success",
            )
        )

        return created

    async def uninstall_package(
        self,
        installation_id: str,
        actor_id: Optional[str] = None,
    ) -> PackageInstallation:
        """Uninstalls a package installation and records audit evidence."""
        inst = await self.repo.get_installation_by_id(installation_id)
        if not inst or inst.status == "uninstalled":
            raise PackageNotFoundError(installation_id)

        now = datetime.now(timezone.utc)
        inst.status = "uninstalled"
        inst.uninstalled_at = now
        inst.updated_at = now
        updated = await self.repo.update_installation(inst)

        await self.evidence_logger.record_evidence(
            organization_id=inst.organization_id,
            action="uninstalled",
            package_id=inst.package_id,
            version=inst.package_version.version if inst.package_version else "unknown",
            actor_id=actor_id,
            details={"installation_id": inst.id},
        )
        await self.repo.record_usage(
            MarketplaceUsageRecord(
                package_id=inst.package_id,
                package_version_id=inst.package_version_id,
                organization_id=inst.organization_id,
                workspace_id=inst.workspace_id,
                installation_id=inst.id,
                operation="uninstall",
                status="success",
            )
        )

        return updated
