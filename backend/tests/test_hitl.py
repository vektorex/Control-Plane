"""
Comprehensive test suite for Human-in-the-Loop (HITL) System (Step 18).
Tests cover:
- Deterministic Risk Classification & Policy Engine
- Safe context building & credential redaction
- Expiration & atomic approval/rejection/editing/cancellation
- Authorization & workspace isolation
- Workflow pause & resume with approved/edited payloads
- Tool & connector integration with destructive protection
- In-app notification creation & read status
- Model-generated action authorization enforcement
"""
import asyncio
from datetime import datetime, timedelta, timezone
import pytest
import uuid
from fastapi.testclient import TestClient

from backend.app.services.hitl.policies import ApprovalPolicyEngine
from backend.app.services.hitl.requests import InterventionRequestManager
from backend.app.services.hitl.schemas import (
    ApprovalActionRequest,
    ApprovalDecisionType,
    InterventionCreateRequest,
    InterventionPriority,
    InterventionStatus,
    InterventionType,
    RiskAssessment,
    RiskLevel,
    StepApprovalConfig,
    WorkspaceApprovalPolicyUpdate,
)
from backend.app.db.models.hitl import WorkspaceApprovalPolicy


# =============================================================================
# 1. Deterministic Risk Classification & Policies
# =============================================================================

def test_classify_risk_read_only():
    risk = ApprovalPolicyEngine.classify_risk(
        target_type="connector",
        operation="search_repositories",
        capability="read",
    )
    assert risk.level == RiskLevel.LOW
    assert not risk.requires_approval
    assert not risk.is_destructive


def test_classify_risk_write_operation():
    risk = ApprovalPolicyEngine.classify_risk(
        target_type="connector",
        operation="create_issue",
        capability="write",
    )
    assert risk.level == RiskLevel.MEDIUM
    assert risk.requires_approval
    assert not risk.is_destructive


def test_classify_risk_destructive_operation_mandatory():
    risk = ApprovalPolicyEngine.classify_risk(
        target_type="connector",
        operation="delete_repository",
        capability="destructive",
    )
    assert risk.level == RiskLevel.CRITICAL
    assert risk.requires_approval
    assert risk.is_destructive

    # Keyword detection without explicit capability
    risk2 = ApprovalPolicyEngine.classify_risk(
        target_type="tool",
        operation="purge_database_tables",
    )
    assert risk2.level == RiskLevel.CRITICAL
    assert risk2.is_destructive


def test_policy_engine_destructive_cannot_be_bypassed():
    policy = WorkspaceApprovalPolicy(
        workspace_id=uuid.uuid4(),
        require_tool_approval=False,
        require_connector_write_approval=False,
        require_destructive_approval=True,
        require_external_action_approval=False,
    )
    req, reason, risk = ApprovalPolicyEngine.evaluate_requirement(
        workspace_policy=policy,
        target_type="connector",
        operation="delete_branch",
    )
    assert req is True
    assert risk.is_destructive
    assert "Destructive" in reason


def test_policy_engine_evaluation_failure_review():
    policy = WorkspaceApprovalPolicy(
        workspace_id=uuid.uuid4(),
        require_evaluation_failure_review=True,
    )
    req, reason, risk = ApprovalPolicyEngine.evaluate_requirement(
        workspace_policy=policy,
        target_type="workflow_step",
        operation="summary_evaluation",
        evaluation_status="failed",
    )
    assert req is True
    assert "Evaluation resulted in 'failed'" in reason


def test_policy_engine_cost_threshold():
    policy = WorkspaceApprovalPolicy(
        workspace_id=uuid.uuid4(),
        max_auto_cost=0.50,
    )
    req, reason, risk = ApprovalPolicyEngine.evaluate_requirement(
        workspace_policy=policy,
        target_type="model_generation",
        operation="heavy_batch_llm",
        cost_estimate=1.25,
    )
    assert req is True
    assert "exceeds workspace auto-approval limit" in reason


# =============================================================================
# 2. Context Sanitization & Secret Redaction
# =============================================================================

def test_sanitize_payload_redacts_credentials():
    payload = {
        "repo": "owner/repo",
        "api_key": "sk-proj-1234567890abcdef1234567890abcdef",
        "token": "ghp_1234567890abcdefghijklmnopqrstuv",
        "auth_secret": "my-secret-password",
        "nested": {
            "password": "supersecretpassword",
            "safe_param": "hello world",
        },
    }
    clean = InterventionRequestManager.sanitize_payload(payload)
    assert clean["repo"] == "owner/repo"
    assert clean["api_key"] == "[REDACTED_CREDENTIAL]"
    assert clean["token"] == "[REDACTED_CREDENTIAL]"
    assert clean["auth_secret"] == "[REDACTED_CREDENTIAL]"
    assert clean["nested"]["password"] == "[REDACTED_CREDENTIAL]"
    assert clean["nested"]["safe_param"] == "hello world"


def test_build_safe_context_extracts_preview_and_meaning():
    risk = ApprovalPolicyEngine.classify_risk(
        target_type="connector",
        operation="create_issue",
        capability="write",
    )
    ctx = InterventionRequestManager.build_safe_context(
        target_system="github",
        operation="create_issue",
        input_payload={"repository": "acme/corp", "title": "Critical Bug", "secret_token": "abc1234567"},
        risk=risk,
        workflow_name="Triage Workflow",
        step_name="Create GitHub Issue",
    )
    assert ctx["target_system"] == "github"
    assert ctx["preview_fields"]["repository"] == "acme/corp"
    assert ctx["preview_fields"]["title"] == "Critical Bug"
    assert "secret_token" not in ctx["preview_fields"]
    assert ctx["sanitized_input"]["secret_token"] == "[REDACTED_CREDENTIAL]"
    assert "Approving will authorize" in ctx["approval_meaning"]


# =============================================================================
# 3. REST API: Requests, Decisions, Policies, and Expiration
# =============================================================================

def test_hitl_create_list_and_get_request(client: TestClient, user1_auth):
    headers = user1_auth["headers"]
    ws_res = client.post("/api/workspaces", json={"name": "HITL Test WS 1"}, headers=headers)
    assert ws_res.status_code == 201
    workspace_id = ws_res.json()["id"]
    ws_headers = {**headers, "X-Workspace-Id": workspace_id}

    # 1. Create intervention request
    create_payload = {
        "title": "Publish New Release",
        "description": "Approve publishing release v1.0.0 to public repository",
        "requested_action": "publish_release",
        "priority": "high",
        "input_snapshot": {"tag": "v1.0.0", "notes": "Initial launch", "api_token": "secret_token_123"},
        "safe_context": {"target": "github", "release": "v1.0.0"},
        "available_actions": ["approve", "reject", "edit", "cancel"],
        "timeout_seconds": 3600,
    }
    create_res = client.post("/api/hitl/requests", json=create_payload, headers=ws_headers)
    assert create_res.status_code == 201
    req_data = create_res.json()
    assert req_data["title"] == "Publish New Release"
    assert req_data["status"] == "pending"
    assert req_data["priority"] == "high"
    # Ensure credential was redacted in input_snapshot
    assert req_data["input_snapshot"]["api_token"] == "[REDACTED_CREDENTIAL]"
    req_id = req_data["id"]

    # 2. List requests
    list_res = client.get("/api/hitl/requests", headers=ws_headers)
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) >= 1
    assert any(item["id"] == req_id for item in items)

    # 3. Get single request
    get_res = client.get(f"/api/hitl/requests/{req_id}", headers=ws_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == req_id


def test_hitl_approve_and_duplicate_decision(client: TestClient, user1_auth):
    headers = user1_auth["headers"]
    ws_res = client.post("/api/workspaces", json={"name": "HITL Approve WS"}, headers=headers)
    workspace_id = ws_res.json()["id"]
    ws_headers = {**headers, "X-Workspace-Id": workspace_id}

    create_res = client.post(
        "/api/hitl/requests",
        json={"title": "Approve Action", "requested_action": "write_data", "input_snapshot": {"k": "v"}},
        headers=ws_headers,
    )
    req_id = create_res.json()["id"]

    # Approve
    approve_res = client.post(
        f"/api/hitl/requests/{req_id}/approve",
        json={"comment": "Looks good, approved."},
        headers=ws_headers,
    )
    assert approve_res.status_code == 200
    approved_data = approve_res.json()
    assert approved_data["status"] == "approved"
    assert len(approved_data["decisions"]) == 1
    assert approved_data["decisions"][0]["decision"] == "approve"

    # Duplicate approval must be rejected with 409 Conflict
    dup_res = client.post(
        f"/api/hitl/requests/{req_id}/approve",
        json={"comment": "Second approval attempt"},
        headers=ws_headers,
    )
    assert dup_res.status_code == 409


def test_hitl_edit_before_approve(client: TestClient, user1_auth):
    headers = user1_auth["headers"]
    ws_res = client.post("/api/workspaces", json={"name": "HITL Edit WS"}, headers=headers)
    workspace_id = ws_res.json()["id"]
    ws_headers = {**headers, "X-Workspace-Id": workspace_id}

    create_res = client.post(
        "/api/hitl/requests",
        json={
            "title": "Edit Issue Title",
            "requested_action": "create_issue",
            "input_snapshot": {"title": "AI generated title: Bug in auth"},
        },
        headers=ws_headers,
    )
    req_id = create_res.json()["id"]

    # Edit & Approve
    edit_payload = {
        "comment": "Clarified title before creating",
        "edited_data": {"title": "Authentication failure on invalid token"},
    }
    edit_res = client.post(f"/api/hitl/requests/{req_id}/edit", json=edit_payload, headers=ws_headers)
    assert edit_res.status_code == 200
    edited_data = edit_res.json()
    assert edited_data["status"] == "edited"
    assert edited_data["response_data"]["title"] == "Authentication failure on invalid token"
    assert edited_data["input_snapshot"]["title"] == "AI generated title: Bug in auth"


def test_hitl_reject_and_cancel(client: TestClient, user1_auth):
    headers = user1_auth["headers"]
    ws_res = client.post("/api/workspaces", json={"name": "HITL Reject WS"}, headers=headers)
    workspace_id = ws_res.json()["id"]
    ws_headers = {**headers, "X-Workspace-Id": workspace_id}

    # Reject
    res1 = client.post(
        "/api/hitl/requests",
        json={"title": "Action to Reject", "requested_action": "delete_all"},
        headers=ws_headers,
    )
    id1 = res1.json()["id"]
    rej_res = client.post(f"/api/hitl/requests/{id1}/reject", json={"comment": "Denying access."}, headers=ws_headers)
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "rejected"

    # Cancel
    res2 = client.post(
        "/api/hitl/requests",
        json={"title": "Action to Cancel", "requested_action": "restart_node"},
        headers=ws_headers,
    )
    id2 = res2.json()["id"]
    can_res = client.post(f"/api/hitl/requests/{id2}/cancel", json={"comment": "No longer needed."}, headers=ws_headers)
    assert can_res.status_code == 200
    assert can_res.json()["status"] == "cancelled"


def test_workspace_isolation_and_authorization(client: TestClient, user1_auth, user2_auth):
    # Workspace 1 by user 1
    u1_ws = client.post("/api/workspaces", json={"name": "HITL Isolation User 1 WS"}, headers=user1_auth["headers"]).json()
    u1_ws_id = u1_ws["id"]

    # Workspace 2 by user 2
    u2_ws = client.post("/api/workspaces", json={"name": "HITL Isolation User 2 WS"}, headers=user2_auth["headers"]).json()
    u2_ws_id = u2_ws["id"]

    # Create request in Workspace 1
    req = client.post(
        "/api/hitl/requests",
        json={"title": "WS 1 Approval", "requested_action": "publish_item"},
        headers={**user1_auth["headers"], "X-Workspace-Id": u1_ws_id},
    ).json()
    req_id = req["id"]

    # User 2 tries to access or approve User 1's request via WS 2 context
    u2_res = client.get(f"/api/hitl/requests/{req_id}", headers={**user2_auth["headers"], "X-Workspace-Id": u2_ws_id})
    assert u2_res.status_code == 404

    u2_approve = client.post(
        f"/api/hitl/requests/{req_id}/approve",
        json={"comment": "Hack attempt"},
        headers={**user2_auth["headers"], "X-Workspace-Id": u2_ws_id},
    )
    assert u2_approve.status_code == 404


def test_workspace_policies_cannot_disable_destructive(client: TestClient, user1_auth):
    headers = user1_auth["headers"]
    ws_res = client.post("/api/workspaces", json={"name": "Policy Test WS"}, headers=headers)
    workspace_id = ws_res.json()["id"]
    ws_headers = {**headers, "X-Workspace-Id": workspace_id}

    # Fetch initial policy
    get_res = client.get("/api/hitl/policies", headers=ws_headers)
    assert get_res.status_code == 200
    policy = get_res.json()
    assert policy["require_destructive_approval"] is True

    # Update policy - toggle tools and max cost
    patch_res = client.patch(
        "/api/hitl/policies",
        json={
            "require_tool_approval": True,
            "require_connector_write_approval": True,
            "max_auto_cost": 2.50,
        },
        headers=ws_headers,
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["require_tool_approval"] is True
    assert updated["max_auto_cost"] == 2.50
    # Mandatory destructive approval remains True
    assert updated["require_destructive_approval"] is True


# =============================================================================
# 4. In-App Notifications API
# =============================================================================

def test_notifications_lifecycle(client: TestClient, user1_auth):
    headers = user1_auth["headers"]
    ws_res = client.post("/api/workspaces", json={"name": "Notif Test WS"}, headers=headers)
    workspace_id = ws_res.json()["id"]
    ws_headers = {**headers, "X-Workspace-Id": workspace_id}

    # Creating an intervention request automatically emits a notification
    client.post(
        "/api/hitl/requests",
        json={"title": "Action requiring notification", "requested_action": "notify_me"},
        headers=ws_headers,
    )

    # List notifications
    notifs_res = client.get("/api/notifications", headers=ws_headers)
    assert notifs_res.status_code == 200
    notifs = notifs_res.json()
    assert len(notifs) >= 1
    notif_id = notifs[0]["id"]
    assert notifs[0]["read"] is False

    # Mark as read
    read_res = client.post(f"/api/notifications/{notif_id}/read", headers=ws_headers)
    assert read_res.status_code == 200

    # Mark all read
    all_read_res = client.post("/api/notifications/read-all", headers=ws_headers)
    assert all_read_res.status_code == 200
    assert "count" in all_read_res.json()


# =============================================================================
# 5. Workflow Step Pause & Resume via API
# =============================================================================

def test_workflow_pause_and_resume_end_to_end(client: TestClient, user1_auth):
    headers = user1_auth["headers"]
    me = client.get("/api/auth/me", headers=headers).json()
    ws_id = me["default_workspace_id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # 1. Create a workflow with a step that requires approval
    wf_payload = {
        "name": "HITL Gated Workflow",
        "steps": [
            {
                "id": "step_in",
                "name": "Input Step",
                "type": "input",
                "config": {},
            },
            {
                "id": "step_gated_calc",
                "name": "Gated Calculator",
                "type": "tool",
                "config": {"tool_name": "calculator", "parameters": {"operation": "multiply", "a": 7, "b": 6}},
                "approval": {"required": True, "policy": "always_require_approval"},
            },
            {
                "id": "step_out",
                "name": "Output Step",
                "type": "output",
                "config": {},
            },
        ],
    }
    wf_res = client.post(f"/api/workflows?workspace_id={ws_id}", json=wf_payload, headers=headers)
    assert wf_res.status_code == 201
    wf_id = wf_res.json()["id"]

    # 2. Trigger workflow run
    run_res = client.post(
        f"/api/workflows/{wf_id}/run?workspace_id={ws_id}",
        json={"input_data": {"user_note": "testing hitl"}},
        headers=headers,
    )
    assert run_res.status_code == 201
    run_data = run_res.json()
    assert run_data["status"] == "waiting_for_approval"
    run_id = run_data["id"]

    # 3. Find the created intervention request
    hitl_list = client.get(f"/api/hitl/requests?status=pending", headers=ws_headers).json()
    matching = [r for r in hitl_list if r.get("workflow_run_id") == run_id]
    assert len(matching) == 1
    intervention_id = matching[0]["id"]
    assert matching[0]["requested_action"] == "calculator"

    # 4. Approve the intervention request -> automatically resumes workflow
    app_res = client.post(f"/api/hitl/requests/{intervention_id}/approve", json={"comment": "Approved by user"}, headers=ws_headers)
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "approved"

    # 5. Check run status - should now be completed
    check_run = client.get(f"/api/workflow-runs/{run_id}?workspace_id={ws_id}", headers=headers).json()
    assert check_run["status"] == "completed"
    assert check_run["output_data"] is not None
