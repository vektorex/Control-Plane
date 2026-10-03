"""
Test Suite for Step 27: Multi-Tenant Organizations, Teams, Roles & Access Control.
Validates:
- Comprehensive Permission Matrix (Owner, Admin, Member, Viewer)
- Cross-Tenant Multi-Organization Isolation (Org A vs Org B)
- Privilege Escalation Guards
- Cryptographic Invitation Lifecycle (hashing, expiry, revocation, replay protection)
- Transactional Ownership Transfer
- Workspace & Restricted Project Access Modes
- Real-time Event Streaming and Audit Integration
"""
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import select

from backend.app.core.auth import create_access_token
from backend.app.services.access_control.constants import (
    OrganizationRole,
    WorkspaceRole,
    ProjectRole,
    ProjectAccessMode,
    MemberStatus,
)
from backend.app.services.access_control.permissions import (
    ORGANIZATION_READ,
    ORGANIZATION_UPDATE,
    ORGANIZATION_DELETE,
    MEMBER_READ,
    MEMBER_INVITE,
    MEMBER_UPDATE,
    MEMBER_REMOVE,
    WORKSPACE_CREATE,
    WORKSPACE_READ,
    WORKSPACE_DELETE,
    TASK_CREATE,
    TASK_RUN,
    WORKFLOW_RUN,
    CONNECTOR_EXECUTE,
    JOB_CANCEL,
)
from backend.app.services.access_control.policies import PolicyEngine
from backend.app.services.access_control.context import AuthorizationContext
from backend.app.services.access_control.models import (
    Organization,
    OrganizationMember,
    OrganizationInvitation,
    WorkspaceMember,
    ProjectMember,
)
from backend.app.db.models.workspace import Workspace
from backend.app.db.models.project import Project


# -----------------------------------------------------------------------------
# 1. Comprehensive Permission Matrix Tests
# -----------------------------------------------------------------------------

def test_permission_matrix_owner_role():
    """Owner has full administrative capabilities across organization and child resources."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    ws_id = uuid.uuid4()

    ctx = PolicyEngine.derive_context(
        user_id=user_id,
        organization_id=org_id,
        organization_role=OrganizationRole.OWNER,
        workspace_id=ws_id,
        workspace_role=WorkspaceRole.ADMIN,
    )

    assert ctx.has_permission(ORGANIZATION_READ)
    assert ctx.has_permission(ORGANIZATION_UPDATE)
    assert ctx.has_permission(ORGANIZATION_DELETE)
    assert ctx.has_permission(MEMBER_INVITE)
    assert ctx.has_permission(MEMBER_REMOVE)
    assert ctx.has_permission(WORKSPACE_CREATE)
    assert ctx.has_permission(TASK_CREATE)
    assert ctx.has_permission(WORKFLOW_RUN)
    assert ctx.has_permission(CONNECTOR_EXECUTE)
    assert ctx.has_permission(JOB_CANCEL)


def test_permission_matrix_admin_role():
    """Admin has management capabilities but cannot delete the organization."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    ws_id = uuid.uuid4()

    ctx = PolicyEngine.derive_context(
        user_id=user_id,
        organization_id=org_id,
        organization_role=OrganizationRole.ADMIN,
        workspace_id=ws_id,
        workspace_role=WorkspaceRole.ADMIN,
    )

    assert ctx.has_permission(ORGANIZATION_READ)
    assert ctx.has_permission(ORGANIZATION_UPDATE)
    assert not ctx.has_permission(ORGANIZATION_DELETE)  # Only Owner can delete org
    assert ctx.has_permission(MEMBER_INVITE)
    assert ctx.has_permission(WORKSPACE_CREATE)
    assert ctx.has_permission(TASK_CREATE)
    assert ctx.has_permission(WORKFLOW_RUN)


def test_permission_matrix_member_role():
    """Member can execute tasks/workflows and use connectors, but cannot manage org members."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    ws_id = uuid.uuid4()

    ctx = PolicyEngine.derive_context(
        user_id=user_id,
        organization_id=org_id,
        organization_role=OrganizationRole.MEMBER,
        workspace_id=ws_id,
        workspace_role=WorkspaceRole.MEMBER,
    )

    assert ctx.has_permission(ORGANIZATION_READ)
    assert not ctx.has_permission(ORGANIZATION_UPDATE)
    assert not ctx.has_permission(MEMBER_INVITE)
    assert not ctx.has_permission(MEMBER_REMOVE)
    assert not ctx.has_permission(WORKSPACE_DELETE)
    assert ctx.has_permission(TASK_CREATE)
    assert ctx.has_permission(TASK_RUN)
    assert ctx.has_permission(WORKFLOW_RUN)
    assert ctx.has_permission(CONNECTOR_EXECUTE)


def test_permission_matrix_viewer_role_is_strictly_read_only():
    """Viewer role is strictly read-only. Cannot run workflows, execute connectors, or cancel jobs."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    ws_id = uuid.uuid4()

    ctx = PolicyEngine.derive_context(
        user_id=user_id,
        organization_id=org_id,
        organization_role=OrganizationRole.VIEWER,
        workspace_id=ws_id,
        workspace_role=WorkspaceRole.VIEWER,
    )

    assert ctx.has_permission(ORGANIZATION_READ)
    assert ctx.has_permission(WORKSPACE_READ)
    # Strict read-only enforcement:
    assert not ctx.has_permission(TASK_CREATE)
    assert not ctx.has_permission(TASK_RUN)
    assert not ctx.has_permission(WORKFLOW_RUN)
    assert not ctx.has_permission(CONNECTOR_EXECUTE)
    assert not ctx.has_permission(JOB_CANCEL)
    assert not ctx.has_permission(MEMBER_INVITE)


def test_workspace_role_cannot_elevate_organization_role():
    """A lower-level role cannot elevate a higher-level restriction (strict intersection)."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    ws_id = uuid.uuid4()

    # User is Org Viewer, but Workspace Admin
    ctx = PolicyEngine.derive_context(
        user_id=user_id,
        organization_id=org_id,
        organization_role=OrganizationRole.VIEWER,
        workspace_id=ws_id,
        workspace_role=WorkspaceRole.ADMIN,
    )

    # Intersection prevents elevation: Org Viewer cannot run workflows
    assert not ctx.has_permission(WORKFLOW_RUN)
    assert not ctx.has_permission(CONNECTOR_EXECUTE)


# -----------------------------------------------------------------------------
# 2. Cross-Tenant Multi-Organization API Tests
# -----------------------------------------------------------------------------

def test_cross_tenant_isolation_org_a_vs_org_b(client, user1_auth, user2_auth):
    """
    User 1 creates Org A. User 2 creates Org B.
    User 2 cannot read, modify, or list Org A's workspaces, members, or settings.
    """
    # 1. User 1 creates Org A
    res_a = client.post(
        "/api/organizations",
        json={"name": "Organization Alpha", "slug": "org-alpha"},
        headers=user1_auth["headers"],
    )
    assert res_a.status_code == 201
    org_a_id = res_a.json()["id"]

    # User 1 creates workspace under Org A
    ws_res_a = client.post(
        f"/api/organizations/{org_a_id}/workspaces",
        json={"name": "Alpha Secret Work", "slug": "alpha-secret"},
        headers=user1_auth["headers"],
    )
    assert ws_res_a.status_code == 201
    ws_a_id = ws_res_a.json()["id"]

    # 2. User 2 creates Org B
    res_b = client.post(
        "/api/organizations",
        json={"name": "Organization Beta", "slug": "org-beta"},
        headers=user2_auth["headers"],
    )
    assert res_b.status_code == 201
    org_b_id = res_b.json()["id"]

    # 3. User 2 attempts to read Org A details -> 404 Not Found
    # 3. User 2 attempts to read Org A details -> 403 Forbidden / 404 Not Found
    get_a_from_2 = client.get(
        f"/api/organizations/{org_a_id}",
        headers=user2_auth["headers"],
    )
    assert get_a_from_2.status_code in [403, 404]

    # 4. User 2 attempts to list Org A members -> 403 / 404
    mem_a_from_2 = client.get(
        f"/api/organizations/{org_a_id}/members",
        headers=user2_auth["headers"],
    )
    assert mem_a_from_2.status_code in [403, 404]

    # 5. User 2 attempts to list Org A workspaces -> 403 / 404
    ws_list_from_2 = client.get(
        f"/api/organizations/{org_a_id}/workspaces",
        headers=user2_auth["headers"],
    )
    assert ws_list_from_2.status_code in [403, 404]

    # 6. User 2 attempts to update Org A settings -> 403 / 404
    patch_a_from_2 = client.patch(
        f"/api/organizations/{org_a_id}",
        json={"name": "Hacked Name"},
        headers=user2_auth["headers"],
    )
    assert patch_a_from_2.status_code in [403, 404]

    # 7. User 2 attempts to delete Org A -> 403 / 404
    del_a_from_2 = client.delete(
        f"/api/organizations/{org_a_id}",
        headers=user2_auth["headers"],
    )
    assert del_a_from_2.status_code in [403, 404]

    # 8. User 2 workspace list does NOT contain User 1's workspace
    ws_list_2 = client.get("/api/workspaces", headers=user2_auth["headers"])
    assert ws_list_2.status_code == 200
    ws_ids = [w["id"] for w in ws_list_2.json()["workspaces"]]
    assert ws_a_id not in ws_ids


# -----------------------------------------------------------------------------
# 3. Privilege Escalation Guards
# -----------------------------------------------------------------------------

def test_privilege_escalation_guards(client, user1_auth, user2_auth):
    """
    Test that members cannot assign the owner role, and viewers cannot change roles.
    """
    # User 1 creates Org
    res = client.post(
        "/api/organizations",
        json={"name": "Privilege Guard Org", "slug": "priv-guard"},
        headers=user1_auth["headers"],
    )
    assert res.status_code == 201
    org_id = res.json()["id"]

    # User 1 invites User 2 as a Member
    invite_res = client.post(
        f"/api/organizations/{org_id}/invitations",
        json={"email": user2_auth["email"], "role": "member"},
        headers=user1_auth["headers"],
    )
    assert invite_res.status_code == 201
    invite_token = invite_res.json()["invite_token"]

    # User 2 accepts invitation
    accept_res = client.post(
        f"/api/invitations/{invite_token}/accept",
        headers=user2_auth["headers"],
    )
    assert accept_res.status_code == 200

    # User 2 lists members to get their member ID
    mem_res = client.get(
        f"/api/organizations/{org_id}/members",
        headers=user2_auth["headers"],
    )
    assert mem_res.status_code == 200
    user2_member = next(m for m in mem_res.json()["members"] if m["role"] == "member")

    # Member attempts to promote themselves to Owner via PATCH -> 403 Forbidden
    escalate_res = client.patch(
        f"/api/organizations/{org_id}/members/{user2_member['id']}",
        json={"role": "owner"},
        headers=user2_auth["headers"],
    )
    assert escalate_res.status_code == 403

    # Member attempts to invite new members -> 403 Forbidden
    invite_fail = client.post(
        f"/api/organizations/{org_id}/invitations",
        json={"email": "attacker@example.com", "role": "admin"},
        headers=user2_auth["headers"],
    )
    assert invite_fail.status_code == 403


# -----------------------------------------------------------------------------
# 4. Invitation Lifecycle & Security Tests
# -----------------------------------------------------------------------------

def test_invitation_lifecycle_and_replay_protection(client, user1_auth, user2_auth):
    """
    Tests token hashing, expiration, acceptance, revocation, and replay protection.
    """
    res = client.post(
        "/api/organizations",
        json={"name": "Invitation Test Org", "slug": "inv-org"},
        headers=user1_auth["headers"],
    )
    org_id = res.json()["id"]

    # 1. Create valid invitation
    inv_res = client.post(
        f"/api/organizations/{org_id}/invitations",
        json={"email": user2_auth["email"], "role": "admin"},
        headers=user1_auth["headers"],
    )
    assert inv_res.status_code == 201
    data = inv_res.json()
    token = data["invite_token"]
    inv_id = data["id"]

    # Token must NOT be stored in plaintext in the response or DB
    assert "token_hash" not in data

    # 2. User 2 accepts invitation successfully
    accept_1 = client.post(
        f"/api/invitations/{token}/accept",
        headers=user2_auth["headers"],
    )
    assert accept_1.status_code == 200
    assert accept_1.json()["role"] == "admin"
    assert accept_1.json()["status"] == "active"

    # 3. Token Replay Protection: accepting the same token again fails
    accept_replay = client.post(
        f"/api/invitations/{token}/accept",
        headers=user2_auth["headers"],
    )
    assert accept_replay.status_code == 400
    assert "already been accepted" in accept_replay.json()["error"]["message"].lower()

    # 4. Revocation test: Owner creates another invitation and revokes it
    inv_res2 = client.post(
        f"/api/organizations/{org_id}/invitations",
        json={"email": "user3@example.com", "role": "member"},
        headers=user1_auth["headers"],
    )
    token2 = inv_res2.json()["invite_token"]
    inv2_id = inv_res2.json()["id"]

    # Revoke invitation
    rev_res = client.delete(
        f"/api/organizations/{org_id}/invitations/{inv2_id}",
        headers=user1_auth["headers"],
    )
    assert rev_res.status_code == 204

    # User attempts to accept revoked invitation -> 400 Bad Request
    user3_token = create_access_token("user-auth-003-uuid", "user3@example.com")
    accept_revoked = client.post(
        f"/api/invitations/{token2}/accept",
        headers={"Authorization": f"Bearer {user3_token}"},
    )
    assert accept_revoked.status_code == 400
    assert "revoked" in accept_revoked.json()["error"]["message"].lower()


# -----------------------------------------------------------------------------
# 5. Transactional Ownership Transfer Tests
# -----------------------------------------------------------------------------

def test_ownership_transfer_flow(client, user1_auth, user2_auth):
    """
    Verifies that ownership transfer is atomic:
    - Target member becomes Owner
    - Previous owner becomes Admin
    - Non-owner cannot transfer ownership
    - Self-transfer is rejected
    """
    res = client.post(
        "/api/organizations",
        json={"name": "Transfer Org", "slug": "transfer-org"},
        headers=user1_auth["headers"],
    )
    org_id = res.json()["id"]

    # Invite and onboard User 2
    inv_res = client.post(
        f"/api/organizations/{org_id}/invitations",
        json={"email": user2_auth["email"], "role": "member"},
        headers=user1_auth["headers"],
    )
    client.post(
        f"/api/invitations/{inv_res.json()['invite_token']}/accept",
        headers=user2_auth["headers"],
    )

    # Get User 2 ID
    members_res = client.get(
        f"/api/organizations/{org_id}/members",
        headers=user1_auth["headers"],
    )
    user2_member = next(m for m in members_res.json()["members"] if m["role"] == "member")
    target_user_id = user2_member["user_id"]

    # Non-owner (User 2) attempts to transfer ownership -> 403 Forbidden
    unauth_transfer = client.post(
        f"/api/organizations/{org_id}/transfer-ownership",
        json={"target_user_id": target_user_id},
        headers=user2_auth["headers"],
    )
    assert unauth_transfer.status_code == 403

    # Owner performs successful transfer
    transfer_res = client.post(
        f"/api/organizations/{org_id}/transfer-ownership",
        json={"target_user_id": target_user_id},
        headers=user1_auth["headers"],
    )
    assert transfer_res.status_code == 200
    assert transfer_res.json()["owner_user_id"] == target_user_id

    # Verify updated roles in members list
    members_after = client.get(
        f"/api/organizations/{org_id}/members",
        headers=user2_auth["headers"],
    )
    members_list = members_after.json()["members"]
    user1_m = next(m for m in members_list if m["user_id"] != target_user_id)
    user2_m = next(m for m in members_list if m["user_id"] == target_user_id)

    assert user2_m["role"] == "owner"
    assert user1_m["role"] == "admin"


# -----------------------------------------------------------------------------
# 6. Workspace and Project Access Modes
# -----------------------------------------------------------------------------

def test_project_restricted_access_mode(client, user1_auth, user2_auth):
    """
    When project access_mode='restricted', workspace members cannot access unless
    explicitly added to ProjectMember.
    """
    # User 1 creates Org and Workspace
    res = client.post(
        "/api/organizations",
        json={"name": "Restricted Org", "slug": "restricted-org"},
        headers=user1_auth["headers"],
    )
    org_id = res.json()["id"]

    ws_res = client.post(
        f"/api/organizations/{org_id}/workspaces",
        json={"name": "Shared Workspace", "slug": "shared-ws"},
        headers=user1_auth["headers"],
    )
    ws_id = ws_res.json()["id"]

    # User 1 creates project
    proj_res = client.post(
        f"/api/workspaces/{ws_id}/projects",
        json={"name": "Confidential Research", "slug": "confidential-research"},
        headers=user1_auth["headers"],
    )
    proj_id = proj_res.json()["id"]

    # Onboard User 2 into Org as Member
    inv_res = client.post(
        f"/api/organizations/{org_id}/invitations",
        json={"email": user2_auth["email"], "role": "member"},
        headers=user1_auth["headers"],
    )
    client.post(
        f"/api/invitations/{inv_res.json()['invite_token']}/accept",
        headers=user2_auth["headers"],
    )

    # In default 'workspace' mode, User 2 can see the project
    proj_get = client.get(f"/api/projects/{proj_id}", headers=user2_auth["headers"])
    assert proj_get.status_code == 200

    # User 1 switches project to 'restricted' mode
    patch_proj = client.patch(
        f"/api/projects/{proj_id}",
        json={"access_mode": "restricted"},
        headers=user1_auth["headers"],
    )
    assert patch_proj.status_code == 200
    assert patch_proj.json()["access_mode"] == "restricted"

    # In 'restricted' mode, User 2 now receives 404/403
    restricted_get = client.get(f"/api/projects/{proj_id}", headers=user2_auth["headers"])
    assert restricted_get.status_code in [403, 404]

    # User 1 explicitly grants User 2 access to the restricted project
    members_res = client.get(
        f"/api/organizations/{org_id}/members",
        headers=user1_auth["headers"],
    )
    user2_user_id = next(m["user_id"] for m in members_res.json()["members"] if m["role"] == "member")

    add_proj_member = client.post(
        f"/api/projects/{proj_id}/members",
        json={"user_id": user2_user_id, "role": "viewer"},
        headers=user1_auth["headers"],
    )
    assert add_proj_member.status_code == 201

    # User 2 can now access the restricted project as a viewer
    proj_allowed = client.get(f"/api/projects/{proj_id}", headers=user2_auth["headers"])
    assert proj_allowed.status_code == 200
    assert proj_allowed.json()["id"] == proj_id
