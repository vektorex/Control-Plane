import pytest
import uuid


def test_create_and_list_runs_for_task(client):
    # 1. Create Workspace -> Project -> Task
    ws_res = client.post("/api/workspaces", json={"name": "WS Runs Test"})
    ws_id = ws_res.json()["id"]

    proj_res = client.post(f"/api/workspaces/{ws_id}/projects", json={"name": "Proj Runs Test"})
    proj_id = proj_res.json()["id"]

    task_res = client.post(f"/api/projects/{proj_id}/tasks", json={"title": "Task for Execution Runs"})
    task_id = task_res.json()["id"]

    # 2. Record Run
    run_payload = {
        "status": "completed",
        "model_provider": "openai",
        "model_name": "gpt-4o-mini",
        "input_tokens": 120,
        "output_tokens": 45,
        "total_tokens": 165,
        "latency_ms": 820,
    }
    run_res = client.post(f"/api/tasks/{task_id}/runs", json=run_payload)
    assert run_res.status_code == 201
    run_data = run_res.json()
    assert run_data["status"] == "completed"
    assert run_data["model_provider"] == "openai"
    assert run_data["model_name"] == "gpt-4o-mini"
    assert run_data["total_tokens"] == 165
    assert run_data["task_id"] == task_id
    run_id = run_data["id"]

    # 3. Retrieve Runs for Task
    list_res = client.get(f"/api/tasks/{task_id}/runs")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(r["id"] == run_id for r in list_data["runs"])


def test_runs_not_found_on_invalid_task(client):
    random_id = str(uuid.uuid4())
    res = client.get(f"/api/tasks/{random_id}/runs")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOT_FOUND"
