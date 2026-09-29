import uuid
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from backend.app.config import settings
from backend.app.db.models.observability import ExecutionTraceEvent, RunTelemetry, UsageRecord
from backend.app.services.models.base import CostMetadata, ModelDefinition
from backend.app.services.models.registry import ModelRegistry
from backend.app.services.observability import (
    CostCalculator,
    ExecutionTracer,
    ObservabilityService,
    TraceEventStatus,
    TraceEventType,
    default_cost_calculator,
    extract_error_code,
    normalize_provider_usage,
    sanitize_error_message,
    sanitize_metadata,
)


def test_cost_calculation_per_1m_formula():
    calc = CostCalculator()
    # gpt-4o-mini is $0.15 / 1M in, $0.60 / 1M out
    cost = calc.calculate_generation_cost(
        model_id="gpt-4o-mini",
        provider="openai",
        input_tokens=1_000_000,
        output_tokens=1_000_000,
    )
    assert cost == 0.75

    # 10,000 input = 0.0015, 2,000 output = 0.0012 => total 0.0027
    cost_small = calc.calculate_generation_cost(
        model_id="gpt-4o-mini",
        provider="openai",
        input_tokens=10_000,
        output_tokens=2_000,
    )
    assert cost_small == 0.0027


def test_cost_calculation_missing_pricing_returns_none():
    reg = ModelRegistry()
    reg.register_model(
        ModelDefinition(
            provider="custom_provider",
            model_id="no-pricing-model",
            display_name="No Pricing Model",
            cost_metadata=None,
        )
    )
    calc = CostCalculator(registry=reg)
    cost = calc.calculate_generation_cost(
        model_id="no-pricing-model",
        provider="custom_provider",
        input_tokens=5000,
        output_tokens=2000,
    )
    assert cost is None, "Missing pricing metadata must strictly return None without guessing."


def test_provider_usage_normalization():
    # 1. OpenAI style
    openai_raw = {
        "prompt_tokens": 150,
        "completion_tokens": 50,
        "total_tokens": 200,
        "prompt_tokens_details": {"cached_tokens": 20},
    }
    norm_openai = normalize_provider_usage(provider="openai", model="gpt-4o-mini", raw_usage=openai_raw)
    assert norm_openai.input_tokens == 150
    assert norm_openai.output_tokens == 50
    assert norm_openai.total_tokens == 200
    assert norm_openai.cached_input_tokens == 20
    assert norm_openai.usage_source == "provider"
    assert norm_openai.estimated_cost is not None

    # 2. Anthropic style
    anthropic_raw = {
        "input_tokens": 300,
        "output_tokens": 100,
        "cache_read_input_tokens": 50,
    }
    norm_anthropic = normalize_provider_usage(provider="anthropic", model="claude-3-5-sonnet", raw_usage=anthropic_raw)
    assert norm_anthropic.input_tokens == 300
    assert norm_anthropic.output_tokens == 100
    assert norm_anthropic.total_tokens == 400
    assert norm_anthropic.cached_input_tokens == 50
    assert norm_anthropic.usage_source == "provider"

    # 3. Local estimation
    est_raw = {"estimated_prompt_tokens": 80, "estimated_completion_tokens": 40}
    norm_est = normalize_provider_usage(provider="mock", model="mock-model", raw_usage=None, estimated_tokens=est_raw)
    assert norm_est.input_tokens == 80
    assert norm_est.output_tokens == 40
    assert norm_est.total_tokens == 120
    assert norm_est.usage_source == "estimated"


def test_metadata_sanitization_removes_secrets_and_cot():
    raw_meta = {
        "api_key": "sk-1234567890abcdef1234567890abcdef",
        "authorization": "Bearer secret-token-xyz-1234567",
        "password": "super-secret-password",
        "chain_of_thought": "Thinking step by step...",
        "internal_reasoning": "Hidden private reasoning...",
        "evaluator_prompt": "Internal evaluator system prompt...",
        "user_query": "Compare React and Vue",
        "details": {
            "token": "bearer 9876543210fedcba9876543210fedcba",
            "nested_safe": "Observable safe value",
        },
    }

    sanitized = sanitize_metadata(raw_meta)
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["authorization"] == "[REDACTED]"
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["chain_of_thought"] == "[REDACTED]"
    assert sanitized["internal_reasoning"] == "[REDACTED]"
    assert sanitized["evaluator_prompt"] == "[REDACTED]"
    assert sanitized["user_query"] == "Compare React and Vue"
    assert sanitized["details"]["token"] == "[REDACTED]"
    assert sanitized["details"]["nested_safe"] == "Observable safe value"


def test_error_sanitization_and_code_extraction():
    raw_err = "Failed authentication with Bearer sk-abcdef1234567890abcdef1234567890 password=my_db_password"
    safe = sanitize_error_message(raw_err)
    assert "sk-" not in safe or "[REDACTED]" in safe
    assert "my_db_password" not in safe

    class CustomTestError(Exception):
        code = "CUSTOM_ORCHESTRATION_ERROR"

    code = extract_error_code(CustomTestError("Something failed"))
    assert code == "CUSTOM_ORCHESTRATION_ERROR"


def test_execution_tracer_ordering():
    run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    tracer = ExecutionTracer(run_id=run_id, workspace_id=workspace_id)

    tracer.record_event(TraceEventType.RUN_STARTED, status=TraceEventStatus.STARTED)
    tracer.record_event(TraceEventType.PLANNING_STARTED, status=TraceEventStatus.STARTED)
    tracer.record_event(TraceEventType.PLANNING_COMPLETED, status=TraceEventStatus.COMPLETED)
    tracer.record_event(TraceEventType.RETRIEVAL_STARTED, step_type="retrieve", status=TraceEventStatus.STARTED)
    tracer.record_event(TraceEventType.RETRIEVAL_COMPLETED, step_type="retrieve", status=TraceEventStatus.COMPLETED)
    tracer.record_event(TraceEventType.GENERATION_STARTED, step_type="generate", status=TraceEventStatus.STARTED)
    tracer.record_event(TraceEventType.GENERATION_COMPLETED, step_type="generate", status=TraceEventStatus.COMPLETED)
    tracer.record_event(TraceEventType.EVALUATION_STARTED, status=TraceEventStatus.STARTED)
    tracer.record_event(TraceEventType.EVALUATION_COMPLETED, status=TraceEventStatus.COMPLETED)
    tracer.record_event(TraceEventType.RUN_COMPLETED, status=TraceEventStatus.COMPLETED)

    assert len(tracer.events) == 10
    for idx, e in enumerate(tracer.events, start=1):
        assert e["sequence_number"] == idx
        assert e["run_id"] == run_id
        assert e["workspace_id"] == workspace_id

    assert tracer.events[0]["event_type"] == TraceEventType.RUN_STARTED.value
    assert tracer.events[-1]["event_type"] == TraceEventType.RUN_COMPLETED.value


def test_full_task_execution_records_telemetry_and_trace(client, user1_auth):
    """Executing a task creates RunTelemetry, trace events in order, and granular UsageRecords."""
    me = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws_id = me["default_workspace_id"]

    proj_res = client.post(
        f"/api/workspaces/{ws_id}/projects",
        json={"name": "Obs Project", "slug": f"obs-proj-{uuid.uuid4().hex[:6]}"},
        headers=user1_auth["headers"],
    )
    proj_id = proj_res.json()["id"]

    task_res = client.post(
        f"/api/projects/{proj_id}/tasks",
        json={
            "title": "Observability Test Task",
            "instructions": "Explain Python async event loop in 2 bullet points.",
            "evaluation_mode": "standard",
        },
        headers=user1_auth["headers"],
    )
    assert task_res.status_code == 201
    task_id = task_res.json()["id"]

    # Execute task with mock-model-v1
    run_res = client.post(
        f"/api/tasks/{task_id}/run",
        json={"model": "mock-model-v1", "evaluation_mode": "basic"},
        headers=user1_auth["headers"],
    )
    assert run_res.status_code == 201
    run_data = run_res.json()
    run_id = run_data["id"]

    # 1. Check Run Telemetry endpoint
    telem_res = client.get(f"/api/runs/{run_id}/telemetry", headers=user1_auth["headers"])
    assert telem_res.status_code == 200
    telem_data = telem_res.json()
    assert telem_data is not None
    assert telem_data["run_id"] == run_id
    assert telem_data["workspace_id"] == ws_id
    assert telem_data["status"] == "completed"
    assert telem_data["generation_model"] == "mock-model-v1"
    assert telem_data["execution_steps"] >= 1

    # 2. Check Run Trace events endpoint
    trace_res = client.get(f"/api/runs/{run_id}/trace", headers=user1_auth["headers"])
    assert trace_res.status_code == 200
    events = trace_res.json()
    assert len(events) >= 3
    event_types = [e["event_type"] for e in events]
    assert "run_started" in event_types
    assert "run_completed" in event_types
    for idx, e in enumerate(events, start=1):
        assert e["sequence_number"] == idx

    # 3. Check Run Usage records endpoint
    usage_res = client.get(f"/api/runs/{run_id}/usage", headers=user1_auth["headers"])
    assert usage_res.status_code == 200
    usage_list = usage_res.json()
    assert len(usage_list) >= 1
    assert usage_list[0]["operation"] == "generation"
    assert usage_list[0]["model"] == "mock-model-v1"


def test_failed_task_execution_records_telemetry_and_failed_trace(client, user1_auth):
    """Failed executions record status='failed', error code, safe error message, and run_failed trace event."""
    from backend.app.main import app
    from backend.app.services.llm.factory import LLMProviderFactory, get_llm_factory
    from backend.tests.conftest import MockTestProvider

    failing_factory = LLMProviderFactory()
    failing_provider = MockTestProvider(configured=True, should_fail=True, fail_type="api_error")
    failing_factory.register_provider(failing_provider)
    app.dependency_overrides[get_llm_factory] = lambda: failing_factory

    try:
        me = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
        ws_id = me["default_workspace_id"]

        proj_res = client.post(
            f"/api/workspaces/{ws_id}/projects",
            json={"name": "Failing Project", "slug": f"fail-proj-{uuid.uuid4().hex[:6]}"},
            headers=user1_auth["headers"],
        )
        proj_id = proj_res.json()["id"]

        task_res = client.post(
            f"/api/projects/{proj_id}/tasks",
            json={
                "title": "Failing Task",
                "instructions": "This will fail deliberately.",
            },
            headers=user1_auth["headers"],
        )
        task_id = task_res.json()["id"]

        run_res = client.post(
            f"/api/tasks/{task_id}/run",
            json={"model": "mock-model-v1"},
            headers=user1_auth["headers"],
        )
        assert run_res.status_code >= 400

        # Query latest run for task via runs list
        task_runs_res = client.get(f"/api/tasks/{task_id}/runs", headers=user1_auth["headers"])
        assert task_runs_res.status_code == 200
        runs = task_runs_res.json()["runs"]
        assert len(runs) >= 1
        failed_run = runs[0]
        assert failed_run["status"] == "failed"

        # Query telemetry endpoint
        telem_res = client.get(f"/api/runs/{failed_run['id']}/telemetry", headers=user1_auth["headers"])
        assert telem_res.status_code == 200
        t_data = telem_res.json()
        assert t_data["status"] == "failed"
        assert "Mock upstream API failure" in (t_data["error_message_safe"] or "")

        # Query trace events endpoint
        trace_res = client.get(f"/api/runs/{failed_run['id']}/trace", headers=user1_auth["headers"])
        assert trace_res.status_code == 200
        events = trace_res.json()
        types = [e["event_type"] for e in events]
        assert "run_failed" in types
    finally:
        app.dependency_overrides.clear()



def test_analytics_endpoints_and_aggregations(client, user1_auth):
    """Analytics endpoints compute aggregations across overview, usage, models, providers, latency, and evaluations."""
    me = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws_id = me["default_workspace_id"]

    proj_res = client.post(
        f"/api/workspaces/{ws_id}/projects",
        json={"name": "Analytics Proj", "slug": f"an-proj-{uuid.uuid4().hex[:6]}"},
        headers=user1_auth["headers"],
    )
    proj_id = proj_res.json()["id"]

    # Create and run 2 tasks to populate telemetry
    t1 = client.post(
        f"/api/projects/{proj_id}/tasks",
        json={"title": "Analytics Task 1", "instructions": "Explain A"},
        headers=user1_auth["headers"],
    )
    client.post(f"/api/tasks/{t1.json()['id']}/run", json={"model": "mock-model-v1"}, headers=user1_auth["headers"])

    t2 = client.post(
        f"/api/projects/{proj_id}/tasks",
        json={"title": "Analytics Task 2", "instructions": "Explain B"},
        headers=user1_auth["headers"],
    )
    client.post(f"/api/tasks/{t2.json()['id']}/run", json={"model": "mock-model-v1"}, headers=user1_auth["headers"])

    # 1. Overview analytics (filtered by project)
    overview_res = client.get(f"/api/analytics/overview?workspace_id={ws_id}&project_id={proj_id}", headers=user1_auth["headers"])
    assert overview_res.status_code == 200
    overview = overview_res.json()
    assert overview["runs"]["total"] == 2
    assert overview["runs"]["successful"] == 2
    assert overview["runs"]["success_rate"] == 100.0

    # 1b. Overview analytics (workspace level)
    ws_overview_res = client.get(f"/api/analytics/overview?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert ws_overview_res.status_code == 200
    ws_overview = ws_overview_res.json()
    assert ws_overview["runs"]["total"] >= 2
    assert ws_overview["runs"]["successful"] >= 2
    assert ws_overview["runs"]["success_rate"] is not None

    # 2. Usage analytics
    usage_res = client.get(f"/api/analytics/usage?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert usage_res.status_code == 200
    usage_data = usage_res.json()
    assert len(usage_data["points"]) >= 1

    # 3. Models analytics
    models_res = client.get(f"/api/analytics/models?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert models_res.status_code == 200
    models_data = models_res.json()
    assert len(models_data["models"]) >= 1
    assert models_data["models"][0]["model"] == "mock-model-v1"

    # 4. Providers analytics
    prov_res = client.get(f"/api/analytics/providers?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert prov_res.status_code == 200
    prov_data = prov_res.json()
    assert len(prov_data["providers"]) >= 1

    # 5. Latency analytics
    lat_res = client.get(f"/api/analytics/latency?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert lat_res.status_code == 200
    lat_data = lat_res.json()
    assert "overall" in lat_data
    assert "stages" in lat_data

    # 6. Evaluation analytics
    eval_res = client.get(f"/api/analytics/evaluations?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert "passed" in eval_data
    assert "total" in eval_data


def test_cross_workspace_telemetry_isolation(client, user1_auth, user2_auth):
    """User 2 cannot inspect or aggregate User 1's telemetry, trace events, or usage."""
    me1 = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws1_id = me1["default_workspace_id"]

    me2 = client.get("/api/auth/me", headers=user2_auth["headers"]).json()
    ws2_id = me2["default_workspace_id"]

    proj1 = client.post(
        f"/api/workspaces/{ws1_id}/projects",
        json={"name": "User 1 Proj", "slug": f"u1-proj-{uuid.uuid4().hex[:6]}"},
        headers=user1_auth["headers"],
    )
    t1 = client.post(
        f"/api/projects/{proj1.json()['id']}/tasks",
        json={"title": "User 1 Task", "instructions": "Do something"},
        headers=user1_auth["headers"],
    )
    r1 = client.post(f"/api/tasks/{t1.json()['id']}/run", json={"model": "mock-model-v1"}, headers=user1_auth["headers"])
    run_id = r1.json()["id"]

    # User 2 tries to access user 1's run trace and telemetry
    t_res = client.get(f"/api/runs/{run_id}/telemetry", headers=user2_auth["headers"])
    assert t_res.status_code == 404, "Cross-user run telemetry query must be rejected with 404."

    trace_res = client.get(f"/api/runs/{run_id}/trace", headers=user2_auth["headers"])
    assert trace_res.status_code == 404, "Cross-user run trace query must be rejected with 404."

    # User 2 queries overview analytics for ws2 - should not show user 1 data
    ov2 = client.get(f"/api/analytics/overview?workspace_id={ws2_id}", headers=user2_auth["headers"])
    assert ov2.status_code == 200
    assert ov2.json()["runs"]["total"] == 0


def test_observability_retention_cleanup(client, user1_auth):
    """Admin cleanup endpoint deletes trace events, usage records, and telemetry older than retention without deleting tasks."""
    me = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws_id = me["default_workspace_id"]

    # Call admin cleanup endpoint with retention_days=30
    cleanup_res = client.post(
        f"/api/admin/observability/cleanup?workspace_id={ws_id}&retention_days=30",
        headers=user1_auth["headers"],
    )
    assert cleanup_res.status_code == 200
    c_data = cleanup_res.json()
    assert "deleted_telemetry_records" in c_data
    assert "deleted_trace_events" in c_data
    assert "deleted_usage_records" in c_data


def test_unauthenticated_analytics_rejected(client):
    res = client.get("/api/analytics/overview")
    assert res.status_code == 401


def test_evaluation_and_revision_telemetry_capture(client, user1_auth):
    """Evaluation telemetry and trace events are recorded when evaluation is enabled."""
    me = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws_id = me["default_workspace_id"]

    proj_res = client.post(
        f"/api/workspaces/{ws_id}/projects",
        json={"name": "Eval Telemetry Proj", "slug": f"eval-obs-{uuid.uuid4().hex[:6]}"},
        headers=user1_auth["headers"],
    )
    proj_id = proj_res.json()["id"]

    task_res = client.post(
        f"/api/projects/{proj_id}/tasks",
        json={
            "title": "Eval Telemetry Task",
            "instructions": "Generate 3 key points about observability.",
            "evaluation_mode": "basic",
        },
        headers=user1_auth["headers"],
    )
    task_id = task_res.json()["id"]

    run_res = client.post(
        f"/api/tasks/{task_id}/run",
        json={"model": "mock-model-v1", "evaluation_mode": "basic"},
        headers=user1_auth["headers"],
    )
    assert run_res.status_code == 201
    run_id = run_res.json()["id"]

    # Check telemetry contains evaluation fields
    telem_res = client.get(f"/api/runs/{run_id}/telemetry", headers=user1_auth["headers"])
    assert telem_res.status_code == 200
    telem = telem_res.json()
    assert telem["evaluation_status"] in ["passed", "warning", "failed"]

    # Check trace contains evaluation events
    trace_res = client.get(f"/api/runs/{run_id}/trace", headers=user1_auth["headers"])
    assert trace_res.status_code == 200
    trace_events = trace_res.json()
    types = [e["event_type"] for e in trace_events]
    assert "evaluation_started" in types
    assert "evaluation_completed" in types

