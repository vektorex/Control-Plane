import pytest
import uuid


def test_create_and_list_workspace_projects(client):
    # 1. Create workspace
    ws_res = client.post("/api/workspaces", json={"name": "Projects Parent WS"})
    workspace_id = ws_res.json()["id"]

    # 2. Create project under workspace
    proj_payload = {
        "name": "Backend Refactor",
        "description": "Migrate data layer to PostgreSQL and SQLAlchemy 2.0",
    }
    proj_res = client.post(f"/api/workspaces/{workspace_id}/projects", json=proj_payload)
    assert proj_res.status_code == 201
    proj_data = proj_res.json()
    assert proj_data["name"] == "Backend Refactor"
    assert proj_data["slug"] == "backend-refactor"
    assert proj_data["workspace_id"] == workspace_id
    project_id = proj_data["id"]

    # 3. List projects for workspace
    list_res = client.get(f"/api/workspaces/{workspace_id}/projects")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(p["id"] == project_id for p in list_data["projects"])


def test_project_slug_conflict_within_same_workspace(client):
    ws_res = client.post("/api/workspaces", json={"name": "WS Slug Conflict"})
    workspace_id = ws_res.json()["id"]

    proj_payload = {"name": "Duplicate Project", "slug": "dup-proj"}
    res1 = client.post(f"/api/workspaces/{workspace_id}/projects", json=proj_payload)
    assert res1.status_code == 201

    res2 = client.post(f"/api/workspaces/{workspace_id}/projects", json=proj_payload)
    assert res2.status_code == 409
    assert res2.json()["error"]["code"] == "CONFLICT"


def test_get_project_by_id(client):
    ws_res = client.post("/api/workspaces", json={"name": "WS Get Project"})
    workspace_id = ws_res.json()["id"]

    proj_res = client.post(
        f"/api/workspaces/{workspace_id}/projects",
        json={"name": "Target Project"},
    )
    project_id = proj_res.json()["id"]

    get_res = client.get(f"/api/projects/{project_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == project_id
    assert data["name"] == "Target Project"


def test_update_project(client):
    ws_res = client.post("/api/workspaces", json={"name": "WS Update Project"})
    workspace_id = ws_res.json()["id"]

    proj_res = client.post(
        f"/api/workspaces/{workspace_id}/projects",
        json={"name": "Old Project Name", "description": "Old desc"},
    )
    project_id = proj_res.json()["id"]

    patch_res = client.patch(
        f"/api/projects/{project_id}",
        json={"name": "New Project Name", "description": "Updated desc"},
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["name"] == "New Project Name"
    assert data["description"] == "Updated desc"


def test_delete_project_and_cascade(client):
    ws_res = client.post("/api/workspaces", json={"name": "WS Delete Project"})
    workspace_id = ws_res.json()["id"]

    proj_res = client.post(
        f"/api/workspaces/{workspace_id}/projects",
        json={"name": "To Delete Project"},
    )
    project_id = proj_res.json()["id"]

    del_res = client.delete(f"/api/projects/{project_id}")
    assert del_res.status_code == 204

    get_res = client.get(f"/api/projects/{project_id}")
    assert get_res.status_code == 404
