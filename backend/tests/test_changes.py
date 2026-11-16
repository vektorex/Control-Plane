import pytest


def test_change_intelligence_lifecycle_full(auth_client):
    # 1. Create Change Request
    payload = {
        "title": "Update RAG embedding model configuration",
        "description": "Switching embeddings from text-embedding-ada-002 to text-embedding-3-small",
        "change_type": "model_configuration_change",
        "subject_type": "embedding_config",
        "subject_id": "emb-config-v2",
        "scope": {"service": "retrieval", "pipeline": "vector_search"},
        "proposed_change": {"dimensions": 1536, "model": "text-embedding-3-small"},
        "reason": "Lower cost and improved retrieval recall",
        "expected_benefit": "35% lower embedding latency and 12% MRR boost",
    }
    create_resp = auth_client.post("/api/changes", json=payload)
    assert create_resp.status_code == 201, create_resp.text
    change_req = create_resp.json()
    change_id = change_req["id"]
    assert change_req["title"] == payload["title"]
    assert change_req["status"] == "draft"

    # 2. List Change Requests
    list_resp = auth_client.get("/api/changes")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert any(c["id"] == change_id for c in items)

    # 3. Get Change Request
    get_resp = auth_client.get(f"/api/changes/{change_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == change_id

    # 4. Parse Change
    parse_resp = auth_client.post(f"/api/changes/{change_id}/parse")
    assert parse_resp.status_code == 200
    assert parse_resp.json()["status"] == "parsed"

    # 5. Analyze Change
    analyze_resp = auth_client.post(f"/api/changes/{change_id}/analyze")
    assert analyze_resp.status_code == 200
    summary = analyze_resp.json()
    assert summary["direct_impacts"] >= 1
    assert summary["indirect_impacts"] >= 1
    assert summary["revalidation_reqs"] >= 1

    # 6. Get Impact
    impact_resp = auth_client.get(f"/api/changes/{change_id}/impact")
    assert impact_resp.status_code == 200
    impacts = impact_resp.json()
    assert len(impacts) >= 2
    assert any(i["impact_type"] == "direct" for i in impacts)

    # 7. Get Dependencies
    deps_resp = auth_client.get(f"/api/changes/{change_id}/dependencies")
    assert deps_resp.status_code == 200
    deps = deps_resp.json()
    assert len(deps) >= 2

    # 8. Get Risks
    risks_resp = auth_client.get(f"/api/changes/{change_id}/risks")
    assert risks_resp.status_code == 200
    risks = risks_resp.json()
    assert len(risks) >= 1
    assert "risk" in risks[0]

    # 9. Get Evidence
    evi_resp = auth_client.get(f"/api/changes/{change_id}/evidence")
    assert evi_resp.status_code == 200
    evidence = evi_resp.json()
    assert len(evidence) >= 1
    assert evidence[0]["verified"] is True

    # 10. Get Rollback Analysis
    rb_resp = auth_client.get(f"/api/changes/{change_id}/rollback")
    assert rb_resp.status_code == 200
    rb_data = rb_resp.json()
    assert rb_data["rollback_possible"] is True
    assert "resource" in rb_data


def test_change_not_found(auth_client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    assert auth_client.get(f"/api/changes/{fake_id}").status_code == 404
    assert auth_client.post(f"/api/changes/{fake_id}/parse").status_code == 404
    assert auth_client.post(f"/api/changes/{fake_id}/analyze").status_code == 404
    assert auth_client.get(f"/api/changes/{fake_id}/impact").status_code == 404
    assert auth_client.get(f"/api/changes/{fake_id}/dependencies").status_code == 404
    assert auth_client.get(f"/api/changes/{fake_id}/risks").status_code == 404
    assert auth_client.get(f"/api/changes/{fake_id}/evidence").status_code == 404
    assert auth_client.get(f"/api/changes/{fake_id}/rollback").status_code == 404
