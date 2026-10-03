"""
Marketplace Package Update Service.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.marketplace.exceptions import (
    PackageInstallationNotFoundError,
    PackageVersionNotFoundError,
    PackageSecurityBlockedError,
    PackageRevokedError,
    PackageIncompatibleError,
)
from backend.app.services.marketplace.models import PackageInstallation, MarketplaceUsageRecord
from backend.app.services.marketplace.repository import MarketplaceRepository
from backend.app.services.marketplace.policies import MarketplaceGovernanceEvaluator
from backend.app.services.marketplace.evidence import MarketplaceEvidenceLogger
from backend.app.services.marketplace.compatibility import CompatibilityChecker


class PackageUpdateService:
    """Safely updates an installed package to a newer version without silent automatic execution."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = MarketplaceRepository(session)
        self.gov_evaluator = MarketplaceGovernanceEvaluator(session)
        self.evidence_logger = MarketplaceEvidenceLogger(session)

    async def check_for_updates(self, installation_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Checks if an update is available for an installation.
        Returns (has_update, current_version, latest_version).
        """
        inst = await self.repo.get_installation_by_id(installation_id)
        if not inst:
            raise PackageInstallationNotFoundError(installation_id)

        pkg = inst.package
        if not pkg or not pkg.current_version_id:
            return False, None, None

        current_ver = inst.package_version.version if inst.package_version else None
        latest_ver_record = await self.repo.get_version_by_id(pkg.current_version_id)
        if not latest_ver_record:
            return False, current_ver, None

        has_update = (latest_ver_record.id != inst.package_version_id) and (latest_ver_record.version > (current_ver or ""))
        return has_update, current_ver, latest_ver_record.version

    async def update_installation(
        self,
        installation_id: str,
        target_version_id: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> PackageInstallation:
        """
        Applies a package update after rigorous verification of dependencies, security status, and governance.
        """
        inst = await self.repo.get_installation_by_id(installation_id)
        if not inst or inst.status == "uninstalled":
            raise PackageInstallationNotFoundError(installation_id)

        pkg = inst.package
        # Resolve target version
        if target_version_id:
            new_ver = await self.repo.get_version_by_id(target_version_id)
        elif pkg.current_version_id:
            new_ver = await self.repo.get_version_by_id(pkg.current_version_id)
        else:
            raise PackageVersionNotFoundError(inst.package_id, "latest")

        if not new_ver:
            raise PackageVersionNotFoundError(inst.package_id, "target")

        # Safety: blocked or revoked packages cannot be applied as updates
        if new_ver.security_status == "blocked":
            raise PackageSecurityBlockedError("Update blocked: new version contains unresolved security findings.")
        if new_ver.security_status == "revoked" or new_ver.publication_status == "revoked":
            raise PackageRevokedError(inst.package_id, new_ver.version)

        # Compatibility verification
        c_status, c_reasons = CompatibilityChecker.check_compatibility(new_ver.manifest.get("compatibility", {}))
        if c_status == "incompatible":
            raise PackageIncompatibleError(f"Cannot update: incompatible ({', '.join(c_reasons)}).", missing_capabilities=c_reasons)

        # Governance evaluation
        perms = new_ver.manifest.get("permissions", [])
        await self.gov_evaluator.evaluate_action(
            organization_id=inst.organization_id,
            action="update",
            package_id=inst.package_id,
            package_version=new_ver.version,
            security_status=new_ver.security_status,
            requested_permissions=[p for entry in perms for p in entry.get("permissions", [])],
        )

        old_ver_str = inst.package_version.version if inst.package_version else "unknown"

        # Apply update
        now = datetime.now(timezone.utc)
        inst.package_version_id = new_ver.id
        inst.status = "installed"
        inst.updated_at = now
        updated = await self.repo.update_installation(inst)

        # Record evidence & telemetry
        await self.evidence_logger.record_evidence(
            organization_id=inst.organization_id,
            action="updated",
            package_id=inst.package_id,
            version=new_ver.version,
            actor_id=actor_id,
            details={"previous_version": old_ver_str, "new_version": new_ver.version},
        )
        await self.repo.record_usage(
            MarketplaceUsageRecord(
                package_id=inst.package_id,
                package_version_id=new_ver.id,
                organization_id=inst.organization_id,
                workspace_id=inst.workspace_id,
                installation_id=inst.id,
                operation="update",
                status="success",
            )
        )

        return updated
