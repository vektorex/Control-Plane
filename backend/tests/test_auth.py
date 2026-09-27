import pytest
import time
import jwt
from backend.app.core.auth import create_access_token, DEV_JWT_SECRET, decode_jwt_token


def test_unauthenticated_requests_rejected(client):
    """Verify that unauthenticated requests to protected endpoints return 401."""
    protected_endpoints = [
        ("GET", "/api/auth/me"),
        ("GET", "/api/workspaces"),
        ("POST", "/api/workspaces"),
        ("GET", "/api/projects"),
        ("GET", "/api/tasks"),
        ("POST", "/api/llm/generate"),
    ]
    for method, url in protected_endpoints:
        if method == "GET":
            res = client.get(url)
        else:
            res = client.post(url, json={})
        assert res.status_code == 401, f"Expected 401 for {method} {url}, got {res.status_code}"
        assert res.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_valid_authenticated_request_accepted(client, user1_auth):
    """Verify that a request with a valid Bearer token is accepted (200)."""
    res = client.get("/api/auth/me", headers=user1_auth["headers"])
    assert res.status_code == 200
    data = res.json()
    assert data["auth_user_id"] == user1_auth["auth_user_id"]
    assert data["email"] == user1_auth["email"]
    assert "default_workspace_id" in data
    assert data["default_workspace_id"] is not None


def test_invalid_token_rejected(client):
    """Verify that malformed or tampered tokens return 401."""
    invalid_tokens = [
        "Bearer not-a-valid-jwt-token",
        "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.payload",
        "Bearer " + create_access_token("user-id", "test@test.com", secret="wrong-secret-key-that-is-at-least-32-chars!"),
    ]
    for auth_header in invalid_tokens:
        res = client.get("/api/auth/me", headers={"Authorization": auth_header})
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_expired_token_rejected(client):
    """Verify that expired tokens return 401."""
    expired_token = create_access_token(
        auth_user_id="user-expired",
        email="expired@example.com",
        expires_in_seconds=-100,  # Expired 100 seconds ago
    )
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401
    data = res.json()
    assert data["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert "expired" in data["error"]["message"].lower()


def test_first_login_creates_exactly_one_default_workspace(client):
    """Verify that a brand new user's first login automatically provisions exactly one default workspace."""
    new_user_auth_id = "brand-new-user-001"
    new_user_email = "newbie@example.com"
    token = create_access_token(new_user_auth_id, new_user_email)
    headers = {"Authorization": f"Bearer {token}"}

    # First call
    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200
    profile = res.json()
    assert profile["email"] == new_user_email
    assert profile["default_workspace_id"] is not None

    # List workspaces
    ws_res = client.get("/api/workspaces", headers=headers)
    assert ws_res.status_code == 200
    workspaces = ws_res.json()["workspaces"]
    assert len(workspaces) == 1
    assert workspaces[0]["name"] == "Default Workspace"
    assert workspaces[0]["slug"] == "default"


def test_repeated_login_does_not_create_duplicates(client):
    """Verify that repeated logins/requests do not create duplicate default workspaces."""
    repeat_user_auth_id = "repeat-user-002"
    repeat_user_email = "repeat@example.com"
    token = create_access_token(repeat_user_auth_id, repeat_user_email)
    headers = {"Authorization": f"Bearer {token}"}

    # Call /api/auth/me and /api/workspaces multiple times
    for _ in range(5):
        res = client.get("/api/auth/me", headers=headers)
        assert res.status_code == 200

    ws_res = client.get("/api/workspaces", headers=headers)
    assert ws_res.status_code == 200
    data = ws_res.json()
    assert data["total"] == 1
    assert len(data["workspaces"]) == 1


def test_jwt_integration_verification(client):
    """Integration test verifying full end-to-end token generation, signature validation, and database resolution."""
    auth_user_id = "integration-test-user-999"
    email = "integration-tester@example.com"

    # 1. Encode custom token
    token = create_access_token(
        auth_user_id=auth_user_id,
        email=email,
        expires_in_seconds=7200,
        audience="authenticated",
    )

    # 2. Verify decode utility independently
    claims = decode_jwt_token(token)
    assert claims["sub"] == auth_user_id
    assert claims["email"] == email
    assert claims["aud"] == "authenticated"

    # 3. Use in full HTTP API request
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    profile = res.json()
    assert profile["auth_user_id"] == auth_user_id
    assert profile["email"] == email

    # 4. Create custom workspace with this user
    ws_create = client.post(
        "/api/workspaces",
        json={"name": "Integration Workspace", "slug": "int-ws"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ws_create.status_code == 201
    ws_data = ws_create.json()
    assert ws_data["name"] == "Integration Workspace"
    assert ws_data["owner_user_id"] == profile["id"]
