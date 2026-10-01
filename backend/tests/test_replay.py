import asyncio
import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.db.models.run import Run
from backend.app.db.models.task import Task
from backend.app.db.models.project import Project
from backend.app.db.models.workspace import Workspace
from backend.app.db.models.user import User
from backend.app.db.models.workflow import WorkflowRun, Workflow
from backend.app.db.models.replay import ReplayRun
from backend.app.db.models.enums import RunStatus
from backend.app.services.replay import (
    ReplayService,
    ReplayRunner,
    ReplaySnapshotService,
    ReplayComparator,
    ReplayPolicy,
    ReplayEligibilityChecker,
    ErrorAnalysisService,
    sanitize_replay_snapshot,
    ReplayMode,
    ReplayStatus,
    RetrievalReplayMode,
    ReplayRunCreateRequest,
    ReplayStepRequest,
    ReplayError,
    ReplayNotFoundError,
    ReplayEligibilityError,
)


# =============================================================================
# 1. Snapshot Sanitization Tests
# =============================================================================

def test_sanitize_replay_snapshot_redacts_secrets():
    payload = {
        "api_key": "sk-1234567890abcdef1234567890abcdef",
        "authorization": "Bearer ya29.a0AfH6SMD_secret_token",
        "database_url": "postgresql://user:super_secret_pw@localhost:5432/db",
        "nested": {
            "github_token": "ghp_1234567890abcdefghijklmnopqrstuvwxyz",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0...",
            "safe_metadata": "public project info",
        },
        "safe_number": 42,
    }

    sanitized = sanitize_replay_snapshot(payload)
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["authorization"] == "[REDACTED]"
    assert sanitized["nested"]["github_token"] == "[REDACTED]"
    assert sanitized["nested"]["private_key"] == "[REDACTED]"
    assert sanitized["nested"]["safe_metadata"] == "public project info"
    assert sanitized["safe_number"] == 42


def test_sanitize_replay_snapshot_oversized_payload():
    payload = {"huge_content": "x" * 200000}
    sanitized = sanitize_replay_snapshot(payload)
    assert "TRUNCATED DUE TO SIZE LIMIT" in sanitized["huge_content"]

    with pytest.raises(Exception):
        sanitize_replay_snapshot(payload, max_bytes=100)


# =============================================================================
# 2. Replay Policy & Side-Effect Tests
# =============================================================================

def test_replay_policy_blocks_write_operations_in_dry_run():
    # Read operation: should NOT block
    assert not ReplayPolicy.should_block_side_effect("read_document", dry_run=True)
    assert not ReplayPolicy.should_block_side_effect("search_web", dry_run=True)

    # Write operations: MUST block in dry_run
    assert ReplayPolicy.should_block_side_effect("github_create_issue", dry_run=True)
    assert ReplayPolicy.should_block_side_effect("send_email", dry_run=True)
    assert ReplayPolicy.should_block_side_effect("delete_record", dry_run=True)
    assert ReplayPolicy.should_block_side_effect("database_mutate", dry_run=True)


def test_replay_policy_format_dry_run_simulation():
    sim = ReplayPolicy.format_dry_run_simulation(
        operation="create_issue",
        tool_name="github_create_issue",
        inputs={"title": "Fix bug", "repo": "org/repo"},
    )
    assert sim["dry_run"] is True
    assert sim["side_effect_blocked"] is True
    assert "Would execute" in sim["message"]
    assert sim["simulation_notice"] == "External side effects are disabled by default during replay."


# =============================================================================
# 3. Output Comparison Tests
# =============================================================================

def test_replay_comparator_factual_differences():
    orig_run = MagicMock(spec=Run)
    orig_run.id = uuid.uuid4()
    orig_run.output_content = "Line 1: Analysis completed\nLine 2: Result found\nLine 3: Done"
    orig_run.total_tokens = 150
    orig_run.latency_ms = 1200
    orig_run.estimated_cost = 0.005
    orig_run.model_name = "gpt-4o-mini"
    orig_run.model_provider = "openai"
    orig_run.context_sources = ["doc-1", "doc-2"]
    orig_run.tools_used = ["search_web"]
    orig_run.completion_evaluation = {"status": "passed", "grounded": True}

    replay_run = MagicMock(spec=ReplayRun)
    replay_run.id = uuid.uuid4()
    replay_run.original_run_id = orig_run.id
    replay_run.replay_output = "Line 1: Analysis completed\nLine 2: Updated result found\nLine 3: Done"
    replay_run.replay_metadata = {
        "final_model": "gpt-4o-mini",
        "model_provider": "openai",
        "duration_ms": 1100,
        "token_usage": {"total_tokens": 160},
        "context_sources": ["doc-1"],
        "tools_used": ["search_web"],
        "evaluation_result": {"status": "passed", "grounded": True},
    }

    comp = ReplayComparator.compare_runs(orig_run, replay_run)

    # Verify factual diffs
    assert comp.output_diff["same_output"] is False
    assert comp.output_diff["similarity_ratio"] >= 0.5
    assert comp.usage_diff["tokens_delta"] == 10
    assert comp.usage_diff["duration_ms_delta"] == -100
    assert comp.model_diff["same_model"] is True
    assert "doc-2" in comp.context_diff["removed_sources"]
    assert comp.determinism_indicators["same_model"] is True


# =============================================================================
# 4. Error Analysis & Failure Insights Tests
# =============================================================================

def test_error_analysis_service_diagnostics():
    failed_run = MagicMock(spec=Run)
    failed_run.id = uuid.uuid4()
    failed_run.status = RunStatus.FAILED
    failed_run.error_message = "Provider API timeout after 60s during completion request"
    failed_run.failed_step = {"step_type": "generate", "provider": "openai", "model": "gpt-4o"}
    failed_run.model_provider = "openai"
    failed_run.model_name = "gpt-4o"
    failed_run.repair_count = 2
    failed_run.latency_ms = 60000

    insights = ErrorAnalysisService.analyze_failure(failed_run)

    assert insights.failure_code == "PROVIDER_TIMEOUT"
    assert insights.stage.lower() == "generation"
    assert insights.provider == "openai"
    assert insights.retry_attempts == 2
    assert "timeout" in insights.suggested_action.lower()


# =============================================================================
# 5. Replay Runner Execution & Safety Tests (Async)
# =============================================================================

@pytest.mark.asyncio
async def test_replay_runner_inspect_mode():
    runner = ReplayRunner()

    orig_run = MagicMock(spec=Run)
    orig_run.id = uuid.uuid4()
    orig_run.output_content = "Original historical output text"
    orig_run.latency_ms = 850
    orig_run.total_tokens = 220
    orig_run.execution_steps = [{"step_id": "step-1", "type": "plan"}]

    replay_run = MagicMock(spec=ReplayRun)
    replay_run.id = uuid.uuid4()
    replay_run.workspace_id = uuid.uuid4()
    replay_run.original_run_id = orig_run.id
    replay_run.replay_mode = ReplayMode.INSPECT.value
    replay_run.status = ReplayStatus.QUEUED.value
    replay_run.dry_run = True
    replay_run.snapshot_version = "1.0"
    replay_run.original_run = orig_run
    replay_run.snapshot = {"task_configuration": {"title": "Test Task"}}
    replay_run.created_by = None
    replay_run.replay_metadata = {}

    session = AsyncMock()

    res = await runner.execute_replay(replay_run, overrides=None, session=session)
    assert res.status == ReplayStatus.COMPLETED.value
    assert res.replay_output == "Original historical output text"
    assert res.replay_metadata["mode"] == "inspect"


@pytest.mark.asyncio
async def test_replay_runner_cooperative_cancellation():
    runner = ReplayRunner()

    replay_run = MagicMock(spec=ReplayRun)
    replay_run.status = ReplayStatus.RUNNING.value

    session = AsyncMock()
    cancelled = await runner.cancel_replay(replay_run, session)
    assert cancelled.status == ReplayStatus.CANCELLED.value


@pytest.mark.asyncio
async def test_replay_runner_step_replay_dry_run_blocks_side_effect():
    runner = ReplayRunner()

    orig_run = MagicMock(spec=Run)
    orig_run.id = uuid.uuid4()
    orig_run.execution_steps = [
        {
            "id": "step-github",
            "type": "tool",
            "tool": "github_create_issue",
            "tool_input": {"title": "Bug report"},
        }
    ]

    session = AsyncMock()

    result = await runner.replay_single_step(
        original_run=orig_run,
        step_id="step-github",
        dry_run=True,
        overrides=None,
        session=session,
    )

    assert result["dry_run"] is True
    assert result["side_effect_blocked"] is True
    assert "Would execute" in result["message"]


# =============================================================================
# 6. Replay Eligibility Checker Tests
# =============================================================================

@pytest.mark.asyncio
async def test_replay_eligibility_missing_task():
    orig_run = MagicMock(spec=Run)
    orig_run.id = uuid.uuid4()
    orig_run.workspace_id = uuid.uuid4()
    orig_run.task_id = uuid.uuid4()
    orig_run.task = None
    orig_run.workflow_run_id = None
    orig_run.model_name = "gpt-4o-mini"
    orig_run.tools_used = []

    session = AsyncMock()
    session.execute = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_res

    eligibility = await ReplayEligibilityChecker.check_run_eligibility(orig_run, session)
    assert eligibility.eligible is False
    assert any("task" in w.lower() for w in eligibility.warnings)


# =============================================================================
# 7. Snapshot Creation Tests
# =============================================================================

@pytest.mark.asyncio
async def test_create_snapshot_from_run_sanitizes():
    ws_id = uuid.uuid4()
    task_id = uuid.uuid4()

    orig_run = MagicMock(spec=Run)
    orig_run.id = uuid.uuid4()
    orig_run.workspace_id = ws_id
    orig_run.task_id = task_id
    orig_run.workflow_run_id = None
    orig_run.model_name = "gpt-4o-mini"
    orig_run.model_provider = "openai"
    orig_run.input_snapshot = {
        "prompt": "Test prompt",
        "api_key": "sk-1234567890abcdef1234567890abcdef",
    }
    orig_run.task = MagicMock()
    orig_run.task.id = task_id
    orig_run.task.title = "Test Task"
    orig_run.task.instructions = "Instructions"
    orig_run.task.project_id = uuid.uuid4()
    orig_run.task.resolved_requirements = {"mode": "direct"}
    orig_run.task.evaluation_mode = "standard"
    orig_run.retrieval_strategy = "hybrid"
    orig_run.retrieval_scope = "project"
    orig_run.retrieval_top_k = 5
    orig_run.retrieval_sources = []
    orig_run.tools_used = []
    orig_run.context_sources = []
    orig_run.created_at = datetime.now(timezone.utc)

    session = AsyncMock()

    snapshot = await ReplaySnapshotService.create_snapshot_from_run(orig_run, session)

    assert snapshot.run_id == str(orig_run.id)
    assert snapshot.snapshot_version == "1.0"
    # Ensure sanitized: api_key must NOT be present in plaintext
    assert "sk-12345" not in str(snapshot.model_dump())


# =============================================================================
# 8. API Endpoint Integration Tests
# =============================================================================

def test_replay_api_inspect_dry_run_and_compare(auth_client):
    # 1. Create Workspace -> Project -> Task -> Run
    ws_res = auth_client.post("/api/workspaces", json={"name": "Replay Studio WS"})
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]

    proj_res = auth_client.post(f"/api/workspaces/{ws_id}/projects", json={"name": "Replay Proj"})
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["id"]

    task_res = auth_client.post(
        f"/api/projects/{proj_id}/tasks",
        json={"title": "Replay Test Task", "instructions": "Analyze trends and output summary."},
    )
    assert task_res.status_code == 201
    task_id = task_res.json()["id"]

    run_payload = {
        "status": "completed",
        "model_provider": "mock",
        "model_name": "mock-model-v1",
        "input_tokens": 100,
        "output_tokens": 50,
        "total_tokens": 150,
        "latency_ms": 750,
        "output_content": "Original execution response: trends are positive.",
        "execution_steps": [
            {"step_id": "step-1", "type": "plan", "description": "Planned analysis"},
            {"step_id": "step-2", "type": "generate", "description": "Generated content"},
        ],
    }
    run_res = auth_client.post(f"/api/tasks/{task_id}/runs", json=run_payload)
    assert run_res.status_code == 201
    run_id = run_res.json()["id"]

    headers = {"X-Workspace-Id": ws_id}

    # 2. Inspect Mode Replay
    inspect_res = auth_client.post(f"/api/runs/{run_id}/replay/inspect", headers=headers)
    assert inspect_res.status_code == 200
    inspect_data = inspect_res.json()
    assert inspect_data["replay_mode"] == "inspect"
    assert inspect_data["status"] == "completed"
    assert inspect_data["dry_run"] is True
    assert inspect_data["original_run_id"] == run_id
    assert "Original execution response" in inspect_data["replay_output"]
    replay_id = inspect_data["id"]

    # 3. Dry-Run Mode Replay
    dry_res = auth_client.post(
        f"/api/runs/{run_id}/replay/dry-run",
        json={"mode": "dry_run", "dry_run": True, "overrides": {"model": "mock-model-v1"}},
        headers=headers,
    )
    assert dry_res.status_code == 200
    dry_data = dry_res.json()
    assert dry_data["replay_mode"] == "dry_run"
    assert dry_data["dry_run"] is True

    # 4. List Replays
    list_res = auth_client.get(f"/api/replays?workspace_id={ws_id}", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 2
    assert any(r["id"] == replay_id for r in list_data["replays"])

    # 5. Get Replay Detail
    detail_res = auth_client.get(f"/api/replays/{replay_id}", headers=headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["id"] == replay_id
    assert detail_data["snapshot"] is not None

    # 6. Compare Replay
    comp_res = auth_client.get(f"/api/replays/{replay_id}/compare", headers=headers)
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert comp_data["replay_id"] == replay_id
    assert "output_diff" in comp_data
    assert "model_diff" in comp_data
    assert "usage_diff" in comp_data
    assert "determinism_indicators" in comp_data

    # 7. Check Replay Eligibility
    elig_res = auth_client.get(f"/api/runs/{run_id}/replay/eligibility", headers=headers)
    assert elig_res.status_code == 200
    assert elig_res.json()["eligible"] is True

    # 8. Replay Individual Step
    step_res = auth_client.post(
        f"/api/runs/{run_id}/steps/step-1/replay",
        json={"dry_run": True},
        headers=headers,
    )
    assert step_res.status_code == 200
    step_data = step_res.json()
    assert step_data["step_id"] == "step-1"
    assert step_data["dry_run"] is True


def test_replay_api_workspace_isolation(auth_client):
    random_ws = str(uuid.uuid4())
    random_run = str(uuid.uuid4())

    # Mismatched workspace / non-existent run
    res = auth_client.post(
        f"/api/runs/{random_run}/replay/inspect",
        headers={"X-Workspace-Id": random_ws},
    )
    assert res.status_code == 404

