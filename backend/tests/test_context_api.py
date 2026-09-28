import pytest
from uuid import uuid4


@pytest.fixture
def test_workspace_and_project(auth_client):
    """Helper fixture to create workspace, project, and task for user1."""
    suffix = uuid4().hex[:8]
    # 1. Create workspace
    ws_res = auth_client.post("/api/workspaces", json={"name": f"Context WS {suffix}"})
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]

    # 2. Create project
    proj_res = auth_client.post(f"/api/workspaces/{ws_id}/projects", json={"name": f"Context Proj {suffix}"})
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["id"]

    # 3. Create task
    task_res = auth_client.post(
        f"/api/projects/{proj_id}/tasks",
        json={
            "title": "Review Security Architecture",
            "instructions": "Audit OAuth flow and token lifetimes",
            "context_text": "Task-level background context text",
        },
    )
    assert task_res.status_code == 201
    task_id = task_res.json()["id"]

    return {
        "workspace_id": ws_id,
        "project_id": proj_id,
        "task_id": task_id,
    }


def test_create_and_list_task_context(auth_client, test_workspace_and_project):
    """Tests creating manual context items for a task and listing them."""
    task_id = test_workspace_and_project["task_id"]

    # 1. Create manual context item
    create_payload = {
        "title": "JWT Expiration Policy",
        "content": "Access tokens expire in 15 minutes. Refresh tokens expire in 7 days.",
        "source_type": "manual",
        "priority": 75,
        "metadata": {"category": "security", "author": "lead-sec"},
    }
    res = auth_client.post(f"/api/tasks/{task_id}/context", json=create_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "JWT Expiration Policy"
    assert data["content"] == create_payload["content"]
    assert data["priority"] == 75
    assert data["source_type"] == "manual"
    assert data["estimated_tokens"] > 0
    context_id = data["id"]

    # 2. Create second item
    res2 = auth_client.post(
        f"/api/tasks/{task_id}/context",
        json={
            "title": "Key Rotation Policy",
            "content": "RSA keys are rotated every 90 days via KMS.",
            "priority": 90,
        },
    )
    assert res2.status_code == 201

    # 3. List context items
    list_res = auth_client.get(f"/api/tasks/{task_id}/context")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] == 2
    assert len(list_data["contexts"]) == 2
    assert list_data["total_estimated_tokens"] > 0
    # Highest priority should be first
    assert list_data["contexts"][0]["priority"] >= list_data["contexts"][1]["priority"]


def test_update_and_delete_context(auth_client, test_workspace_and_project):
    """Tests updating and deleting an individual TaskContext record."""
    task_id = test_workspace_and_project["task_id"]

    # Create item
    res = auth_client.post(
        f"/api/tasks/{task_id}/context",
        json={
            "title": "Initial Title",
            "content": "Initial Content",
            "priority": 10,
        },
    )
    assert res.status_code == 201
    context_id = res.json()["id"]

    # Update item
    patch_res = auth_client.patch(
        f"/api/context/{context_id}",
        json={
            "title": "Updated Title",
            "content": "Updated content with more details.",
            "priority": 85,
        },
    )
    assert patch_res.status_code == 200
    patch_data = patch_res.json()
    assert patch_data["title"] == "Updated Title"
    assert patch_data["content"] == "Updated content with more details."
    assert patch_data["priority"] == 85

    # Delete item
    del_res = auth_client.delete(f"/api/context/{context_id}")
    assert del_res.status_code == 204

    # Verify gone
    get_res = auth_client.get(f"/api/context/{context_id}")
    assert get_res.status_code == 404


def test_cross_user_isolation_context(client, user1_auth, user2_auth, test_workspace_and_project):
    """Ensures that User B cannot access, create, update, or delete User A's context."""
    user1_task_id = test_workspace_and_project["task_id"]

    # 1. User 1 creates context
    u1_res = client.post(
        f"/api/tasks/{user1_task_id}/context",
        headers=user1_auth["headers"],
        json={
            "title": "User1 Private Context",
            "content": "Sensitive proprietary instructions",
            "priority": 50,
        },
    )
    assert u1_res.status_code == 201
    u1_context_id = u1_res.json()["id"]

    # 2. User 2 attempts to list User 1's task context -> 404
    u2_list = client.get(
        f"/api/tasks/{user1_task_id}/context",
        headers=user2_auth["headers"],
    )
    assert u2_list.status_code == 404

    # 3. User 2 attempts to add context to User 1's task -> 404
    u2_post = client.post(
        f"/api/tasks/{user1_task_id}/context",
        headers=user2_auth["headers"],
        json={"title": "Malicious Injection", "content": "Tampered context"},
    )
    assert u2_post.status_code == 404

    # 4. User 2 attempts to update User 1's context item -> 404
    u2_patch = client.patch(
        f"/api/context/{u1_context_id}",
        headers=user2_auth["headers"],
        json={"title": "Hacked Title"},
    )
    assert u2_patch.status_code == 404

    # 5. User 2 attempts to delete User 1's context item -> 404
    u2_del = client.delete(
        f"/api/context/{u1_context_id}",
        headers=user2_auth["headers"],
    )
    assert u2_del.status_code == 404


def test_context_inspect_endpoint(auth_client, test_workspace_and_project):
    """Tests the /api/tasks/{task_id}/context/inspect debug endpoint."""
    task_id = test_workspace_and_project["task_id"]

    # Add manual context
    auth_client.post(
        f"/api/tasks/{task_id}/context",
        json={
            "title": "Debug Notes",
            "content": "Debugging information for context inspection endpoint.",
            "priority": 60,
        },
    )

    inspect_res = auth_client.get(f"/api/tasks/{task_id}/context/inspect?max_context_tokens=4000")
    assert inspect_res.status_code == 200
    data = inspect_res.json()

    assert data["task_id"] == task_id
    assert data["total_items"] >= 2  # Task context + Manual context
    assert data["estimated_tokens"] > 0
    assert "task" in data["sources"]
    assert "manual" in data["sources"]
    assert data["truncated"] is False
    assert data["max_context_tokens"] == 4000
    assert data["formatted_prompt_preview"] is not None
    assert "SYSTEM" in data["formatted_prompt_preview"]
    assert "USER" in data["formatted_prompt_preview"]
