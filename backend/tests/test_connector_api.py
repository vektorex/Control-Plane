"""
API route tests for Connector endpoints (Step 16).
"""
import uuid
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.auth import create_access_token
from backend.app.services.connectors.github.client import GitHubClient


@pytest.fixture
def auth_headers(user1_auth):
    return user1_auth["headers"]



def test_list_connectors_api(client: TestClient, auth_headers):
    response = client.get("/api/connectors", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    gh = next(c for c in data if c["name"] == "github")
    assert gh["display_name"] == "GitHub"
    assert gh["category"] == "code"
    assert "read" in gh["capabilities"]
    assert "token" not in gh
    assert "secret" not in gh


def test_get_connector_api(client: TestClient, auth_headers):
    response = client.get("/api/connectors/github", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "github"
    assert len(data["supported_operations"]) == 10


def test_get_connector_operations_api(client: TestClient, auth_headers):
    response = client.get("/api/connectors/github/operations", headers=auth_headers)
    assert response.status_code == 200
    ops = response.json()
    assert isinstance(ops, list)
    assert len(ops) == 10
    op_names = [o["name"] for o in ops]
    assert "search_repositories" in op_names
    assert "search_issues" in op_names
    assert "get_file_contents" in op_names


def test_get_connector_status_disconnected(client: TestClient, auth_headers):
    response = client.get("/api/connectors/github/status", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["connector"] == "github"
    assert data["status"] in ("connected", "disconnected")
    assert "secret" not in data


def test_connect_and_disconnect_flow(client: TestClient, auth_headers):
    mock_user = {
        "login": "octocat",
        "name": "The Octocat",
        "html_url": "https://github.com/octocat",
        "avatar_url": "https://avatars.githubusercontent.com/u/583231",
        "public_repos": 8,
    }

    with patch.object(GitHubClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_user

        # 1. Connect
        connect_payload = {
            "credential": "ghp_validTokenForTesting1234567890",
            "credential_type": "pat",
            "metadata": {"label": "Work Account"},
        }
        resp = client.post("/api/connectors/github/connect", json=connect_payload, headers=auth_headers)
        assert resp.status_code == 200
        status_data = resp.json()
        assert status_data["status"] == "connected"
        assert status_data["has_credentials"] is True
        assert status_data["account"]["login"] == "octocat"
        assert "ghp_" not in str(status_data)

        # 2. Test Connection
        test_resp = client.post("/api/connectors/github/test", headers=auth_headers)
        assert test_resp.status_code == 200
        assert test_resp.json()["success"] is True

        # 3. Disconnect
        disc_resp = client.delete("/api/connectors/github/disconnect", headers=auth_headers)
        assert disc_resp.status_code == 200
        assert disc_resp.json()["disconnected"] is True

        # 4. Status after disconnect
        status_resp2 = client.get("/api/connectors/github/status", headers=auth_headers)
        assert status_resp2.status_code == 200
        assert status_resp2.json()["status"] == "disconnected"


def test_connector_permissions_api(client: TestClient, auth_headers):
    # 1. List permissions
    list_resp = client.get("/api/connectors/github/permissions", headers=auth_headers)
    assert list_resp.status_code == 200
    perms = list_resp.json()
    assert isinstance(perms, list)
    assert len(perms) == 10

    # 2. Update permission
    patch_payload = {
        "operation": "search_code",
        "enabled": False,
        "permission_level": "read",
    }
    patch_resp = client.patch("/api/connectors/github/permissions", json=patch_payload, headers=auth_headers)
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["operation"] == "search_code"
    assert updated["enabled"] is False


def test_connector_execute_api(client: TestClient, auth_headers):
    mock_search = {
        "total_count": 1,
        "items": [
            {
                "id": 1,
                "name": "demo-project",
                "full_name": "user/demo-project",
                "html_url": "https://github.com/user/demo-project",
            }
        ],
    }

    # First connect
    with patch.object(GitHubClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"login": "user"}
        client.post(
            "/api/connectors/github/connect",
            json={"credential": "ghp_validToken12345"},
            headers=auth_headers,
        )

        mock_get.return_value = mock_search
        exec_payload = {
            "operation": "search_repositories",
            "arguments": {"query": "demo"},
        }
        exec_resp = client.post("/api/connectors/github/execute", json=exec_payload, headers=auth_headers)
        assert exec_resp.status_code == 200
        res_data = exec_resp.json()
        assert res_data["success"] is True
        assert res_data["connector"] == "github"
        assert len(res_data["items"]) == 1
        assert res_data["items"][0]["trust_level"] == "external_untrusted"
        assert "ghp_" not in str(res_data)
