"""
Comprehensive backend tests for Step 23: Workflow Triggers & Event Automation.
"""
import asyncio
import hashlib
import hmac
import json
import time
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.services.triggers import (
    EventTriggerService,
    FilterConfiguration,
    FilterLogic,
    FilterOperator,
    FilterRule,
    RetryConfiguration,
    ScheduleConfiguration,
    TriggerConcurrencyError,
    TriggerDeduplicationError,
    TriggerDeduplicationService,
    TriggerDisabledError,
    TriggerError,
    TriggerExecutor,
    TriggerFilterEngine,
    TriggerNotFoundError,
    TriggerPayloadMapper,
    TriggerPolicyEngine,
    TriggerPolicyError,
    TriggerRateLimitError,
    TriggerRegistry,
    TriggerRetryManager,
    TriggerRunResponse,
    TriggerRunStatus,
    TriggerScheduler,
    TriggerService,
    TriggerStatus,
    TriggerTestRequest,
    TriggerType,
    TriggerValidationError,
    WebhookSecretResponse,
    WebhookSecretStore,
    WebhookSignatureError,
    WebhookTriggerService,
    WorkflowTriggerCreateRequest,
    WorkflowTriggerResponse,
    WorkflowTriggerUpdateRequest,
    trigger_registry,
)
from backend.app.db.models.trigger import WorkflowTrigger, TriggerRun
from backend.app.db.models.workflow import Workflow, WorkflowRun
from backend.app.db.models.user import User


# =============================================================================
# 1. Event Normalization Tests (GitHub & Generic Webhooks)
# =============================================================================

def test_github_issue_created_normalization():
    ws_id = uuid.uuid4()
    raw = {
        "action": "opened",
        "issue": {
            "number": 1337,
            "title": "Database connection leak in connection pool",
            "body": "Connection pool leaks under load...",
            "state": "open",
            "labels": [{"name": "bug"}, {"name": "priority-high"}],
            "user": {"login": "octocat"},
        },
        "repository": {
            "id": 9999,
            "name": "ai-layer",
            "full_name": "org/ai-layer",
            "owner": {"login": "org"},
        },
    }
    headers = {
        "x-github-event": "issues",
        "x-github-delivery": "deliv-12345",
    }
    event = EventTriggerService.normalize_github_event(raw, headers, ws_id)

    assert event.event_type == "github.issue.created"
    assert event.source == "github"
    assert event.workspace_id == ws_id
    assert event.event_id == "deliv-12345"
    assert event.payload["issue"]["number"] == 1337
    assert "bug" in event.payload["issue"]["labels"]
    assert event.payload["repository"]["full_name"] == "org/ai-layer"


def test_github_pull_request_opened_normalization():
    ws_id = uuid.uuid4()
    raw = {
        "action": "opened",
        "pull_request": {
            "number": 42,
            "title": "Step 23: Workflow Triggers",
            "head": {"ref": "feature/step23"},
            "base": {"ref": "main"},
            "labels": [{"name": "enhancement"}],
        },
        "repository": {"full_name": "org/ai-layer"},
    }
    headers = {"x-github-event": "pull_request", "x-github-delivery": "deliv-pr-42"}
    event = EventTriggerService.normalize_github_event(raw, headers, ws_id)

    assert event.event_type == "github.pull_request.opened"
    assert event.payload["pull_request"]["number"] == 42
    assert event.payload["pull_request"]["head"]["ref"] == "feature/step23"


def test_generic_webhook_normalization():
    ws_id = uuid.uuid4()
    raw = {"alert_name": "High CPU", "server": "app-01", "load": 94.5}
    headers = {"x-request-id": "req-987", "content-type": "application/json"}
    event = EventTriggerService.normalize_generic_webhook(raw, headers, ws_id)

    assert event.source == "webhook"
    assert event.event_id == "req-987"
    assert event.payload["alert_name"] == "High CPU"
    assert event.payload["load"] == 94.5


# =============================================================================
# 2. Filter Engine Tests (All Operators, AND / OR)
# =============================================================================

def test_filter_engine_operators():
    payload = {
        "repository": {"full_name": "org/ai-layer"},
        "issue": {
            "title": "Critical security bug found",
            "labels": ["security", "bug", "p0"],
            "comments_count": 5,
        },
        "env": "production",
    }

    # Equals
    config_eq = {"rules": [{"field": "repository.full_name", "operator": "equals", "value": "org/ai-layer"}]}
    matched, details = TriggerFilterEngine.evaluate(config_eq, payload)
    assert matched is True

    # Not Equals
    config_neq = {"rules": [{"field": "env", "operator": "not_equals", "value": "staging"}]}
    matched, _ = TriggerFilterEngine.evaluate(config_neq, payload)
    assert matched is True

    # Contains (in list)
    config_contains = {"rules": [{"field": "issue.labels", "operator": "contains", "value": "bug"}]}
    matched, _ = TriggerFilterEngine.evaluate(config_contains, payload)
    assert matched is True

    # Contains (in string)
    config_str_contains = {"rules": [{"field": "issue.title", "operator": "contains", "value": "security"}]}
    matched, _ = TriggerFilterEngine.evaluate(config_str_contains, payload)
    assert matched is True

    # Starts with & Ends with
    config_starts = {"rules": [{"field": "issue.title", "operator": "starts_with", "value": "Critical"}]}
    matched, _ = TriggerFilterEngine.evaluate(config_starts, payload)
    assert matched is True

    config_ends = {"rules": [{"field": "issue.title", "operator": "ends_with", "value": "found"}]}
    matched, _ = TriggerFilterEngine.evaluate(config_ends, payload)
    assert matched is True

    # Exists
    config_exists = {"rules": [{"field": "issue.comments_count", "operator": "exists", "value": True}]}
    matched, _ = TriggerFilterEngine.evaluate(config_exists, payload)
    assert matched is True

    config_not_exists = {"rules": [{"field": "issue.non_existent_key", "operator": "exists", "value": False}]}
    matched, _ = TriggerFilterEngine.evaluate(config_not_exists, payload)
    assert matched is True

    # Numeric comparisons
    config_num = {
        "rules": [
            {"field": "issue.comments_count", "operator": "greater_than", "value": 3},
            {"field": "issue.comments_count", "operator": "less_or_equal", "value": 5},
        ]
    }
    matched, _ = TriggerFilterEngine.evaluate(config_num, payload)
    assert matched is True


def test_filter_engine_and_or_logic():
    payload = {
        "repository": {"full_name": "org/ai-layer"},
        "issue": {"labels": ["question"]},
    }

    # AND logic where one fails -> Overall False
    config_and = {
        "logic": "AND",
        "rules": [
            {"field": "repository.full_name", "operator": "equals", "value": "org/ai-layer"},
            {"field": "issue.labels", "operator": "contains", "value": "bug"},
        ],
    }
    matched, details = TriggerFilterEngine.evaluate(config_and, payload)
    assert matched is False
    assert details["rule_results"][0]["passed"] is True
    assert details["rule_results"][1]["passed"] is False

    # OR logic where one succeeds -> Overall True
    config_or = {
        "logic": "OR",
        "rules": [
            {"field": "repository.full_name", "operator": "equals", "value": "different/repo"},
            {"field": "issue.labels", "operator": "contains", "value": "question"},
        ],
    }
    matched, details = TriggerFilterEngine.evaluate(config_or, payload)
    assert matched is True


# =============================================================================
# 3. Payload Mapping Tests (Safe Interpolation)
# =============================================================================

def test_payload_mapping_resolution():
    event_payload = {
        "repository": {"full_name": "org/automation-core"},
        "issue": {
            "number": 99,
            "title": "Fix memory leak",
        },
        "author": "dev-user",
    }
    mapping_tmpl = {
        "repo": "{{payload.repository.full_name}}",
        "task_title": "Issue #{{payload.issue.number}}: {{payload.issue.title}}",
        "assignee": "{{payload.author}}",
        "constant_val": "automated",
    }
    result = TriggerPayloadMapper.map_inputs(mapping_tmpl, event_payload)

    assert result["repo"] == "org/automation-core"
    assert result["task_title"] == "Issue #99: Fix memory leak"
    assert result["assignee"] == "dev-user"
    assert result["constant_val"] == "automated"


# =============================================================================
# 4. Schedule & Timezone Validation Tests
# =============================================================================

def test_schedule_cron_and_timezone_computation():
    # Predefined shortcut: @hourly
    expr = TriggerScheduler.normalize_expression("@hourly")
    assert expr == "0 * * * *"

    # Valid timezone
    tz = TriggerScheduler.validate_timezone("Asia/Kolkata")
    assert str(tz) == "Asia/Kolkata"

    # Invalid timezone raises TriggerValidationError
    with pytest.raises(TriggerValidationError):
        TriggerScheduler.validate_timezone("Invalid/Nowhere_City")

    # Cron parsing
    mins, hours, doms, months, dows = TriggerScheduler.parse_cron("*/15 9-17 1,15 * 1-5")
    assert 0 in mins and 15 in mins and 45 in mins
    assert 9 in hours and 17 in hours and 8 not in hours
    assert 1 in doms and 15 in doms

    # Next run computation in UTC
    base_time = datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc)
    next_run = TriggerScheduler.compute_next_run("0 * * * *", "UTC", after_dt=base_time)
    assert next_run == datetime(2026, 10, 1, 13, 0, 0, tzinfo=timezone.utc)


# =============================================================================
# 5. Webhook Security: HMAC Signature & Timestamp Validation Tests
# =============================================================================

def test_webhook_hmac_verification_and_replay_protection():
    store = WebhookSecretStore()
    plain_secret = "whsec_test_secret_1234567890abcdef"
    enc_secret = store.encrypt_secret(plain_secret)

    raw_body = b'{"event":"ping","timestamp":12345}'
    computed_sig = WebhookTriggerService.compute_signature(raw_body, plain_secret)

    valid_headers = {
        "x-hub-signature-256": computed_sig,
        "x-webhook-timestamp": str(int(time.time())),
    }

    # 1. Valid signature passes
    assert WebhookTriggerService.verify_request(raw_body, valid_headers, enc_secret) is True

    # 2. Tampered body raises WebhookSignatureError
    tampered_body = b'{"event":"malicious_tamper"}'
    with pytest.raises(WebhookSignatureError):
        WebhookTriggerService.verify_request(tampered_body, valid_headers, enc_secret)

    # 3. Invalid signature raises WebhookSignatureError
    bad_sig_headers = {
        "x-hub-signature-256": "sha256=0000000000000000000000000000000000000000000000000000000000000000",
        "x-webhook-timestamp": str(int(time.time())),
    }
    with pytest.raises(WebhookSignatureError):
        WebhookTriggerService.verify_request(raw_body, bad_sig_headers, enc_secret)

    # 4. Expired timestamp beyond tolerance (e.g. 500s ago) raises WebhookSignatureError
    expired_headers = {
        "x-hub-signature-256": computed_sig,
        "x-webhook-timestamp": str(int(time.time()) - 500),
    }
    with pytest.raises(WebhookSignatureError):
        WebhookTriggerService.verify_request(raw_body, expired_headers, enc_secret, tolerance_seconds=300)


# =============================================================================
# 6. Idempotency & Debouncing Tests
# =============================================================================

@pytest.mark.asyncio
async def test_idempotency_deduplication():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    # First check: not in DB
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    trig_id = uuid.uuid4()
    key = "unique-delivery-id-777"

    # First call: not duplicate
    is_dup, reason = await TriggerDeduplicationService.check_and_record_idempotency(
        mock_session, trig_id, idempotency_key=key
    )
    assert is_dup is False

    # Second call (same key): hot-path in-memory duplicate detected
    is_dup2, reason2 = await TriggerDeduplicationService.check_and_record_idempotency(
        mock_session, trig_id, idempotency_key=key
    )
    assert is_dup2 is True
    assert "Duplicate key" in reason2


@pytest.mark.asyncio
async def test_debouncing():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    # Mock recent run 10 seconds ago
    recent_time = datetime.now(timezone.utc) - timedelta(seconds=10)
    mock_result.scalar_one_or_none.return_value = recent_time
    mock_session.execute.return_value = mock_result

    trig_id = uuid.uuid4()
    # 60-second debounce window -> 10s elapsed -> should debounce with ~50s remaining
    is_debounced, rem_sec = await TriggerDeduplicationService.check_debounce(
        mock_session, trig_id, debounce_seconds=60
    )
    assert is_debounced is True
    assert rem_sec is not None and rem_sec > 40


# =============================================================================
# 7. Rate Limiting & Concurrency Tests
# =============================================================================

def test_trigger_rate_limiting():
    trig_id = uuid.uuid4()
    ws_id = uuid.uuid4()

    # Reset in-memory rate limiter windows
    TriggerPolicyEngine._rate_limit_windows.clear()

    # Under limit (59 calls) passes
    for _ in range(59):
        passed, _ = TriggerPolicyEngine.check_rate_limit(trig_id, ws_id)
        assert passed is True

    # 60th call passes (reaches max limit)
    passed, _ = TriggerPolicyEngine.check_rate_limit(trig_id, ws_id)
    assert passed is True

    # 61st call exceeds TRIGGER_RATE_LIMIT_PER_MINUTE (60)
    passed_fail, err_msg = TriggerPolicyEngine.check_rate_limit(trig_id, ws_id)
    assert passed_fail is False
    assert "Rate limit" in err_msg


@pytest.mark.asyncio
async def test_workspace_concurrency_limit():
    mock_session = AsyncMock()
    mock_res = MagicMock()
    # Mock 5 active runs (at MAX_TRIGGER_CONCURRENCY_PER_WORKSPACE=5)
    mock_res.scalar.return_value = 5
    mock_session.execute.return_value = mock_res

    ws_id = uuid.uuid4()
    passed, active, max_c = await TriggerPolicyEngine.check_workspace_concurrency(mock_session, ws_id)
    assert passed is False
    assert active == 5
    assert max_c == 5


# =============================================================================
# 8. Retries & Exponential Backoff Tests
# =============================================================================

def test_retry_transient_classification():
    # Transient errors are retryable
    assert TriggerRetryManager.should_retry("provider_unavailable", "Service down", 0, 2) is True
    assert TriggerRetryManager.should_retry("gateway_timeout", "Connection timed out", 1, 2) is True
    assert TriggerRetryManager.should_retry("temporary_network_failure", "Socket closed", 0, 2) is True

    # Non-transient errors are NEVER retried
    assert TriggerRetryManager.should_retry("authorization_failure", "401 Unauthorized", 0, 2) is False
    assert TriggerRetryManager.should_retry("invalid_workflow", "Schema invalid", 0, 2) is False
    assert TriggerRetryManager.should_retry("policy_denial", "HITL rejected", 0, 2) is False

    # Max retries reached
    assert TriggerRetryManager.should_retry("provider_unavailable", "Service down", 2, 2) is False


def test_retry_exponential_backoff():
    d0 = TriggerRetryManager.calculate_backoff_delay(0, backoff_factor=2.0, base_seconds=2.0)
    d1 = TriggerRetryManager.calculate_backoff_delay(1, backoff_factor=2.0, base_seconds=2.0)
    d2 = TriggerRetryManager.calculate_backoff_delay(2, backoff_factor=2.0, base_seconds=2.0)

    assert d0 == 2.0
    assert d1 == 4.0
    assert d2 == 8.0


# =============================================================================
# 9. Trigger Policy & State Validation Tests
# =============================================================================

@pytest.mark.asyncio
async def test_trigger_policy_validation():
    mock_session = AsyncMock()
    ws_id = uuid.uuid4()

    trigger = WorkflowTrigger(
        id=uuid.uuid4(),
        workspace_id=ws_id,
        workflow_id=uuid.uuid4(),
        name="Scheduled Data Ingestion",
        trigger_type="schedule",
        status="paused",  # Paused
        configuration={},
        retry_configuration={},
    )
    workflow = Workflow(id=trigger.workflow_id, workspace_id=ws_id, name="Test Flow", status="published")

    # Disabled trigger raises TriggerDisabledError
    with pytest.raises(TriggerDisabledError):
        await TriggerPolicyEngine.validate_trigger_execution(mock_session, trigger, workflow)

    # Active trigger on archived workflow raises TriggerPolicyError
    trigger.status = "active"
    workflow.status = "archived"
    with pytest.raises(TriggerPolicyError):
        await TriggerPolicyEngine.validate_trigger_execution(mock_session, trigger, workflow)


# =============================================================================
# 10. Test Mode Dry-Run Evaluation Tests
# =============================================================================

@pytest.mark.asyncio
async def test_trigger_test_mode_dry_run():
    mock_session = AsyncMock()
    service = TriggerService(mock_session)

    ws_id = uuid.uuid4()
    wf_id = uuid.uuid4()
    trig_id = uuid.uuid4()

    mock_trigger = WorkflowTrigger(
        id=trig_id,
        workspace_id=ws_id,
        workflow_id=wf_id,
        name="GitHub Bug Auto-Triage",
        trigger_type="connector_event",
        status="active",
        configuration={
            "input_mapping": {
                "ticket_title": "{{payload.issue.title}}",
                "repo": "{{payload.repository.full_name}}",
            }
        },
        filter_configuration={
            "logic": "AND",
            "rules": [
                {"field": "issue.labels", "operator": "contains", "value": "bug"},
            ],
        },
        retry_configuration={"max_retries": 2},
    )

    mock_workflow = Workflow(
        id=wf_id,
        workspace_id=ws_id,
        name="Triage Workflow",
        status="published",
        input_schema={"type": "object", "properties": {"ticket_title": {"type": "string"}}},
    )

    service.get_trigger_or_raise = AsyncMock(return_value=mock_trigger)
    service.wf_repo.get_workflow_by_id_or_raise = AsyncMock(return_value=mock_workflow)

    test_req = TriggerTestRequest(
        sample_payload={
            "issue": {"title": "Null pointer on login", "labels": ["bug", "auth"]},
            "repository": {"full_name": "corp/auth-svc"},
        }
    )

    res = await service.test_trigger(trig_id, ws_id, test_req)
    assert res.accepted is True
    assert res.filter_matched is True
    assert res.mapped_inputs["ticket_title"] == "Null pointer on login"
    assert res.mapped_inputs["repo"] == "corp/auth-svc"
    assert len(res.policy_warnings) == 0


# =============================================================================
# 11. Trigger Registry Completeness Test
# =============================================================================

def test_trigger_registry_defaults():
    reg = TriggerRegistry()
    assert reg.exists("manual.workflow.run")
    assert reg.exists("schedule.workflow.run")
    assert reg.exists("webhook.workflow.run")
    assert reg.exists("github.issue.created")
    assert reg.exists("github.issue.updated")
    assert reg.exists("github.pull_request.opened")
    assert reg.exists("github.pull_request.updated")
    assert len(reg.list()) >= 7


# =============================================================================
# 12. Scheduler Due-Trigger Claiming Tests
# =============================================================================

@pytest.mark.asyncio
async def test_scheduler_claim_due_triggers():
    mock_session = AsyncMock()
    mock_res = MagicMock()

    now = datetime.now(timezone.utc)
    due_trigger = WorkflowTrigger(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        workflow_id=uuid.uuid4(),
        name="Hourly Pipeline",
        trigger_type="schedule",
        status="active",
        configuration={"schedule": {"expression": "0 * * * *", "timezone": "UTC"}},
        retry_configuration={"max_retries": 2},
        next_run_at=now - timedelta(minutes=5),  # in the past (due!)
    )
    mock_res.scalars.return_value.all.return_value = [due_trigger]
    mock_session.execute.return_value = mock_res

    claimed = await TriggerScheduler.identify_and_claim_due_triggers(mock_session)
    assert len(claimed) == 1
    assert claimed[0].last_triggered_at is not None
    assert claimed[0].next_run_at > now


# =============================================================================
# 13. End-to-End API Routes Tests
# =============================================================================

def test_workflow_trigger_api_lifecycle(client, user1_auth):
    """Full lifecycle: create trigger -> list -> pause -> resume -> test -> delete."""
    me = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws_id = me["default_workspace_id"]

    # 1. Create target workflow
    wf_res = client.post(
        f"/api/workflows?workspace_id={ws_id}",
        json={
            "name": "Trigger Target Pipeline",
            "steps": [{"id": "in", "name": "Input Step", "type": "input", "config": {}}],
            "input_schema": {"type": "object", "properties": {"alert_name": {"type": "string"}}},
        },
        headers=user1_auth["headers"],
    )
    assert wf_res.status_code == 201
    wf_id = wf_res.json()["id"]

    # 2. Create Webhook Trigger
    trig_create_res = client.post(
        f"/api/workflows/{wf_id}/triggers?workspace_id={ws_id}",
        json={
            "name": "Production Alert Ingestion",
            "trigger_type": "webhook",
            "configuration": {
                "input_mapping": {"alert_name": "{{payload.alert_name}}"},
            },
            "filter_configuration": {
                "logic": "AND",
                "rules": [{"field": "env", "operator": "equals", "value": "production"}],
            },
            "debounce_seconds": 30,
        },
        headers=user1_auth["headers"],
    )
    assert trig_create_res.status_code == 201
    trig_data = trig_create_res.json()
    assert trig_data["name"] == "Production Alert Ingestion"
    assert trig_data["trigger_type"] == "webhook"
    assert trig_data["status"] == "active"
    assert "public_trigger_id" in trig_data
    assert "webhook_secret" in trig_data  # Returned strictly once on creation
    trig_id = trig_data["id"]
    public_id = trig_data["public_trigger_id"]
    wh_secret = trig_data["webhook_secret"]

    # 3. List triggers for workflow
    list_res = client.get(f"/api/workflows/{wf_id}/triggers?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert list_res.status_code == 200
    assert len(list_res.json()["triggers"]) >= 1

    # 4. Pause Trigger
    pause_res = client.post(f"/api/triggers/{trig_id}/pause?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "paused"

    # 5. Resume Trigger
    resume_res = client.post(f"/api/triggers/{trig_id}/resume?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert resume_res.status_code == 200
    assert resume_res.json()["status"] == "active"

    # 6. Test Trigger (Dry-run mode)
    test_res = client.post(
        f"/api/triggers/{trig_id}/test?workspace_id={ws_id}",
        json={
            "sample_payload": {"alert_name": "DB Disk Full", "env": "production"},
        },
        headers=user1_auth["headers"],
    )
    assert test_res.status_code == 200
    test_json = test_res.json()
    assert test_json["filter_matched"] is True
    assert test_json["mapped_inputs"]["alert_name"] == "DB Disk Full"

    # 7. Get Webhook Status
    status_res = client.get(f"/api/triggers/{trig_id}/webhook/status?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert status_res.status_code == 200
    assert status_res.json()["configured"] is True
    assert status_res.json()["public_trigger_id"] == public_id

    # 8. Regenerate Secret
    regen_res = client.post(f"/api/triggers/{trig_id}/webhook/regenerate-secret?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert regen_res.status_code == 200
    new_secret = regen_res.json()["secret"]
    assert new_secret != wh_secret

    # 9. Delete Trigger
    del_res = client.delete(f"/api/triggers/{trig_id}?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert del_res.status_code == 204


def test_public_webhook_signature_verification(client, user1_auth):
    """Public webhook receiver validates HMAC signatures and filters."""
    me = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws_id = me["default_workspace_id"]

    wf_res = client.post(
        f"/api/workflows?workspace_id={ws_id}",
        json={"name": "Webhook Flow", "steps": [{"id": "in", "name": "In", "type": "input"}]},
        headers=user1_auth["headers"],
    )
    wf_id = wf_res.json()["id"]

    trig_res = client.post(
        f"/api/workflows/{wf_id}/triggers?workspace_id={ws_id}",
        json={
            "name": "Secured Webhook Trigger",
            "trigger_type": "webhook",
            "configuration": {},
        },
        headers=user1_auth["headers"],
    )
    trig_data = trig_res.json()
    public_id = trig_data["public_trigger_id"]
    secret = trig_data["webhook_secret"]

    # 1. Unsigned request fails with 401
    raw_payload = b'{"msg":"hello world"}'
    fail_res = client.post(f"/api/webhooks/{public_id}", data=raw_payload, headers={"Content-Type": "application/json"})
    assert fail_res.status_code == 401

    # 2. Correct HMAC signature succeeds with 202
    sig = f"sha256={hmac.new(secret.encode(), raw_payload, hashlib.sha256).hexdigest()}"
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": sig,
        "X-Webhook-Timestamp": str(int(time.time())),
        "X-Idempotency-Key": f"idemp-{uuid.uuid4().hex[:8]}",
    }
    ok_res = client.post(f"/api/webhooks/{public_id}", data=raw_payload, headers=headers)
    assert ok_res.status_code == 202
    assert ok_res.json()["accepted"] is True


def test_manual_trigger_run_api(client, user1_auth):
    """Manual trigger run executes through WorkflowExecutor and returns completed TriggerRun."""
    me = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws_id = me["default_workspace_id"]

    wf_res = client.post(
        f"/api/workflows?workspace_id={ws_id}",
        json={"name": "Manual Flow", "steps": [{"id": "in", "name": "Input", "type": "input"}]},
        headers=user1_auth["headers"],
    )
    wf_id = wf_res.json()["id"]

    trig_res = client.post(
        f"/api/workflows/{wf_id}/triggers?workspace_id={ws_id}",
        json={"name": "Manual Button Run", "trigger_type": "manual"},
        headers=user1_auth["headers"],
    )
    trig_id = trig_res.json()["id"]

    run_res = client.post(
        f"/api/workflows/{wf_id}/triggers/{trig_id}/run?workspace_id={ws_id}",
        json={"input_data": {"test_key": "test_val"}},
        headers=user1_auth["headers"],
    )
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert run_data["trigger_id"] == trig_id
    assert run_data["status"] == "completed"
    assert run_data["workflow_run_id"] is not None

    # Check run history
    runs_res = client.get(f"/api/triggers/{trig_id}/runs?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert runs_res.status_code == 200
    assert runs_res.json()["total"] >= 1


def test_hitl_approval_preserved_on_trigger(client, user1_auth):
    """Triggered workflows reaching an approval step transition to waiting_for_approval and do NOT auto-approve."""
    me = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws_id = me["default_workspace_id"]

    wf_res = client.post(
        f"/api/workflows?workspace_id={ws_id}",
        json={
            "name": "HITL Protected Flow",
            "steps": [
                {
                    "id": "appr_step",
                    "name": "Critical Action",
                    "type": "tool",
                    "approval": {"required": True, "timeout_seconds": 3600},
                }
            ],
        },
        headers=user1_auth["headers"],
    )
    wf_id = wf_res.json()["id"]

    trig_res = client.post(
        f"/api/workflows/{wf_id}/triggers?workspace_id={ws_id}",
        json={"name": "HITL Trigger", "trigger_type": "manual"},
        headers=user1_auth["headers"],
    )
    trig_id = trig_res.json()["id"]

    run_res = client.post(
        f"/api/workflows/{wf_id}/triggers/{trig_id}/run?workspace_id={ws_id}",
        json={},
        headers=user1_auth["headers"],
    )
    assert run_res.status_code == 200
    run_data = run_res.json()
    wf_run_id = run_data["workflow_run_id"]

    # Verify workflow run state is paused / waiting_for_approval
    wf_run = client.get(f"/api/workflow-runs/{wf_run_id}?workspace_id={ws_id}", headers=user1_auth["headers"]).json()
    assert wf_run["status"] in ("waiting_for_approval", "paused")


def test_cross_workspace_trigger_isolation(client, user1_auth, user2_auth):
    """User 2 cannot inspect, update, or run User 1's triggers."""
    me1 = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws1_id = me1["default_workspace_id"]
    me2 = client.get("/api/auth/me", headers=user2_auth["headers"]).json()
    ws2_id = me2["default_workspace_id"]

    # User 1 creates workflow and trigger
    wf = client.post(
        f"/api/workflows?workspace_id={ws1_id}",
        json={"name": "User 1 Confidential Flow"},
        headers=user1_auth["headers"],
    ).json()

    trig = client.post(
        f"/api/workflows/{wf['id']}/triggers?workspace_id={ws1_id}",
        json={"name": "Confidential Trigger", "trigger_type": "manual"},
        headers=user1_auth["headers"],
    ).json()
    trig_id = trig["id"]

    # User 2 attempts to get User 1's trigger using ws2 context -> 404
    get_res = client.get(f"/api/triggers/{trig_id}?workspace_id={ws2_id}", headers=user2_auth["headers"])
    assert get_res.status_code == 404

    # User 2 attempts to run User 1's trigger -> 404
    run_res = client.post(
        f"/api/workflows/{wf['id']}/triggers/{trig_id}/run?workspace_id={ws2_id}",
        headers=user2_auth["headers"],
    )
    assert run_res.status_code == 404
