import asyncio
import json
import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.config import settings
from backend.app.db.models.evaluation_lab import (
    EvaluationCase,
    EvaluationDataset,
    EvaluationDatasetVersion,
    EvaluationExperiment,
    EvaluationExperimentRun,
)
from backend.app.services.evaluation_lab import (
    AssertionDefinition,
    AssertionEngine,
    AssertionType,
    CaseRunStatus,
    DatasetImportError,
    DatasetNotFoundError,
    DatasetService,
    DatasetValidationError,
    DatasetVersionLockedError,
    EvaluationCaseCreate,
    EvaluationCaseService,
    EvaluationCaseUpdate,
    EvaluationComparator,
    EvaluationDatasetCreate,
    EvaluationExperimentCreate,
    EvaluationLabPolicy,
    EvaluationLabService,
    EvaluationRunner,
    ExperimentService,
    ExperimentStatus,
    RegressionDetector,
    SideEffectBlockedError,
    TargetType,
    sanitize_value,
    validate_and_sanitize_case_payload,
    validate_dataset_import_payload,
)


# =============================================================================
# 1. Sanitization & Byte Bounds Tests
# =============================================================================

def test_sanitization_secrets_and_byte_limits():
    payload = {
        "api_key": "sk-1234567890abcdef1234567890abcdef",
        "authorization": "Bearer ya29.a0AfH6SMD_secret_token",
        "nested": {
            "password": "super_secret_pw",
            "safe_val": "normal instruction text",
        },
    }
    sanitized = sanitize_value(payload)
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["authorization"] == "[REDACTED]"
    assert sanitized["nested"]["password"] == "[REDACTED]"
    assert sanitized["nested"]["safe_val"] == "normal instruction text"

    # Test oversized case input payload
    oversized = {"big": "a" * (settings.MAX_CASE_INPUT_BYTES + 500)}
    with pytest.raises(DatasetValidationError):
        validate_and_sanitize_case_payload(input_data=oversized)

    # Test oversized dataset import
    oversized_bytes = b"x" * 100
    with pytest.raises(DatasetImportError):
        validate_dataset_import_payload(oversized_bytes, max_bytes=50)


# =============================================================================
# 2. Assertion Engine (All Types) Tests
# =============================================================================

def test_assertion_engine_all_types():
    output_text = "The system uses PostgreSQL for persistence and Redis for caching. [source_1] [doc_2]"
    output_data = {"database": "PostgreSQL", "summary": "DB details", "count": 5}
    retrieval_sources = [{"id": "source_1", "title": "DB Guide"}, {"id": "doc_2", "title": "Cache Doc"}]
    findings = [
        {"check_type": "grounding", "passed": True, "message": "Grounding verified"},
        {"check_type": "safety", "passed": True, "message": "Content safe"},
    ]

    # 1. exact_match
    a_exact = AssertionDefinition(type=AssertionType.EXACT_MATCH, value="PostgreSQL", path="database")
    res_exact = AssertionEngine.evaluate_assertion(a_exact, output_text, output_data=output_data)
    assert res_exact.passed is True

    # 2. contains & not_contains
    a_contains = AssertionDefinition(type=AssertionType.CONTAINS, value="PostgreSQL")
    res_contains = AssertionEngine.evaluate_assertion(a_contains, output_text)
    assert res_contains.passed is True

    a_not_contains = AssertionDefinition(type=AssertionType.NOT_CONTAINS, value="Oracle")
    res_not_contains = AssertionEngine.evaluate_assertion(a_not_contains, output_text)
    assert res_not_contains.passed is True

    # 3. regex
    a_regex = AssertionDefinition(type=AssertionType.REGEX, value=r"Redis\s+for\s+caching")
    res_regex = AssertionEngine.evaluate_assertion(a_regex, output_text)
    assert res_regex.passed is True

    # 4. json_fields
    json_out = json.dumps({"status": "ok", "items": [1, 2], "meta": {"owner": "test"}})
    a_json = AssertionDefinition(type=AssertionType.JSON_FIELDS, fields=["status", "items"])
    res_json = AssertionEngine.evaluate_assertion(a_json, json_out)
    assert res_json.passed is True

    # 5. citation_exists & citation_matches_source
    a_cite_exists = AssertionDefinition(type=AssertionType.CITATION_EXISTS)
    res_cite = AssertionEngine.evaluate_assertion(a_cite_exists, output_text)
    assert res_cite.passed is True

    a_cite_matches = AssertionDefinition(type=AssertionType.CITATION_MATCHES_SOURCE)
    res_cite_match = AssertionEngine.evaluate_assertion(
        a_cite_matches, output_text, retrieval_sources=retrieval_sources
    )
    assert res_cite_match.passed is True

    # 6. grounded_claims
    a_grounding = AssertionDefinition(type=AssertionType.GROUNDED_CLAIMS)
    res_ground = AssertionEngine.evaluate_assertion(a_grounding, output_text, evaluator_findings=findings)
    assert res_ground.passed is True

    # 7. required_fields
    a_req = AssertionDefinition(type=AssertionType.REQUIRED_FIELDS, fields=["PostgreSQL", "Redis"])
    res_req = AssertionEngine.evaluate_assertion(a_req, output_text)
    assert res_req.passed is True

    # 8. output_format
    a_fmt = AssertionDefinition(type=AssertionType.OUTPUT_FORMAT, value="json")
    res_fmt = AssertionEngine.evaluate_assertion(a_fmt, json_out)
    assert res_fmt.passed is True

    # 9. evaluator_check
    a_eval_check = AssertionDefinition(type=AssertionType.EVALUATOR_CHECK, check_name="safety")
    res_eval_check = AssertionEngine.evaluate_assertion(a_eval_check, output_text, evaluator_findings=findings)
    assert res_eval_check.passed is True


# =============================================================================
# 3. Side-Effect & Policy Tests
# =============================================================================

def test_side_effect_policy_blocking():
    # Destructive operation without fresh approval must be blocked
    with pytest.raises(SideEffectBlockedError):
        EvaluationLabPolicy.enforce_safe_execution_policy(
            operation_name="delete_database_table",
            is_write=True,
            is_destructive=True,
            has_fresh_approval=False,
        )

    # Write operation without fresh approval must be simulated in dry-run
    res = EvaluationLabPolicy.enforce_safe_execution_policy(
        operation_name="create_github_issue",
        is_write=True,
        is_destructive=False,
        has_fresh_approval=False,
    )
    assert res["blocked"] is True
    assert res["simulated"] is True
    assert "Would execute" in res["message"]


# =============================================================================
# 4. Dataset Versioning & Immutability Unit Tests
# =============================================================================

@pytest.mark.asyncio
async def test_dataset_versioning_and_locked_version():
    session = AsyncMock()
    ws_id = uuid.uuid4()
    dataset_in = EvaluationDatasetCreate(name="QA Benchmark", description="Core benchmark cases")

    # Mock DB interaction for create_dataset
    dataset, version = await DatasetService.create_dataset(
        session=session,
        workspace_id=ws_id,
        dataset_in=dataset_in,
    )
    assert dataset.version == 1
    assert version.version == 1

    # Verify locked version error when completed experiment exists
    completed_exp = EvaluationExperiment(
        id=uuid.uuid4(),
        workspace_id=ws_id,
        dataset_version_id=version.id,
        target_type="model",
        name="Completed Exp",
        status="completed",
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = completed_exp
    session.execute.return_value = mock_result

    with pytest.raises(DatasetVersionLockedError):
        await EvaluationLabPolicy.assert_dataset_version_editable(session, version.id)


# =============================================================================
# 5. Regression Detection Tests
# =============================================================================

@pytest.mark.asyncio
async def test_regression_detector_thresholds_and_lost_checks():
    session = AsyncMock()
    base_id = uuid.uuid4()
    cand_id = uuid.uuid4()

    exp_base = EvaluationExperiment(id=base_id, name="Baseline", workspace_id=uuid.uuid4())
    exp_cand = EvaluationExperiment(id=cand_id, name="Candidate", workspace_id=exp_base.workspace_id)

    case_1 = EvaluationCase(id=uuid.uuid4(), case_key="case_1", name="Case 1")
    case_2 = EvaluationCase(id=uuid.uuid4(), case_key="case_2", name="Case 2")

    # Baseline: both passed, low latency, low cost
    run_b1 = EvaluationExperimentRun(
        id=uuid.uuid4(), experiment_id=base_id, case_id=case_1.id, status="passed",
        latency_ms=100, estimated_cost=0.001,
        evaluation_result={"assertions": [{"assertion_type": "contains", "passed": True}]}
    )
    run_b2 = EvaluationExperimentRun(
        id=uuid.uuid4(), experiment_id=base_id, case_id=case_2.id, status="passed",
        latency_ms=120, estimated_cost=0.001,
        evaluation_result={"assertions": [{"assertion_type": "contains", "passed": True}]}
    )

    # Candidate: case_1 failed, high latency, high cost
    run_c1 = EvaluationExperimentRun(
        id=uuid.uuid4(), experiment_id=cand_id, case_id=case_1.id, status="failed",
        latency_ms=300, estimated_cost=0.005,
        evaluation_result={"assertions": [{"assertion_type": "contains", "passed": False}]}
    )
    run_c2 = EvaluationExperimentRun(
        id=uuid.uuid4(), experiment_id=cand_id, case_id=case_2.id, status="passed",
        latency_ms=300, estimated_cost=0.005,
        evaluation_result={"assertions": [{"assertion_type": "contains", "passed": True}]}
    )

    # Configure session mocks
    m1 = MagicMock(); m1.scalar_one_or_none.return_value = exp_base
    m2 = MagicMock(); m2.scalar_one_or_none.return_value = exp_cand
    m3 = MagicMock(); m3.all.return_value = [(run_b1, case_1), (run_b2, case_2)]
    m4 = MagicMock(); m4.all.return_value = [(run_c1, case_1), (run_c2, case_2)]
    session.execute.side_effect = [m1, m2, m3, m4]

    reg_res = await RegressionDetector.detect_regressions(
        session=session,
        baseline_experiment_id=base_id,
        candidate_experiment_id=cand_id,
    )

    assert reg_res.regression_detected is True
    # At least case_status regression, latency regression (>25%), cost regression (>25%), failure rate (>5%)
    assert len(reg_res.regressions) >= 2
    checks = [r.check for r in reg_res.regressions]
    assert "case_status" in checks
    assert "latency_threshold" in checks


# =============================================================================
# 6. Evaluation Comparator Factual Diffs
# =============================================================================

@pytest.mark.asyncio
async def test_evaluation_comparator_factual_differences():
    session = AsyncMock()
    exp_a_id = uuid.uuid4()
    exp_b_id = uuid.uuid4()

    exp_a = EvaluationExperiment(id=exp_a_id, name="Exp A", target_type="model", target_configuration={}, workspace_id=uuid.uuid4())
    exp_b = EvaluationExperiment(id=exp_b_id, name="Exp B", target_type="model", target_configuration={}, workspace_id=exp_a.workspace_id)

    case_1 = EvaluationCase(id=uuid.uuid4(), case_key="case_1", name="Case 1")
    run_a = EvaluationExperimentRun(
        id=uuid.uuid4(), experiment_id=exp_a_id, case_id=case_1.id, status="passed",
        latency_ms=100, input_tokens=50, output_tokens=20, estimated_cost=0.0001,
        evaluation_result={"assertions": [{"assertion_type": "contains", "passed": True}]}
    )
    run_b = EvaluationExperimentRun(
        id=uuid.uuid4(), experiment_id=exp_b_id, case_id=case_1.id, status="failed",
        latency_ms=150, input_tokens=60, output_tokens=30, estimated_cost=0.0002,
        evaluation_result={"assertions": [{"assertion_type": "contains", "passed": False}]}
    )

    ca1 = MagicMock(); ca1.scalar_one_or_none.return_value = exp_a
    ca2 = MagicMock(); ca2.scalar_one_or_none.return_value = exp_b
    ca3 = MagicMock(); ca3.all.return_value = [(run_a, case_1)]
    ca4 = MagicMock(); ca4.all.return_value = [(run_b, case_1)]
    session.execute.side_effect = [ca1, ca2, ca3, ca4]

    comp_res = await EvaluationComparator.compare_experiments(
        session=session,
        experiment_a_id=exp_a_id,
        experiment_b_id=exp_b_id,
    )

    assert comp_res.summary["cases_difference"] == 1
    assert comp_res.latency_difference["delta_ms"] == 50.0
    assert comp_res.token_difference["delta_tokens"] == 20
    assert len(comp_res.regressions) == 1
    assert comp_res.regressions[0]["case_key"] == "case_1"


# =============================================================================
# 7. API Integration Tests
# =============================================================================

def test_evaluation_lab_api_full_flow(auth_client):
    # 1. Create Workspace
    ws_res = auth_client.post("/api/workspaces", json={"name": "Eval Lab Workspace"})
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]
    headers = {"X-Workspace-Id": ws_id}

    # 2. Create Evaluation Dataset
    ds_res = auth_client.post(
        "/api/evaluation/datasets",
        json={"name": "LLM Verification Dataset", "description": "Gold standard prompt tests"},
        headers=headers,
    )
    assert ds_res.status_code == 201
    ds_data = ds_res.json()
    dataset_id = ds_data["id"]
    version_id = ds_data["active_version_id"]
    assert ds_data["name"] == "LLM Verification Dataset"
    assert ds_data["version"] == 1

    # 3. Add Evaluation Case
    case_payload = {
        "case_key": "test_math_1",
        "name": "Basic arithmetic calculation",
        "input_data": {"input": "What is 40 + 2?"},
        "expected_output": "42",
        "assertions": [
            {"type": "contains", "value": "42", "path": "text"},
            {"type": "required_fields", "fields": ["42"]},
        ],
    }
    case_res = auth_client.post(
        f"/api/evaluation/datasets/{dataset_id}/cases?version_id={version_id}",
        json=case_payload,
        headers=headers,
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 4. Import Cases via JSON
    import_payload = {
        "file_format": "json",
        "content": json.dumps([
            {
                "case_key": "import_case_2",
                "name": "Second imported case",
                "input_data": {"input": "Hello world"},
                "expected_output": "Hello world",
                "assertions": [{"type": "contains", "value": "Hello"}],
            }
        ]),
        "target_version_id": version_id,
    }
    import_res = auth_client.post(
        f"/api/evaluation/datasets/{dataset_id}/import",
        json=import_payload,
        headers=headers,
    )
    assert import_res.status_code == 200
    assert import_res.json()["imported_count"] == 1

    # 5. Export Cases
    export_res = auth_client.get(f"/api/evaluation/datasets/{dataset_id}/export?format=json", headers=headers)
    assert export_res.status_code == 200
    exported_data = export_res.json()
    assert len(exported_data["cases"]) == 2

    # 6. Create Experiment
    exp_payload = {
        "name": "Prompt Evaluation Experiment v1",
        "dataset_version_id": version_id,
        "target_type": "prompt",
        "target_configuration": {"template": "Answer directly: {input}"},
    }
    exp_res = auth_client.post("/api/evaluation/experiments", json=exp_payload, headers=headers)
    assert exp_res.status_code == 201
    exp_id = exp_res.json()["id"]
    assert exp_res.json()["status"] == "draft"

    # 7. Run Experiment
    run_res = auth_client.post(f"/api/evaluation/experiments/{exp_id}/run", headers=headers)
    assert run_res.status_code == 200
    assert run_res.json()["status"] == "completed"

    # 8. Get Experiment Results
    results_res = auth_client.get(f"/api/evaluation/experiments/{exp_id}/results", headers=headers)
    assert results_res.status_code == 200
    results_data = results_res.json()
    assert results_data["summary"]["total_cases"] == 2
    assert len(results_data["runs"]) == 2

    # 9. Test Workspace Isolation (Unauthorized Workspace ID)
    unauth_headers = {"X-Workspace-Id": str(uuid.uuid4())}
    bad_res = auth_client.get(f"/api/evaluation/datasets/{dataset_id}", headers=unauth_headers)
    assert bad_res.status_code == 404

    # 10. Compare and Regression endpoints
    comp_res = auth_client.post(
        "/api/evaluation/compare",
        json={"experiment_a": exp_id, "experiment_b": exp_id},
        headers=headers,
    )
    assert comp_res.status_code == 200
    assert comp_res.json()["summary"]["cases_difference"] == 0

    reg_res = auth_client.post(
        "/api/evaluation/regressions/check",
        json={"baseline_experiment": exp_id, "candidate_experiment": exp_id},
        headers=headers,
    )
    assert reg_res.status_code == 200
    assert reg_res.json()["regression_detected"] is False


def test_dataset_import_jsonl_and_csv(auth_client):
    ws_res = auth_client.post("/api/workspaces", json={"name": "Import Test WS"})
    ws_id = ws_res.json()["id"]
    headers = {"X-Workspace-Id": ws_id}

    ds_res = auth_client.post("/api/evaluation/datasets", json={"name": "Import Formats Dataset"}, headers=headers)
    ds_id = ds_res.json()["id"]

    # 1. Test JSONL import
    jsonl_content = '{"case_key": "c_jsonl_1", "name": "JSONL Case 1", "input_data": {"input": "test 1"}}\n{"case_key": "c_jsonl_2", "name": "JSONL Case 2", "input_data": {"input": "test 2"}}'
    import_jsonl = auth_client.post(
        f"/api/evaluation/datasets/{ds_id}/import",
        json={"file_format": "jsonl", "content": jsonl_content},
        headers=headers,
    )
    assert import_jsonl.status_code == 200
    assert import_jsonl.json()["imported_count"] == 2

    # 2. Test CSV import
    csv_content = 'case_key,name,input,expected_output\nc_csv_1,CSV Case 1,Question A,Answer A\nc_csv_2,CSV Case 2,Question B,Answer B'
    import_csv = auth_client.post(
        f"/api/evaluation/datasets/{ds_id}/import",
        json={"file_format": "csv", "content": csv_content},
        headers=headers,
    )
    assert import_csv.status_code == 200
    assert import_csv.json()["imported_count"] == 2

    # 3. Export as JSONL
    export_jsonl = auth_client.get(f"/api/evaluation/datasets/{ds_id}/export?format=jsonl", headers=headers)
    assert export_jsonl.status_code == 200
    lines = export_jsonl.text.strip().splitlines()
    assert len(lines) == 4
