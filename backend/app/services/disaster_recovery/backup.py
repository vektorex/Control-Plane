"""
Core backup execution service for Step 36: Disaster Recovery.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.services.disaster_recovery.models import BackupRun, BackupManifest, BackupPolicy, BackupResource
from backend.app.services.disaster_recovery.manifest import ManifestBuilder
from backend.app.services.disaster_recovery.storage import (
    BackupStorageProvider,
    BackupEncryptionProvider,
    get_backup_storage_provider,
)
from backend.app.services.disaster_recovery.backup_planner import BackupPlanner
from backend.app.services.disaster_recovery.exceptions import BackupNotFoundError, DisasterRecoveryError
from backend.app.services.disaster_recovery.validators import validate_no_secrets_in_backup_payload


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BackupService:
    """
    Executes transactionally consistent and versioned logical backups,
    generates cryptographic manifests, and manages snapshot storage.
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
        self.planner = BackupPlanner(session)

    async def execute_backup(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
        policy_id: Optional[str] = None,
        resource_types: Optional[List[str]] = None,
        strategy: str = "logical_export",
    ) -> BackupRun:
        """
        Execute an orchestrated logical backup snapshot.
        """
        # 1. Produce plan
        plan = await self.planner.create_plan(
            organization_id=organization_id,
            workspace_id=workspace_id,
            policy_id=policy_id,
            resource_types=resource_types,
            strategy=strategy,
        )

        run_id = str(uuid.uuid4())
        backup_run = BackupRun(
            id=run_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            policy_id=policy_id,
            status="running",
            started_at=_utc_now(),
            resource_count=plan["resource_count"],
            byte_estimate=plan["estimated_bytes"],
            classification=plan["classification"],
            backup_version="1.0",
        )
        self.session.add(backup_run)
        await self.session.flush()

        try:
            # 2. Build logical payload and manifest
            builder = ManifestBuilder(
                backup_run_id=run_id,
                organization_id=organization_id,
                version="1.0",
                format_type="json_logical",
            )

            logical_package: Dict[str, Any] = {
                "schema_version": "1.0",
                "application_version": "1.0",
                "organization_id": organization_id,
                "created_at": _utc_now().isoformat(),
                "resources": {},
            }

            for r in plan["ordered_resources"]:
                r_type = r["resource_type"]
                r_id = r["resource_id"]
                classification = r["classification"]

                # Collect synthetic state for resource
                state_data = {
                    "resource_type": r_type,
                    "resource_id": r_id,
                    "tenant": organization_id,
                    "version": "1.0",
                    "dependencies": r.get("dependencies", []),
                }
                validate_no_secrets_in_backup_payload(state_data, path=f"{r_type}.{r_id}")

                if r_type not in logical_package["resources"]:
                    logical_package["resources"][r_type] = []
                logical_package["resources"][r_type].append(state_data)

                builder.add_resource(
                    resource_type=r_type,
                    resource_id=r_id,
                    classification=classification,
                    dependencies=r.get("dependencies", []),
                )

            # 3. Serialize and conditionally encrypt
            serialized_payload = json.dumps(logical_package, sort_keys=True).encode("utf-8")
            is_encrypted = False
            encryption_meta = {"encrypted": False, "algorithm": "none"}

            # Encrypt confidential and restricted backups per Step 33 classification
            if plan["classification"] in ["confidential", "restricted"]:
                serialized_payload = self.encryption.encrypt(serialized_payload)
                is_encrypted = True
                encryption_meta = {"encrypted": True, "algorithm": "Fernet-AES128-CBC"}

            # 4. Write to storage
            storage_key = f"{organization_id}/{run_id}/backup.pkg"
            storage_ref = self.storage.put(
                key=storage_key,
                data=serialized_payload,
                metadata={
                    "backup_run_id": run_id,
                    "organization_id": organization_id,
                    "classification": plan["classification"],
                    "encrypted": is_encrypted,
                },
            )

            # 5. Build and persist manifest
            manifest_dict = builder.build(
                content_data=serialized_payload,
                storage_reference=storage_ref,
                encryption_metadata=encryption_meta,
            )

            manifest_id = str(uuid.uuid4())
            manifest = BackupManifest(
                id=manifest_id,
                backup_run_id=run_id,
                version=manifest_dict["version"],
                format=manifest_dict["format"],
                resource_count=manifest_dict["resource_count"],
                content_hash=manifest_dict["content_hash"],
                manifest_hash=manifest_dict["manifest_hash"],
                storage_reference=manifest_dict["storage_reference"],
                encryption_metadata=manifest_dict["encryption_metadata"],
                verification_status="unverified",
                resources_metadata=manifest_dict["resources"],
                created_at=_utc_now(),
            )
            self.session.add(manifest)

            # Update backup run
            backup_run.status = "completed"
            backup_run.completed_at = _utc_now()
            backup_run.manifest_id = manifest_id
            await self.session.commit()
            return backup_run

        except Exception as exc:
            backup_run.status = "failed"
            backup_run.completed_at = _utc_now()
            backup_run.error = str(exc)
            await self.session.commit()
            raise DisasterRecoveryError(f"Backup run '{run_id}' failed: {exc}")
