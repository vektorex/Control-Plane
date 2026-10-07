import pytest
import uuid


# ---------------------------------------------------------------------------
# API Tests (Synchronous using TestClient)
# ---------------------------------------------------------------------------

def test_get_overview(client, user1_auth):
    headers = {**user1_auth["headers"], "X-Workspace-Id": "test_ws"}
    resp = client.get("/api/control-tower/overview", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "workspace_id" in data
    assert "active_tasks" in data["sections"]
    assert "open_security_incidents" in data["sections"]


def test_get_attention_prioritization(client, user1_auth):
    headers = {**user1_auth["headers"], "X-Workspace-Id": "test_ws"}
    resp = client.get("/api/control-tower/attention", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_search_isolation(client, user1_auth):
    headers = {**user1_auth["headers"], "X-Workspace-Id": "test_ws"}
    resp = client.get("/api/control-tower/search?q=secret_leak", headers=headers)
    assert resp.status_code == 200
    assert "results" in resp.json()


def test_view_crud(client, user1_auth):
    headers = {**user1_auth["headers"], "X-Workspace-Id": "test_ws"}
    # Create
    create_resp = client.post(
        "/api/control-tower/views",
        json={"name": "My View", "configuration": {"x": 1}},
        headers=headers,
    )
    assert create_resp.status_code == 201
    view_id = create_resp.json()["id"]

    # List
    list_resp = client.get("/api/control-tower/views", headers=headers)
    assert list_resp.status_code == 200
    assert any(v["id"] == view_id for v in list_resp.json())

    # Update
    update_resp = client.patch(
        f"/api/control-tower/views/{view_id}",
        json={"name": "Updated View"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Updated View"

    # Delete
    del_resp = client.delete(
        f"/api/control-tower/views/{view_id}", headers=headers
    )
    assert del_resp.status_code == 204


def test_generate_briefing_authorization(client, user1_auth):
    headers = {**user1_auth["headers"], "X-Workspace-Id": "test_ws"}
    # Generates a briefing, should not crash, returns 200
    resp = client.post(
        "/api/control-tower/briefing",
        json={"mode": "brief"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "statements" in data
    assert len(data["statements"]) > 0


# ---------------------------------------------------------------------------
# Unit / Policy Tests
# ---------------------------------------------------------------------------

def test_security_policy_cross_tenant():
    from backend.app.services.control_tower.policies import ControlTowerPolicies
    ok = ControlTowerPolicies.validate_no_cross_tenant_data("ws1", "ws1", "task")
    assert ok is True
    ok = ControlTowerPolicies.validate_no_cross_tenant_data("ws1", "ws2", "task")
    assert ok is False

def test_permissions_role_presets():
    from backend.app.services.control_tower.permissions import ControlTowerPermissions
    preset = ControlTowerPermissions.get_role_preset("security_operator")
    assert "security" in preset["visible_sections"]
    
def test_permissions_section_visibility():
    from backend.app.services.control_tower.permissions import ControlTowerPermissions
    assert ControlTowerPermissions.validate_section_visibility("security", ["security:read"]) is True
    assert ControlTowerPermissions.validate_section_visibility("security", ["tasks:read"]) is False
    assert ControlTowerPermissions.validate_section_visibility("overview", ["tasks:read"]) is True # No specific permission required
