import io
import pytest


def test_document_upload_and_lifecycle(auth_client):
    # 1. Create workspace and project
    ws_res = auth_client.post("/api/workspaces", json={"name": "Docs Workspace"})
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]

    proj_res = auth_client.post(f"/api/workspaces/{ws_id}/projects", json={"name": "Docs Project"})
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["id"]

    # 2. Upload text document
    file_bytes = b"This is a system architecture reference for RAG pipeline testing."
    upload_res = auth_client.post(
        f"/api/workspaces/{ws_id}/documents",
        data={"project_id": proj_id},
        files={"file": ("architecture.txt", io.BytesIO(file_bytes), "text/plain")},
    )
    assert upload_res.status_code == 201
    doc_data = upload_res.json()
    assert doc_data["filename"] == "architecture.txt"
    assert doc_data["workspace_id"] == ws_id
    assert doc_data["project_id"] == proj_id
    assert doc_data["file_size"] == len(file_bytes)
    assert doc_data["status"] in ["pending", "ready", "processing"]
    doc_id = doc_data["id"]

    # 3. Get single document
    get_res = auth_client.get(f"/api/documents/{doc_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == doc_id

    # 4. List workspace documents
    list_res = auth_client.get(f"/api/workspaces/{ws_id}/documents")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(d["id"] == doc_id for d in list_data["items"])

    # 5. List document chunks
    chunks_res = auth_client.get(f"/api/documents/{doc_id}/chunks")
    assert chunks_res.status_code == 200

    # 6. Delete document
    del_res = auth_client.delete(f"/api/documents/{doc_id}")
    assert del_res.status_code == 204

    # Verify deletion
    get_again = auth_client.get(f"/api/documents/{doc_id}")
    assert get_again.status_code == 404


def test_document_validation_errors(auth_client):
    ws_res = auth_client.post("/api/workspaces", json={"name": "Val Workspace"})
    ws_id = ws_res.json()["id"]

    # Unsupported executable format
    exe_res = auth_client.post(
        f"/api/workspaces/{ws_id}/documents",
        files={"file": ("malicious.exe", io.BytesIO(b"MZ..."), "application/octet-stream")},
    )
    assert exe_res.status_code == 415

    # Empty file
    empty_res = auth_client.post(
        f"/api/workspaces/{ws_id}/documents",
        files={"file": ("empty.txt", io.BytesIO(b""), "text/plain")},
    )
    assert empty_res.status_code == 400


def test_document_multi_tenant_security(client, user1_auth, user2_auth):
    # User 1 creates workspace and uploads doc
    h1 = user1_auth["headers"]
    h2 = user2_auth["headers"]

    ws1_res = client.post("/api/workspaces", json={"name": "User 1 Workspace"}, headers=h1)
    assert ws1_res.status_code == 201
    ws1_id = ws1_res.json()["id"]

    doc1_res = client.post(
        f"/api/workspaces/{ws1_id}/documents",
        headers=h1,
        files={"file": ("secret_u1.txt", io.BytesIO(b"Secret for User 1 only"), "text/plain")},
    )
    assert doc1_res.status_code == 201
    doc1_id = doc1_res.json()["id"]

    # User 2 tries to upload into User 1's workspace -> 404
    u2_upload = client.post(
        f"/api/workspaces/{ws1_id}/documents",
        headers=h2,
        files={"file": ("hack.txt", io.BytesIO(b"hack"), "text/plain")},
    )
    assert u2_upload.status_code == 404

    # User 2 tries to list User 1's documents -> 404
    u2_list = client.get(f"/api/workspaces/{ws1_id}/documents", headers=h2)
    assert u2_list.status_code == 404

    # User 2 tries to get User 1's document -> 404
    u2_get = client.get(f"/api/documents/{doc1_id}", headers=h2)
    assert u2_get.status_code == 404

    # User 2 tries to delete User 1's document -> 404
    u2_del = client.delete(f"/api/documents/{doc1_id}", headers=h2)
    assert u2_del.status_code == 404
