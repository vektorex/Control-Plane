import json
from backend.app.main import app
from backend.app.services.llm.factory import get_llm_factory, LLMProviderFactory
from backend.tests.conftest import MockTestProvider


def test_generate_success(client):
    payload = {
        "model": "mock-model-v1",
        "messages": [
            {"role": "user", "content": "Hello, work layer!"}
        ],
        "temperature": 0.5,
    }
    response = client.post("/api/llm/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Mock response for: Hello, work layer!"
    assert data["model"] == "mock-model-v1"
    assert data["provider"] == "mock_provider"
    assert data["usage"]["input_tokens"] == 15
    assert data["usage"]["output_tokens"] == 25
    assert data["usage"]["total_tokens"] == 40


def test_generate_validation_error_empty_messages(client):
    payload = {
        "model": "mock-model-v1",
        "messages": [],
    }
    response = client.post("/api/llm/generate", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_generate_validation_error_invalid_temperature(client):
    payload = {
        "model": "mock-model-v1",
        "messages": [{"role": "user", "content": "test"}],
        "temperature": 5.0,  # Max is 2.0
    }
    response = client.post("/api/llm/generate", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_generate_model_not_found(client):
    payload = {
        "model": "completely-unknown-model-xyz",
        "messages": [{"role": "user", "content": "test"}],
    }
    response = client.post("/api/llm/generate", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "MODEL_NOT_FOUND"


def test_generate_stream_success(client):
    payload = {
        "model": "mock-model-v1",
        "messages": [{"role": "user", "content": "Stream me"}],
    }
    response = client.post("/api/llm/generate/stream", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    lines = [line.strip() for line in response.text.split("\n") if line.strip()]
    data_lines = [l for l in lines if l.startswith("data:")]

    assert len(data_lines) >= 2
    assert data_lines[-1] == "data: [DONE]"

    # Parse first data chunk
    first_chunk_json = json.loads(data_lines[0].replace("data: ", ""))
    assert "content" in first_chunk_json
    assert first_chunk_json["model"] == "mock-model-v1"


def test_generate_provider_auth_failure():
    factory = LLMProviderFactory()
    failing_provider = MockTestProvider(configured=True, should_fail=True, fail_type="auth")
    factory.register_provider(failing_provider)

    app.dependency_overrides[get_llm_factory] = lambda: factory
    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        response = test_client.post("/api/llm/generate", json={
            "model": "mock-model-v1",
            "messages": [{"role": "user", "content": "test"}]
        })
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "PROVIDER_AUTHENTICATION_ERROR"
    app.dependency_overrides.clear()


def test_generate_provider_rate_limit():
    factory = LLMProviderFactory()
    failing_provider = MockTestProvider(configured=True, should_fail=True, fail_type="rate_limit")
    factory.register_provider(failing_provider)

    app.dependency_overrides[get_llm_factory] = lambda: factory
    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        response = test_client.post("/api/llm/generate", json={
            "model": "mock-model-v1",
            "messages": [{"role": "user", "content": "test"}]
        })
        assert response.status_code == 429
        data = response.json()
        assert data["error"]["code"] == "PROVIDER_RATE_LIMIT_ERROR"
    app.dependency_overrides.clear()
