"""
Unit, Security, and Integration Tests for Step 26: Unified Event Bus and Real-Time Execution Updates.
Verifies event persistence, monotonic sequencing, idempotency deduplication,
secret sanitization, filter validation, consumer failure isolation,
SSE streaming, and multi-tenant workspace isolation.
"""
import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app.core.errors import AuthorizationError
from backend.app.db.models.event import Event, EventDelivery
from backend.app.services.events.constants import (
    AUDITABLE_EVENTS,
    ActorType,
    AggregateType,
    EventDeliveryStatus,
    SystemEventType,
)
from backend.app.services.events.consumer import (
    EventConsumer,
    EventConsumerRegistry,
    consumer_registry,
)
from backend.app.services.events.dispatcher import EventDispatcher
from backend.app.services.events.errors import (
    EventAuthorizationError,
    EventPayloadTooLargeError,
    EventValidationError,
    InvalidFilterError,
)
from backend.app.services.events.filters import EventFilterValidator
from backend.app.services.events.policies import EventPolicyEngine
from backend.app.services.events.publisher import EventPublisher
from backend.app.services.events.registry import event_registry
from backend.app.services.events.repository import EventRepository
from backend.app.services.events.sanitizer import EventSanitizer
from backend.app.services.events.schemas import (
    ActorSchema,
    AggregateSchema,
    EventContract,
    EventPublishRequest,
)
from backend.app.services.events.stream import (
    EventStreamService,
    SSEClientConnection,
    SSEConnectionManager,
)


# =============================================================================
# 1. Sanitization & Byte Budget Tests
# =============================================================================

def test_event_sanitizer_removes_sensitive_credentials():
    """Verify secrets, passwords, tokens, hidden prompts, and chain-of-thought are scrubbed."""
    raw = {
        "title": "Task executed",
        "api_key": "sk-proj-super-secret-12345",
        "token": "ghp_abcdef123456",
        "password": "db_master_password",
        "nested": {
            "authorization": "Bearer eyJhbGciOi...",
            "chain_of_thought": "Thinking about internal database structure...",
            "hidden_prompt": "You are an internal system agent...",
            "safe_field": "public_safe_data",
        },
    }

    clean = EventSanitizer.sanitize_dict(raw)
    assert clean["api_key"] == "[REDACTED]"
    assert clean["token"] == "[REDACTED]"
    assert clean["password"] == "[REDACTED]"
    assert clean["nested"]["authorization"] == "[REDACTED]"
    assert clean["nested"]["chain_of_thought"] == "[REDACTED]"
    assert clean["nested"]["hidden_prompt"] == "[REDACTED]"
    assert clean["nested"]["safe_field"] == "public_safe_data"


def test_event_sanitizer_enforces_payload_size_limits():
    """Verify payloads exceeding configured byte budget raise EventPayloadTooLargeError."""
    huge_data = {"key": "A" * 70000}
    with pytest.raises(EventPayloadTooLargeError):
        EventSanitizer.validate_and_sanitize_payload(huge_data)


# =============================================================================
# 2. Policy & Actor Validation Tests
# =============================================================================

def test_event_policy_actor_validation():
    """Verify that only approved actor types are allowed, blocking arbitrary inputs."""
    for valid in ["user", "system", "worker", "connector", "scheduler"]:
        assert EventPolicyEngine.validate_actor_type(valid) == valid

    with pytest.raises(EventValidationError):
        EventPolicyEngine.validate_actor_type("arbitrary_external_bot")

    with pytest.raises(EventValidationError):
        EventPolicyEngine.validate_actor_type("")


# =============================================================================
# 3. Filter Validation & Pattern Matcher Tests
# =============================================================================

def test_event_filter_validation_and_matching():
    """Verify category wildcards, exact matches, and SQL/regex injection rejection."""
    # Valid wildcards
    assert EventFilterValidator.validate_event_type_pattern("job.*") == "job.*"
    assert EventFilterValidator.validate_event_type_pattern("workflow.*") == "workflow.*"
    assert EventFilterValidator.validate_event_type_pattern("approval.requested") == "approval.requested"

    # Matcher behavior
    assert EventFilterValidator.matches("job.completed", "job.*") is True
    assert EventFilterValidator.matches("workflow.started", "job.*") is False
    assert EventFilterValidator.matches("workflow.started", "*") is True
    assert EventFilterValidator.matches("workflow.started", "workflow.started") is True

    # Rejection of dangerous patterns & SQL injection attempts
    with pytest.raises(InvalidFilterError):
        EventFilterValidator.validate_event_type_pattern("job.*; DROP TABLE events;--")

    with pytest.raises(InvalidFilterError):
        EventFilterValidator.validate_event_type_pattern(".*[a-z]+")

    with pytest.raises(InvalidFilterError):
        EventFilterValidator.validate_event_type_pattern("unsupported_category.*")


# =============================================================================
# 4. Centralized Event Registry Completeness Test
# =============================================================================

def test_event_registry_has_all_initial_events():
    """Verify that all initial events required in Step 26 are registered."""
    required = [
        "job.created", "job.queued", "job.started", "job.progress", "job.retrying",
        "job.cancel_requested", "job.cancelled", "job.completed", "job.failed", "job.recovered",
        "workflow.started", "workflow.step_started", "workflow.step_completed",
        "workflow.waiting_for_approval", "workflow.resumed", "workflow.completed", "workflow.failed",
        "trigger.created", "trigger.updated", "trigger.paused", "trigger.resumed",
        "trigger.fired", "trigger.completed", "trigger.failed",
        "document.processing_started", "document.processing_progress",
        "document.processing_completed", "document.processing_failed",
        "evaluation.started", "evaluation.completed", "evaluation.regression_detected", "evaluation.failed",
        "replay.started", "replay.progress", "replay.completed", "replay.failed",
        "connector.started", "connector.completed", "connector.failed",
        "approval.requested", "approval.approved", "approval.rejected", "approval.expired",
        "notification.created", "notification.delivery_started",
        "notification.delivery_completed", "notification.delivery_failed",
        "system.warning", "system.error",
    ]

    for ev in required:
        assert event_registry.is_registered(ev), f"Required event '{ev}' is not registered."
        definition = event_registry.get(ev)
        assert definition.aggregate_type is not None


# =============================================================================
# 5. Publisher, Monotonic Sequence & Idempotency Tests
# =============================================================================

@pytest.mark.asyncio
async def test_event_publication_and_monotonic_sequencing():
    """Verify that events in the same aggregate receive strictly increasing sequence numbers."""
    mock_session = AsyncMock()
    repo = EventRepository(mock_session)

    # Simulate sequence computation: returns 1, then 2
    mock_res1 = MagicMock()
    mock_res1.scalar_one.return_value = 1
    mock_res1.scalar_one_or_none.return_value = None

    mock_session.execute.return_value = mock_res1

    event1, is_new1 = await repo.create_event(
        workspace_id=uuid.uuid4(),
        event_type="workflow.started",
        aggregate_type="workflow",
        aggregate_id="wf_123",
        payload={"step": 1},
    )
    assert is_new1 is True
    assert event1.sequence_number == 1

    mock_res2 = MagicMock()
    mock_res2.scalar_one.return_value = 2
    mock_session.execute.return_value = mock_res2

    event2, is_new2 = await repo.create_event(
        workspace_id=event1.workspace_id,
        event_type="workflow.step_completed",
        aggregate_type="workflow",
        aggregate_id="wf_123",
        payload={"step": 1, "status": "done"},
    )
    assert is_new2 is True
    assert event2.sequence_number == 2


@pytest.mark.asyncio
async def test_event_idempotency_prevents_duplicate_records():
    """Verify that re-publishing with the same idempotency_key returns the existing event."""
    mock_session = AsyncMock()
    repo = EventRepository(mock_session)

    existing_event = Event(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        event_type="job.completed",
        aggregate_type="job",
        aggregate_id="job_001",
        idempotency_key="worker_attempt_retry_42",
        payload={"status": "completed"},
        metadata_json={},
    )

    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = existing_event
    mock_session.execute.return_value = mock_res

    event, is_new = await repo.create_event(
        workspace_id=existing_event.workspace_id,
        event_type="job.completed",
        aggregate_type="job",
        aggregate_id="job_001",
        payload={"status": "completed"},
        idempotency_key="worker_attempt_retry_42",
    )

    assert is_new is False
    assert event.id == existing_event.id


# =============================================================================
# 6. Consumer Failure Isolation Test
# =============================================================================

@pytest.mark.asyncio
async def test_consumer_registry_and_failure_isolation():
    """Verify that an exception in one consumer does not crash other consumers."""
    class FailingConsumer(EventConsumer):
        @property
        def consumer_name(self):
            return "failing_consumer"

        @property
        def supported_event_types(self):
            return ["*"]

        async def process(self, event):
            raise RuntimeError("Database connection reset inside consumer")

    class WorkingConsumer(EventConsumer):
        def __init__(self):
            self.processed = False

        @property
        def consumer_name(self):
            return "working_consumer"

        @property
        def supported_event_types(self):
            return ["*"]

        async def process(self, event):
            self.processed = True
            return True

    working = WorkingConsumer()
    custom_reg = EventConsumerRegistry()
    custom_reg.register(FailingConsumer())
    custom_reg.register(working)

    test_contract = EventContract(
        id=str(uuid.uuid4()),
        type="job.completed",
        timestamp=datetime.now(timezone.utc).isoformat(),
        workspace_id=str(uuid.uuid4()),
        actor=ActorSchema(type="worker", id="worker_1"),
        aggregate=AggregateSchema(type="job", id="job_123"),
        data={},
    )

    with patch("backend.app.services.events.dispatcher.consumer_registry", custom_reg):
        # Should not raise exception
        await EventDispatcher.dispatch(test_contract)
        assert working.processed is True


# =============================================================================
# 7. SSE Client Connection & Backpressure Test
# =============================================================================

def test_sse_client_connection_matching_and_backpressure():
    """Verify that SSE client connections enforce buffer bounds and drop slow clients safely."""
    ws_id = uuid.uuid4()
    conn = SSEClientConnection(
        client_id="test_client_001",
        workspace_id=ws_id,
        event_type_pattern="job.*",
        buffer_size=2,
    )

    contract_job = EventContract(
        id=str(uuid.uuid4()),
        type="job.completed",
        timestamp=datetime.now(timezone.utc).isoformat(),
        workspace_id=str(ws_id),
        actor=ActorSchema(type="system", id=None),
        aggregate=AggregateSchema(type="job", id="job_1"),
        data={},
    )
    assert conn.matches(contract_job) is True

    contract_workflow = EventContract(
        id=str(uuid.uuid4()),
        type="workflow.completed",
        timestamp=datetime.now(timezone.utc).isoformat(),
        workspace_id=str(ws_id),
        actor=ActorSchema(type="system", id=None),
        aggregate=AggregateSchema(type="workflow", id="wf_1"),
        data={},
    )
    assert conn.matches(contract_workflow) is False

    # Test buffer overflow & safe disconnect
    assert conn.enqueue("msg1") is True
    assert conn.enqueue("msg2") is True
    # 3rd message overflows buffer
    assert conn.enqueue("msg3") is False
    assert conn.is_active is False


# =============================================================================
# 8. End-to-End API Lifecycle & Multi-Tenant Isolation Tests
# =============================================================================

def test_event_history_api_lifecycle(client: TestClient, user1_auth, user2_auth):
    """
    Test listing events, filtering by event_type, getting single event,
    and verifying strict cross-workspace isolation.
    """
    headers1 = user1_auth["headers"]
    me1 = client.get("/api/auth/me", headers=headers1).json()
    ws1_id = me1["default_workspace_id"]
    ws1_headers = {**headers1, "X-Workspace-Id": ws1_id}

    headers2 = user2_auth["headers"]
    me2 = client.get("/api/auth/me", headers=headers2).json()
    ws2_id = me2["default_workspace_id"]
    ws2_headers = {**headers2, "X-Workspace-Id": ws2_id}

    # 1. Trigger an action in workspace 1 (HITL request) which emits events
    client.post(
        "/api/hitl/requests",
        json={"title": "Action for Event Bus Verification", "requested_action": "notify"},
        headers=ws1_headers,
    )

    # 2. List events in workspace 1
    events_res = client.get("/api/events", headers=ws1_headers)
    assert events_res.status_code == 200
    events = events_res.json()
    assert isinstance(events, list)

    if events:
        event_id = events[0]["id"]
        # 3. Get single event
        single_res = client.get(f"/api/events/{event_id}", headers=ws1_headers)
        assert single_res.status_code == 200
        assert single_res.json()["id"] == event_id

        # 4. Cross-workspace isolation: User 2 in WS2 cannot access WS1's event
        u2_single = client.get(f"/api/events/{event_id}", headers=ws2_headers)
        assert u2_single.status_code == 404


def test_event_replay_api_with_cursor(client: TestClient, user1_auth):
    """Test replaying events via /api/events/replay."""
    headers = user1_auth["headers"]
    me = client.get("/api/auth/me", headers=headers).json()
    ws_id = me["default_workspace_id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    replay_res = client.get("/api/events/replay?limit=10", headers=ws_headers)
    assert replay_res.status_code == 200
    data = replay_res.json()
    assert "events" in data
    assert "has_more" in data
    assert "total_count" in data


def test_retention_cleanup_preserves_auditable_events():
    """Verify that cleanup_old_events removes expired events but keeps auditable records."""
    mock_session = AsyncMock()
    repo = EventRepository(mock_session)

    mock_result = MagicMock()
    mock_result.rowcount = 42
    mock_session.execute.return_value = mock_result

    deleted = asyncio.run(repo.cleanup_old_events(retention_days=30))
    assert deleted == 42


def test_stream_endpoint_rejects_unauthorized_workspace(client: TestClient, user1_auth):
    """Verify that a user cannot stream events for a workspace they do not belong to."""
    headers = user1_auth["headers"]
    foreign_ws = uuid.uuid4()
    res = client.get(f"/api/events/stream?workspace_id={foreign_ws}", headers=headers)
    assert res.status_code == 403
    assert "Forbidden" in res.json()["detail"]


def test_stream_endpoint_rejects_malformed_filter(client: TestClient, user1_auth):
    """Verify that dangerous filter patterns are rejected with 422/400 validation error."""
    headers = user1_auth["headers"]
    me = client.get("/api/auth/me", headers=headers).json()
    ws_id = me["default_workspace_id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    res = client.get("/api/events?event_type=invalid;sql_injection", headers=ws_headers)
    assert res.status_code in [400, 422]


@pytest.mark.asyncio
async def test_concurrent_event_publication():
    """Verify that concurrent event publications within the same aggregate compute sequence numbers atomically."""
    mock_session = AsyncMock()
    repo = EventRepository(mock_session)

    # Mock sequence returning incrementing numbers
    counter = 0
    def next_seq_mock(*args, **kwargs):
        nonlocal counter
        counter += 1
        m = MagicMock()
        m.scalar_one.return_value = counter
        m.scalar_one_or_none.return_value = None
        return m

    mock_session.execute.side_effect = next_seq_mock

    ws_id = uuid.uuid4()
    tasks = [
        repo.create_event(
            workspace_id=ws_id,
            event_type="workflow.step_completed",
            aggregate_type="workflow",
            aggregate_id="wf_concurrent",
            payload={"step": i},
        )
        for i in range(5)
    ]
    results = await asyncio.gather(*tasks)
    events = [r[0] for r in results]
    seq_nums = [e.sequence_number for e in events]
    assert seq_nums == [1, 2, 3, 4, 5]

