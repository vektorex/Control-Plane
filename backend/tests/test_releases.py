import pytest


def test_release_lifecycle_full(auth_client):
    # 1. Create a change request to reference
    change_payload = {
        "title": "Prompt Optimization for Chat Assistant",
        "description": "Improving context window usage and system instructions",
        "change_type": "prompt_update",
        "subject_type": "prompt",
        "subject_id": "prompt-chat-v1",
        "reason": "Improve response accuracy",
        "expected_benefit": "Higher benchmark scores",
    }
    change_resp = auth_client.post("/api/changes", json=change_payload)
    assert change_resp.status_code == 201, change_resp.text
    change_data = change_resp.json()
    change_id = change_data["id"]

    # 2. Create Release
    release_payload = {
        "name": "Release v1.1.0 - Assistant Prompt",
        "description": "Production rollout for prompt optimizations",
        "change_request_id": change_id,
        "release_type": "prompt_release",
        "source_environment": "staging",
        "target_environment": "production",
    }
    create_resp = auth_client.post("/api/releases", json=release_payload)
    assert create_resp.status_code == 201, create_resp.text
    rel = create_resp.json()
    release_id = rel["id"]
    assert rel["name"] == release_payload["name"]
    assert rel["status"] == "draft"
    assert rel["change_request_id"] == change_id

    # 3. List Releases & Filter by status
    list_resp = auth_client.get("/api/releases")
    assert list_resp.status_code == 200
    all_releases = list_resp.json()
    assert any(r["id"] == release_id for r in all_releases)

    filter_resp = auth_client.get("/api/releases?status=draft")
    assert filter_resp.status_code == 200
    filtered = filter_resp.json()
    assert all(r["status"] == "draft" for r in filtered)

    # 4. Get Release by ID
    get_resp = auth_client.get(f"/api/releases/{release_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == release_id

    # 5. Build Release Plan
    plan_resp = auth_client.post(f"/api/releases/{release_id}/build-plan")
    assert plan_resp.status_code == 200
    assert plan_resp.json()["status"] == "planning"

    get_plan_resp = auth_client.get(f"/api/releases/{release_id}/plan")
    assert get_plan_resp.status_code == 200
    plan_body = get_plan_resp.json()
    assert "stages" in plan_body
    assert len(plan_body["stages"]) >= 3

    # 6. Validate Release
    val_resp = auth_client.post(f"/api/releases/{release_id}/validate")
    assert val_resp.status_code == 200
    assert val_resp.json()["status"] == "ready"

    # 7. Submit for Approval
    appr_resp = auth_client.post(f"/api/releases/{release_id}/submit-approval")
    assert appr_resp.status_code == 200
    assert appr_resp.json()["status"] == "approval_required"

    # 8. Deploy to Staging
    stage_resp = auth_client.post(f"/api/releases/{release_id}/stage")
    assert stage_resp.status_code == 200
    assert stage_resp.json()["status"] == "in_progress"

    # 9. Verify Staging
    vstage_resp = auth_client.post(f"/api/releases/{release_id}/verify-staging")
    assert vstage_resp.status_code == 200
    assert vstage_resp.json()["status"] == "verifying"

    # 10. Promote Release
    promote_resp = auth_client.post(f"/api/releases/{release_id}/promote")
    assert promote_resp.status_code == 200
    assert promote_resp.json()["status"] == "in_progress"

    # 11. Complete Release
    comp_resp = auth_client.post(f"/api/releases/{release_id}/complete")
    assert comp_resp.status_code == 200
    assert comp_resp.json()["status"] == "completed"

    # 12. Execute Rollback
    rb_resp = auth_client.post(f"/api/releases/{release_id}/rollback")
    assert rb_resp.status_code == 200
    assert rb_resp.json()["status"] == "rolled_back"

    # 13. Get Evidence
    evi_resp = auth_client.get(f"/api/releases/{release_id}/evidence")
    assert evi_resp.status_code == 200
    evidence_list = evi_resp.json()
    assert len(evidence_list) > 0
    assert evidence_list[0]["verified"] is True

    # 14. Get Timeline
    timeline_resp = auth_client.get(f"/api/releases/{release_id}/timeline")
    assert timeline_resp.status_code == 200
    timeline = timeline_resp.json()
    assert len(timeline) >= 5


def test_release_not_found(auth_client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    assert auth_client.get(f"/api/releases/{fake_id}").status_code == 404
    assert auth_client.post(f"/api/releases/{fake_id}/build-plan").status_code == 404
    assert auth_client.get(f"/api/releases/{fake_id}/plan").status_code == 404
    assert auth_client.post(f"/api/releases/{fake_id}/validate").status_code == 404
