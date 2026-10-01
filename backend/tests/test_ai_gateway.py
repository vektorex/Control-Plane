import asyncio
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from backend.app.schemas.llm import LLMGenerateResponse, LLMStreamChunk, TokenUsage
from backend.app.services.ai_gateway import (
    AIGateway,
    AllFallbacksFailedError,
    CircuitBreaker,
    CircuitOpenError,
    ConcurrencyLimiter,
    ConcurrencyLimitError,
    FallbackEngine,
    GatewayError,
    GatewayRequest,
    GatewayResponse,
    GatewayUsage,
    ModelNotAllowedError,
    ModelNotFoundError,
    ModelProviderAdapter,
    ModelTimeoutError,
    NormalizedStreamEvent,
    OpenAIAdapter,
    MockAdapter,
    PolicyDeniedError,
    ProviderRegistry,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitedError,
    RetryPolicy,
    WorkspaceModelPolicyManager,
    default_ai_gateway,
    default_health_service,
    default_provider_registry,
)
from backend.app.services.models.base import FallbackCandidate, ModelDefinition, ModelRequirements


# =============================================================================
# 1. Request, Response, and Streaming Normalization Tests
# =============================================================================

def test_gateway_request_normalization():
    req = GatewayRequest(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello world"}],
        temperature=0.5,
        max_tokens=200,
        stream=False,
    )
    assert req.model == "gpt-4o-mini"
    assert len(req.messages) == 1
    assert req.temperature == 0.5
    assert req.max_tokens == 200
    fp = req.get_fingerprint()
    assert isinstance(fp, str)
    assert len(fp) == 64  # SHA256 hex


def test_gateway_response_and_usage_normalization():
    usage = GatewayUsage(input_tokens=10, output_tokens=25, total_tokens=35, usage_source="provider", estimated_cost=0.00015)
    res = GatewayResponse(
        request_id="req-123",
        provider="mock",
        model="mock-gpt",
        content="Test content",
        usage=usage,
        latency_ms=45.2,
    )
    assert res.request_id == "req-123"
    assert res.provider == "mock"
    assert res.content == "Test content"
    assert res.usage.total_tokens == 35
    assert res.usage.estimated_cost == 0.00015


def test_normalized_streaming_events():
    d_evt = NormalizedStreamEvent.delta("Hello")
    assert d_evt["type"] == "delta"
    assert d_evt["content"] == "Hello"

    u_evt = NormalizedStreamEvent.usage({"input_tokens": 5, "output_tokens": 10, "total_tokens": 15}, estimated_cost=0.00005)
    assert u_evt["type"] == "usage"
    assert u_evt["usage"]["estimated_cost"] == 0.00005

    fb_evt = NormalizedStreamEvent.fallback(from_model="primary", to_model="backup", provider="mock", attempt=1)
    assert fb_evt["type"] == "model_fallback"
    assert fb_evt["from_model"] == "primary"

    c_evt = NormalizedStreamEvent.completed()
    assert c_evt["type"] == "completed"


# =============================================================================
# 2. Provider Adapter & Registry Tests
# =============================================================================

def test_provider_registry_lookup_and_metadata():
    reg = ProviderRegistry()
    assert reg.exists("mock")
    mock_adapter = reg.get("mock")
    assert mock_adapter.provider_id == "mock"
    assert mock_adapter.is_configured is True

    providers_list = reg.list()
    assert len(providers_list) >= 1
    mock_meta = next(p for p in providers_list if p["name"] == "mock")
    assert "Mock" in mock_meta["display_name"]
    assert "models" in mock_meta
    assert "api_key" not in str(mock_meta)  # Secrets never exposed


@pytest.mark.asyncio
async def test_mock_adapter_generate_and_stream():
    adapter = MockAdapter()
    req = GatewayRequest(
        model="mock-model",
        messages=[{"role": "user", "content": "Respond with greeting"}],
        temperature=0.0,
    )
    resp = await adapter.generate(req)
    assert resp.provider == "mock"
    assert resp.content != ""
    assert resp.usage.total_tokens > 0

    chunks = []
    async for event in adapter.generate_stream(req):
        chunks.append(event)
    assert any(c["type"] == "delta" for c in chunks)
    assert any(c["type"] == "completed" for c in chunks)


# =============================================================================
# 3. Workspace Model Policy Enforcement Tests
# =============================================================================

def test_workspace_policy_enforcement_allowed_providers():
    policy = {
        "allowed_providers": ["openai"],
        "allowed_models": [],
        "max_tokens_per_request": 1000,
    }
    req = GatewayRequest(
        model="mock-model",
        provider="mock",
        messages=[{"role": "user", "content": "hi"}],
    )
    with pytest.raises(PolicyDeniedError) as exc_info:
        WorkspaceModelPolicyManager.validate_request_policy(req, policy, resolved_provider="mock")
    assert "not permitted by workspace model policy" in str(exc_info.value)


def test_workspace_policy_enforcement_allowed_models():
    policy = {
        "allowed_providers": ["openai", "mock"],
        "allowed_models": ["gpt-4o-mini"],
        "max_tokens_per_request": 1000,
    }
    req = GatewayRequest(
        model="disallowed-model",
        provider="openai",
        messages=[{"role": "user", "content": "hi"}],
    )
    with pytest.raises(ModelNotAllowedError) as exc_info:
        WorkspaceModelPolicyManager.validate_request_policy(req, policy, resolved_provider="openai")
    assert "not permitted by workspace model policy" in str(exc_info.value)


def test_workspace_policy_enforcement_token_limit():
    policy = {
        "allowed_providers": ["openai", "mock"],
        "allowed_models": [],
        "max_tokens_per_request": 500,
    }
    req = GatewayRequest(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=1000,
    )
    with pytest.raises(PolicyDeniedError) as exc_info:
        WorkspaceModelPolicyManager.validate_request_policy(req, policy)
    assert "exceeds workspace policy limit" in str(exc_info.value)


# =============================================================================
# 4. Fallback Engine & Safety Tests
# =============================================================================

def test_fallback_eligibility():
    assert FallbackEngine.is_eligible_for_fallback(RateLimitedError("429 Too Many Requests")) is True
    assert FallbackEngine.is_eligible_for_fallback(ProviderTimeoutError("Timed out")) is True
    assert FallbackEngine.is_eligible_for_fallback(PolicyDeniedError("Disallowed provider")) is False
    assert FallbackEngine.is_eligible_for_fallback(ModelNotAllowedError("Disallowed model")) is False


def test_fallback_candidate_safety_resolution():
    candidates = [
        FallbackCandidate(provider="mock", model_id="gpt-4o-mini", display_name="GPT-4o Mini", reason="Backup"),
        FallbackCandidate(provider="openai", model_id="gpt-4o", display_name="GPT-4o", reason="High quality"),
    ]
    policy = {"allowed_providers": ["mock"], "allowed_models": []}
    req = GatewayRequest(model="test", messages=[{"role": "user", "content": "hi"}])
    safe = FallbackEngine.resolve_fallback_candidates(candidates, req, workspace_policy=policy)
    assert len(safe) == 1
    assert safe[0].provider == "mock"


# =============================================================================
# 5. Circuit Breaker & Health Service Tests
# =============================================================================

def test_circuit_breaker_lifecycle():
    cb = CircuitBreaker(failure_threshold=3, reset_seconds=0.5)
    key = "mock/test-model"

    assert cb.can_execute(key) is True
    assert cb.get_state(key) == "closed"

    # Fail 3 times -> circuit OPEN
    cb.record_failure(key)
    cb.record_failure(key)
    cb.record_failure(key)

    assert cb.get_state(key) == "open"
    assert cb.can_execute(key) is False

    # Success on recovery resets
    cb.record_success(key)
    assert cb.get_state(key) == "closed"
    assert cb.can_execute(key) is True


def test_model_health_service_metrics():
    health = default_health_service
    health.record_request_success("mock", "gpt-4o-mini", 120.0)
    rep = health.get_health_status(provider="mock", model="gpt-4o-mini")
    assert rep["total_requests"] >= 1
    assert rep["status"] in ("healthy", "degraded")
    assert rep["average_latency_ms"] > 0


# =============================================================================
# 6. Concurrency Limiter & Retry Policy Tests
# =============================================================================

@pytest.mark.asyncio
async def test_concurrency_limiter_bounds():
    limiter = ConcurrencyLimiter(max_concurrent=2)
    await limiter.acquire("ws-test", limit=2)
    await limiter.acquire("ws-test", limit=2)

    # 3rd acquire exceeds capacity
    with pytest.raises(ConcurrencyLimitError):
        await limiter.acquire("ws-test", limit=2)

    limiter.release("ws-test")
    # Now slot is free
    await limiter.acquire("ws-test", limit=2)
    limiter.release("ws-test")
    limiter.release("ws-test")


def test_retry_policy_classification():
    assert RetryPolicy.is_retryable(RateLimitedError("Rate limit reached")) is True
    assert RetryPolicy.is_retryable(ProviderTimeoutError("Timed out")) is True
    assert RetryPolicy.is_retryable(PolicyDeniedError("Forbidden")) is False
    assert RetryPolicy.is_retryable(ModelNotAllowedError("Not allowed")) is False
    assert RetryPolicy.get_backoff(1) == 0.25
    assert RetryPolicy.get_backoff(2) == 0.5


# =============================================================================
# 7. AI Gateway End-to-End Execution & Fallback Tests
# =============================================================================

@pytest.mark.asyncio
async def test_gateway_execute_success():
    gw = default_ai_gateway
    req = GatewayRequest(
        model="gpt-4o-mini",
        provider="mock",
        messages=[{"role": "user", "content": "What is the capital of France?"}],
        temperature=0.2,
    )
    res = await gw.execute(req)
    assert res.content != ""
    assert res.provider == "mock"
    assert res.usage.total_tokens > 0


@pytest.mark.asyncio
async def test_gateway_execute_fallback_on_transient_error():
    gw = AIGateway()
    # Mock primary adapter failing with rate limit
    mock_adapter = MockAdapter()
    call_count = 0

    async def flaky_generate(req: GatewayRequest) -> GatewayResponse:
        nonlocal call_count
        call_count += 1
        if req.model == "primary-model":
            raise RateLimitedError("Primary rate limit exceeded")
        return GatewayResponse(
            request_id="req-fb",
            provider="mock",
            model="backup-model",
            content="Recovered from fallback",
            usage=GatewayUsage(input_tokens=10, output_tokens=10, total_tokens=20),
            latency_ms=20.0,
        )

    mock_adapter.generate = flaky_generate
    reg = ProviderRegistry()
    reg.register(mock_adapter)
    gw.providers = reg

    # Create mock router that returns primary with backup fallback
    class MockRouter:
        def route_request(self, req, policy=None):
            from backend.app.services.models.base import ModelSelection
            return ModelSelection(
                provider="mock",
                model_id="primary-model",
                display_name="Primary",
                reason="Primary selection",
                fallback_candidates=[
                    FallbackCandidate(provider="mock", model_id="backup-model", display_name="Backup", reason="Fallback candidate")
                ],
            )

    gw.router = MockRouter()

    req = GatewayRequest(
        model="primary-model",
        provider="mock",
        messages=[{"role": "user", "content": "hello"}],
    )
    res = await gw.execute(req)
    assert res.model == "backup-model"
    assert res.content == "Recovered from fallback"


# =============================================================================
# 8. REST API Endpoints Tests
# =============================================================================

def test_gateway_api_models_endpoint(client: TestClient, user1_auth):
    resp = client.get("/api/gateway/models", headers=user1_auth["headers"])
    assert resp.status_code == 200
    models = resp.json()
    assert isinstance(models, list)
    assert len(models) > 0
    assert any("gpt-4o" in m["model_id"] for m in models)


def test_gateway_api_providers_endpoint(client: TestClient, user1_auth):
    resp = client.get("/api/gateway/providers", headers=user1_auth["headers"])
    assert resp.status_code == 200
    providers = resp.json()
    assert any(p["name"] == "mock" for p in providers)


def test_gateway_api_health_endpoint(client: TestClient, user1_auth):
    resp = client.get("/api/gateway/health", headers=user1_auth["headers"])
    assert resp.status_code == 200
    health_data = resp.json()
    assert health_data["status"] == "healthy"
    assert "providers" in health_data


def test_gateway_api_preview_endpoint(client: TestClient, user1_auth):
    # Create workspace
    ws = client.post("/api/workspaces", json={"name": "GW Preview WS"}, headers=user1_auth["headers"]).json()
    ws_id = ws["id"]

    resp = client.post(
        "/api/gateway/preview",
        json={"model": "auto", "latency_preference": "low", "cost_preference": "low"},
        headers={**user1_auth["headers"], "X-Workspace-Id": ws_id},
    )
    assert resp.status_code == 200
    preview = resp.json()
    assert "selected_model" in preview
    assert "selected_provider" in preview
    assert "fallback_candidates" in preview


def test_gateway_api_test_endpoint(client: TestClient, user1_auth):
    ws = client.post("/api/workspaces", json={"name": "GW Test WS"}, headers=user1_auth["headers"]).json()
    ws_id = ws["id"]

    resp = client.post(
        "/api/gateway/test",
        json={"model": "gpt-4o-mini", "provider": "mock", "prompt": "Ping gateway test"},
        headers={**user1_auth["headers"], "X-Workspace-Id": ws_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "content" in data
    assert data["provider"] in ("mock", "mock_provider")
    assert data["usage"]["total_tokens"] > 0


def test_gateway_api_policies_lifecycle(client: TestClient, user1_auth):
    ws = client.post("/api/workspaces", json={"name": "GW Policies WS"}, headers=user1_auth["headers"]).json()
    ws_id = ws["id"]

    # 1. Get default policy
    get_res = client.get("/api/gateway/policies", headers={**user1_auth["headers"], "X-Workspace-Id": ws_id})
    assert get_res.status_code == 200
    pol = get_res.json()
    assert pol["fallback_enabled"] is True

    # 2. Update policy
    patch_res = client.patch(
        "/api/gateway/policies",
        json={"max_tokens_per_request": 2048, "fallback_enabled": False, "allowed_providers": ["mock"]},
        headers={**user1_auth["headers"], "X-Workspace-Id": ws_id},
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["max_tokens_per_request"] == 2048
    assert updated["fallback_enabled"] is False
    assert updated["allowed_providers"] == ["mock"]
