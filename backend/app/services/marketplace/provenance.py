"""
Marketplace Package Provenance Tracking.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.services.marketplace.models import PackageProvenance


class PackageProvenanceService:
    """Records and verifies package lineage and origin."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_provenance(
        self,
        package_version_id: str,
        creator_organization_id: str,
        content_hash: str,
        creator_user_id: Optional[str] = None,
        source_type: str = "native",
        source_reference: Optional[str] = None,
        parent_version_id: Optional[str] = None,
    ) -> PackageProvenance:
        """Creates an immutable provenance record for a published package version."""
        provenance = PackageProvenance(
            package_version_id=package_version_id,
            source_type=source_type,
            source_reference=source_reference,
            creator_organization_id=creator_organization_id,
            creator_user_id=creator_user_id,
            content_hash=content_hash,
            parent_version_id=parent_version_id,
        )
        self.session.add(provenance)
        await self.session.commit()
        await self.session.refresh(provenance)
        return provenance
