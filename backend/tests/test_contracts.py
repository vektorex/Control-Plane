import pytest


def test_contracts_listing_and_lifecycle(auth_client):
    # 1. List contracts initially
    initial_resp = auth_client.get("/api/contracts")
    assert initial_resp.status_code == 200
    assert isinstance(initial_resp.json(), list)

    # 2. Create a contract
    contract_payload = {
        "name": "Model SLA Contract - Support Agent",
        "contract_type": "operational",
        "description": "Defines SLA metrics and deliverables for Support Agent",
        "workspace_id": "default-workspace",
        "requester_type": "user",
        "requester_id": "usr-12345",
    }
    create_resp = auth_client.post("/api/contracts", json=contract_payload)
    assert create_resp.status_code == 200, create_resp.text
    contract = create_resp.json()
    contract_id = contract["id"]
    assert contract["name"] == contract_payload["name"]
    assert contract["status"] == "draft"

    # 3. List contracts again and check created contract is included
    list_resp = auth_client.get("/api/contracts")
    assert list_resp.status_code == 200
    contracts = list_resp.json()
    assert any(c["id"] == contract_id for c in contracts)

    # 4. Filter by workspace_id
    filtered_resp = auth_client.get("/api/contracts?workspace_id=default-workspace")
    assert filtered_resp.status_code == 200
    filtered = filtered_resp.json()
    assert any(c["id"] == contract_id for c in filtered)

    # 5. Get contract
    get_resp = auth_client.get(f"/api/contracts/{contract_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == contract_id
