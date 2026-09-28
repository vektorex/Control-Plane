import json
import pytest
from uuid import uuid4


@pytest.fixture
def execution_test_setup(auth_client):
    """Sets up a workspace, project, and task with manual context for execution testing."""
    suffix = uuid4().hex[:8]
    # 1. Workspace
    ws_res = auth_client.post("/api/workspaces", json={"name": f"Exec WS {suffix}"})
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]

    # 2. Project
    proj_res = auth_client.post(f"/api/workspaces/{ws_id}/projects", json={"name": f"Exec Proj {suffix}"})
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["id"]

    # 3. Task
    task_res = auth_client.post(
        f"/api/projects/{proj_id}/tasks",
        json={
            "title": "Code Review Task",
            "instructions": "Audit code for SQL injection vulnerabilities",
            "context_text": "Using SQLAlchemy async ORM with parameterized queries.",
        },
    )
    assert task_res.status_code == 201
    task_id = task_res.json()["id"]

    # 4. Add manual context item
    auth_client.post(
        f"/api/tasks/{task_id}/context",
        json={
            "title": "Coding Standard Guideline",
            "content": "Raw SQL strings using text() must always use bound parameters (:param).",
            "priority": 85,
        },
    )

    return {
        "workspace_id": ws_id,
        "project_id": proj_id,
        "task_id": task_id,
    }


def test_task_execution_with_context_telemetry(auth_client, execution_test_setup):
    """Tests that executing a task captures context telemetry in the Run record."""
    task_id = execution_test_setup["task_id"]

    run_res = auth_client.post(
        f"/api/tasks/{task_id}/run",
        json={
            "model": "mock-model-v1",
            "temperature": 0.2,
            "max_context_tokens": 8000,
        },
    )
    assert run_res.status_code == 201
    run_data = run_res.json()

    assert run_data["status"] == "completed"
    assert run_data["context_item_count"] >= 2  # Task background context + Manual context item
    assert run_data["estimated_context_tokens"] > 0
    assert run_data["context_truncated"] is False
    assert "task" in run_data["context_sources"]
    assert "manual" in run_data["context_sources"]

    # Verify input_snapshot has context summary
    assert "input_snapshot" in run_data
    snapshot = run_data["input_snapshot"]
    assert "context_summary" in snapshot
    assert snapshot["context_summary"]["item_count"] == run_data["context_item_count"]
    assert snapshot["context_summary"]["truncated"] is False


def test_task_execution_budget_truncation(auth_client, execution_test_setup):
    """Tests that specifying a tight max_context_tokens truncates context and records flag in Run."""
    task_id = execution_test_setup["task_id"]

    # Execute with very low context budget
    run_res = auth_client.post(
        f"/api/tasks/{task_id}/run",
        json={
            "model": "mock-model-v1",
            "temperature": 0.1,
            "max_context_tokens": 20,  # Tight budget
        },
    )
    assert run_res.status_code == 201
    run_data = run_res.json()

    assert run_data["status"] == "completed"
    assert run_data["context_truncated"] is True
    assert run_data["input_snapshot"]["context_summary"]["truncated"] is True


def test_task_execution_streaming_with_context(auth_client, execution_test_setup):
    """Tests SSE streaming execution delivering context metadata in initial event."""
    task_id = execution_test_setup["task_id"]

    stream_res = auth_client.post(
        f"/api/tasks/{task_id}/run/stream",
        json={
            "model": "mock-model-v1",
            "temperature": 0.2,
            "max_context_tokens": 8000,
        },
    )
    assert stream_res.status_code == 200

    lines = stream_res.text.strip().split("\n\n")
    first_event = None
    completed_event = None

    for line in lines:
        if line.startswith("data:"):
            data_str = line[5:].strip()
            if data_str == "[DONE]":
                continue
            try:
                parsed = json.loads(data_str)
                if parsed.get("type") == "run_start" and not first_event:
                    first_event = parsed
                if parsed.get("type") == "run_completed":
                    completed_event = parsed
            except Exception:
                pass

    assert first_event is not None
    assert first_event["type"] == "run_start"
    assert first_event["context_item_count"] >= 2
    assert first_event["estimated_context_tokens"] > 0

    assert completed_event is not None
    run_payload = completed_event["run"]
    assert run_payload["status"] == "completed"
    assert run_payload["context_item_count"] >= 2
    assert run_payload["estimated_context_tokens"] > 0
