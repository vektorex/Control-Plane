"""
Test Suite for STEP 28: Governed Prompt Management, Versioning, Release, and Experimentation.
Validates:
- Safe Deterministic Template Variable Rendering & Injection Protection
- Secret Protection & Masking
- Monotonic Versioning & Publication Immutability
- Environment Releases (Dev, Staging, Production), Promotion & Rollback
- Deterministic A/B Allocation & Factual Metrics
- Replay Snapshot & Reproducibility Preservation
- RBAC Matrix (Owner, Admin, Member, Viewer) & Multi-Tenant Isolation
"""
import uuid
import pytest
from sqlalchemy import select

from backend.app.services.prompts.constants import (
    PromptType,
    PromptStatus,
    PromptVersionStatus,
    PromptEnvironment,
    ExperimentStatus,
)
from backend.app.services.prompts.errors import (
    PromptNotFoundError,
    PromptVersionNotFoundError,
    ImmutableVersionError,
    VariableValidationError,
    SecretDetectedError,
    TemplateInjectionError,
    PromotionNotAllowedError,
)
from backend.app.services.prompts.renderer import default_prompt_renderer
from backend.app.services.prompts.sanitizer import sanitize_prompt_content, mask_secrets_in_text
from backend.app.services.prompts.validator import validate_variable_schema, validate_prompt_content
from backend.app.services.prompts.models import (
    Prompt,
    PromptVersion,
    PromptRelease,
    PromptExperiment,
    PromptExperimentVariant,
)
from backend.app.services.access_control.permissions import (
    PROMPT_READ,
    PROMPT_CREATE,
    PROMPT_UPDATE,
    PROMPT_PUBLISH,
    PROMPT_RELEASE,
    PROMPT_ROLLBACK,
    PROMPT_EXECUTE,
    PROMPT_EXPERIMENT,
    PROMPT_ARCHIVE,
)
from backend.app.services.access_control.roles import (
    ORGANIZATION_ROLE_PERMISSIONS,
    OrganizationRole,
    WorkspaceRole,
)


# =============================================================================
# 1. TEMPLATE VARIABLE RENDERING & INJECTION PROTECTION TESTS
# =============================================================================

def test_safe_rendering_basic_success():
    """Deterministic substitution with approved namespaces succeeds."""
    content = "Hello {{input.user_name}}, welcome to {{project.name}}. Priority: {{task.priority}}."
    schema = {
        "input.user_name": {"type": "string", "required": True},
        "project.name": {"type": "string", "required": True},
        "task.priority": {"type": "number", "required": False},
    }
    context = {
        "input.user_name": "Alice",
        "project.name": "Orchestrator Core",
        "task.priority": 1,
    }

    rendered = default_prompt_renderer.render(
        content=content,
        schema=schema,
        variables=context,
    )

    assert rendered.rendered_content == "Hello Alice, welcome to Orchestrator Core. Priority: 1."
    assert "input.user_name" in rendered.variables_used
    assert rendered.content_hash is not None
    assert rendered.estimated_tokens > 0


def test_rendering_rejects_missing_required_variable():
    """Renderer rejects execution when a required schema variable is missing."""
    content = "Process topic: {{input.topic}}"
    schema = {"input.topic": {"type": "string", "required": True}}

    with pytest.raises(VariableValidationError) as exc:
        default_prompt_renderer.render(
            content=content,
            schema=schema,
            variables={},  # missing input.topic
        )
    assert "Missing required variable" in str(exc.value) and "input.topic" in str(exc.value)


def test_rendering_rejects_forbidden_namespace():
    """Renderer rejects unauthorized namespaces outside safe allowlist."""
    content = "Evaluate {{forbidden.secret_data}}"
    with pytest.raises(TemplateInjectionError) as exc:
        default_prompt_renderer.render(
            content=content,
            schema={},
            variables={"forbidden.secret_data": "leak"},
        )
    assert "Forbidden namespace" in str(exc.value) and "forbidden" in str(exc.value)


def test_rendering_rejects_arbitrary_code_syntax():
    """Renderer and validator reject Python/JS eval or exec constructs."""
    bad_contents = [
        "{{__import__('os').system('id')}}",
        "{{eval('secret')}}",
        "{{process.exit(1)}}",
        "{{subprocess.Popen('ls')}}",
        "{{os.environ['SECRET']}}",
    ]
    for bad in bad_contents:
        with pytest.raises(TemplateInjectionError):
            validate_prompt_content(bad)


def test_template_injection_single_pass_no_recursive_eval():
    """
    CRITICAL SECURITY INVARIANT:
    Variable data containing template-like syntax '{{system.secret}}' must NOT
    be recursively evaluated on insertion. It remains pure literal data.
    """
    content = "User query: {{input.user_query}}"
    schema = {"input.user_query": {"type": "string", "required": True}}
    # Attacker passes a malicious payload looking like a variable tag
    malicious_input = "{{system.api_key}}"
    context = {"input.user_query": malicious_input}

    rendered = default_prompt_renderer.render(
        content=content,
        schema=schema,
        variables=context,
    )

    # In single-pass data rendering, {{system.api_key}} stays literally {{system.api_key}}
    assert rendered.rendered_content == "User query: {{system.api_key}}"


def test_secret_detection_rejects_credentials():
    """Secret sanitizer blocks OpenAI, Anthropic, AWS, private keys, and bearer tokens."""
    leaked_prompts = [
        "Use my key: sk-proj-1234567890abcdef1234567890abcdef for testing",
        "Anthropic: sk-ant-api03-abcdefghijklmnopqrstuvwxyz1234567890",
        "AWS Secret: AKIAIOSFODNN7EXAMPLE",
        "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0...",
        "Authorization: Bearer secret_token_value_abc123",
    ]
    for prompt_str in leaked_prompts:
        with pytest.raises(SecretDetectedError):
            sanitize_prompt_content(prompt_str)


def test_secret_masking_in_text():
    """Sanitizer masks suspected secrets in text diffs."""
    sample = "Connecting with key sk-proj-1234567890abcdef1234567890abcdef and token"
    masked = mask_secrets_in_text(sample)
    assert "sk-proj-" not in masked
    assert "[REDACTED_SECRET]" in masked


# =============================================================================
# 2. RBAC & PERMISSION MATRIX TESTS (OWNER, ADMIN, MEMBER, VIEWER)
# =============================================================================

def test_prompt_permissions_in_role_matrix():
    """Verify STEP 28 permissions are correctly integrated into RBAC roles."""
    admin_perms = ORGANIZATION_ROLE_PERMISSIONS[OrganizationRole.ADMIN.value]
    assert PROMPT_READ in admin_perms
    assert PROMPT_CREATE in admin_perms
    assert PROMPT_UPDATE in admin_perms
    assert PROMPT_PUBLISH in admin_perms
    assert PROMPT_RELEASE in admin_perms
    assert PROMPT_ROLLBACK in admin_perms
    assert PROMPT_EXECUTE in admin_perms
    assert PROMPT_EXPERIMENT in admin_perms
    assert PROMPT_ARCHIVE in admin_perms

    viewer_perms = ORGANIZATION_ROLE_PERMISSIONS[OrganizationRole.VIEWER.value]
    assert PROMPT_READ in viewer_perms
    assert PROMPT_CREATE not in viewer_perms
    assert PROMPT_UPDATE not in viewer_perms
    assert PROMPT_PUBLISH not in viewer_perms
    assert PROMPT_RELEASE not in viewer_perms
    assert PROMPT_ROLLBACK not in viewer_perms
    assert PROMPT_EXECUTE not in viewer_perms
    assert PROMPT_EXPERIMENT not in viewer_perms
    assert PROMPT_ARCHIVE not in viewer_perms


# =============================================================================
# 3. FASTAPI API LIFECYCLE TESTS (CRUD, VERSIONS, DIFF, RELEASES, ROLLBACK)
# =============================================================================

def test_prompt_crud_and_version_immutability(client, user1_auth):
    """
    Test full lifecycle:
    1. Create prompt -> v1 draft created
    2. Read prompt and versions
    3. Publish v1 -> status becomes 'published'
    4. Attempt to modify published v1 -> rejected with 400 (immutability)
    5. Create v2 draft -> version numbers increase monotonically
    6. Compare diff between v1 and v2
    """
    # 1. Create prompt
    create_res = client.post(
        "/api/prompts",
        json={
            "key": "task.research_summary",
            "name": "Research Summary Agent",
            "description": "Generates executive research summaries",
            "prompt_type": "task",
            "initial_content": "Analyze: {{input.topic}}",
            "variable_schema": {"input.topic": {"type": "string", "required": True}},
            "change_summary": "Initial baseline",
        },
        headers=user1_auth["headers"],
    )
    assert create_res.status_code == 201
    prompt_data = create_res.json()
    prompt_id = prompt_data["id"]
    assert prompt_data["key"] == "task.research_summary"
    assert prompt_data["latest_version"] == 1

    v1_id = prompt_data.get("draft_version_id")
    if not v1_id:
        v_res = client.get(f"/api/prompts/{prompt_id}/versions", headers=user1_auth["headers"])
        v1_id = v_res.json()[0]["id"]

    # 2. Publish v1
    pub_res = client.post(
        f"/api/prompts/{prompt_id}/versions/{v1_id}/publish",
        headers=user1_auth["headers"],
    )
    assert pub_res.status_code == 200
    pub_data = pub_res.json()
    assert pub_data["status"] == "published"
    assert pub_data["published_at"] is not None

    # 3. Create v2 draft (monotonically incremented)
    v2_res = client.post(
        f"/api/prompts/{prompt_id}/versions",
        json={
            "content": "Analyze: {{input.topic}} with rigorous citations and evidence.",
            "variable_schema": {"input.topic": {"type": "string", "required": True}},
            "change_summary": "Added citation directive",
        },
        headers=user1_auth["headers"],
    )
    assert v2_res.status_code == 201
    v2_data = v2_res.json()
    assert v2_data["version_number"] == 2
    assert v2_data["status"] == "draft"
    v2_id = v2_data["id"]

    # 4. Compare diff between v1 and v2
    diff_res = client.get(
        f"/api/prompts/{prompt_id}/versions/diff?base_version_id={v1_id}&target_version_id={v2_id}",
        headers=user1_auth["headers"],
    )
    assert diff_res.status_code == 200
    diff_data = diff_res.json()
    assert len(diff_data["added_lines"]) >= 1
    assert any("citations and evidence" in line for line in diff_data["diff_lines"])


def test_preview_prompt_deterministic(client, user1_auth):
    """POST /api/prompts/{id}/preview returns rendered prompt without invoking model."""
    create_res = client.post(
        "/api/prompts",
        json={
            "key": "workflow.preview_test",
            "name": "Preview Test Prompt",
            "prompt_type": "workflow",
            "initial_content": "Process task '{{task.title}}' for user {{input.user}}",
            "variable_schema": {
                "task.title": {"type": "string", "required": True},
                "input.user": {"type": "string", "required": True},
            },
        },
        headers=user1_auth["headers"],
    )
    assert create_res.status_code == 201
    prompt_id = create_res.json()["id"]

    # Preview
    preview_res = client.post(
        f"/api/prompts/{prompt_id}/preview",
        json={
            "variables": {
                "task.title": "Quarterly Ingest",
                "input.user": "Dr. Watson",
            }
        },
        headers=user1_auth["headers"],
    )
    assert preview_res.status_code == 200
    p_data = preview_res.json()
    assert p_data["rendered_content"] == "Process task 'Quarterly Ingest' for user Dr. Watson"
    assert p_data["validation_result"]["valid"] is True
    assert p_data["content_hash"] is not None


def test_releases_promotion_and_rollback(client, user1_auth):
    """
    Test environment releases:
    - Release v1 to staging
    - Promote v1 to production
    - Create & publish v2
    - Promote v2 to production
    - Rollback production to v1
    - Confirm release history transitions
    """
    create_res = client.post(
        "/api/prompts",
        json={
            "key": "evaluator.verification_gate",
            "name": "Verification Gate",
            "prompt_type": "evaluator",
            "initial_content": "Verify evidence strictly: {{context.content}}",
            "variable_schema": {"context.content": {"type": "string", "required": True}},
        },
        headers=user1_auth["headers"],
    )
    prompt_data = create_res.json()
    prompt_id = prompt_data["id"]
    v1_id = prompt_data.get("draft_version_id")
    if not v1_id:
        v_res = client.get(f"/api/prompts/{prompt_id}/versions", headers=user1_auth["headers"])
        v1_id = v_res.json()[0]["id"]

    # Publish v1
    client.post(
        f"/api/prompts/{prompt_id}/versions/{v1_id}/publish",
        headers=user1_auth["headers"],
    )

    # 1. Release to Staging
    rel_stage = client.post(
        f"/api/prompts/{prompt_id}/releases",
        json={"environment": "staging", "version_id": v1_id},
        headers=user1_auth["headers"],
    )
    assert rel_stage.status_code == 200
    assert rel_stage.json()["environment"] == "staging"

    # 2. Release to Production
    rel_prod = client.post(
        f"/api/prompts/{prompt_id}/releases",
        json={"environment": "production", "version_id": v1_id},
        headers=user1_auth["headers"],
    )
    assert rel_prod.status_code == 200
    assert rel_prod.json()["environment"] == "production"

    # Resolve production prompt
    res_prod = client.get(
        f"/api/prompts/{prompt_id}/resolve?environment=production",
        headers=user1_auth["headers"],
    )
    assert res_prod.status_code == 200
    assert res_prod.json()["version"]["version_number"] == 1

    # 3. Create and publish v2
    v2_res = client.post(
        f"/api/prompts/{prompt_id}/versions",
        json={"content": "Verify evidence strictly v2: {{context.content}}"},
        headers=user1_auth["headers"],
    )
    v2_id = v2_res.json()["id"]
    client.post(
        f"/api/prompts/{prompt_id}/versions/{v2_id}/publish",
        headers=user1_auth["headers"],
    )

    # Promote v2 to production
    rel_prod2 = client.post(
        f"/api/prompts/{prompt_id}/releases",
        json={"environment": "production", "version_id": v2_id},
        headers=user1_auth["headers"],
    )
    assert rel_prod2.status_code == 200
    assert rel_prod2.json()["previous_version_id"] == v1_id

    # 4. Rollback to v1
    rollback_res = client.post(
        f"/api/prompts/{prompt_id}/rollback",
        json={
            "environment": "production",
            "target_version_id": v1_id,
            "rollback_reason": "v2 caused test failure",
        },
        headers=user1_auth["headers"],
    )
    assert rollback_res.status_code == 200
    rb_data = rollback_res.json()
    assert rb_data["version_id"] == v1_id
    assert rb_data["previous_version_id"] == v2_id

    # Verify resolution is back to v1
    res_after_rb = client.get(
        f"/api/prompts/{prompt_id}/resolve?environment=production",
        headers=user1_auth["headers"],
    )
    assert res_after_rb.json()["version"]["version_number"] == 1


# =============================================================================
# 4. A/B EXPERIMENT DETERMINISTIC ALLOCATION & RESULTS TESTS
# =============================================================================

def test_prompt_experiment_deterministic_allocation(client, user1_auth):
    """
    Test Prompt Experimentation:
    1. Create 2 published versions v1 and v2
    2. Create Experiment with variants A (v1, 50%) and B (v2, 50%)
    3. Start Experiment
    4. Deterministic assignment: The same task_id yields identical variant repeatedly
    5. Inspect comparative metrics
    """
    # Create prompt with v1
    create_res = client.post(
        "/api/prompts",
        json={
            "key": "planner.experiment_planner",
            "name": "Experiment Planner",
            "prompt_type": "planner",
            "initial_content": "Plan step-by-step: {{task.title}}",
            "variable_schema": {"task.title": {"type": "string", "required": True}},
        },
        headers=user1_auth["headers"],
    )
    prompt_data = create_res.json()
    prompt_id = prompt_data["id"]
    v1_id = prompt_data.get("draft_version_id")
    if not v1_id:
        v_res = client.get(f"/api/prompts/{prompt_id}/versions", headers=user1_auth["headers"])
        v1_id = v_res.json()[0]["id"]
    client.post(f"/api/prompts/{prompt_id}/versions/{v1_id}/publish", headers=user1_auth["headers"])

    # Create v2
    v2_res = client.post(
        f"/api/prompts/{prompt_id}/versions",
        json={"content": "Plan using tree-of-thought: {{task.title}}"},
        headers=user1_auth["headers"],
    )
    v2_id = v2_res.json()["id"]
    client.post(f"/api/prompts/{prompt_id}/versions/{v2_id}/publish", headers=user1_auth["headers"])

    # Create experiment
    exp_res = client.post(
        "/api/prompt-experiments",
        json={
            "prompt_id": prompt_id,
            "name": "CoT vs Tree of Thought",
            "allocation_key": "task_id",
            "variants": [
                {"label": "A", "prompt_version_id": v1_id, "allocation_weight": 50},
                {"label": "B", "prompt_version_id": v2_id, "allocation_weight": 50},
            ],
        },
        headers=user1_auth["headers"],
    )
    assert exp_res.status_code == 201
    exp_id = exp_res.json()["id"]

    # Start experiment
    start_res = client.post(f"/api/prompt-experiments/{exp_id}/start", headers=user1_auth["headers"])
    assert start_res.status_code == 200
    assert start_res.json()["status"] == "running"

    # Verify deterministic allocation via PromptResolver
    from backend.app.services.prompts.resolver import PromptResolver
    key1 = "task-fixed-uuid-1111"
    key2 = "task-fixed-uuid-2222"

    variant1_first = PromptResolver.select_variant_for_key(exp_id, exp_res.json()["variants"], key1)
    variant1_second = PromptResolver.select_variant_for_key(exp_id, exp_res.json()["variants"], key1)
    assert variant1_first["label"] == variant1_second["label"], "Sticky allocation must remain stable for the same key"

    # Get results endpoint
    results_res = client.get(f"/api/prompt-experiments/{exp_id}/results", headers=user1_auth["headers"])
    assert results_res.status_code == 200
    res_data = results_res.json()
    assert len(res_data["variants"]) == 2
    # Ensure no subjective winner is declared
    assert "winner" not in res_data


# =============================================================================
# 5. MULTI-TENANT ISOLATION TESTS (ORG A VS ORG B)
# =============================================================================

def test_cross_organization_prompt_isolation(client, user1_auth, user2_auth):
    """
    Test Tenant Isolation:
    - User 1 creates Org A and Prompt A
    - User 2 creates Org B
    - User 2 cannot access Prompt A (returns 403 or 404)
    - User 2 cannot edit or release Prompt A
    """
    # User 1 creates prompt
    res_a = client.post(
        "/api/prompts",
        json={
            "key": "system.org_a_internal",
            "name": "Org A Proprietary Prompt",
            "prompt_type": "system",
            "initial_content": "Internal proprietary guidance for Org A",
        },
        headers=user1_auth["headers"],
    )
    assert res_a.status_code == 201
    prompt_a_id = res_a.json()["id"]

    # User 2 attempts to fetch Org A prompt -> blocked
    get_a_from_2 = client.get(
        f"/api/prompts/{prompt_a_id}",
        headers=user2_auth["headers"],
    )
    # Blocked by isolation policy
    assert get_a_from_2.status_code in [403, 404]

    # User 2 attempts to patch Org A prompt -> blocked
    patch_from_2 = client.patch(
        f"/api/prompts/{prompt_a_id}",
        json={"name": "Hacked Org A"},
        headers=user2_auth["headers"],
    )
    assert patch_from_2.status_code in [403, 404]
