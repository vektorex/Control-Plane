"""
Comprehensive Unit & Integration Test Suite for Step 36:
Disaster Recovery, Backup & Business Continuity Layer.
"""
import json
import os
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.services.disaster_recovery.exceptions import (
    CrossTenantRestoreBlockedError,
    ElevatedAuthorizationRequiredError,
    ReplaceExistingNotPermittedError,
    ProductionExerciseBlockedError,
    DeletedDataResurrectionBlockedError,
    LegalHoldConflictError,
    ManifestTamperedError,
    BackupIntegrityError,
    StorageProviderError,
    DisasterRecoveryError,
)
from backend.app.services.disaster_recovery.validators import (
    validate_tenant_restore_boundary,
    validate_no_secrets_in_backup_payload,
    validate_replace_existing_conflict_policy,
    validate_production_exercise_safety,
    validate_restore_data_lifecycle,
)
from backend.app.services.disaster_recovery.storage import (
    LocalBackupStorageProvider,
    BackupEncryptionProvider,
)
from backend.app.services.disaster_recovery.manifest import (
    ManifestBuilder,
    calculate_content_hash,
    calculate_manifest_hash,
)
from backend.app.services.disaster_recovery.integrity import BackupIntegrityService
from backend.app.services.disaster_recovery.dependencies import (
    sort_resources_by_dependencies,
    resolve_recovery_service_order,
)
from backend.app.services.disaster_recovery.backup_planner import (
    resolve_highest_classification,
    BackupPlanner,
)


def _uuid() -> str:
    return str(uuid.uuid4())


# ===========================================================================
# 1. Security & Validation Tests
# ===========================================================================
def test_cross_tenant_restore_is_strictly_blocked():
    """Verify cross-tenant restore attempts are immediately rejected."""
    with pytest.raises(CrossTenantRestoreBlockedError):
        validate_tenant_restore_boundary(
            backup_org_id="org-alpha-123",
            target_org_id="org-bravo-456",
            target_environment="sandbox",
        )


def test_same_tenant_restore_permitted():
    """Verify same-tenant restore passes validation."""
    validate_tenant_restore_boundary(
        backup_org_id="org-alpha-123",
        target_org_id="org-alpha-123",
        target_environment="production",
    )


def test_plaintext_secrets_in_backup_blocked():
    """Verify plaintext API keys and credentials raise an error during backup serialization."""
    payload_with_secret = {
        "workspace_id": "ws-1",
        "api_key": "sk-secret-live-12345",
    }
    with pytest.raises(DisasterRecoveryError) as exc_info:
        validate_no_secrets_in_backup_payload(payload_with_secret)
    assert "Plaintext secret detected" in str(exc_info.value)


def test_safe_secret_references_permitted():
    """Verify vault references and redacted values pass secret validation."""
    payload_with_ref = {
        "workspace_id": "ws-1",
        "api_key": "vault://credentials/openai/production",
        "password": "[REDACTED_BY_STEP_36]",
    }
    validate_no_secrets_in_backup_payload(payload_with_ref)


def test_replace_existing_requires_admin_role():
    """Verify non-admin roles cannot request replace_existing conflict policy."""
    with pytest.raises(ElevatedAuthorizationRequiredError):
        validate_replace_existing_conflict_policy(
            conflict_policy="replace_existing",
            user_role="member",
            has_hitl_approval=False,
        )


def test_replace_existing_requires_hitl_approval():
    """Verify admin role without HITL approval cannot execute replace_existing."""
    with pytest.raises(ReplaceExistingNotPermittedError):
        validate_replace_existing_conflict_policy(
            conflict_policy="replace_existing",
            user_role="admin",
            has_hitl_approval=False,
        )


def test_replace_existing_permitted_with_admin_and_hitl():
    """Verify admin role with HITL approval is permitted."""
    validate_replace_existing_conflict_policy(
        conflict_policy="replace_existing",
        user_role="admin",
        has_hitl_approval=True,
    )


def test_production_exercise_blocked_without_clearance():
    """Verify production disaster exercises are rejected by default."""
    with pytest.raises(ProductionExerciseBlockedError):
        validate_production_exercise_safety(
            environment="production",
            has_governance_approval=False,
            has_hitl_approval=False,
        )


def test_sandbox_exercise_permitted():
    """Verify sandbox exercises are permitted without production clearance."""
    validate_production_exercise_safety(environment="sandbox")


def test_deleted_data_resurrection_blocked():
    """Verify data legally deleted under Step 33 cannot be silently resurrected."""
    with pytest.raises(DeletedDataResurrectionBlockedError):
        validate_restore_data_lifecycle(
            resource_id="doc-deleted-999",
            is_legally_deleted=True,
            is_under_legal_hold=False,
            mode="sandbox",
        )


def test_legal_hold_blocks_non_sandbox_restore():
    """Verify active legal holds prevent non-sandbox restoration mutations."""
    with pytest.raises(LegalHoldConflictError):
        validate_restore_data_lifecycle(
            resource_id="asset-held-123",
            is_legally_deleted=False,
            is_under_legal_hold=True,
            mode="authorized_restore",
        )


# ===========================================================================
# 2. Storage & Encryption Tests
# ===========================================================================
def test_local_storage_put_get_delete(tmp_path):
    """Verify local filesystem storage provider operations."""
    provider = LocalBackupStorageProvider(base_path=str(tmp_path))
    data = b"Simulated backup payload content for disaster recovery test"
    key = "org-test/run-1/backup.pkg"

    ref = provider.put(key, data, metadata={"backup_id": "run-1"})
    assert ref.startswith("local://")
    assert provider.exists(key) is True

    retrieved = provider.get(key)
    assert retrieved == data

    meta = provider.get_metadata(key)
    assert meta.get("backup_id") == "run-1"

    deleted = provider.delete(key)
    assert deleted is True
    assert provider.exists(key) is False


def test_storage_path_traversal_blocked(tmp_path):
    """Verify path traversal sequences are detected and rejected."""
    provider = LocalBackupStorageProvider(base_path=str(tmp_path))
    with pytest.raises(StorageProviderError):
        provider.put("../../etc/passwd", b"malicious")


def test_backup_encryption_roundtrip():
    """Verify Fernet encryption provider roundtrip for confidential backups."""
    enc = BackupEncryptionProvider(key=b"test-32-byte-secret-key-123456789012")
    data = json.dumps({"resource": "customer_database", "records": 500}).encode("utf-8")

    token = enc.encrypt(data)
    assert token != data
    assert enc.is_encrypted(token) is True

    decrypted = enc.decrypt(token)
    assert decrypted == data


# ===========================================================================
# 3. Manifest & Cryptographic Integrity Tests
# ===========================================================================
def test_manifest_builder_and_hashing():
    """Verify manifest creation and deterministic hash generation."""
    builder = ManifestBuilder(
        backup_run_id="run-test-1",
        organization_id="org-test",
    )
    builder.add_resource(
        resource_type="workflow",
        resource_id="wf-100",
        classification="internal",
    )
    content = b"logical payload contents"
    manifest = builder.build(content_data=content, storage_reference="local://pkg")

    assert manifest["resource_count"] == 1
    assert manifest["content_hash"] == calculate_content_hash(content)
    assert "manifest_hash" in manifest


def test_integrity_service_detects_tampered_manifest():
    """Verify integrity service flags tampered manifest."""
    storage_mock = MagicMock()
    service = BackupIntegrityService(storage_mock)

    manifest = {
        "backup_run_id": "run-1",
        "version": "1.0",
        "format": "json_logical",
        "resource_count": 1,
        "content_hash": "abc",
        "manifest_hash": "falsified_hash_value",
        "resources": [],
    }
    ok, msg = service.verify_manifest(manifest)
    assert ok is False
    assert "mismatch" in msg


def test_integrity_service_detects_content_mismatch():
    """Verify integrity service flags content hash mismatch."""
    storage_mock = MagicMock()
    service = BackupIntegrityService(storage_mock)

    manifest = {"content_hash": "expected_hash_value"}
    ok, msg = service.verify_content(b"different content", manifest)
    assert ok is False
    assert "mismatch" in msg


# ===========================================================================
# 4. Dependency Resolution & Ordering Tests
# ===========================================================================
def test_resource_topological_sorting():
    """Verify resources are sorted according to dependency hierarchy."""
    resources = [
        {"resource_type": "workflow", "resource_id": "wf-1", "dependencies": ["doc-1"]},
        {"resource_type": "document", "resource_id": "doc-1", "dependencies": []},
        {"resource_type": "organization", "resource_id": "org-1", "dependencies": []},
        {"resource_type": "job", "resource_id": "job-1", "dependencies": ["wf-1"]},
    ]
    sorted_res = sort_resources_by_dependencies(resources)
    order = [r["resource_id"] for r in sorted_res]

    # Organization before documents, documents before workflows, workflows before jobs
    assert order.index("org-1") < order.index("job-1")
    assert order.index("doc-1") < order.index("wf-1")
    assert order.index("wf-1") < order.index("job-1")


def test_recovery_service_order_resolution():
    """Verify critical service restoration order follows architectural dependencies."""
    services = ["notifications", "database", "workflows", "authentication", "governance"]
    order = resolve_recovery_service_order(services)

    assert order.index("database") < order.index("authentication")
    assert order.index("authentication") < order.index("governance")
    assert order.index("database") < order.index("workflows")
    assert order.index("database") < order.index("notifications")


def test_resolve_highest_classification():
    """Verify classification inheritance propagates to highest tier."""
    assert resolve_highest_classification(["public", "internal"]) == "internal"
    assert resolve_highest_classification(["internal", "confidential"]) == "confidential"
    assert resolve_highest_classification(["internal", "restricted", "public"]) == "restricted"
