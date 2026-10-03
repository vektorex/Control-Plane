"""
Manifest creation, serialization, and cryptographic hashing for Step 36: Disaster Recovery.
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.services.disaster_recovery.validators import validate_no_secrets_in_backup_payload


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def calculate_content_hash(data: bytes) -> str:
    """Compute SHA-256 hash of raw or serialized backup content."""
    return hashlib.sha256(data).hexdigest()


def calculate_manifest_hash(manifest_payload: Dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hash of manifest structure excluding volatile fields."""
    canonical_payload = {
        "backup_run_id": manifest_payload.get("backup_run_id"),
        "version": manifest_payload.get("version"),
        "format": manifest_payload.get("format"),
        "resource_count": manifest_payload.get("resource_count"),
        "content_hash": manifest_payload.get("content_hash"),
        "resources": manifest_payload.get("resources", []),
        "encryption_metadata": manifest_payload.get("encryption_metadata", {}),
    }
    serialized = json.dumps(canonical_payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


class ManifestBuilder:
    """
    Constructs a cryptographic manifest describing all resources contained in a backup snapshot.
    """

    def __init__(
        self,
        backup_run_id: str,
        organization_id: str,
        version: str = "1.0",
        format_type: str = "json_logical",
    ):
        self.backup_run_id = backup_run_id
        self.organization_id = organization_id
        self.version = version
        self.format_type = format_type
        self.resources: List[Dict[str, Any]] = []

    def add_resource(
        self,
        resource_type: str,
        resource_id: str,
        classification: str = "internal",
        version: str = "1.0",
        dependencies: Optional[List[str]] = None,
        content_hash: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record resource entry in manifest. Validates that no plaintext secrets exist in metadata.
        """
        clean_metadata = metadata or {}
        validate_no_secrets_in_backup_payload(clean_metadata, path=f"{resource_type}.{resource_id}")

        entry = {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "tenant": self.organization_id,
            "classification": classification,
            "version": version,
            "dependencies": dependencies or [],
            "content_hash": content_hash or hashlib.sha256(f"{resource_type}:{resource_id}".encode("utf-8")).hexdigest(),
            "created_at": created_at or _utc_now_iso(),
            "updated_at": updated_at or _utc_now_iso(),
            "metadata": clean_metadata,
        }
        self.resources.append(entry)

    def build(
        self,
        content_data: bytes,
        storage_reference: str,
        encryption_metadata: Optional[Dict[str, Any]] = None,
        previous_manifest_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Produce finalized manifest dictionary with computed hashes.
        """
        content_hash = calculate_content_hash(content_data)
        manifest_payload = {
            "backup_run_id": self.backup_run_id,
            "organization_id": self.organization_id,
            "version": self.version,
            "format": self.format_type,
            "created_at": _utc_now_iso(),
            "resource_count": len(self.resources),
            "content_hash": content_hash,
            "previous_manifest_hash": previous_manifest_hash,
            "storage_reference": storage_reference,
            "encryption_metadata": encryption_metadata or {"encrypted": False, "algorithm": "none"},
            "resources": self.resources,
        }
        manifest_hash = calculate_manifest_hash(manifest_payload)
        manifest_payload["manifest_hash"] = manifest_hash
        return manifest_payload
