import pytest
import uuid


def test_create_workspace(client):
    payload = {
        "name": "Engineering Workspace",
        "slug": "eng-workspace",
    }
    response = client.post("/api/workspaces", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Engineering Workspace"
    assert data["slug"] == "eng-workspace"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_workspace_auto_slug(client):
    payload = {
        "name": "Product Strategy & Design",
    }
    response = client.post("/api/workspaces", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Product Strategy & Design"
    assert data["slug"] == "product-strategy-design"


def test_create_workspace_duplicate_slug_conflict(client):
    payload = {
        "name": "Duplicate Test",
        "slug": "unique-slug-1",
    }
    res1 = client.post("/api/workspaces", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/workspaces", json=payload)
    assert res2.status_code == 409
    data = res2.json()
    assert data["error"]["code"] == "CONFLICT"


def test_list_workspaces(client):
    response = client.get("/api/workspaces")
    assert response.status_code == 200
    data = response.json()
    assert "workspaces" in data
    assert "total" in data
    assert data["total"] >= 1


def test_get_workspace_by_id(client):
    create_res = client.post("/api/workspaces", json={"name": "Fetch Target"})
    workspace_id = create_res.json()["id"]

    response = client.get(f"/api/workspaces/{workspace_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == workspace_id
    assert data["name"] == "Fetch Target"


def test_get_workspace_not_found(client):
    random_id = str(uuid.uuid4())
    response = client.get(f"/api/workspaces/{random_id}")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"


def test_update_workspace(client):
    create_res = client.post("/api/workspaces", json={"name": "Before Update"})
    workspace_id = create_res.json()["id"]

    response = client.patch(
        f"/api/workspaces/{workspace_id}",
        json={"name": "After Update", "slug": "after-update"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "After Update"
    assert data["slug"] == "after-update"


def test_delete_workspace(client):
    create_res = client.post("/api/workspaces", json={"name": "To Delete"})
    workspace_id = create_res.json()["id"]

    del_res = client.delete(f"/api/workspaces/{workspace_id}")
    assert del_res.status_code == 204

    get_res = client.get(f"/api/workspaces/{workspace_id}")
    assert get_res.status_code == 404
