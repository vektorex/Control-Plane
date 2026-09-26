def test_models_endpoint(client):
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert "providers" in data
    assert len(data["models"]) > 0
    assert len(data["providers"]) > 0

    # Verify model structure
    first_model = data["models"][0]
    assert "id" in first_model
    assert "name" in first_model
    assert "provider" in first_model
    assert "supports_streaming" in first_model

    # Verify mock model is present
    model_ids = [m["id"] for m in data["models"]]
    assert "mock-model-v1" in model_ids
