import io
import pytest


def test_rag_task_execution_with_document_retrieval(auth_client):
    """
    Tests end-to-end task execution with Hybrid RAG retrieval enabled,
    verifying ContextEngine -> RAGContextProvider -> HybridRetriever -> LLM -> Run telemetry.
    """
    # 1. Create Workspace, Project, Task
    ws_res = auth_client.post("/api/workspaces", json={"name": "RAG Testing WS"})
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]

    proj_res = auth_client.post(f"/api/workspaces/{ws_id}/projects", json={"name": "RAG Testing Project"})
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["id"]

    task_res = auth_client.post(
        f"/api/projects/{proj_id}/tasks",
        json={
            "title": "Explain Hybrid RAG Architecture",
            "instructions": "Describe how Reciprocal Rank Fusion merges vector and keyword scores.",
        },
    )
    assert task_res.status_code == 201
    task_id = task_res.json()["id"]

    # 2. Upload Document into Project Knowledge
    doc_content = b"Reciprocal Rank Fusion merges vector similarity scores and BM25 keyword rankings deterministically."
    upload_res = auth_client.post(
        f"/api/workspaces/{ws_id}/documents",
        data={"project_id": proj_id},
        files={"file": ("rag_architecture.md", io.BytesIO(doc_content), "text/markdown")},
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # 3. Execute Task with retrieval_enabled=True
    run_res = auth_client.post(
        f"/api/tasks/{task_id}/run",
        json={
            "model": "mock-model-v1",
            "temperature": 0.2,
            "max_context_tokens": 8000,
            "retrieval_enabled": True,
            "retrieval_top_k": 5,
            "retrieval_project_scope": True,
        },
    )
    assert run_res.status_code == 201
    run_data = run_res.json()

    # 4. Verify Run telemetry and retrieval diagnostics
    assert run_data["status"] == "completed"
    assert run_data["retrieval_enabled"] is True
    assert run_data["retrieved_chunk_count"] is not None and run_data["retrieved_chunk_count"] >= 1
    assert run_data["retrieval_latency_ms"] is not None and run_data["retrieval_latency_ms"] >= 0
    assert run_data["retrieval_sources"] is not None
    assert len(run_data["retrieval_sources"]) >= 1
    assert any("rag_architecture" in s["filename"] for s in run_data["retrieval_sources"])


def test_rag_task_execution_with_retrieval_disabled(auth_client):
    """
    Tests that when retrieval_enabled is False, RAGContextProvider is bypassed.
    """
    ws_res = auth_client.post("/api/workspaces", json={"name": "No RAG WS"})
    ws_id = ws_res.json()["id"]

    proj_res = auth_client.post(f"/api/workspaces/{ws_id}/projects", json={"name": "No RAG Proj"})
    proj_id = proj_res.json()["id"]

    task_res = auth_client.post(
        f"/api/projects/{proj_id}/tasks",
        json={
            "title": "Simple Task Without Retrieval",
            "instructions": "Say hello to the user.",
        },
    )
    task_id = task_res.json()["id"]

    run_res = auth_client.post(
        f"/api/tasks/{task_id}/run",
        json={
            "model": "mock-model-v1",
            "retrieval_enabled": False,
        },
    )
    assert run_res.status_code == 201
    run_data = run_res.json()
    assert run_data["status"] == "completed"
    assert run_data["retrieval_enabled"] is False
    assert not run_data.get("retrieved_chunk_count")


def test_rag_cross_tenant_retrieval_isolation(client, user1_auth, user2_auth):
    """
    Verifies that User 1 cannot retrieve document chunks belonging to User 2's workspace.
    """
    h1 = user1_auth["headers"]
    h2 = user2_auth["headers"]

    # User 2 uploads confidential document in User 2's workspace
    ws2_res = client.post("/api/workspaces", json={"name": "User 2 Confidential WS"}, headers=h2)
    assert ws2_res.status_code == 201
    ws2_id = ws2_res.json()["id"]

    secret_content = b"TOP SECRET PROJECT PLANS FOR USER 2 ONLY - CODE RED DELTA."
    doc2_res = client.post(
        f"/api/workspaces/{ws2_id}/documents",
        headers=h2,
        files={"file": ("user2_secret.txt", io.BytesIO(secret_content), "text/plain")},
    )
    assert doc2_res.status_code == 201

    # User 1 creates workspace and task searching for User 2's secret phrase
    ws1_res = client.post("/api/workspaces", json={"name": "User 1 Research WS"}, headers=h1)
    ws1_id = ws1_res.json()["id"]

    proj1_res = client.post(f"/api/workspaces/{ws1_id}/projects", json={"name": "User 1 Proj"}, headers=h1)
    proj1_id = proj1_res.json()["id"]

    task1_res = client.post(
        f"/api/projects/{proj1_id}/tasks",
        json={
            "title": "Search Secrets",
            "instructions": "Find TOP SECRET PROJECT PLANS FOR USER 2 ONLY - CODE RED DELTA.",
        },
        headers=h1,
    )
    task1_id = task1_res.json()["id"]

    # User 1 runs task with retrieval enabled
    run_res = client.post(
        f"/api/tasks/{task1_id}/run",
        json={
            "model": "mock-model-v1",
            "retrieval_enabled": True,
            "retrieval_top_k": 10,
        },
        headers=h1,
    )
    assert run_res.status_code == 201
    run_data = run_res.json()

    # User 1 must NOT receive any chunks from User 2
    assert run_data["retrieved_chunk_count"] == 0
    assert not run_data.get("retrieval_sources")
