"""
Verification engine for confirming backup integrity, schema compliance, and dry-run restore simulation.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.services.disaster_recovery.models import (
    BackupRun,
    BackupManifest,
    BackupVerification,
)
from backend.app.services.disaster_recovery.integrity import BackupIntegrityService
from backend.app.services.disaster_recovery.storage import (
    BackupStorageProvider,
    BackupEncryptionProvider,
    get_backup_storage_provider,
)
from backend.app.services.disaster_recovery.exceptions import (
    BackupNotFoundError,
    BackupIntegrityError,
    DisasterRecoveryError,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BackupVerificationService:
    """
    Executes multi-phase verification on completed backups before certifying them restorable.
    """

    def __init__(
        self,
        session: AsyncSession,
        storage_provider: Optional[BackupStorageProvider] = None,
        encryption_provider: Optional[BackupEncryptionProvider] = None,
    ):
        self.session = session
        self.storage = storage_provider or get_backup_storage_provider()
        self.encryption = encryption_provider or BackupEncryptionProvider()
        self.integrity = BackupIntegrityService(self.storage)

    async def verify_backup(self, backup_run_id: str) -> List[BackupVerification]:
        """
        Execute full battery of verifications: manifest, integrity, schema, dependency, and restore_simulation.
        """
        res = await self.session.execute(
            select(BackupRun).where(BackupRun.id == backup_run_id)
        )
        backup_run = res.scalar_one_or_none()
        if not backup_run:
            raise BackupNotFoundError(f"Backup run '{backup_run_id}' not found.")

        res_manifest = await self.session.execute(
            select(BackupManifest).where(BackupManifest.backup_run_id == backup_run_id)
        )
        manifest = res_manifest.scalar_one_or_none()
        if not manifest:
            raise BackupNotFoundError(f"Manifest for backup run '{backup_run_id}' not found.")

        # Read stored artifact
        storage_key = manifest.storage_reference.replace("local://", "")
        content_bytes = self.storage.get(storage_key)

        verifications: List[BackupVerification] = []

        manifest_dict = {
            "backup_run_id": manifest.backup_run_id,
            "version": manifest.version,
            "format": manifest.format,
            "resource_count": manifest.resource_count,
            "content_hash": manifest.content_hash,
            "manifest_hash": manifest.manifest_hash,
            "encryption_metadata": manifest.encryption_metadata,
            "resources": manifest.resources_metadata,
            "organization_id": backup_run.organization_id,
        }

        # 1. Manifest verification
        v_manifest = BackupVerification(
            id=str(uuid.uuid4()),
            backup_run_id=backup_run_id,
            verification_type="manifest",
            status="running",
            started_at=_utc_now(),
        )
        self.session.add(v_manifest)
        manifest_ok, manifest_msg = self.integrity.verify_manifest(manifest_dict)
        v_manifest.status = "passed" if manifest_ok else "failed"
        v_manifest.completed_at = _utc_now()
        v_manifest.details = {"message": manifest_msg}
        verifications.append(v_manifest)

        # 2. Cryptographic content & tenant integrity
        v_integrity = BackupVerification(
            id=str(uuid.uuid4()),
            backup_run_id=backup_run_id,
            verification_type="integrity",
            status="running",
            started_at=_utc_now(),
        )
        self.session.add(v_integrity)
        content_ok, content_msg = self.integrity.verify_content(content_bytes, manifest_dict)
        tenant_ok, tenant_msg = self.integrity.verify_tenant_boundary(manifest_dict, backup_run.organization_id)
        integrity_passed = content_ok and tenant_ok
        v_integrity.status = "passed" if integrity_passed else "failed"
        v_integrity.completed_at = _utc_now()
        v_integrity.details = {
            "content": content_msg,
            "tenant_boundary": tenant_msg,
        }
        verifications.append(v_integrity)

        # 3. Schema compliance
        v_schema = BackupVerification(
            id=str(uuid.uuid4()),
            backup_run_id=backup_run_id,
            verification_type="schema",
            status="running",
            started_at=_utc_now(),
        )
        self.session.add(v_schema)
        # Check schema version
        schema_passed = manifest.version in ["1.0"] and manifest.format in ["json_logical"]
        v_schema.status = "passed" if schema_passed else "failed"
        v_schema.completed_at = _utc_now()
        v_schema.details = {
            "version": manifest.version,
            "format": manifest.format,
            "supported": schema_passed,
        }
        verifications.append(v_schema)

        # 4. Dependency consistency
        v_dep = BackupVerification(
            id=str(uuid.uuid4()),
            backup_run_id=backup_run_id,
            verification_type="dependency",
            status="running",
            started_at=_utc_now(),
        )
        self.session.add(v_dep)
        # Check that resources in manifest have resolvable dependencies
        known_ids = {r.get("resource_id") for r in manifest.resources_metadata}
        missing_deps = []
        for r in manifest.resources_metadata:
            for dep in r.get("dependencies", []):
                if dep not in known_ids:
                    missing_deps.append({"resource": r.get("resource_id"), "missing_dep": dep})
        
        dep_passed = len(missing_deps) == 0
        v_dep.status = "passed" if dep_passed else "warning"
        v_dep.completed_at = _utc_now()
        v_dep.details = {
            "missing_dependencies_count": len(missing_deps),
            "missing_dependencies": missing_deps[:10],
        }
        verifications.append(v_dep)

        # 5. Restore Simulation (dry-run)
        v_sim = BackupVerification(
            id=str(uuid.uuid4()),
            backup_run_id=backup_run_id,
            verification_type="restore_simulation",
            status="running",
            started_at=_utc_now(),
        )
        self.session.add(v_sim)
        # Simulation verifies payload decryption (if encrypted) and JSON deserialization
        sim_passed = True
        sim_msg = "Dry-run restore simulation deserialized payload successfully without modifying production state."
        try:
            raw_data = content_bytes
            if manifest.encryption_metadata.get("encrypted"):
                raw_data = self.encryption.decrypt(raw_data)
            parsed = json.loads(raw_data.decode("utf-8"))
            if "resources" not in parsed:
                sim_passed = False
                sim_msg = "Simulated payload missing 'resources' root key."
        except Exception as exc:
            sim_passed = False
            sim_msg = f"Dry-run simulation failed during decryption/parsing: {exc}"

        v_sim.status = "passed" if sim_passed else "failed"
        v_sim.completed_at = _utc_now()
        v_sim.details = {
            "simulation_passed": sim_passed,
            "message": sim_msg,
            "simulated_resource_count": manifest.resource_count,
        }
        verifications.append(v_sim)

        # If all essential checks passed, certify manifest verification status
        if manifest_ok and integrity_passed and schema_passed and sim_passed:
            manifest.verification_status = "verified"
        else:
            manifest.verification_status = "failed"

        await self.session.commit()
        return verifications
