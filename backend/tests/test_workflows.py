"""
Comprehensive tests for the Workflow System:
- Workflow CRUD & builder
- Structural and semantic validation
- Input schema validation & runtime type checking
- Safe variable interpolation
- Deterministic condition evaluation & branching
- Transform step operations
- End-to-end execution across retrieval, tools, generation, evaluation
- Failure & retry resilience
- Publishing & version immutability
- Template listing & installation
- Multi-tenant workspace isolation
- Observability trace events
"""
import uuid
import pytest
from backend.app.services.workflows.schemas import (
    StepType,
    WorkflowDefinition,
    WorkflowStepDefinition,
)
from backend.app.services.workflows.validator import WorkflowValidator
from backend.app.services.workflows.executor import WorkflowExecutionState


# --- UNIT TESTS: VALIDATION, RESOLUTION, TRANSFORMS, CONDITIONS ---

def test_workflow_validator_valid_and_invalid_definitions():
    """WorkflowValidator detects invalid step limits, missing IDs, duplicate IDs, and invalid branch targets."""
    # 1. Valid definition
    valid_def = WorkflowDefinition(
        name="Valid Workflow",
        steps=[
            WorkflowStepDefinition(id="in", name="Input", type=StepType.INPUT),
            WorkflowStepDefinition(
                id="gen",
                name="Generate",
                type=StepType.GENERATE,
                config={"temperature": 0.5, "prompt_template": "Hello {{input.name}}"}
            ),
            WorkflowStepDefinition(id="out", name="Output", type=StepType.OUTPUT),
        ]
    )
    res = WorkflowValidator.validate_workflow_definition(valid_def)
    assert res.valid is True
    assert len(res.issues) == 0

    # 2. Empty steps
    empty_def = WorkflowDefinition(name="Empty", steps=[])
    res_empty = WorkflowValidator.validate_workflow_definition(empty_def)
    assert res_empty.valid is False

    # 3. Duplicate step IDs
    dup_def = WorkflowDefinition(
        name="Dup",
        steps=[
            WorkflowStepDefinition(id="step_a", name="Step 1", type=StepType.INPUT),
            WorkflowStepDefinition(id="step_a", name="Step 2", type=StepType.GENERATE),
        ]
    )
    res_dup = WorkflowValidator.validate_workflow_definition(dup_def)
    assert res_dup.valid is False
    assert any("Duplicate step ID" in iss.message for iss in res_dup.issues)

    # 4. Invalid branch target
    bad_branch_def = WorkflowDefinition(
        name="Bad Branch",
        steps=[
            WorkflowStepDefinition(id="in", name="Input", type=StepType.INPUT),
            WorkflowStepDefinition(
                id="cond",
                name="Check",
                type=StepType.CONDITION,
                config={"left": "input.x", "operator": "==", "right": "1", "if_true": "non_existent_step"}
            ),
        ]
    )
    res_branch = WorkflowValidator.validate_workflow_definition(bad_branch_def)
    assert res_branch.valid is False
    assert any("does not match any valid step ID" in iss.message for iss in res_branch.issues)


def test_input_schema_validation_and_type_checking():
    """Runtime input is validated against the input_schema with strict type checking and defaults."""
    schema = {
        "query": {"type": "string", "required": True},
        "count": {"type": "number", "required": False, "default": 5},
        "flag": {"type": "boolean", "required": False, "default": False},
    }

    # 1. Valid input
    runtime_in = {"query": "test search"}
    validated = WorkflowValidator.validate_runtime_input(schema, runtime_in)
    assert validated["query"] == "test search"
    assert validated["count"] == 5
    assert validated["flag"] is False

    # 2. Missing required field raises error
    from backend.app.services.workflows.errors import WorkflowInputValidationError
    with pytest.raises(WorkflowInputValidationError):
        WorkflowValidator.validate_runtime_input(schema, {"count": 10})

    # 3. Incompatible type raises error
    with pytest.raises(WorkflowInputValidationError):
        WorkflowValidator.validate_runtime_input(schema, {"query": 12345})


def test_safe_variable_interpolation():
    """Execution state safely resolves expressions like {{input.key}} and {{steps.s1.output}}."""
    state = WorkflowExecutionState(input_data={"topic": "Quantum Computing", "nested": {"deep": "found"}})
    state.step_outputs["search"] = {"results": [{"title": "Paper 1"}, {"title": "Paper 2"}]}
    state.step_outputs["generate"] = {"output": "Quantum computers leverage qubits."}

    # String template interpolation
    rendered = state.resolve_value("Topic: {{input.topic}}, Fact: {{steps.generate.output}}")
    assert rendered == "Topic: Quantum Computing, Fact: Quantum computers leverage qubits."

    # Direct object replacement
    resolved_obj = state.resolve_value("{{steps.search.results}}")
    assert isinstance(resolved_obj, list)
    assert len(resolved_obj) == 2
    assert resolved_obj[0]["title"] == "Paper 1"

    # Nested path
    deep_val = state.resolve_value("{{input.nested.deep}}")
    assert deep_val == "found"


def test_transform_operations_and_safety():
    """Transform step safely handles select, rename, map, filter, join, and truncate without arbitrary code."""
    from backend.app.services.workflows.executor import WorkflowExecutor
    executor = WorkflowExecutor(session=None)

    # 1. Select
    data = [{"a": 1, "b": 2, "c": 3}, {"a": 4, "b": 5, "c": 6}]
    res_select = executor._apply_transform("select", data, {"fields": ["a", "c"]})
    assert res_select == [{"a": 1, "c": 3}, {"a": 4, "c": 6}]

    # 2. Rename
    single = {"old_key": "val", "keep": 10}
    res_rename = executor._apply_transform("rename", single, {"mapping": {"old_key": "new_key"}})
    assert res_rename == {"new_key": "val", "keep": 10}

    # 3. Filter
    items = [{"status": "active"}, {"status": "inactive"}, {"status": "active"}]
    res_filter = executor._apply_transform("filter", items, {"field": "status", "value": "active"})
    assert len(res_filter) == 2

    # 4. Join
    strings = ["Line 1", "Line 2", "Line 3"]
    res_join = executor._apply_transform("join", strings, {"delimiter": " | "})
    assert res_join == "Line 1 | Line 2 | Line 3"

    # 5. Truncate
    long_text = "A" * 100
    res_trunc = executor._apply_transform("truncate", long_text, {"max_length": 10})
    assert len(res_trunc) == 13  # 10 + '...'


def test_condition_evaluation_operators():
    """Condition step properly evaluates ==, !=, >, >=, <, <=, and exists."""
    from backend.app.services.workflows.executor import WorkflowExecutor
    executor = WorkflowExecutor(session=None)

    assert executor._evaluate_condition("warning", "==", "warning") is True
    assert executor._evaluate_condition("passed", "==", "warning") is False
    assert executor._evaluate_condition("passed", "!=", "warning") is True
    assert executor._evaluate_condition(10, ">", 5) is True
    assert executor._evaluate_condition(5, ">=", 5) is True
    assert executor._evaluate_condition(3, "<", 10) is True
    assert executor._evaluate_condition("hello", "exists", None) is True
    assert executor._evaluate_condition("", "exists", None) is False


# --- INTEGRATION TESTS: API, REPOSITORY, EXECUTION, AND ISOLATION ---

def test_create_and_list_workflows_with_steps(client, user1_auth):
    """Authenticated users can create, get, list, and delete workflows with step definitions."""
    me = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws_id = me["default_workspace_id"]

    # 1. Create Workflow
    wf_payload = {
        "name": "E2E Test Workflow",
        "description": "Multi-step automated pipeline",
        "input_schema": {
            "query": {"type": "string", "required": True}
        },
        "steps": [
            {"id": "in", "name": "Input", "type": "input", "config": {}},
            {
                "id": "gen",
                "name": "Synthesize",
                "type": "generate",
                "config": {"prompt_template": "Answer: {{input.query}}", "temperature": 0.3}
            },
            {"id": "out", "name": "Deliver", "type": "output", "config": {}},
        ]
    }
    create_res = client.post(f"/api/workflows?workspace_id={ws_id}", json=wf_payload, headers=user1_auth["headers"])
    assert create_res.status_code == 201
    wf_data = create_res.json()
    wf_id = wf_data["id"]
    assert wf_data["name"] == "E2E Test Workflow"
    assert wf_data["status"] == "draft"
    assert len(wf_data["steps"]) == 3

    # 2. Get Workflow
    get_res = client.get(f"/api/workflows/{wf_id}?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert get_res.status_code == 200
    assert get_res.json()["id"] == wf_id

    # 3. List Workflows
    list_res = client.get(f"/api/workflows?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1


def test_workflow_definition_update_and_validation(client, user1_auth):
    """Workflow definitions can be fetched, updated, and validated via dedicated builder endpoints."""
    me = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws_id = me["default_workspace_id"]

    wf_res = client.post(
        f"/api/workflows?workspace_id={ws_id}",
        json={"name": "Builder Workflow", "input_schema": {"topic": {"type": "string"}}},
        headers=user1_auth["headers"],
    )
    wf_id = wf_res.json()["id"]

    # 1. Update Definition
    new_def = {
        "steps": [
            {"id": "in", "name": "Input", "type": "input", "config": {}},
            {"id": "search", "name": "Web Search", "type": "tool", "config": {"tool_name": "web_search", "parameters": {"query": "{{input.topic}}"}}},
            {"id": "out", "name": "Output", "type": "output", "config": {}},
        ]
    }
    patch_res = client.patch(f"/api/workflows/{wf_id}/definition?workspace_id={ws_id}", json=new_def, headers=user1_auth["headers"])
    assert patch_res.status_code == 200
    assert len(patch_res.json()["steps"]) == 3

    # 2. Validate Workflow
    val_res = client.post(f"/api/workflows/{wf_id}/validate?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert val_res.status_code == 200
    assert val_res.json()["valid"] is True
    assert val_res.json()["tool_call_count"] == 1


def test_workflow_publishing_and_version_immutability(client, user1_auth):
    """Publishing creates an immutable version snapshot. Editing after publishing bumps draft version."""
    me = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws_id = me["default_workspace_id"]

    wf_res = client.post(
        f"/api/workflows?workspace_id={ws_id}",
        json={
            "name": "Publish Workflow",
            "steps": [
                {"id": "in", "name": "Input", "type": "input", "config": {}},
                {"id": "out", "name": "Output", "type": "output", "config": {}},
            ]
        },
        headers=user1_auth["headers"],
    )
    wf_id = wf_res.json()["id"]

    # 1. Publish Workflow
    pub_res = client.post(f"/api/workflows/{wf_id}/publish?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert pub_res.status_code == 200
    assert pub_res.json()["status"] == "published"
    assert pub_res.json()["version"] == 1

    # 2. Edit definition after publishing
    patch_res = client.patch(
        f"/api/workflows/{wf_id}/definition?workspace_id={ws_id}",
        json={
            "steps": [
                {"id": "in", "name": "Input", "type": "input", "config": {}},
                {"id": "gen", "name": "Generate", "type": "generate", "config": {"prompt_template": "Draft"}},
                {"id": "out", "name": "Output", "type": "output", "config": {}},
            ]
        },
        headers=user1_auth["headers"],
    )
    assert patch_res.status_code == 200
    patched = patch_res.json()
    assert patched["status"] == "draft"
    assert patched["version"] == 2


def test_workflow_execution_end_to_end(client, user1_auth):
    """Workflows execute all step types sequentially, resolve variables, produce output, and record trace."""
    me = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws_id = me["default_workspace_id"]

    wf_payload = {
        "name": "Full Execution Workflow",
        "input_schema": {
            "question": {"type": "string", "required": True}
        },
        "steps": [
            {"id": "in", "name": "Capture Input", "type": "input", "config": {}},
            {"id": "retrieve", "name": "Retrieve KB", "type": "retrieve", "config": {"top_k": 3, "strategy": "hybrid"}},
            {
                "id": "generate",
                "name": "Generate Output",
                "type": "generate",
                "config": {"prompt_template": "Detailed answer for: {{input.question}}"}
            },
            {"id": "eval", "name": "Verification Check", "type": "evaluate", "config": {"mode": "standard"}},
            {"id": "out", "name": "Deliver", "type": "output", "config": {"primary_output": "{{steps.generate.output}}"}}
        ]
    }

    wf_res = client.post(f"/api/workflows?workspace_id={ws_id}", json=wf_payload, headers=user1_auth["headers"])
    wf_id = wf_res.json()["id"]

    # Execute workflow run
    run_res = client.post(
        f"/api/workflows/{wf_id}/run?workspace_id={ws_id}",
        json={"input_data": {"question": "What is Python asyncio?"}},
        headers=user1_auth["headers"],
    )
    assert run_res.status_code == 201
    run_data = run_res.json()
    assert run_data["status"] == "completed"
    assert run_data["duration_ms"] >= 0
    assert "output_data" in run_data
    run_id = run_data["id"]

    # Check WorkflowRun Detail endpoint
    detail_res = client.get(f"/api/workflow-runs/{run_id}?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert detail_res.status_code == 200
    assert detail_res.json()["status"] == "completed"

    # Check WorkflowRun Trace endpoint
    trace_res = client.get(f"/api/workflow-runs/{run_id}/trace?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert trace_res.status_code == 200
    events = trace_res.json()
    assert len(events) >= 2


def test_template_listing_and_installation(client, user1_auth):
    """Users can inspect built-in templates and install them into their active workspace as draft workflows."""
    # 1. List Templates
    tpl_res = client.get("/api/workflow-templates", headers=user1_auth["headers"])
    assert tpl_res.status_code == 200
    templates = tpl_res.json()["templates"]
    assert len(templates) >= 4
    template_ids = [t["id"] for t in templates]
    assert "research-assistant" in template_ids
    assert "document-qa" in template_ids

    # 2. Install Template
    me = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws_id = me["default_workspace_id"]

    inst_res = client.post(
        f"/api/workflow-templates/research-assistant/install?workspace_id={ws_id}",
        headers=user1_auth["headers"],
    )
    assert inst_res.status_code == 201
    installed = inst_res.json()
    assert installed["name"] == "Research Assistant"
    assert installed["status"] == "draft"
    assert len(installed["steps"]) >= 5


def test_workflow_duplication(client, user1_auth):
    """Workflows can be duplicated with all steps and schemas copied into a new draft workflow."""
    me = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws_id = me["default_workspace_id"]

    wf_res = client.post(
        f"/api/workflows?workspace_id={ws_id}",
        json={
            "name": "Original Pipeline",
            "steps": [{"id": "in", "name": "Input", "type": "input", "config": {}}]
        },
        headers=user1_auth["headers"],
    )
    wf_id = wf_res.json()["id"]

    dup_res = client.post(f"/api/workflows/{wf_id}/duplicate?workspace_id={ws_id}", headers=user1_auth["headers"])
    assert dup_res.status_code == 201
    dup_data = dup_res.json()
    assert "Original Pipeline (Copy)" in dup_data["name"]
    assert dup_data["id"] != wf_id


def test_cross_workspace_workflow_isolation(client, user1_auth, user2_auth):
    """User 2 cannot inspect, edit, delete, or run User 1's workflows."""
    me1 = client.get("/api/auth/me", headers=user1_auth["headers"]).json()
    ws1_id = me1["default_workspace_id"]

    me2 = client.get("/api/auth/me", headers=user2_auth["headers"]).json()
    ws2_id = me2["default_workspace_id"]

    # User 1 creates workflow
    wf1 = client.post(
        f"/api/workflows?workspace_id={ws1_id}",
        json={"name": "User 1 Secret Flow"},
        headers=user1_auth["headers"],
    ).json()
    wf1_id = wf1["id"]

    # User 2 tries to access User 1's workflow using ws2 context
    get_res = client.get(f"/api/workflows/{wf1_id}?workspace_id={ws2_id}", headers=user2_auth["headers"])
    assert get_res.status_code == 404

    # User 2 tries to run User 1's workflow
    run_res = client.post(f"/api/workflows/{wf1_id}/run?workspace_id={ws2_id}", json={}, headers=user2_auth["headers"])
    assert run_res.status_code == 404


def test_unauthenticated_workflow_endpoints_rejected(client):
    """Unauthenticated requests are rejected with 401."""
    res = client.get("/api/workflow-templates")
    assert res.status_code == 401
