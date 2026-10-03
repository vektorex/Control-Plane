"""
Marketplace Package Publishing Service.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.marketplace.exceptions import (
    PackageNotFoundError,
    PackageVersionNotFoundError,
    PackageSecurityBlockedError,
    PackageIncompatibleError,
    MarketplaceGovernanceDeniedError,
)
from backend.app.services.marketplace.models import MarketplacePackage, MarketplacePackageVersion
from backend.app.services.marketplace.repository import MarketplaceRepository
from backend.app.services.marketplace.validator import PackageValidator
from backend.app.services.marketplace.security_scanner import MarketplaceSecurityScanner
from backend.app.services.marketplace.dependencies import DependencyResolver
from backend.app.services.marketplace.compatibility import CompatibilityChecker
from backend.app.services.marketplace.permissions import MarketplacePermissionManager
from backend.app.services.marketplace.policies import MarketplaceGovernanceEvaluator
from backend.app.services.marketplace.evidence import MarketplaceEvidenceLogger
from backend.app.services.marketplace.provenance import PackageProvenanceService
from backend.app.services.marketplace.schemas import SecurityStatus


class PackagePublishingService:
    """Orchestrates multi-stage publication pipeline with validation, scanning, and governance."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = MarketplaceRepository(session)
        self.gov_evaluator = MarketplaceGovernanceEvaluator(session)
        self.evidence_logger = MarketplaceEvidenceLogger(session)
        self.provenance_service = PackageProvenanceService(session)

    async def publish_version(
        self,
        package_id: str,
        version_id: str,
        actor_id: Optional[str] = None,
        is_org_admin: bool = False,
    ) -> MarketplacePackageVersion:
        """
        Executes publication pipeline:
        1. Validate manifest structure
        2. Execute security scan
        3. Validate dependencies & detect cycles
        4. Validate compatibility
        5. Evaluate governance
        6. Record provenance & evidence
        7. Transition version to 'published'
        """
        pkg = await self.repo.get_package_by_id(package_id)
        if not pkg:
            raise PackageNotFoundError(package_id)

        ver = await self.repo.get_version_by_id(version_id)
        if not ver or ver.package_id != package_id:
            raise PackageVersionNotFoundError(package_id, version_id)

        manifest = ver.manifest

        # Stage 1: Validation
        PackageValidator.validate_manifest(manifest)
        ver.validation_status = "valid"

        # Stage 2: Security Scan
        sec_status, findings = MarketplaceSecurityScanner.scan_manifest(manifest)
        ver.security_status = sec_status.value
        if sec_status == SecurityStatus.BLOCKED:
            await self.repo.update_version(ver)
            raise PackageSecurityBlockedError(
                f"Publication blocked: package contains security risks ({', '.join(findings)}).",
                findings=findings,
            )

        # Stage 3: Dependencies & Cycles
        deps = manifest.get("dependencies", [])
        DependencyResolver.validate_dependencies_list(deps)

        # Stage 4: Compatibility
        compat = manifest.get("compatibility", {})
        c_status, c_reasons = CompatibilityChecker.check_compatibility(compat)
        if c_status == "incompatible":
            await self.repo.update_version(ver)
            raise PackageIncompatibleError(
                f"Publication blocked: package is incompatible ({', '.join(c_reasons)}).",
                missing_capabilities=c_reasons,
            )

        # Stage 5: Permissions & Governance
        perms = manifest.get("permissions", [])
        sensitive_perms = MarketplacePermissionManager.identify_sensitive_permissions(perms)
        if sensitive_perms and not is_org_admin:
            raise MarketplaceGovernanceDeniedError(
                f"Publishing package with sensitive permissions requires organization admin: {', '.join(sensitive_perms)}"
            )

        await self.gov_evaluator.evaluate_action(
            organization_id=pkg.owner_organization_id,
            action="publish",
            package_id=package_id,
            package_version=ver.version,
            security_status=ver.security_status,
            requested_permissions=[p for entry in perms for p in entry.get("permissions", [])],
            is_public=(pkg.visibility == "public"),
        )

        # Stage 6: Provenance & Evidence
        await self.provenance_service.record_provenance(
            package_version_id=ver.id,
            creator_organization_id=pkg.owner_organization_id,
            content_hash=ver.content_hash,
            creator_user_id=actor_id,
            source_type="native",
        )
        await self.evidence_logger.record_evidence(
            organization_id=pkg.owner_organization_id,
            action="published",
            package_id=package_id,
            version=ver.version,
            actor_id=actor_id,
            details={"content_hash": ver.content_hash, "security_status": ver.security_status},
        )

        # Stage 7: Finalize publication
        now = datetime.now(timezone.utc)
        ver.publication_status = "published"
        ver.published_at = now
        await self.repo.update_version(ver)

        pkg.status = "published"
        pkg.current_version_id = ver.id
        await self.repo.update_package(pkg)

        return ver
