import pytest
import uuid


def test_workspace_isolation(client, user1_auth, user2_auth):
    """User 1 owns a workspace; User 2 receives 404 when attempting to access, edit, or delete it."""
    # User 1 creates a workspace
    create_res = client.post(
        "/api/workspaces",
        json={"name": "User 1 Secret Workspace", "slug": "user1-secret"},
        headers=user1_auth["headers"],
    )
    assert create_res.status_code == 201
    ws_id = create_res.json()["id"]

    # User 1 can access
    get_res1 = client.get(f"/api/workspaces/{ws_id}", headers=user1_auth["headers"])
    assert get_res1.status_code == 200
    assert get_res1.json()["name"] == "User 1 Secret Workspace"

    # User 2 receives 404
    get_res2 = client.get(f"/api/workspaces/{ws_id}", headers=user2_auth["headers"])
    assert get_res2.status_code == 404
    assert get_res2.json()["error"]["code"] == "NOT_FOUND"

    # User 2 cannot update User 1's workspace
    patch_res = client.patch(
        f"/api/workspaces/{ws_id}",
        json={"name": "Hacked Name"},
        headers=user2_auth["headers"],
    )
    assert patch_res.status_code == 404

    # User 2 cannot delete User 1's workspace
    del_res = client.delete(f"/api/workspaces/{ws_id}", headers=user2_auth["headers"])
    assert del_res.status_code == 404

    # Workspace list for User 2 does NOT show User 1's workspace
    list_res2 = client.get("/api/workspaces", headers=user2_auth["headers"])
    assert list_res2.status_code == 200
    user2_ws_ids = [w["id"] for w in list_res2.json()["workspaces"]]
    assert ws_id not in user2_ws_ids


def test_same_slug_allowed_for_different_users(client, user1_auth, user2_auth):
    """Users can independently have workspaces and projects with the same slug."""
    # User 1 creates custom slug
    res1 = client.post(
        "/api/workspaces",
        json={"name": "Analytics Hub", "slug": "analytics-hub"},
        headers=user1_auth["headers"],
    )
    assert res1.status_code == 201

    # User 2 creates same slug
    res2 = client.post(
        "/api/workspaces",
        json={"name": "Analytics Hub", "slug": "analytics-hub"},
        headers=user2_auth["headers"],
    )
    assert res2.status_code == 201
    assert res1.json()["id"] != res2.json()["id"]


def test_project_isolation(client, user1_auth, user2_auth):
    """User 1 creates project; User 2 receives 404 attempting to access or create tasks in it."""
    # User 1 gets default workspace
    me1 = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws1_id = me1["default_workspace_id"]

    # User 1 creates project
    proj_res = client.post(
        f"/api/workspaces/{ws1_id}/projects",
        json={"name": "Confidential AI Pipeline", "slug": "ai-pipeline"},
        headers=user1_auth["headers"],
    )
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["id"]

    # User 1 can view project
    get_p1 = client.get(f"/api/projects/{proj_id}", headers=user1_auth["headers"])
    assert get_p1.status_code == 200

    # User 2 receives 404
    get_p2 = client.get(f"/api/projects/{proj_id}", headers=user2_auth["headers"])
    assert get_p2.status_code == 404

    # User 2 cannot create task in User 1's project
    task_attack = client.post(
        f"/api/projects/{proj_id}/tasks",
        json={"title": "Injected Task"},
        headers=user2_auth["headers"],
    )
    assert task_attack.status_code == 404


def test_task_and_run_isolation(client, user1_auth, user2_auth):
    """User 1 creates task and run; User 2 receives 404 trying to access or manipulate them."""
    # User 1 workspace & project
    me1 = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws1_id = me1["default_workspace_id"]

    proj_res = client.post(
        f"/api/workspaces/{ws1_id}/projects",
        json={"name": "Task Isolation Proj"},
        headers=user1_auth["headers"],
    )
    proj_id = proj_res.json()["id"]

    # User 1 creates task
    task_res = client.post(
        f"/api/projects/{proj_id}/tasks",
        json={"title": "User 1 Private Task", "status": "active"},
        headers=user1_auth["headers"],
    )
    assert task_res.status_code == 201
    task_id = task_res.json()["id"]

    # User 1 creates run
    run_res = client.post(
        f"/api/tasks/{task_id}/runs",
        json={"status": "completed", "model_name": "gpt-4o-mini", "total_tokens": 120},
        headers=user1_auth["headers"],
    )
    assert run_res.status_code == 201
    run_id = run_res.json()["id"]

    # User 1 can access task and runs
    t1 = client.get(f"/api/tasks/{task_id}", headers=user1_auth["headers"])
    assert t1.status_code == 200
    runs1 = client.get(f"/api/tasks/{task_id}/runs", headers=user1_auth["headers"])
    assert runs1.status_code == 200
    assert runs1.json()["total"] == 1

    # User 2 cannot access task -> 404
    t2 = client.get(f"/api/tasks/{task_id}", headers=user2_auth["headers"])
    assert t2.status_code == 404

    # User 2 cannot access runs -> 404
    runs2 = client.get(f"/api/tasks/{task_id}/runs", headers=user2_auth["headers"])
    assert runs2.status_code == 404

    # User 2 cannot update User 1's task
    patch_t2 = client.patch(
        f"/api/tasks/{task_id}",
        json={"title": "Tampered Title"},
        headers=user2_auth["headers"],
    )
    assert patch_t2.status_code == 404

    # User 2 cannot delete User 1's task
    del_t2 = client.delete(f"/api/tasks/{task_id}", headers=user2_auth["headers"])
    assert del_t2.status_code == 404
