import json
import pytest
import uuid
from backend.app.main import app
from backend.app.services.llm.factory import get_llm_factory, LLMProviderFactory
from backend.tests.conftest import MockTestProvider, override_get_db


def test_authenticated_user_can_execute_own_task(auth_client):
    """Verify that an authenticated user can execute their task and persist a completed Run."""
    # 1. Create workspace, project, and task
    ws_res = auth_client.post("/api/workspaces", json={"name": "Execution Test WS"})
    ws_id = ws_res.json()["id"]

    proj_res = auth_client.post(f"/api/workspaces/{ws_id}/projects", json={"name": "Execution Project"})
    proj_id = proj_res.json()["id"]

    task_res = auth_client.post(
        f"/api/projects/{proj_id}/tasks",
        json={
            "title": "Analyze architecture",
            "instructions": "Extract key technical components and summarize latency expectations.",
            "context_text": "Antigravity system running on FastAPI + Next.js 15.",
        },
    )
    assert task_res.status_code == 201
    task_id = task_res.json()["id"]

    # 2. Execute the task
    run_res = auth_client.post(
        f"/api/tasks/{task_id}/run",
        json={"model": "mock-model-v1", "temperature": 0.3},
    )
    assert run_res.status_code == 201
    run_data = run_res.json()

    # 3. Verify Run attributes & telemetry persistence
    assert run_data["task_id"] == task_id
    assert run_data["status"] == "completed"
    assert run_data["model_name"] == "mock-model-v1"
    assert run_data["model_provider"] == "mock_provider"
    assert run_data["input_tokens"] == 15
    assert run_data["output_tokens"] == 25
    assert run_data["total_tokens"] == 40
    assert run_data["latency_ms"] is not None and run_data["latency_ms"] >= 0
    assert "Mock response for:" in run_data["output_content"]
    assert "Extract key technical components" in run_data["output_content"]
    assert run_data["input_snapshot"] is not None
    assert run_data["completed_at"] is not None


def test_unauthenticated_execution_rejected(client):
    """Verify that unauthenticated execution requests return 401."""
    random_task_id = str(uuid.uuid4())
    res = client.post(f"/api/tasks/{random_task_id}/run", json={})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

    stream_res = client.post(f"/api/tasks/{random_task_id}/run/stream", json={})
    assert stream_res.status_code == 401


def test_another_user_cannot_execute_task(client, user1_auth, user2_auth):
    """User 1 owns a task; User 2 cannot execute it (returns 404 to avoid leaking existence)."""
    # User 1 sets up workspace, project, task
    ws_res = client.post("/api/workspaces", json={"name": "User 1 Space"}, headers=user1_auth["headers"])
    ws_id = ws_res.json()["id"]

    proj_res = client.post(f"/api/workspaces/{ws_id}/projects", json={"name": "User 1 Proj"}, headers=user1_auth["headers"])
    proj_id = proj_res.json()["id"]

    task_res = client.post(
        f"/api/projects/{proj_id}/tasks",
        json={"title": "Private Task", "instructions": "Private confidential instruction"},
        headers=user1_auth["headers"],
    )
    task_id = task_res.json()["id"]

    # User 2 attempts execution
    attack_res = client.post(
        f"/api/tasks/{task_id}/run",
        json={"model": "mock-model-v1"},
        headers=user2_auth["headers"],
    )
    assert attack_res.status_code == 404
    assert attack_res.json()["error"]["code"] == "NOT_FOUND"


def test_run_detail_enforces_ownership(client, user1_auth, user2_auth):
    """User 1 executes task; User 2 cannot retrieve run details via GET /api/runs/{run_id}."""
    # User 1 setup & run
    me1 = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws1_id = me1["default_workspace_id"]

    proj_res = client.post(f"/api/workspaces/{ws1_id}/projects", json={"name": "Runs Test Proj"}, headers=user1_auth["headers"])
    proj_id = proj_res.json()["id"]

    task_res = client.post(
        f"/api/projects/{proj_id}/tasks",
        json={"title": "Run Detail Task", "instructions": "Explain quantum computing."},
        headers=user1_auth["headers"],
    )
    task_id = task_res.json()["id"]

    run_res = client.post(
        f"/api/tasks/{task_id}/run",
        json={"model": "mock-model-v1"},
        headers=user1_auth["headers"],
    )
    run_id = run_res.json()["id"]

    # User 1 can view run detail
    get_run1 = client.get(f"/api/runs/{run_id}", headers=user1_auth["headers"])
    assert get_run1.status_code == 200
    assert get_run1.json()["id"] == run_id
    assert get_run1.json()["status"] == "completed"

    # User 2 gets 404
    get_run2 = client.get(f"/api/runs/{run_id}", headers=user2_auth["headers"])
    assert get_run2.status_code == 404
    assert get_run2.json()["error"]["code"] == "NOT_FOUND"


def test_provider_failure_persists_failed_run(client, user1_auth):
    """Verify that upstream provider failures persist a failed Run with error message."""
    failing_factory = LLMProviderFactory()
    failing_provider = MockTestProvider(configured=True, should_fail=True, fail_type="api_error")
    failing_factory.register_provider(failing_provider)

    app.dependency_overrides[get_llm_factory] = lambda: failing_factory

    # Setup task
    me1 = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws_id = me1["default_workspace_id"]

    proj_res = client.post(f"/api/workspaces/{ws_id}/projects", json={"name": "Failure Test Proj"}, headers=user1_auth["headers"])
    proj_id = proj_res.json()["id"]

    task_res = client.post(
        f"/api/projects/{proj_id}/tasks",
        json={"title": "Failing Task", "instructions": "This will fail"},
        headers=user1_auth["headers"],
    )
    task_id = task_res.json()["id"]

    # Attempt execution (will raise error)
    run_attempt = client.post(
        f"/api/tasks/{task_id}/run",
        json={"model": "mock-model-v1"},
        headers=user1_auth["headers"],
    )
    assert run_attempt.status_code >= 400

    # Verify that a Run was recorded with status='failed'
    runs_res = client.get(f"/api/tasks/{task_id}/runs", headers=user1_auth["headers"])
    assert runs_res.status_code == 200
    runs = runs_res.json()["runs"]
    assert len(runs) >= 1
    failed_run = runs[0]
    assert failed_run["status"] == "failed"
    assert failed_run["error_message"] is not None
    assert "Mock upstream API failure" in failed_run["error_message"]

    app.dependency_overrides.clear()


def test_task_streaming_execution(auth_client):
    """Verify that POST /api/tasks/{task_id}/run/stream streams chunks and completes the Run."""
    ws_res = auth_client.post("/api/workspaces", json={"name": "Streaming WS"})
    ws_id = ws_res.json()["id"]

    proj_res = auth_client.post(f"/api/workspaces/{ws_id}/projects", json={"name": "Streaming Proj"})
    proj_id = proj_res.json()["id"]

    task_res = auth_client.post(
        f"/api/projects/{proj_id}/tasks",
        json={"title": "Stream Task", "instructions": "Stream this content live."},
    )
    task_id = task_res.json()["id"]

    stream_res = auth_client.post(
        f"/api/tasks/{task_id}/run/stream",
        json={"model": "mock-model-v1", "temperature": 0.5},
    )
    assert stream_res.status_code == 200
    assert "text/event-stream" in stream_res.headers["content-type"]

    lines = [line.strip() for line in stream_res.text.split("\n") if line.strip()]
    data_lines = [l.replace("data: ", "") for l in lines if l.startswith("data:")]

    assert len(data_lines) >= 3
    assert data_lines[-1] == "[DONE]"

    # Verify run_start event
    first_event = json.loads(data_lines[0])
    assert first_event["type"] == "run_start"
    run_id = first_event["run_id"]

    # Verify run_completed event
    completed_event = json.loads(data_lines[-2])
    assert completed_event["type"] == "run_completed"
    assert completed_event["run"]["status"] == "completed"
    assert completed_event["run"]["output_content"] == "Mock streamed response!"

    # Verify persisted run via GET /api/runs/{run_id}
    persisted_run = auth_client.get(f"/api/runs/{run_id}").json()
    assert persisted_run["status"] == "completed"
    assert persisted_run["output_content"] == "Mock streamed response!"
    assert persisted_run["total_tokens"] == 18
