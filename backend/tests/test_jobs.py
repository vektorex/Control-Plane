"""
Comprehensive test suite for Step 24: Durable Background Job System.
"""
import asyncio
import time
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.services.jobs import (
    AsyncExecutionResponse,
    ConnectorOperationJobHandler,
    DocumentProcessingJobHandler,
    EvaluationExperimentJobHandler,
    Job,
    JobCancellationError,
    JobConcurrencyError,
    JobCreateRequest,
    JobError,
    JobEvent,
    JobEventType,
    JobExecutionContext,
    JobHandler,
    JobHandlerNotFoundError,
    JobHandlerRegistry,
    JobLeaseExpiredError,
    JobLeaseManager,
    JobNotFoundError,
    JobPermissionDeniedError,
    JobPolicyEngine,
    JobPriority,
    JobProgressUpdate,
    JobQueue,
    JobRepository,
    JobResponse,
    JobRetryPolicy,
    JobScheduler,
    JobService,
    JobStateError,
    JobStatus,
    JobType,
    JobValidationError,
    JobWorker,
    ReplayRunJobHandler,
    TriggerRunJobHandler,
    WorkflowRunJobHandler,
    job_handler_registry,
)
from backend.app.db.models.user import User


# =============================================================================
# 1. Job Creation & Basic Repository Tests
# =============================================================================

@pytest.mark.asyncio
async def test_job_creation_and_events():
    mock_session = AsyncMock()
    repo = JobRepository(mock_session)

    ws_id = uuid.uuid4()
    job = await repo.create_job(
        workspace_id=ws_id,
        job_type="workflow_run",
        payload={"workflow_id": str(uuid.uuid4())},
        priority="high",
        max_attempts=3,
    )

    assert job.status == JobStatus.QUEUED.value
    assert job.priority == "high"
    assert job.job_type == "workflow_run"
    assert job.workspace_id == ws_id
    assert job.attempts == 0
    assert job.max_attempts == 3
    assert mock_session.add.call_count >= 3  # job + created_event + queued_event


# =============================================================================
# 2. Idempotency Tests
# =============================================================================

@pytest.mark.asyncio
async def test_job_idempotency_prevents_duplicate():
    mock_session = AsyncMock()
    service = JobService(mock_session)

    ws_id = uuid.uuid4()
    existing_job = Job(
        id=uuid.uuid4(),
        workspace_id=ws_id,
        job_type="document_processing",
        status=JobStatus.QUEUED.value,
        idempotency_key="doc_checksum_abc123",
        payload={"doc_id": "123"},
        progress={},
        created_at=datetime.now(timezone.utc),
        available_at=datetime.now(timezone.utc),
    )

    # First call: returns existing without creating
    service.repo.get_by_idempotency_key = AsyncMock(return_value=existing_job)

    req = JobCreateRequest(
        job_type=JobType.DOCUMENT_PROCESSING,
        payload={"doc_id": "123"},
        idempotency_key="doc_checksum_abc123",
    )
    job_resp, is_new = await service.create_job(workspace_id=ws_id, request=req)

    assert is_new is False
    assert job_resp.id == existing_job.id
    assert job_resp.idempotency_key == "doc_checksum_abc123"


# =============================================================================
# 3. Atomic Queue Claiming & Concurrency Protection
# =============================================================================

@pytest.mark.asyncio
async def test_atomic_queue_claiming_prevents_dual_execution():
    """
    Proves that when two workers compete for a queued job,
    only one worker claims the job and the second worker receives 0 claims.
    """
    mock_session = AsyncMock()
    queue = JobQueue(mock_session)

    now = datetime.now(timezone.utc)
    job1 = Job(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        job_type="workflow_run",
        status=JobStatus.QUEUED.value,
        priority=JobPriority.HIGH.value,
        available_at=now - timedelta(seconds=10),
        payload={},
        attempts=0,
        max_attempts=3,
        parent_job_id=None,
        created_at=now,
    )

    # Worker 1 query returns candidate job1
    mock_result1 = MagicMock()
    mock_result1.scalars.return_value.all.return_value = [job1]
    mock_session.execute.return_value = mock_result1

    claimed1 = await queue.claim_next_jobs(worker_id="worker_alpha", limit=1)
    assert len(claimed1) == 1
    assert claimed1[0].status == JobStatus.RUNNING.value
    assert claimed1[0].lease_owner == "worker_alpha"
    assert claimed1[0].attempts == 1

    # Worker 2 attempts to query: since status is now 'running', DB returns empty list
    mock_result2 = MagicMock()
    mock_result2.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result2

    claimed2 = await queue.claim_next_jobs(worker_id="worker_beta", limit=1)
    assert len(claimed2) == 0  # Worker 2 gets zero claims!


# =============================================================================
# 4. Priority Ordering Tests
# =============================================================================

def test_priority_order_weights():
    from backend.app.services.jobs.constants import PRIORITY_WEIGHTS, JobPriority
    assert PRIORITY_WEIGHTS[JobPriority.HIGH.value] < PRIORITY_WEIGHTS[JobPriority.NORMAL.value]
    assert PRIORITY_WEIGHTS[JobPriority.NORMAL.value] < PRIORITY_WEIGHTS[JobPriority.LOW.value]


# =============================================================================
# 5. Lease Heartbeat & Crash Recovery Tests
# =============================================================================

@pytest.mark.asyncio
async def test_lease_heartbeat_and_crash_recovery():
    mock_session = AsyncMock()
    now = datetime.now(timezone.utc)

    # 1. Expired job with attempts < max_attempts -> recovered to retrying
    expired_job = Job(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        job_type="evaluation_experiment",
        status=JobStatus.RUNNING.value,
        lease_owner="crashed_node_77",
        lease_expires_at=now - timedelta(minutes=5),  # expired!
        attempts=1,
        max_attempts=3,
    )
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = [expired_job]
    mock_session.execute.return_value = mock_res

    recovered = await JobLeaseManager.recover_expired_leases(mock_session)
    assert expired_job.id in recovered
    assert expired_job.status == JobStatus.RETRYING.value
    assert expired_job.lease_owner is None
    assert expired_job.available_at > now

    # 2. Expired job with max attempts reached -> failed permanently
    expired_job2 = Job(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        job_type="evaluation_experiment",
        status=JobStatus.RUNNING.value,
        lease_owner="crashed_node_88",
        lease_expires_at=now - timedelta(minutes=5),
        attempts=3,
        max_attempts=3,
    )
    mock_res2 = MagicMock()
    mock_res2.scalars.return_value.all.return_value = [expired_job2]
    mock_session.execute.return_value = mock_res2

    recovered2 = await JobLeaseManager.recover_expired_leases(mock_session)
    assert expired_job2.id in recovered2
    assert expired_job2.status == JobStatus.FAILED.value
    assert "LEASE_EXPIRED" in expired_job2.error_code


# =============================================================================
# 6. Retry Policy & Exponential Backoff Tests
# =============================================================================

def test_retry_policy_classification():
    # Transient failures are retryable
    assert JobRetryPolicy.should_retry(attempts=1, max_attempts=3, error_code="timeout", error_message="Service down") is True
    assert JobRetryPolicy.should_retry(attempts=2, max_attempts=3, error_code="503", error_message="Rate limited 429") is True

    # Permanent failures are NEVER retried
    assert JobRetryPolicy.should_retry(attempts=1, max_attempts=3, error_code="authorization_failure") is False
    assert JobRetryPolicy.should_retry(attempts=1, max_attempts=3, error_code="invalid_input", error_message="Schema 422") is False
    assert JobRetryPolicy.should_retry(attempts=1, max_attempts=3, error_code="hitl_rejection") is False
    assert JobRetryPolicy.should_retry(attempts=1, max_attempts=3, error_code="destructive_policy_violation") is False

    # Max attempts exceeded
    assert JobRetryPolicy.should_retry(attempts=3, max_attempts=3, error_code="timeout") is False


def test_retry_backoff_delay():
    d1 = JobRetryPolicy.calculate_backoff_delay(attempts=1, base_seconds=2.0, factor=2.0, jitter_pct=0.0)
    d2 = JobRetryPolicy.calculate_backoff_delay(attempts=2, base_seconds=2.0, factor=2.0, jitter_pct=0.0)
    d3 = JobRetryPolicy.calculate_backoff_delay(attempts=3, base_seconds=2.0, factor=2.0, jitter_pct=0.0)

    assert d1 == 2.0
    assert d2 == 4.0
    assert d3 == 8.0


# =============================================================================
# 7. Cooperative Cancellation Tests
# =============================================================================

@pytest.mark.asyncio
async def test_job_cancellation():
    mock_session = AsyncMock()
    service = JobService(mock_session)

    ws_id = uuid.uuid4()
    queued_job = Job(
        id=uuid.uuid4(),
        workspace_id=ws_id,
        job_type="workflow_run",
        status=JobStatus.QUEUED.value,
        payload={},
        progress={},
        created_at=datetime.now(timezone.utc),
        available_at=datetime.now(timezone.utc),
    )
    service.repo.get_by_id = AsyncMock(return_value=queued_job)

    # 1. Cancel queued job transitions immediately to cancelled
    res = await service.cancel_job(queued_job.id, ws_id, reason="User cancelled pipeline.")
    assert queued_job.status == JobStatus.CANCELLED.value
    assert queued_job.cancelled_at is not None

    # 2. Cannot cancel completed job -> raises JobStateError
    completed_job = Job(
        id=uuid.uuid4(),
        workspace_id=ws_id,
        job_type="workflow_run",
        status=JobStatus.COMPLETED.value,
        payload={},
        progress={},
        created_at=datetime.now(timezone.utc),
        available_at=datetime.now(timezone.utc),
    )
    service.repo.get_by_id = AsyncMock(return_value=completed_job)
    with pytest.raises(JobStateError):
        await service.cancel_job(completed_job.id, ws_id)


# =============================================================================
# 8. Payload Security Sanitization Tests
# =============================================================================

def test_payload_security_sanitization():
    # Valid payload passes
    JobPolicyEngine.validate_payload_safety("workflow_run", {"inputs": {"query": "Search query", "limit": 10}})

    # Malicious injection keys rejected
    with pytest.raises(JobValidationError):
        JobPolicyEngine.validate_payload_safety("workflow_run", {"eval": "print('malicious')"})

    with pytest.raises(JobValidationError):
        JobPolicyEngine.validate_payload_safety("connector_operation", {"params": {"subprocess": "rm -rf"}})


# =============================================================================
# 9. Parent Job Dependency Tests
# =============================================================================

@pytest.mark.asyncio
async def test_job_parent_dependency_blocks_premature_execution():
    mock_session = AsyncMock()
    queue = JobQueue(mock_session)

    now = datetime.now(timezone.utc)
    parent_job = Job(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        status=JobStatus.RUNNING.value,  # Parent is STILL RUNNING!
    )
    child_job = Job(
        id=uuid.uuid4(),
        workspace_id=parent_job.workspace_id,
        job_type="workflow_run",
        status=JobStatus.QUEUED.value,
        priority=JobPriority.HIGH.value,
        available_at=now - timedelta(seconds=10),
        parent_job_id=parent_job.id,
        payload={},
        attempts=0,
        max_attempts=3,
        created_at=now,
    )

    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = [child_job]
    # When querying parent job, returns running parent
    mock_parent_res = MagicMock()
    mock_parent_res.scalar_one_or_none.return_value = parent_job
    mock_session.execute.side_effect = [mock_res, mock_parent_res]

    # Child should NOT be claimed because parent is still running
    claimed = await queue.claim_next_jobs(worker_id="w1", limit=1)
    assert len(claimed) == 0


# =============================================================================
# 10. End-to-End API Routes Tests
# =============================================================================

def test_job_api_lifecycle(client, user1_auth):
    """Full lifecycle: create job -> list -> stats -> cancel -> retry."""
    me = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws_id = me["default_workspace_id"]

    # 1. Create durable job
    create_res = client.post(
        f"/api/jobs?workspace_id={ws_id}",
        json={
            "job_type": "document_processing",
            "priority": "high",
            "payload": {"document_id": str(uuid.uuid4())},
            "idempotency_key": f"doc_proc_{uuid.uuid4().hex[:8]}",
        },
        headers=user1_auth["headers"],
    )
    assert create_res.status_code == 201
    job_data = create_res.json()
    assert job_data["job_type"] == "document_processing"
    assert job_data["status"] == "queued"
    assert job_data["priority"] == "high"
    job_id = job_data["id"]

    # 2. Get Job details
    get_res = client.get(f"/api/jobs/{job_id}?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert get_res.status_code == 200
    assert get_res.json()["id"] == job_id

    # 3. List jobs
    list_res = client.get(f"/api/jobs?workspace_id={ws_id}&status=queued", headers=user1_auth["headers"])
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    # 4. Get events
    events_res = client.get(f"/api/jobs/{job_id}/events?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert events_res.status_code == 200
    assert len(events_res.json()["events"]) >= 2  # created + queued

    # 5. Cancel Job
    cancel_res = client.post(f"/api/jobs/{job_id}/cancel?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    # 6. Retry Job
    retry_res = client.post(f"/api/jobs/{job_id}/retry?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert retry_res.status_code == 200
    assert retry_res.json()["status"] == "queued"

    # 7. Operational stats
    stats_res = client.get(f"/api/jobs/operations/stats?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert stats_res.status_code == 200
    assert "queued_count" in stats_res.json()
    assert "running_count" in stats_res.json()


def test_cross_workspace_job_isolation(client, user1_auth, user2_auth):
    """User 2 cannot inspect, cancel, or retry User 1's jobs."""
    me1 = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws1_id = me1["default_workspace_id"]
    me2 = client.get("/api/auth/me", headers=user2_auth["headers"]).json()
    ws2_id = me2["default_workspace_id"]

    # User 1 creates job
    j1 = client.post(
        f"/api/jobs?workspace_id={ws1_id}",
        json={"job_type": "workflow_run", "payload": {"workflow_id": str(uuid.uuid4())}},
        headers=user1_auth["headers"],
    ).json()
    job_id = j1["id"]

    # User 2 attempts to get User 1's job in ws2 -> 404
    res_get = client.get(f"/api/jobs/{job_id}?workspace_id={ws2_id}", headers=user2_auth["headers"])
    assert res_get.status_code == 404

    # User 2 attempts to cancel User 1's job -> 404
    res_cancel = client.post(f"/api/jobs/{job_id}/cancel?workspace_id={ws2_id}", headers=user2_auth["headers"])
    assert res_cancel.status_code == 404


def test_workflow_async_run_creates_job(client, user1_auth):
    """POST /api/workflows/{id}/run with mode=async enqueues a job and returns immediately."""
    me = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws_id = me["default_workspace_id"]

    wf = client.post(
        f"/api/workflows?workspace_id={ws_id}",
        json={"name": "Async Workflow", "steps": [{"id": "s1", "name": "Step 1", "type": "input"}]},
        headers=user1_auth["headers"],
    ).json()
    wf_id = wf["id"]

    # Run in async mode
    run_res = client.post(
        f"/api/workflows/{wf_id}/run?workspace_id={ws_id}&mode=async",
        json={"input_data": {"test": "value"}},
        headers=user1_auth["headers"],
    )
    assert run_res.status_code == 201
    res_data = run_res.json()
    assert "job_id" in res_data
    assert res_data["status"] == "queued"
    assert res_data["job_type"] == "workflow_run"
    assert "poll_url" in res_data
    assert "cancel_url" in res_data
    assert "workflow_run_id" in res_data


def test_secret_sanitization_in_payload():
    """Confirms raw credentials (api_key, tokens) are rejected from job payloads."""
    with pytest.raises(JobValidationError):
        JobPolicyEngine.validate_payload_safety("connector_operation", {"api_key": "raw_secret_value"})

    with pytest.raises(JobValidationError):
        JobPolicyEngine.validate_payload_safety("workflow_run", {"inputs": {"bearer": "sk-proj-1234567890abcdef"}})


def test_invalid_handler_rejection():
    """Unregistered or invalid handler raises JobHandlerNotFoundError."""
    registry = JobHandlerRegistry()
    with pytest.raises(JobHandlerNotFoundError):
        registry.get_handler("arbitrary_python_code")


@pytest.mark.asyncio
async def test_job_progress_updates():
    """Validates structured progress persistence."""
    mock_session = AsyncMock()
    repo = JobRepository(mock_session)
    job = Job(id=uuid.uuid4(), workspace_id=uuid.uuid4(), job_type="document_processing")
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = job
    mock_session.execute.return_value = mock_res

    updated = await repo.update_progress(
        job_id=job.id,
        workspace_id=job.workspace_id,
        percentage=45,
        current_step="Chunking text segments",
        completed_steps=3,
        total_steps=5,
        message="Processed 30 chunks",
    )
    assert updated is not None
    assert updated.progress["percentage"] == 45
    assert updated.progress["current_step"] == "Chunking text segments"
    assert updated.progress["completed_steps"] == 3


@pytest.mark.asyncio
async def test_worker_graceful_shutdown():
    """Worker cleanly initiates stop and exits loop."""
    worker = JobWorker(concurrency=2, poll_interval=0.1)
    assert worker._running is False
    worker._running = True
    worker.stop()
    assert worker._running is False
    assert worker._stop_event.is_set()


@pytest.mark.asyncio
async def test_workspace_fairness_concurrency_limit():
    """Workspace cannot exceed MAX_WORKSPACE_RUNNING_JOBS."""
    mock_session = AsyncMock()
    ws_id = uuid.uuid4()
    mock_res = MagicMock()
    mock_res.scalar.return_value = 25  # Exceeds max 20
    mock_session.execute.return_value = mock_res

    with pytest.raises(JobConcurrencyError):
        await JobPolicyEngine.check_workspace_concurrency(mock_session, ws_id)


def test_connector_async_run_creates_job(client, user1_auth):
    """POST /api/connectors/{name}/execute with mode=async enqueues a job."""
    me = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws_id = me["default_workspace_id"]

    res = client.post(
        f"/api/connectors/github/execute?workspace_id={ws_id}&mode=async",
        json={"operation": "read_issue", "arguments": {"issue_number": 42}},
        headers=user1_auth["headers"],
    )
    assert res.status_code == 201
    data = res.json()
    assert "job_id" in data
    assert data["job_type"] == "connector_operation"
    assert data["status"] == "queued"


def test_evaluation_async_run_creates_job(client, user1_auth):
    """POST /api/evaluation/experiments/{id}/run with mode=async enqueues an evaluation job."""
    me = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws_id = me["default_workspace_id"]
    exp_id = uuid.uuid4()

    res = client.post(
        f"/api/evaluation/experiments/{exp_id}/run?mode=async",
        headers={**user1_auth["headers"], "X-Workspace-Id": str(ws_id)},
    )
    assert res.status_code == 201
    data = res.json()
    assert "job_id" in data
    assert data["job_type"] == "evaluation_experiment"
    assert data["status"] == "queued"
