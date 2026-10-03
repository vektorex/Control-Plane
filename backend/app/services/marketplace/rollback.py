"""
Marketplace Package Rollback Service.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.marketplace.exceptions import (
    PackageInstallationNotFoundError,
    PackageVersionNotFoundError,
    RollbackNotAllowedError,
    PackageRevokedError,
    PackageSecurityBlockedError,
)
from backend.app.services.marketplace.models import PackageInstallation, MarketplaceUsageRecord
from backend.app.services.marketplace.repository import MarketplaceRepository
from backend.app.services.marketplace.policies import MarketplaceGovernanceEvaluator
from backend.app.services.marketplace.evidence import MarketplaceEvidenceLogger


class PackageRollbackService:
    """Safely rolls back an installation to a previous valid version."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = MarketplaceRepository(session)
        self.gov_evaluator = MarketplaceGovernanceEvaluator(session)
        self.evidence_logger = MarketplaceEvidenceLogger(session)

    async def rollback_installation(
        self,
        installation_id: str,
        target_version_id: str,
        actor_id: Optional[str] = None,
    ) -> PackageInstallation:
        """
        Rolls back installation to target_version_id.
        Enforces that target version exists, is not revoked, and is not security-blocked.
        """
        inst = await self.repo.get_installation_by_id(installation_id)
        if not inst or inst.status == "uninstalled":
            raise PackageInstallationNotFoundError(installation_id)

        target_ver = await self.repo.get_version_by_id(target_version_id)
        if not target_ver or target_ver.package_id != inst.package_id:
            raise PackageVersionNotFoundError(inst.package_id, target_version_id)

        # Disallow rollback to revoked or security-blocked versions
        if target_ver.security_status == "blocked":
            raise PackageSecurityBlockedError("Rollback disallowed: target version is blocked by security policy.")
        if target_ver.security_status == "revoked" or target_ver.publication_status == "revoked":
            raise PackageRevokedError(inst.package_id, target_ver.version)

        # Governance review
        perms = target_ver.manifest.get("permissions", [])
        await self.gov_evaluator.evaluate_action(
            organization_id=inst.organization_id,
            action="rollback",
            package_id=inst.package_id,
            package_version=target_ver.version,
            security_status=target_ver.security_status,
            requested_permissions=[p for entry in perms for p in entry.get("permissions", [])],
        )

        old_ver_str = inst.package_version.version if inst.package_version else "unknown"

        now = datetime.now(timezone.utc)
        inst.package_version_id = target_ver.id
        inst.updated_at = now
        updated = await self.repo.update_installation(inst)

        await self.evidence_logger.record_evidence(
            organization_id=inst.organization_id,
            action="rolled_back",
            package_id=inst.package_id,
            version=target_ver.version,
            actor_id=actor_id,
            details={"previous_version": old_ver_str, "target_version": target_ver.version},
        )
        await self.repo.record_usage(
            MarketplaceUsageRecord(
                package_id=inst.package_id,
                package_version_id=target_ver.id,
                organization_id=inst.organization_id,
                workspace_id=inst.workspace_id,
                installation_id=inst.id,
                operation="rollback",
                status="success",
            )
        )

        return updated
