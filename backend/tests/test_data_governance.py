"""
Comprehensive unit and integration test suite for Step 33: Data Governance, Privacy & Compliance Evidence Layer.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app.services.data_governance.classification import DataClassificationService
from backend.app.services.data_governance.deletion import SafeDeletionEngine
from backend.app.services.data_governance.evidence import ComplianceEvidenceService, compute_evidence_hash, canonical_json
from backend.app.services.data_governance.exceptions import (
    DataAssetNotFoundError,
    DeletionBlockedError,
    ExportSanitizationError,
    InvalidLineageError,
    LegalHoldActiveError,
    UnauthorizedClassificationDowngradeError,
)
from backend.app.services.data_governance.export import DataExportEngine
from backend.app.services.data_governance.inventory import DataInventoryService
from backend.app.services.data_governance.legal_hold import LegalHoldService
from backend.app.services.data_governance.lineage import DataLineageService
from backend.app.services.data_governance.models import (
    ComplianceEvidence,
    DataAsset,
    DeletionRequest,
    ExportRequest,
    LegalHold,
    PrivacyRequest,
    RetentionPolicy,
)
from backend.app.services.data_governance.policy_evidence import PolicyEvidenceRecorder
from backend.app.services.data_governance.privacy_requests import PrivacyRequestService
from backend.app.services.data_governance.redaction import (
    detect_findings,
    mask_preview,
    sanitize_payload,
    sanitize_text,
)
from backend.app.services.data_governance.repository import DataGovernanceRepository
from backend.app.services.data_governance.retention import RetentionPolicyEngine
from backend.app.services.data_governance.schemas import (
    DataAssetCreate,
    DeletionRequestCreate,
    ExportRequestCreate,
    LegalHoldCreate,
    LineageEdgeCreate,
    PrivacyRequestCreate,
    RetentionPolicyCreate,
)
from backend.app.services.data_governance.service import DataGovernanceService
from backend.app.services.data_governance.validators import (
    validate_classification_transition,
    validate_export_scope,
    validate_not_under_legal_hold,
)


def _org() -> str:
    return "10000000-0000-0000-0000-000000000001"


def _ws() -> str:
    return "20000000-0000-0000-0000-000000000002"


def _user() -> str:
    return "30000000-0000-0000-0000-000000000003"


# ---------------------------------------------------------------------------
# Redaction & PII / Secret Detection Tests
# ---------------------------------------------------------------------------

def test_detect_email():
    text = "Contact us at support@example.com for queries."
    findings = detect_findings(text)
    assert len(findings) == 1
    assert findings[0]["finding_type"] == "email"
    assert findings[0]["is_personal_data"] is True
    assert "su***@example.com" in findings[0]["preview"]
    assert findings[0]["fingerprint"] is not None


def test_detect_phone():
    text = "Call customer support at +1 (555) 123-4567 today."
    findings = detect_findings(text)
    assert len(findings) == 1
    assert findings[0]["finding_type"] == "phone"
    assert findings[0]["is_personal_data"] is True
    assert "***-***-4567" in findings[0]["preview"]


def test_detect_secrets_openai():
    secret = "sk-" + "a" * 32
    text = f"My key is {secret}."
    findings = detect_findings(text)
    assert len(findings) == 1
    assert findings[0]["finding_type"] == "api_key_openai"
    assert findings[0]["is_secret"] is True
    assert findings[0]["preview"] != secret
    assert secret not in findings[0]["preview"]


def test_detect_secrets_aws():
    text = "Key: AKIAIOSFODNN7EXAMPLE"
    findings = detect_findings(text)
    assert len(findings) == 1
    assert findings[0]["finding_type"] == "api_key_aws"
    assert findings[0]["is_secret"] is True


def test_sanitize_text():
    text = "User john@example.com used sk-abcdefghijklmnopqrstuvwxyz123456 to login from 192.168.1.1"
    sanitized = sanitize_text(text)
    assert "john@example.com" not in sanitized
    assert "[EMAIL_REDACTED]" in sanitized
    assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in sanitized
    assert "[SECRET_REDACTED]" in sanitized
    assert "192.168.1.1" not in sanitized
    assert "[IP_REDACTED]" in sanitized


def test_sanitize_payload_recursive():
    payload = {
        "user": {"email": "test@example.com", "api_key": "super_secret_123"},
        "logs": ["Failed attempt with token bearer_token_xyz"],
        "safe_int": 42,
    }
    scrubbed = sanitize_payload(payload)
    assert scrubbed["user"]["api_key"] == "[REDACTED]"
    assert scrubbed["safe_int"] == 42


# ---------------------------------------------------------------------------
# Validation Tests
# ---------------------------------------------------------------------------

def test_validate_classification_transition_downgrade_blocked():
    with pytest.raises(UnauthorizedClassificationDowngradeError):
        validate_classification_transition(
            current_classification="restricted",
            target_classification="internal",
            detected_by="rule",
            is_admin=False,
        )


def test_validate_classification_transition_downgrade_allowed_for_admin():
    # Should not raise exception
    validate_classification_transition(
        current_classification="restricted",
        target_classification="internal",
        detected_by="user_confirmed",
        is_admin=True,
    )


def test_validate_classification_transition_upgrade_allowed():
    # Upgrading internal to confidential is always permitted
    validate_classification_transition(
        current_classification="internal",
        target_classification="confidential",
        detected_by="rule",
        is_admin=False,
    )


def test_validate_not_under_legal_hold():
    with pytest.raises(LegalHoldActiveError):
        validate_not_under_legal_hold("asset-1", ["Hold Alpha", "Hold Beta"])


def test_validate_export_scope():
    validate_export_scope("workspace", "ws-123")
    with pytest.raises(ExportSanitizationError):
        validate_export_scope("workspace", "../../../etc/passwd")


# ---------------------------------------------------------------------------
# Evidence Hash Chaining Tests
# ---------------------------------------------------------------------------

def test_compute_evidence_hash_determinism():
    c1 = canonical_json({"a": 1, "b": "test"})
    c2 = canonical_json({"b": "test", "a": 1})
    assert c1 == c2

    h1 = compute_evidence_hash(None, c1)
    h2 = compute_evidence_hash(None, c2)
    assert h1 == h2

    h3 = compute_evidence_hash("PREV_HASH", c1)
    assert h3 != h1


@pytest.mark.asyncio
async def test_evidence_service_chaining():
    session = AsyncMock()
    evidence_svc = ComplianceEvidenceService(session)

    # Mock get_latest_hash returning None initially
    evidence_svc.get_latest_hash = AsyncMock(return_value=None)

    rec1 = await evidence_svc.record_evidence(
        organization_id=_org(),
        evidence_type="governance_decision",
        subject_type="task",
        subject_id="task-1",
        action="allow",
        result="success",
    )
    assert rec1.previous_evidence_hash is None
    assert rec1.evidence_hash is not None

    # Next record in chain
    evidence_svc.get_latest_hash = AsyncMock(return_value=rec1.evidence_hash)
    rec2 = await evidence_svc.record_evidence(
        organization_id=_org(),
        evidence_type="deletion",
        subject_type="asset",
        subject_id="asset-1",
        action="delete",
        result="completed",
    )
    assert rec2.previous_evidence_hash == rec1.evidence_hash


@pytest.mark.asyncio
async def test_policy_evidence_recorder():
    session = AsyncMock()
    recorder = PolicyEvidenceRecorder(session)
    recorder.evidence_service.record_evidence = AsyncMock()

    await recorder.record_governance_decision(
        organization_id=_org(),
        governance_decision_id="dec-123",
        decision="deny",
        reasons=["Blocked frontier model"],
        matched_policies=["pol-1"],
        enforcement_point="task_execution",
        subject_type="task",
        subject_id="task-1",
    )

    recorder.evidence_service.record_evidence.assert_called_once()
    args, kwargs = recorder.evidence_service.record_evidence.call_args
    assert kwargs["evidence_type"] == "governance_decision"
    assert kwargs["result"] == "deny"
    assert kwargs["governance_decision_id"] == "dec-123"


# ---------------------------------------------------------------------------
# Data Inventory Service Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_inventory_register_asset():
    session = AsyncMock()
    # Mock no existing asset
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_res

    inv_svc = DataInventoryService(session)
    data = DataAssetCreate(
        name="Quarterly Report PDF",
        asset_type="document",
        resource_type="document",
        resource_id="doc-999",
        owner_id=_user(),
        data_classification="confidential",
        storage_location="logical:s3/reports",
    )

    asset = await inv_svc.register_asset(
        organization_id=_org(),
        data=data,
        sample_content="User contact is ceo@company.com with budget $50,000",
    )

    assert asset.name == "Quarterly Report PDF"
    assert asset.contains_personal_data is True
    session.add.assert_called()


# ---------------------------------------------------------------------------
# Data Lineage Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_lineage_self_loop_rejected():
    session = AsyncMock()
    lineage_svc = DataLineageService(session)
    edge_data = LineageEdgeCreate(
        source_asset_id="asset-1",
        target_asset_id="asset-1",
        relationship_type="derived_from",
        transformation_type="direct",
    )
    with pytest.raises(InvalidLineageError):
        await lineage_svc.add_edge(_org(), edge_data)


# ---------------------------------------------------------------------------
# Retention Policy Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_retention_policy_create_and_resolve():
    session = AsyncMock()
    ret_engine = RetentionPolicyEngine(session)

    policy_data = RetentionPolicyCreate(
        name="Short-term Runs Policy",
        resource_type="run",
        retention_days=30,
        action="delete",
        grace_period_days=7,
        workspace_id=_ws(),
    )

    policy = await ret_engine.create_policy(_org(), _user(), policy_data)
    assert policy.retention_days == 30
    assert policy.action == "delete"

    # Test resolution
    asset = DataAsset(
        id="run-asset-1",
        organization_id=_org(),
        workspace_id=_ws(),
        resource_type="run",
        retention_policy_id=None,
        status="active",
        created_at=datetime.now(timezone.utc) - timedelta(days=40),
    )

    ret_engine.get_policy = AsyncMock(return_value=policy)
    resolved = await ret_engine.resolve_policy_for_asset(asset)
    assert resolved is not None


# ---------------------------------------------------------------------------
# Legal Hold Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_legal_hold_lifecycle():
    session = AsyncMock()
    hold_svc = LegalHoldService(session)
    hold_svc.evidence_service.record_evidence = AsyncMock()

    mock_res_ast = MagicMock()
    mock_res_ast.scalar_one_or_none.return_value = "asset-1"
    session.execute.return_value = mock_res_ast

    hold_data = LegalHoldCreate(
        name="Litigation Hold 2026",
        reason="Preserve all logs and documents for Case #441",
        asset_ids=["asset-1", "asset-2"],
    )

    hold = await hold_svc.create_hold(_org(), _user(), hold_data)
    assert hold.name == "Litigation Hold 2026"
    assert hold.status == "active"

    # Setup session.execute for release_hold query
    mock_res_hold = MagicMock()
    mock_res_hold.scalar_one_or_none.return_value = hold
    session.execute.return_value = mock_res_hold

    # Release
    released_hold = await hold_svc.release_hold(hold.id, _org(), _user(), reason="Settlement reached")
    assert released_hold.status == "released"
    assert released_hold.released_at is not None


# ---------------------------------------------------------------------------
# Safe Deletion Engine Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_deletion_blocked_by_legal_hold():
    session = AsyncMock()
    deletion_engine = SafeDeletionEngine(session)
    deletion_engine.legal_hold_service.get_active_holds_for_asset = AsyncMock(
        return_value=["Hold Alpha"]
    )
    deletion_engine.evidence_service.record_evidence = AsyncMock()

    del_create = DeletionRequestCreate(
        scope_type="asset",
        scope_id="asset-1",
        reason="User requested GDPR deletion",
    )

    req = await deletion_engine.create_deletion_request(_org(), _user(), del_create)
    assert req.status == "blocked"
    assert "Hold Alpha" in req.error


@pytest.mark.asyncio
async def test_deletion_execution_success():
    session = AsyncMock()
    deletion_engine = SafeDeletionEngine(session)
    deletion_engine.legal_hold_service.is_asset_under_hold = AsyncMock(return_value=False)
    deletion_engine.evidence_service.record_evidence = AsyncMock()

    asset = DataAsset(
        id="asset-delete-me",
        organization_id=_org(),
        workspace_id=_ws(),
        status="active",
        resource_type="document",
        resource_id="doc-1",
    )

    req = DeletionRequest(
        id="del-req-1",
        organization_id=_org(),
        workspace_id=_ws(),
        requested_by=_user(),
        scope_type="asset",
        scope_id="asset-delete-me",
        status="requested",
    )

    mock_res_req = MagicMock()
    mock_res_req.scalar_one_or_none.return_value = req

    mock_res_ast = MagicMock()
    mock_res_ast.scalar_one_or_none.return_value = asset

    session.execute.side_effect = [mock_res_req, mock_res_ast]

    completed_req = await deletion_engine.execute_deletion("del-req-1", _org(), _user())
    assert completed_req.status == "completed"
    assert completed_req.verification_status == "verified"
    assert asset.status == "deleted"
    assert asset.deleted_at is not None


# ---------------------------------------------------------------------------
# Data Export Engine Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_export_engine_sanitization():
    session = AsyncMock()
    export_engine = DataExportEngine(session)
    export_engine.evidence_service.record_evidence = AsyncMock()

    req = ExportRequest(
        id="exp-1",
        organization_id=_org(),
        workspace_id=_ws(),
        requested_by=_user(),
        scope_type="workspace",
        scope_id=_ws(),
        format="json",
        status="requested",
    )

    asset = DataAsset(
        id="asset-export-1",
        organization_id=_org(),
        workspace_id=_ws(),
        name="Sensitive Customer Data",
        description="Contains customer email test@example.com and key sk-12345678901234567890",
        asset_type="document",
        resource_type="document",
        resource_id="doc-77",
        data_classification="confidential",
        owner_id=_user(),
        source_type="direct",
        storage_location="logical:db",
        status="active",
    )

    mock_res_req = MagicMock()
    mock_res_req.scalar_one_or_none.return_value = req

    mock_res_asts = MagicMock()
    mock_res_asts.scalars.return_value.all.return_value = [asset]

    session.execute.side_effect = [mock_res_req, mock_res_asts]

    completed_req, content = await export_engine.execute_export("exp-1", _org())
    assert completed_req.status == "completed"
    assert "sk-12345678901234567890" not in content
    assert "[SECRET_REDACTED]" in content
    assert completed_req.manifest["sanitized"] is True
    assert completed_req.manifest["asset_count"] == 1


# ---------------------------------------------------------------------------
# Privacy Request Service Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_privacy_request_workflow():
    session = AsyncMock()
    privacy_svc = PrivacyRequestService(session)
    privacy_svc.evidence_service.record_evidence = AsyncMock()

    req_data = PrivacyRequestCreate(
        request_type="access",
        scope="user",
        workspace_id=_ws(),
    )

    req = await privacy_svc.create_request(_org(), _user(), req_data)
    assert req.status == "pending"
    assert req.verification_status == "unverified"

    # Verify
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = req
    session.execute.return_value = mock_res

    verified = await privacy_svc.verify_request(req.id, _org(), _user(), "verified")
    assert verified.status == "in_review"
    assert verified.verification_status == "verified"

    # Complete
    completed = await privacy_svc.complete_request(req.id, _org(), _user())
    assert completed.status == "completed"


# ---------------------------------------------------------------------------
# FastAPI Router Endpoints Tests
# ---------------------------------------------------------------------------

def test_api_overview_endpoint(auth_client):
    with patch("backend.app.services.data_governance.service.DataGovernanceService.get_overview") as mock_ov:
        mock_ov.return_value = MagicMock(
            total_assets=42,
            classification_counts={"internal": 30, "confidential": 12},
            active_legal_holds=1,
            pending_deletions=0,
            pending_privacy_requests=2,
            recent_evidence_count=150,
            assets_with_findings=3,
            evidence_chain_valid=True,
        )
        response = auth_client.get("/api/data-governance/overview")
        assert response.status_code == 200
        data = response.json()
        assert data["total_assets"] == 42
        assert data["evidence_chain_valid"] is True


def test_api_reports_retention_endpoint(auth_client):
    with patch("backend.app.services.data_governance.service.DataGovernanceService.get_retention_report") as mock_rep:
        mock_rep.return_value = MagicMock(
            total_policies=3,
            policies_by_action={"delete": 2, "retain": 1},
            assets_expiring_soon=5,
            assets_expired=1,
        )
        response = auth_client.get("/api/data-governance/reports/retention")
        assert response.status_code == 200
        data = response.json()
        assert data["total_policies"] == 3


def test_api_assets_list_endpoint(auth_client):
    with patch("backend.app.services.data_governance.inventory.DataInventoryService.list_assets") as mock_list:
        mock_list.return_value = []
        response = auth_client.get("/api/data-governance/assets")
        assert response.status_code == 200
        assert response.json() == []
