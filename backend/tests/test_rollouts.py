import pytest


def test_rollout_lifecycle_full(auth_client):
    # 1. Setup change request & release
    change_resp = auth_client.post("/api/changes", json={
        "title": "Model Switch for Classification",
        "change_type": "model_configuration_change",
        "subject_type": "model_config",
        "subject_id": "model-classifier-v2",
    })
    assert change_resp.status_code == 201
    change_id = change_resp.json()["id"]

    release_resp = auth_client.post("/api/releases", json={
        "name": "Release Classification Model v2",
        "change_request_id": change_id,
        "release_type": "model_configuration_change",
        "source_environment": "staging",
        "target_environment": "production",
    })
    assert release_resp.status_code == 201
    release_id = release_resp.json()["id"]

    # 2. Create Rollout
    rollout_payload = {
        "name": "Progressive Canary Rollout - Model v2",
        "description": "Gradual 10 -> 50 -> 100 canary release",
        "release_id": release_id,
        "strategy_type": "canary",
        "target_scope": {"environment": "production", "region": "us-east-1"},
        "policy": {"max_error_rate": 0.01, "rollback_on_gate_failure": True},
    }
    create_resp = auth_client.post("/api/rollouts", json=rollout_payload)
    assert create_resp.status_code == 201, create_resp.text
    rollout = create_resp.json()
    rollout_id = rollout["id"]
    assert rollout["name"] == rollout_payload["name"]
    assert rollout["status"] == "draft"
    assert rollout["strategy_type"] == "canary"

    # 3. List Rollouts & Filters
    list_resp = auth_client.get("/api/rollouts")
    assert list_resp.status_code == 200
    all_rollouts = list_resp.json()
    assert any(r["id"] == rollout_id for r in all_rollouts)

    filter_resp = auth_client.get(f"/api/rollouts?release_id={release_id}&status=draft")
    assert filter_resp.status_code == 200
    filtered = filter_resp.json()
    assert any(r["id"] == rollout_id for r in filtered)

    # 4. Get Rollout by ID
    get_resp = auth_client.get(f"/api/rollouts/{rollout_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == rollout_id

    # 5. Validate Rollout
    val_resp = auth_client.post(f"/api/rollouts/{rollout_id}/validate")
    assert val_resp.status_code == 200
    assert val_resp.json()["status"] == "ready"

    # 6. Start Rollout
    start_resp = auth_client.post(f"/api/rollouts/{rollout_id}/start")
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "running"

    # 7. Pause Rollout
    pause_resp = auth_client.post(f"/api/rollouts/{rollout_id}/pause")
    assert pause_resp.status_code == 200
    assert pause_resp.json()["status"] == "paused"

    # 8. Resume Rollout
    resume_resp = auth_client.post(f"/api/rollouts/{rollout_id}/resume")
    assert resume_resp.status_code == 200
    assert resume_resp.json()["status"] == "running"

    # 9. Abort Rollout
    abort_resp = auth_client.post(f"/api/rollouts/{rollout_id}/abort")
    assert abort_resp.status_code == 200
    assert abort_resp.json()["status"] == "cancelled"

    # 10. Get Rollout Stages
    stages_resp = auth_client.get(f"/api/rollouts/{rollout_id}/stages")
    assert stages_resp.status_code == 200
    stages = stages_resp.json()
    assert len(stages) == 3
    assert stages[0]["target_percentage"] == 10

    # 11. Get Rollout Health
    health_resp = auth_client.get(f"/api/rollouts/{rollout_id}/health")
    assert health_resp.status_code == 200
    health = health_resp.json()
    assert len(health) > 0
    assert health[0]["healthy"] is True

    # 12. Get Rollout Evidence
    evi_resp = auth_client.get(f"/api/rollouts/{rollout_id}/evidence")
    assert evi_resp.status_code == 200
    evidence = evi_resp.json()
    assert len(evidence) > 0
    assert evidence[0]["verified"] is True


def test_rollout_not_found(auth_client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    assert auth_client.get(f"/api/rollouts/{fake_id}").status_code == 404
    assert auth_client.post(f"/api/rollouts/{fake_id}/validate").status_code == 404
    assert auth_client.post(f"/api/rollouts/{fake_id}/start").status_code == 404
    assert auth_client.post(f"/api/rollouts/{fake_id}/pause").status_code == 404
    assert auth_client.post(f"/api/rollouts/{fake_id}/resume").status_code == 404
    assert auth_client.post(f"/api/rollouts/{fake_id}/abort").status_code == 404
