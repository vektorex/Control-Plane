import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from backend.app.core.errors import ModelNotFoundError, ValidationError
from backend.app.db.models.task import Task
from backend.app.services.models.base import (
    CostMetadata,
    ModelDefinition,
    ModelRequirements,
    ModelSelection,
)
from backend.app.services.models.capabilities import ModelCapability
from backend.app.services.models.catalog import get_default_catalog
from backend.app.services.models.policies import ModelRoutingPolicy
from backend.app.services.models.registry import ModelRegistry
from backend.app.services.models.router import ModelRequirementAnalyzer, ModelRouter
from backend.app.services.task_execution import calculate_estimated_cost


@pytest.fixture
def custom_registry() -> ModelRegistry:
    """Fixture providing an isolated ModelRegistry containing only controlled test models."""
    reg = ModelRegistry(load_defaults=False)
    reg.register_model(
        ModelDefinition(
            provider="openai",
            model_id="gpt-4o-mini",
            display_name="GPT-4o Mini",
            capabilities=[
                ModelCapability.TEXT_GENERATION.value,
                ModelCapability.STREAMING.value,
                ModelCapability.TOOL_CALLING.value,
                ModelCapability.STRUCTURED_OUTPUT.value,
            ],
            context_window=128000,
            cost_class="low",
            latency_class="low",
            cost_metadata=CostMetadata(input_cost_per_1k_tokens=0.00015, output_cost_per_1k_tokens=0.0006),
            enabled=True,
            is_default=True,
        )
    )
    reg.register_model(
        ModelDefinition(
            provider="openai",
            model_id="gpt-4o",
            display_name="GPT-4o",
            capabilities=[
                ModelCapability.TEXT_GENERATION.value,
                ModelCapability.STREAMING.value,
                ModelCapability.TOOL_CALLING.value,
                ModelCapability.REASONING.value,
                ModelCapability.VISION.value,
            ],
            context_window=128000,
            cost_class="high",
            latency_class="medium",
            cost_metadata=CostMetadata(input_cost_per_1k_tokens=0.005, output_cost_per_1k_tokens=0.015),
            enabled=True,
            is_default=False,
        )
    )
    reg.register_model(
        ModelDefinition(
            provider="anthropic",
            model_id="claude-3-5-sonnet",
            display_name="Claude 3.5 Sonnet",
            capabilities=[
                ModelCapability.TEXT_GENERATION.value,
                ModelCapability.STREAMING.value,
                ModelCapability.TOOL_CALLING.value,
                ModelCapability.REASONING.value,
                ModelCapability.LONG_CONTEXT.value,
            ],
            context_window=200000,
            cost_class="medium",
            latency_class="balanced",
            cost_metadata=CostMetadata(input_cost_per_1k_tokens=0.003, output_cost_per_1k_tokens=0.015),
            enabled=True,
            is_default=True,
        )
    )
    reg.register_model(
        ModelDefinition(
            provider="mock",
            model_id="mock-simple",
            display_name="Mock Simple",
            capabilities=[ModelCapability.TEXT_GENERATION.value, ModelCapability.STREAMING.value],
            context_window=16000,
            cost_class="low",
            latency_class="low",
            supports_tools=False,
            enabled=True,
        )
    )
    reg.register_model(
        ModelDefinition(
            provider="openai",
            model_id="legacy-disabled",
            display_name="Legacy Disabled Model",
            capabilities=[ModelCapability.TEXT_GENERATION.value],
            context_window=8000,
            enabled=False,
        )
    )
    return reg


@pytest.fixture
def custom_router(custom_registry: ModelRegistry) -> ModelRouter:
    return ModelRouter(registry=custom_registry, policy=ModelRoutingPolicy())


# ==============================================================================
# 1. MODEL REGISTRY TESTS
# ==============================================================================

def test_1_register_model(custom_registry: ModelRegistry):
    custom_registry.register_model(
        ModelDefinition(
            provider="mock",
            model_id="test-new-model",
            display_name="Test New Model",
            capabilities=["text_generation"],
            context_window=32000,
        )
    )
    model = custom_registry.get_model("test-new-model", provider="mock")
    assert model is not None
    assert model.display_name == "Test New Model"


def test_2_retrieve_model(custom_registry: ModelRegistry):
    model = custom_registry.get_model("gpt-4o-mini")
    assert model is not None
    assert model.provider == "openai"
    assert model.supports_tools is True


def test_3_list_enabled_models(custom_registry: ModelRegistry):
    enabled = custom_registry.list_models(enabled_only=True)
    model_ids = [m.model_id for m in enabled]
    assert "gpt-4o-mini" in model_ids
    assert "legacy-disabled" not in model_ids


def test_4_capability_validation(custom_registry: ModelRegistry):
    gpt4o = custom_registry.get_model("gpt-4o")
    mock_simple = custom_registry.get_model("mock-simple")
    assert gpt4o.has_capability("reasoning") is True
    assert gpt4o.has_capability("vision") is True
    assert mock_simple.has_capability("vision") is False
    assert mock_simple.supports_tools is False


# ==============================================================================
# 2. MODEL REQUIREMENTS TESTS
# ==============================================================================

def test_5_tool_requirement():
    task = Task(id=uuid4(), title="Search the web", instructions="Find weather")
    reqs = ModelRequirementAnalyzer.analyze(task=task, enable_tools=True)
    assert reqs.requires_tools is True


def test_6_reasoning_requirement():
    task = Task(id=uuid4(), title="Complex Architecture", instructions="Analyze the trade-offs and compare algorithms step by step")
    reqs = ModelRequirementAnalyzer.analyze(task=task)
    assert reqs.requires_reasoning is True


def test_7_vision_requirement():
    reqs = ModelRequirements(requires_vision=True)
    assert reqs.requires_vision is True


def test_8_long_context_requirement():
    task = Task(id=uuid4(), title="Large Context Task", instructions="Analyze large logs")
    reqs = ModelRequirementAnalyzer.analyze(task=task, context_token_estimate=25000)
    assert reqs.requires_long_context is True
    assert reqs.min_context_window >= 29000


def test_9_streaming_requirement():
    task = Task(id=uuid4(), title="Stream Task", instructions="Hello")
    reqs = ModelRequirementAnalyzer.analyze(task=task, streaming=True)
    assert reqs.requires_streaming is True


# ==============================================================================
# 3. ROUTING TESTS
# ==============================================================================

def test_10_compatible_model_selected(custom_router: ModelRouter):
    reqs = ModelRequirements(requires_tools=True, requires_streaming=True)
    selection = custom_router.route(reqs)
    assert selection.model_id in ["gpt-4o-mini", "gpt-4o", "claude-3-5-sonnet"]
    assert selection.provider in ["openai", "anthropic"]
    assert "tools" in selection.reason.lower() or "satisfies" in selection.reason.lower()


def test_11_incompatible_model_rejected(custom_router: ModelRouter):
    # mock-simple does not support tools
    reqs = ModelRequirements(requires_tools=True)
    with pytest.raises(ValidationError):
        custom_router.validate_manual_selection("mock-simple", requirements=reqs)


def test_12_manual_selection_validated(custom_router: ModelRouter):
    selection = custom_router.validate_manual_selection("gpt-4o")
    assert selection.model_id == "gpt-4o"
    assert selection.provider == "openai"
    assert selection.policy == "manual"


def test_13_automatic_selection(custom_router: ModelRouter):
    reqs = ModelRequirements(requires_reasoning=True, requires_tools=True)
    selection = custom_router.route(reqs)
    assert selection.model_id in ["gpt-4o", "claude-3-5-sonnet", "gpt-4o-mini"]
    assert len(selection.fallback_candidates) > 0


def test_14_cost_preference(custom_router: ModelRouter):
    reqs = ModelRequirements(cost_preference="low", latency_preference="low")
    selection = custom_router.route(reqs)
    # Low cost and latency in custom_router should favor gpt-4o-mini or mock-simple
    assert selection.model_id in ["gpt-4o-mini", "mock-simple"]


def test_15_latency_preference(custom_router: ModelRouter):
    reqs = ModelRequirements(latency_preference="low", requires_tools=True)
    selection = custom_router.route(reqs)
    assert selection.model_id == "gpt-4o-mini"


# ==============================================================================
# 4. FALLBACK TESTS
# ==============================================================================

def test_16_fallback_candidates_generated(custom_router: ModelRouter):
    reqs = ModelRequirements(requires_tools=True)
    selection = custom_router.route(reqs)
    assert len(selection.fallback_candidates) >= 1
    fb = selection.fallback_candidates[0]
    assert fb.provider != ""
    assert fb.model_id != ""


def test_17_compatible_fallback_selection(custom_router: ModelRouter):
    reqs = ModelRequirements(requires_tools=True, requires_reasoning=True)
    selection = custom_router.route(reqs)
    for fb in selection.fallback_candidates:
        fb_model = custom_router.registry.get_model(fb.model_id, provider=fb.provider)
        assert fb_model is not None
        assert fb_model.supports_tools is True


def test_18_incompatible_fallback_rejected(custom_router: ModelRouter):
    # mock-simple cannot be a fallback candidate when tools are strictly required
    reqs = ModelRequirements(requires_tools=True)
    selection = custom_router.route(reqs)
    fallback_model_ids = [fb.model_id for fb in selection.fallback_candidates]
    assert "mock-simple" not in fallback_model_ids


def test_19_maximum_fallback_attempts(custom_router: ModelRouter):
    reqs = ModelRequirements()
    selection = custom_router.route(reqs)
    assert len(selection.fallback_candidates) <= 3


# ==============================================================================
# 5. SECURITY & ACCESS POLICY TESTS
# ==============================================================================

def test_20_disabled_model_rejected(custom_router: ModelRouter):
    with pytest.raises(ValidationError):
        custom_router.validate_manual_selection("legacy-disabled")


def test_21_unauthorized_provider_rejected(custom_router: ModelRouter):
    with pytest.raises(ModelNotFoundError):
        custom_router.validate_manual_selection("unauthorized-model", provider="unknown_vendor")


def test_22_cross_user_task_rejected(auth_client, client, user2_auth):
    # Create workspace, project, task for User 1
    ws = auth_client.post("/api/workspaces", json={"name": "MR User 1 WS"}).json()
    proj = auth_client.post(f"/api/workspaces/{ws['id']}/projects", json={"name": "MR User 1 Proj"}).json()
    task = auth_client.post(f"/api/projects/{proj['id']}/tasks", json={"title": "MR Private Task"}).json()

    # User 2 attempts to model-preview User 1's task -> 404 / Forbidden
    res = client.post(
        f"/api/tasks/{task['id']}/model-preview",
        json={"tool_mode": "auto"},
        headers=user2_auth["headers"],
    )
    assert res.status_code in [403, 404]


# ==============================================================================
# 6. USAGE TRACKING & COST TESTS
# ==============================================================================

def test_26_usage_and_cost_calculation():
    cost = calculate_estimated_cost(
        model_id="gpt-4o-mini",
        provider_id="openai",
        input_tokens=2000,
        output_tokens=1000,
    )
    # gpt-4o-mini: input 0.00015/1k ($0.0003) + output 0.0006/1k ($0.0006) = $0.0009
    assert cost is not None
    assert cost == 0.0009


def test_26_b_usage_cost_null_when_unconfigured():
    cost = calculate_estimated_cost(
        model_id="unknown-model-no-cost",
        provider_id="mock",
        input_tokens=2000,
        output_tokens=1000,
    )
    assert cost is None


# ==============================================================================
# 7. API ENDPOINT TESTS
# ==============================================================================

def test_api_list_models(auth_client):
    response = auth_client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert "providers" in data
    assert len(data["models"]) > 0
    # Verify no secret credentials in payload
    for m in data["models"]:
        assert "api_key" not in m
        assert "secret" not in m


def test_api_route_preview(auth_client):
    payload = {
        "requirements": {
            "requires_reasoning": True,
            "requires_tools": True,
            "requires_long_context": False,
            "latency_preference": "balanced",
            "cost_preference": "balanced",
        },
        "policy": "balanced",
    }
    response = auth_client.post("/api/models/route", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "selection" in data
    assert "provider" in data["selection"]
    assert "model_id" in data["selection"]
    assert "reason" in data["selection"]
    assert "best model" not in data["selection"]["reason"].lower()


def test_api_task_model_preview(auth_client):
    # Create workspace, project, task
    ws = auth_client.post("/api/workspaces", json={"name": "WS Preview"}).json()
    proj = auth_client.post(f"/api/workspaces/{ws['id']}/projects", json={"name": "Proj Preview"}).json()
    task = auth_client.post(
        f"/api/projects/{proj['id']}/tasks",
        json={
            "title": "Analyze System Architecture",
            "instructions": "Compare microservices vs monolith architecture with tools",
            "model_mode": "auto",
        },
    ).json()

    response = auth_client.post(
        f"/api/tasks/{task['id']}/model-preview",
        json={"tool_mode": "enabled", "latency_preference": "balanced"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == str(task["id"])
    assert data["model_mode"] == "auto"
    assert "requirements" in data
    assert data["requirements"]["requires_reasoning"] is True
    assert "selection" in data
    assert data["selection"]["provider"] != ""
    assert data["selection"]["model_id"] != ""
