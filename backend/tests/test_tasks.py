import pytest
import uuid


def test_create_and_list_tasks(client):
    # 1. Create Workspace & Project
    ws_res = client.post("/api/workspaces", json={"name": "WS for Tasks"})
    ws_id = ws_res.json()["id"]

    proj_res = client.post(f"/api/workspaces/{ws_id}/projects", json={"name": "Project for Tasks"})
    proj_id = proj_res.json()["id"]

    # 2. Create Task under project
    task_payload = {
        "title": "Build PostgreSQL integration",
        "description": "Establish workspace/project/task relationships",
        "status": "draft",
    }
    task_res = client.post(f"/api/projects/{proj_id}/tasks", json=task_payload)
    assert task_res.status_code == 201
    task_data = task_res.json()
    assert task_data["title"] == "Build PostgreSQL integration"
    assert task_data["status"] == "draft"
    assert task_data["project_id"] == proj_id
    task_id = task_data["id"]

    # 3. List tasks by project
    list_res = client.get(f"/api/projects/{proj_id}/tasks")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(t["id"] == task_id for t in list_data["tasks"])


def test_task_status_lifecycle_update(client):
    ws_res = client.post("/api/workspaces", json={"name": "WS Task Lifecycle"})
    ws_id = ws_res.json()["id"]

    proj_res = client.post(f"/api/workspaces/{ws_id}/projects", json={"name": "Proj Task Lifecycle"})
    proj_id = proj_res.json()["id"]

    task_res = client.post(f"/api/projects/{proj_id}/tasks", json={"title": "Lifecycle Task", "status": "draft"})
    task_id = task_res.json()["id"]

    # Transition to active
    patch1 = client.patch(f"/api/tasks/{task_id}", json={"status": "active"})
    assert patch1.status_code == 200
    assert patch1.json()["status"] == "active"

    # Transition to completed
    patch2 = client.patch(f"/api/tasks/{task_id}", json={"status": "completed"})
    assert patch2.status_code == 200
    assert patch2.json()["status"] == "completed"


def test_task_not_found(client):
    random_id = str(uuid.uuid4())
    res = client.get(f"/api/tasks/{random_id}")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOT_FOUND"


def test_delete_task(client):
    ws_res = client.post("/api/workspaces", json={"name": "WS Task Delete"})
    ws_id = ws_res.json()["id"]

    proj_res = client.post(f"/api/workspaces/{ws_id}/projects", json={"name": "Proj Task Delete"})
    proj_id = proj_res.json()["id"]

    task_res = client.post(f"/api/projects/{proj_id}/tasks", json={"title": "Delete Me Task"})
    task_id = task_res.json()["id"]

    del_res = client.delete(f"/api/tasks/{task_id}")
    assert del_res.status_code == 204

    get_res = client.get(f"/api/tasks/{task_id}")
    assert get_res.status_code == 404
