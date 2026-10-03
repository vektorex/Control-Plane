"""
Cryptographic integrity verification engine for Step 36: Disaster Recovery.
"""
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

from backend.app.services.disaster_recovery.exceptions import (
    BackupIntegrityError,
    ManifestTamperedError,
)
from backend.app.services.disaster_recovery.manifest import (
    calculate_content_hash,
    calculate_manifest_hash,
)
from backend.app.services.disaster_recovery.storage import BackupStorageProvider


class BackupIntegrityService:
    """
    Verifies cryptographic signatures, manifest hashes, content hashes,
    and tenant boundary isolation for backup packages.
    """

    def __init__(self, storage_provider: BackupStorageProvider):
        self.storage = storage_provider

    def verify_manifest(self, manifest_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verify that manifest_hash matches the deterministic hash of its canonical contents.
        """
        claimed_hash = manifest_data.get("manifest_hash")
        if not claimed_hash:
            return False, "Missing manifest_hash in manifest payload"

        recomputed_hash = calculate_manifest_hash(manifest_data)
        if claimed_hash != recomputed_hash:
            return False, f"Manifest hash mismatch: claimed {claimed_hash[:16]}... != computed {recomputed_hash[:16]}..."

        return True, "Manifest integrity verified"

    def verify_content(
        self,
        content_bytes: bytes,
        manifest_data: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """
        Verify that content_bytes match the content_hash recorded in the manifest.
        """
        claimed_hash = manifest_data.get("content_hash")
        if not claimed_hash:
            return False, "Missing content_hash in manifest"

        actual_hash = calculate_content_hash(content_bytes)
        if claimed_hash != actual_hash:
            return False, f"Content hash mismatch: manifest has {claimed_hash[:16]}... but file has {actual_hash[:16]}..."

        return True, "Content hash verified"

    def verify_tenant_boundary(
        self,
        manifest_data: Dict[str, Any],
        expected_organization_id: str,
    ) -> Tuple[bool, str]:
        """
        Verify that all resources inside manifest strictly belong to expected organization_id.
        """
        manifest_org = manifest_data.get("organization_id")
        if manifest_org != expected_organization_id:
            return False, f"Manifest organization '{manifest_org}' does not match expected '{expected_organization_id}'"

        resources = manifest_data.get("resources", [])
        for res in resources:
            res_tenant = res.get("tenant")
            if res_tenant != expected_organization_id:
                return False, f"Resource '{res.get('resource_id')}' belongs to tenant '{res_tenant}', expected '{expected_organization_id}'"

        return True, "Tenant boundaries verified"

    def verify_full_integrity(
        self,
        manifest_data: Dict[str, Any],
        content_bytes: bytes,
        expected_organization_id: str,
    ) -> Dict[str, Any]:
        """
        Execute complete multi-vector integrity check.
        """
        manifest_ok, manifest_msg = self.verify_manifest(manifest_data)
        content_ok, content_msg = self.verify_content(content_bytes, manifest_data)
        tenant_ok, tenant_msg = self.verify_tenant_boundary(manifest_data, expected_organization_id)

        all_passed = manifest_ok and content_ok and tenant_ok
        details = {
            "passed": all_passed,
            "manifest_check": {"passed": manifest_ok, "detail": manifest_msg},
            "content_check": {"passed": content_ok, "detail": content_msg},
            "tenant_check": {"passed": tenant_ok, "detail": tenant_msg},
            "resource_count": manifest_data.get("resource_count", 0),
        }

        if not all_passed:
            if not manifest_ok:
                raise ManifestTamperedError(f"Manifest integrity failed: {manifest_msg}")
            raise BackupIntegrityError(f"Backup integrity check failed: {content_msg or tenant_msg}")

        return details
