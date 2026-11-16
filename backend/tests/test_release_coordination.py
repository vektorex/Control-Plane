import pytest


def test_release_coordination_lifecycle_full(auth_client):
    # 1. Create Portfolio
    portfolio_payload = {
        "name": "Enterprise AI Portfolio",
        "description": "Cross-service portfolio for Q4 AI workflows",
    }
    p_resp = auth_client.post("/api/release-coordination/portfolios", json=portfolio_payload)
    assert p_resp.status_code == 201, p_resp.text
    portfolio = p_resp.json()
    portfolio_id = portfolio["id"]
    assert portfolio["name"] == portfolio_payload["name"]
    assert portfolio["status"] == "draft"

    # 2. List Portfolios
    list_p_resp = auth_client.get("/api/release-coordination/portfolios")
    assert list_p_resp.status_code == 200
    portfolios = list_p_resp.json()
    assert any(p["id"] == portfolio_id for p in portfolios)

    # 3. Get Portfolio
    get_p_resp = auth_client.get(f"/api/release-coordination/portfolios/{portfolio_id}")
    assert get_p_resp.status_code == 200
    assert get_p_resp.json()["id"] == portfolio_id

    # 4. Create Train
    train_payload = {
        "name": "Train Alpha - LLM Pipelines",
        "description": "Coordinated release train for model, prompt, and tool updates",
        "portfolio_id": portfolio_id,
    }
    t_resp = auth_client.post("/api/release-coordination/trains", json=train_payload)
    assert t_resp.status_code == 201, t_resp.text
    train = t_resp.json()
    train_id = train["id"]
    assert train["name"] == train_payload["name"]
    assert train["portfolio_id"] == portfolio_id

    # 5. List Trains & filter by portfolio
    list_t_resp = auth_client.get(f"/api/release-coordination/trains?portfolio_id={portfolio_id}")
    assert list_t_resp.status_code == 200
    trains = list_t_resp.json()
    assert any(t["id"] == train_id for t in trains)

    # 6. Get Train
    get_t_resp = auth_client.get(f"/api/release-coordination/trains/{train_id}")
    assert get_t_resp.status_code == 200
    assert get_t_resp.json()["id"] == train_id

    # 7. Add & Remove Release in Train
    add_rel_resp = auth_client.post(
        f"/api/release-coordination/trains/{train_id}/releases",
        json={"release_id": "rel-001"}
    )
    assert add_rel_resp.status_code == 200
    assert add_rel_resp.json()["status"] == "added"

    rem_rel_resp = auth_client.delete(f"/api/release-coordination/trains/{train_id}/releases/rel-001")
    assert rem_rel_resp.status_code == 200
    assert rem_rel_resp.json()["status"] == "removed"

    # 8. Add & Get & Remove Dependency
    dep_resp = auth_client.post(
        f"/api/release-coordination/trains/{train_id}/dependencies",
        json={
            "source_release_id": "rel-001",
            "target_release_id": "rel-002",
            "dependency_type": "blocks",
        }
    )
    assert dep_resp.status_code == 200
    dep_data = dep_resp.json()
    assert dep_data["status"] == "added"
    dep_id = dep_data["dependency_id"]

    get_deps_resp = auth_client.get(f"/api/release-coordination/trains/{train_id}/dependencies")
    assert get_deps_resp.status_code == 200
    deps = get_deps_resp.json()
    assert any(d["id"] == dep_id for d in deps)

    del_dep_resp = auth_client.delete(f"/api/release-coordination/trains/{train_id}/dependencies/{dep_id}")
    assert del_dep_resp.status_code == 200
    assert del_dep_resp.json()["status"] == "removed"

    # 9. Train Actions: Analyze, Sequence, Validate, Schedule, Handoff
    an_resp = auth_client.post(f"/api/release-coordination/trains/{train_id}/analyze")
    assert an_resp.status_code == 200
    assert an_resp.json()["status"] == "analyzed"

    seq_resp = auth_client.post(f"/api/release-coordination/trains/{train_id}/sequence")
    assert seq_resp.status_code == 200
    assert seq_resp.json()["status"] == "sequenced"

    val_resp = auth_client.post(f"/api/release-coordination/trains/{train_id}/validate")
    assert val_resp.status_code == 200
    assert val_resp.json()["status"] == "validated"

    sch_resp = auth_client.post(f"/api/release-coordination/trains/{train_id}/schedule")
    assert sch_resp.status_code == 200
    assert sch_resp.json()["status"] == "scheduled"

    ho_resp = auth_client.post(f"/api/release-coordination/trains/{train_id}/handoff")
    assert ho_resp.status_code == 200
    assert ho_resp.json()["status"] == "handed_off"

    # 10. Train Inspection: Conflicts, Waves, Calendar, Timeline
    conf_resp = auth_client.get(f"/api/release-coordination/trains/{train_id}/conflicts")
    assert conf_resp.status_code == 200
    assert isinstance(conf_resp.json(), list)

    wave_resp = auth_client.post(
        f"/api/release-coordination/trains/{train_id}/waves",
        json={"name": "Wave 1 - Foundational Models", "sequence_number": 1}
    )
    assert wave_resp.status_code == 200
    assert wave_resp.json()["status"] == "created"

    get_waves_resp = auth_client.get(f"/api/release-coordination/trains/{train_id}/waves")
    assert get_waves_resp.status_code == 200
    assert len(get_waves_resp.json()) >= 1

    cal_resp = auth_client.get(f"/api/release-coordination/trains/{train_id}/calendar")
    assert cal_resp.status_code == 200
    assert len(cal_resp.json()) >= 1

    tl_resp = auth_client.get(f"/api/release-coordination/trains/{train_id}/timeline")
    assert tl_resp.status_code == 200
    assert len(tl_resp.json()) >= 1

    # 11. Coordination Level: Windows, Calendar, Conflicts, Overview
    win_create = auth_client.post(
        "/api/release-coordination/windows",
        json={"name": "Weekly Maintenance Window", "window_type": "standard"}
    )
    assert win_create.status_code == 200
    assert win_create.json()["status"] == "created"

    win_list = auth_client.get("/api/release-coordination/windows")
    assert win_list.status_code == 200
    assert len(win_list.json()) >= 1

    coord_cal = auth_client.get("/api/release-coordination/calendar")
    assert coord_cal.status_code == 200
    assert isinstance(coord_cal.json(), list)

    coord_conf = auth_client.get("/api/release-coordination/conflicts")
    assert coord_conf.status_code == 200
    assert isinstance(coord_conf.json(), list)

    overview = auth_client.get("/api/release-coordination/overview")
    assert overview.status_code == 200
    ov_data = overview.json()
    assert ov_data["active_trains"] >= 1
    assert ov_data["windows"] >= 1


def test_coordination_not_found(auth_client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    assert auth_client.get(f"/api/release-coordination/portfolios/{fake_id}").status_code == 404
    assert auth_client.get(f"/api/release-coordination/trains/{fake_id}").status_code == 404
