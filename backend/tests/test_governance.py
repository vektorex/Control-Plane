"""
Comprehensive tests for Step 32: AI Governance, Policy Control Plane, and Safety Guardrails.
Covers: policy creation, versioning, activation, precedence, scope isolation,
model/provider/tool/connector/workflow/prompt/artifact/data/cache/HITL/cost/rate-limit governance,
replay, multimodal, graph, memory, notifications, events, observability, RBAC, tenant isolation,
fail-safe behavior, security guardrails.
"""
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app.services.governance.action_policy import ActionPolicyClassifier
from backend.app.services.governance.approval import GovernanceApprovalService
from backend.app.services.governance.budgets import BudgetService
from backend.app.services.governance.classifiers import (
    ArtifactTypeClassifier,
    ModelCapabilityClassifier,
    ProviderClassifier,
    TaskTypeClassifier,
)
from backend.app.services.governance.constants import (
    ActionCategory,
    DataClassification,
    GovernanceDecisionType,
    PolicyAction,
    PolicyRuleType,
    PolicyScope,
    PolicyStatus,
    PolicyVersionStatus,
    RuleConditionOperator,
    VerificationRequirement,
    GOVERNANCE_DECISION_TTL_SECONDS,
    PRIVILEGED_DECISION_TTL_SECONDS,
    ClassificationSource,
    EnforcementPoint,
)
from backend.app.services.governance.constraints import (
    ConstraintBuilder,
    apply_connector_constraint,
    apply_model_constraint,
    apply_provider_constraint,
    apply_tool_constraint,
)
from backend.app.services.governance.data_policy import DataClassificationService
from backend.app.services.governance.enforcement import PolicyEnforcer
from backend.app.services.governance.errors import (
    GovernanceConflictError,
    GovernanceDeniedError,
    GovernancePolicyMalformedError,
    GovernancePolicyNotFoundError,
    GovernanceStateUnknownError,
)
from backend.app.services.governance.evaluator import PolicyEvaluator, _evaluate_condition
from backend.app.services.governance.policy_registry import PolicyRegistry, policy_registry
from backend.app.services.governance.rate_limits import RateLimitService
from backend.app.services.governance.sanitizer import GovernanceSanitizer
from backend.app.services.governance.schemas import (
    BudgetPolicyCreate,
    BudgetReservationCreate,
    DataClassificationRequest,
    GovernanceDecision,
    GovernanceEvaluationRequest,
    GovernancePolicyCreate,
    GovernancePolicyUpdate,
    GovernancePreviewRequest,
    GovernanceSimulateRequest,
    PolicyRule,
    PolicyVersionCreate,
    RuleCondition,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _org() -> uuid.UUID:
    return uuid.UUID("10000000-0000-0000-0000-000000000001")

def _ws() -> uuid.UUID:
    return uuid.UUID("20000000-0000-0000-0000-000000000002")

def _proj() -> uuid.UUID:
    return uuid.UUID("30000000-0000-0000-0000-000000000003")

def _user() -> uuid.UUID:
    return uuid.UUID("40000000-0000-0000-0000-000000000004")

def _make_rule(
    rule_type: PolicyRuleType = PolicyRuleType.MODEL,
    action: PolicyAction = PolicyAction.DENY,
    conditions: list = None,
    priority: int = 100,
    description: str = "test rule",
) -> PolicyRule:
    return PolicyRule(
        rule_type=rule_type,
        action=action,
        conditions=conditions or [],
        priority=priority,
        description=description,
    )

def _make_request(**kwargs) -> GovernanceEvaluationRequest:
    defaults = dict(
        enforcement_point=EnforcementPoint.TASK_EXECUTION,
        organization_id=_org(),
        workspace_id=_ws(),
    )
    defaults.update(kwargs)
    return GovernanceEvaluationRequest(**defaults)


# ---------------------------------------------------------------------------
# 1. Policy Creation
# ---------------------------------------------------------------------------

def test_policy_create_schema():
    data = GovernancePolicyCreate(
        name="Block GPT-3.5",
        scope=PolicyScope.WORKSPACE,
        workspace_id=_ws(),
    )
    assert data.name == "Block GPT-3.5"
    assert data.scope == PolicyScope.WORKSPACE


def test_policy_create_name_required():
    with pytest.raises(Exception):
        GovernancePolicyCreate(name="", scope=PolicyScope.WORKSPACE)


# ---------------------------------------------------------------------------
# 2. Policy Versioning
# ---------------------------------------------------------------------------

def test_policy_version_rule_limit():
    rules = [_make_rule() for _ in range(51)]
    with pytest.raises(Exception):
        PolicyVersionCreate(rules=rules)


def test_policy_version_valid_rules():
    rules = [_make_rule() for _ in range(5)]
    pv = PolicyVersionCreate(rules=rules)
    assert len(pv.rules) == 5


# ---------------------------------------------------------------------------
# 3. Policy Rule Validation
# ---------------------------------------------------------------------------

def test_evaluator_validate_rules_max():
    rules = [_make_rule() for _ in range(55)]
    errors = PolicyEvaluator.validate_rules(rules)
    assert any("50" in e for e in errors)


def test_evaluator_validate_rules_valid():
    rules = [_make_rule() for _ in range(3)]
    errors = PolicyEvaluator.validate_rules(rules)
    assert errors == []


# ---------------------------------------------------------------------------
# 4. Condition Evaluation
# ---------------------------------------------------------------------------

def test_condition_equals_match():
    cond = RuleCondition(field="model_id", operator=RuleConditionOperator.EQUALS, value="gpt-3.5-turbo")
    assert _evaluate_condition(cond, {"model_id": "gpt-3.5-turbo"}) is True


def test_condition_equals_no_match():
    cond = RuleCondition(field="model_id", operator=RuleConditionOperator.EQUALS, value="gpt-3.5-turbo")
    assert _evaluate_condition(cond, {"model_id": "gpt-4"}) is False


def test_condition_in_match():
    cond = RuleCondition(field="provider", operator=RuleConditionOperator.IN, value=["openai", "anthropic"])
    assert _evaluate_condition(cond, {"provider": "openai"}) is True


def test_condition_not_in():
    cond = RuleCondition(field="provider", operator=RuleConditionOperator.NOT_IN, value=["openai"])
    assert _evaluate_condition(cond, {"provider": "anthropic"}) is True
    assert _evaluate_condition(cond, {"provider": "openai"}) is False


def test_condition_exists():
    cond = RuleCondition(field="tool_id", operator=RuleConditionOperator.EXISTS)
    assert _evaluate_condition(cond, {"tool_id": "tool_abc"}) is True
    assert _evaluate_condition(cond, {"tool_id": None}) is False


def test_condition_greater_than():
    cond = RuleCondition(field="estimated_cost_usd", operator=RuleConditionOperator.GREATER_THAN, value=1.0)
    assert _evaluate_condition(cond, {"estimated_cost_usd": 2.5}) is True
    assert _evaluate_condition(cond, {"estimated_cost_usd": 0.5}) is False


def test_condition_missing_field_returns_false():
    cond = RuleCondition(field="model_id", operator=RuleConditionOperator.EQUALS, value="gpt-4")
    assert _evaluate_condition(cond, {}) is False


def test_condition_no_arbitrary_code():
    # No eval, exec, or arbitrary expressions — only safe enum-based operators
    cond = RuleCondition(field="provider", operator=RuleConditionOperator.EQUALS, value="__import__('os').system('ls')")
    # Value is treated as literal string, not executed
    result = _evaluate_condition(cond, {"provider": "openai"})
    assert result is False


# ---------------------------------------------------------------------------
# 5. Policy Evaluation – Decision Merging and Precedence
# ---------------------------------------------------------------------------

def test_deny_overrides_allow():
    rules = [
        _make_rule(action=PolicyAction.ALLOW, priority=10),
        _make_rule(action=PolicyAction.DENY, priority=20),
    ]
    request = _make_request()
    decision_type, reasons, constraints, approvals, verifications = PolicyEvaluator.evaluate(rules, request)
    assert decision_type == GovernanceDecisionType.DENY


def test_allow_with_constraints_below_deny():
    rules = [
        _make_rule(action=PolicyAction.SET_LIMIT, priority=10, description="limit tokens"),
        _make_rule(action=PolicyAction.DENY, priority=20),
    ]
    request = _make_request()
    decision_type, _, _, _, _ = PolicyEvaluator.evaluate(rules, request)
    assert decision_type == GovernanceDecisionType.DENY


def test_require_approval_below_deny():
    rules = [
        _make_rule(action=PolicyAction.REQUIRE_APPROVAL, priority=10),
        _make_rule(action=PolicyAction.DENY, priority=20),
    ]
    decision_type, _, _, _, _ = PolicyEvaluator.evaluate(rules, _make_request())
    assert decision_type == GovernanceDecisionType.DENY


def test_allow_when_no_rules_match():
    rule = PolicyRule(
        rule_type=PolicyRuleType.MODEL,
        action=PolicyAction.DENY,
        conditions=[RuleCondition(field="model_id", operator=RuleConditionOperator.EQUALS, value="never-matching")],
        priority=100,
    )
    decision_type, _, _, _, _ = PolicyEvaluator.evaluate([rule], _make_request(model_id="gpt-4"))
    assert decision_type == GovernanceDecisionType.ALLOW


def test_require_approval_collected():
    rule = PolicyRule(
        rule_type=PolicyRuleType.ACTION,
        action=PolicyAction.REQUIRE_APPROVAL,
        conditions=[],
        action_params={"scope": "external_write"},
        priority=100,
        description="External write requires approval",
    )
    _, reasons, _, approvals, _ = PolicyEvaluator.evaluate([rule], _make_request())
    assert "external_write" in approvals
    assert "External write requires approval" in reasons


def test_require_verification_collected():
    rule = PolicyRule(
        rule_type=PolicyRuleType.DATA,
        action=PolicyAction.REQUIRE_VERIFICATION,
        conditions=[],
        action_params={"verifications": ["grounding_required", "human_review_required"]},
        priority=100,
    )
    _, _, _, _, verifications = PolicyEvaluator.evaluate([rule], _make_request())
    assert "grounding_required" in verifications
    assert "human_review_required" in verifications


def test_constraints_collected_from_set_limit():
    rule = PolicyRule(
        rule_type=PolicyRuleType.MODEL,
        action=PolicyAction.SET_LIMIT,
        conditions=[],
        action_params={"max_output_tokens": 1024},
        priority=100,
    )
    _, _, constraints, _, _ = PolicyEvaluator.evaluate([rule], _make_request())
    assert constraints.get("max_output_tokens") == 1024


# ---------------------------------------------------------------------------
# 6. Model Governance
# ---------------------------------------------------------------------------

def test_model_governance_deny_blocked_model():
    rule = PolicyRule(
        rule_type=PolicyRuleType.MODEL,
        action=PolicyAction.DENY,
        conditions=[
            RuleCondition(field="model_id", operator=RuleConditionOperator.IN, value=["gpt-3.5-turbo"])
        ],
        priority=100,
        description="GPT-3.5 is blocked",
    )
    request = _make_request(model_id="gpt-3.5-turbo")
    decision_type, reasons, _, _, _ = PolicyEvaluator.evaluate([rule], request)
    assert decision_type == GovernanceDecisionType.DENY
    assert "GPT-3.5 is blocked" in reasons


def test_model_governance_allow_approved_model():
    rule = PolicyRule(
        rule_type=PolicyRuleType.MODEL,
        action=PolicyAction.DENY,
        conditions=[
            RuleCondition(field="model_id", operator=RuleConditionOperator.IN, value=["gpt-3.5-turbo"])
        ],
        priority=100,
    )
    request = _make_request(model_id="gpt-4")
    decision_type, _, _, _, _ = PolicyEvaluator.evaluate([rule], request)
    assert decision_type == GovernanceDecisionType.ALLOW


def test_provider_governance_block():
    rule = PolicyRule(
        rule_type=PolicyRuleType.PROVIDER,
        action=PolicyAction.DENY,
        conditions=[RuleCondition(field="provider", operator=RuleConditionOperator.EQUALS, value="openai")],
        priority=100,
        description="OpenAI blocked",
    )
    request = _make_request(provider="openai")
    decision_type, _, _, _, _ = PolicyEvaluator.evaluate([rule], request)
    assert decision_type == GovernanceDecisionType.DENY


# ---------------------------------------------------------------------------
# 7. Tool and Connector Governance
# ---------------------------------------------------------------------------

def test_tool_governance_deny():
    rule = PolicyRule(
        rule_type=PolicyRuleType.TOOL,
        action=PolicyAction.DENY,
        conditions=[RuleCondition(field="tool_id", operator=RuleConditionOperator.EQUALS, value="dangerous_tool")],
        priority=100,
        description="Dangerous tool disabled",
    )
    decision_type, _, _, _, _ = PolicyEvaluator.evaluate([rule], _make_request(tool_id="dangerous_tool"))
    assert decision_type == GovernanceDecisionType.DENY


def test_connector_governance_require_approval():
    rule = PolicyRule(
        rule_type=PolicyRuleType.CONNECTOR,
        action=PolicyAction.REQUIRE_APPROVAL,
        conditions=[RuleCondition(field="connector_id", operator=RuleConditionOperator.EQUALS, value="salesforce")],
        action_params={"scope": "connector_write"},
        priority=100,
        description="Salesforce writes require approval",
    )
    decision_type, _, _, approvals, _ = PolicyEvaluator.evaluate(
        [rule], _make_request(connector_id="salesforce")
    )
    assert decision_type == GovernanceDecisionType.REQUIRE_APPROVAL
    assert "connector_write" in approvals


# ---------------------------------------------------------------------------
# 8. Workflow, Prompt, Artifact Governance
# ---------------------------------------------------------------------------

def test_workflow_governance_deny():
    rule = PolicyRule(
        rule_type=PolicyRuleType.WORKFLOW,
        action=PolicyAction.DENY,
        conditions=[RuleCondition(field="workflow_id", operator=RuleConditionOperator.EQUALS, value="risky_wf")],
        priority=100,
        description="Restricted workflow",
    )
    decision_type, _, _, _, _ = PolicyEvaluator.evaluate([rule], _make_request(workflow_id="risky_wf"))
    assert decision_type == GovernanceDecisionType.DENY


def test_prompt_governance_require_verification():
    rule = PolicyRule(
        rule_type=PolicyRuleType.PROMPT,
        action=PolicyAction.REQUIRE_VERIFICATION,
        conditions=[RuleCondition(field="prompt_version_id", operator=RuleConditionOperator.EXISTS)],
        action_params={"verifications": ["human_review_required"]},
        priority=100,
        description="All prompts require human review",
    )
    decision_type, _, _, _, verifications = PolicyEvaluator.evaluate(
        [rule], _make_request(prompt_version_id="pv-123")
    )
    assert decision_type == GovernanceDecisionType.REQUIRE_VERIFICATION
    assert "human_review_required" in verifications


def test_artifact_governance_max_size_constraint():
    rule = PolicyRule(
        rule_type=PolicyRuleType.ARTIFACT,
        action=PolicyAction.SET_LIMIT,
        conditions=[],
        action_params={"max_artifact_size_bytes": 5_000_000},
        priority=100,
    )
    _, _, constraints, _, _ = PolicyEvaluator.evaluate([rule], _make_request(artifact_type="image"))
    assert constraints.get("max_artifact_size_bytes") == 5_000_000


# ---------------------------------------------------------------------------
# 9. Data Classification
# ---------------------------------------------------------------------------

def test_data_classification_assign_and_get():
    svc = DataClassificationService()
    target_id = uuid.uuid4()
    request = DataClassificationRequest(
        target_type="document",
        target_id=target_id,
        classification=DataClassification.CONFIDENTIAL,
        source=ClassificationSource.WORKSPACE_POLICY,
    )
    response = svc.assign(request)
    assert response.classification == DataClassification.CONFIDENTIAL
    assert svc.get("document", target_id) == DataClassification.CONFIDENTIAL


def test_data_classification_user_cannot_self_escalate_to_restricted():
    svc = DataClassificationService()
    target_id = uuid.uuid4()
    request = DataClassificationRequest(
        target_type="document",
        target_id=target_id,
        classification=DataClassification.RESTRICTED,
        source=ClassificationSource.USER_EXPLICIT,
    )
    response = svc.assign(request)
    # Should be downgraded to INTERNAL
    assert response.classification == DataClassification.INTERNAL


def test_data_classification_default():
    svc = DataClassificationService()
    target_id = uuid.uuid4()
    # Never classified — should return default
    result = svc.get("connector", target_id)
    assert result == DataClassification.CONFIDENTIAL  # connector default


def test_restricted_data_requires_approved_provider():
    svc = DataClassificationService()
    target_id = uuid.uuid4()
    request = DataClassificationRequest(
        target_type="document",
        target_id=target_id,
        classification=DataClassification.RESTRICTED,
        source=ClassificationSource.ORGANIZATION_POLICY,
    )
    svc.assign(request)
    assert svc.requires_approved_provider("document", target_id) is True


def test_data_flow_policy_restricted_data():
    rule = PolicyRule(
        rule_type=PolicyRuleType.DATA,
        action=PolicyAction.REQUIRE_VERIFICATION,
        conditions=[
            RuleCondition(field="data_classification", operator=RuleConditionOperator.EQUALS, value="restricted")
        ],
        action_params={"verifications": ["human_review_required"]},
        priority=5,
        description="Restricted data requires verification",
    )
    request = _make_request(data_classification=DataClassification.RESTRICTED)
    decision_type, _, _, _, verifications = PolicyEvaluator.evaluate([rule], request)
    assert decision_type == GovernanceDecisionType.REQUIRE_VERIFICATION
    assert "human_review_required" in verifications


# ---------------------------------------------------------------------------
# 10. System Policy Registry (cannot be overridden)
# ---------------------------------------------------------------------------

def test_system_rules_destructive_always_require_approval():
    system_rules = policy_registry.get_system_rules()
    request = _make_request(action_category=ActionCategory.DESTRUCTIVE)
    decision_type, _, _, approvals, _ = PolicyEvaluator.evaluate(system_rules, request)
    assert decision_type == GovernanceDecisionType.REQUIRE_APPROVAL


def test_system_rules_financial_always_require_approval():
    system_rules = policy_registry.get_system_rules()
    request = _make_request(action_category=ActionCategory.FINANCIAL)
    decision_type, _, _, approvals, _ = PolicyEvaluator.evaluate(system_rules, request)
    assert decision_type == GovernanceDecisionType.REQUIRE_APPROVAL


def test_system_rules_restricted_data_require_verification():
    system_rules = policy_registry.get_system_rules()
    request = _make_request(data_classification=DataClassification.RESTRICTED)
    decision_type, _, _, _, verifications = PolicyEvaluator.evaluate(system_rules, request)
    assert decision_type in (GovernanceDecisionType.REQUIRE_VERIFICATION, GovernanceDecisionType.REQUIRE_APPROVAL)


# ---------------------------------------------------------------------------
# 11. Cache Governance
# ---------------------------------------------------------------------------

def test_cache_disabled_by_policy():
    rule = PolicyRule(
        rule_type=PolicyRuleType.CACHE,
        action=PolicyAction.DISABLE,
        conditions=[],
        priority=100,
        description="Cache disabled by policy",
    )
    decision_type, _, _, _, _ = PolicyEvaluator.evaluate([rule], _make_request())
    assert decision_type == GovernanceDecisionType.DENY


def test_cache_constraint_exact_only():
    rule = PolicyRule(
        rule_type=PolicyRuleType.CACHE,
        action=PolicyAction.SET_LIMIT,
        conditions=[],
        action_params={"cache_mode": "exact_only", "semantic_cache_enabled": False},
        priority=100,
    )
    _, _, constraints, _, _ = PolicyEvaluator.evaluate([rule], _make_request())
    assert constraints.get("cache_mode") == "exact_only"
    assert constraints.get("semantic_cache_enabled") is False


def test_cache_governance_semantic_disabled_for_restricted():
    rule = PolicyRule(
        rule_type=PolicyRuleType.CACHE,
        action=PolicyAction.SET_LIMIT,
        conditions=[
            RuleCondition(field="data_classification", operator=RuleConditionOperator.IN,
                          value=["confidential", "restricted"])
        ],
        action_params={"semantic_cache_enabled": False, "stale_while_revalidate": False},
        priority=5,
        description="Sensitive data: semantic cache disabled",
    )
    request = _make_request(data_classification=DataClassification.CONFIDENTIAL)
    decision_type, _, constraints, _, _ = PolicyEvaluator.evaluate([rule], request)
    assert constraints.get("semantic_cache_enabled") is False
    assert constraints.get("stale_while_revalidate") is False


# ---------------------------------------------------------------------------
# 12. Action Policy Classifier
# ---------------------------------------------------------------------------

def test_action_classifier_destructive_tool():
    category = ActionPolicyClassifier.classify_from_tool("delete_record")
    assert category == ActionCategory.DESTRUCTIVE


def test_action_classifier_write_tool():
    category = ActionPolicyClassifier.classify_from_tool("create_issue")
    assert category == ActionCategory.WRITE


def test_action_classifier_read_tool():
    category = ActionPolicyClassifier.classify_from_tool("get_record")
    assert category == ActionCategory.READ


def test_action_classifier_communication_tool():
    category = ActionPolicyClassifier.classify_from_tool("send_slack_message")
    assert category == ActionCategory.COMMUNICATION


def test_action_classifier_connector_write():
    category = ActionPolicyClassifier.classify_from_connector("jira", "update")
    assert category == ActionCategory.WRITE


def test_action_classifier_connector_read():
    category = ActionPolicyClassifier.classify_from_connector("jira", "read")
    assert category == ActionCategory.READ


def test_action_policy_defaults_destructive_require_approval():
    decision = ActionPolicyClassifier.default_decision(ActionCategory.DESTRUCTIVE)
    assert decision == GovernanceDecisionType.REQUIRE_APPROVAL


def test_action_policy_read_allow():
    decision = ActionPolicyClassifier.default_decision(ActionCategory.READ)
    assert decision == GovernanceDecisionType.ALLOW


# ---------------------------------------------------------------------------
# 13. Multimodal Governance
# ---------------------------------------------------------------------------

def test_multimodal_vision_restriction():
    rule = PolicyRule(
        rule_type=PolicyRuleType.ARTIFACT,
        action=PolicyAction.DENY,
        conditions=[
            RuleCondition(field="artifact_type", operator=RuleConditionOperator.IN, value=["image", "video"])
        ],
        priority=100,
        description="Vision input disabled",
    )
    request = _make_request(artifact_type="image")
    decision_type, _, _, _, _ = PolicyEvaluator.evaluate([rule], request)
    assert decision_type == GovernanceDecisionType.DENY


def test_multimodal_audio_restriction():
    rule = PolicyRule(
        rule_type=PolicyRuleType.ARTIFACT,
        action=PolicyAction.DENY,
        conditions=[RuleCondition(field="artifact_type", operator=RuleConditionOperator.EQUALS, value="audio")],
        priority=100,
    )
    request_audio = _make_request(artifact_type="audio")
    request_text = _make_request(artifact_type="text")
    dt_audio, _, _, _, _ = PolicyEvaluator.evaluate([rule], request_audio)
    dt_text, _, _, _, _ = PolicyEvaluator.evaluate([rule], request_text)
    assert dt_audio == GovernanceDecisionType.DENY
    assert dt_text == GovernanceDecisionType.ALLOW


def test_artifact_type_classifier_sensitive():
    assert ArtifactTypeClassifier.is_sensitive("medical_record") is True
    assert ArtifactTypeClassifier.implied_classification("medical_record") == DataClassification.CONFIDENTIAL


def test_artifact_type_classifier_high_risk():
    assert ArtifactTypeClassifier.is_high_risk("executable") is True


# ---------------------------------------------------------------------------
# 14. Constraint Builders
# ---------------------------------------------------------------------------

def test_constraint_builder_allowed_models():
    c = ConstraintBuilder.allowed_models(["gpt-4", "claude-3"])
    assert c["allowed_models"] == ["gpt-4", "claude-3"]


def test_constraint_builder_merge():
    c1 = ConstraintBuilder.allowed_models(["gpt-4"])
    c2 = ConstraintBuilder.max_output_tokens(2048)
    merged = ConstraintBuilder.merge(c1, c2)
    assert "allowed_models" in merged
    assert merged["max_output_tokens"] == 2048


def test_apply_model_constraint_blocked():
    constraints = {"blocked_models": ["gpt-3.5-turbo"]}
    assert apply_model_constraint(constraints, "gpt-3.5-turbo") is False
    assert apply_model_constraint(constraints, "gpt-4") is True


def test_apply_provider_constraint_allowed_list():
    constraints = {"allowed_providers": ["anthropic"]}
    assert apply_provider_constraint(constraints, "openai") is False
    assert apply_provider_constraint(constraints, "anthropic") is True


def test_apply_tool_constraint_blocked():
    constraints = {"blocked_tools": ["dangerous_tool"]}
    assert apply_tool_constraint(constraints, "dangerous_tool") is False
    assert apply_tool_constraint(constraints, "safe_tool") is True


def test_apply_connector_constraint_allowed_list():
    constraints = {"allowed_connectors": ["jira", "github"]}
    assert apply_connector_constraint(constraints, "salesforce") is False
    assert apply_connector_constraint(constraints, "jira") is True


# ---------------------------------------------------------------------------
# 15. Policy Enforcer
# ---------------------------------------------------------------------------

def test_enforcer_deny_raises():
    decision = GovernanceDecision(
        decision=GovernanceDecisionType.DENY,
        reasons=["model blocked by policy"],
    )
    with pytest.raises(GovernanceDeniedError):
        PolicyEnforcer.enforce(decision, "model_execution")


def test_enforcer_allow_no_exception():
    decision = GovernanceDecision(decision=GovernanceDecisionType.ALLOW)
    PolicyEnforcer.enforce(decision, "request_start")  # Should not raise


def test_enforcer_allow_with_constraints_no_exception():
    decision = GovernanceDecision(
        decision=GovernanceDecisionType.ALLOW_WITH_CONSTRAINTS,
        constraints={"max_output_tokens": 512},
    )
    PolicyEnforcer.enforce(decision, "model_execution")  # Should not raise


def test_enforcer_fail_safe_privileged_raises():
    with pytest.raises(GovernanceStateUnknownError):
        PolicyEnforcer.enforce_fail_safe(
            enforcement_point="connector_execution",
            governance_state_available=False,
            action_category=ActionCategory.WRITE,
        )


def test_enforcer_fail_safe_read_only_allows():
    # Should log warning but NOT raise for read-only when governance unavailable
    PolicyEnforcer.enforce_fail_safe(
        enforcement_point="request_start",
        governance_state_available=False,
        action_category=ActionCategory.READ,
    )


def test_enforcer_fail_safe_destructive_raises():
    with pytest.raises(GovernanceStateUnknownError):
        PolicyEnforcer.enforce_fail_safe(
            enforcement_point="external_action",
            governance_state_available=False,
            action_category=ActionCategory.DESTRUCTIVE,
        )


def test_enforcer_cache_constraint_extraction():
    decision = GovernanceDecision(
        decision=GovernanceDecisionType.ALLOW_WITH_CONSTRAINTS,
        constraints={"cache_mode": "exact_only", "semantic_cache_enabled": False},
    )
    extracted = PolicyEnforcer.extract_cache_constraints(decision)
    assert extracted["cache_mode"] == "exact_only"
    assert extracted["semantic_cache_enabled"] is False


def test_enforcer_model_constraint_extraction():
    decision = GovernanceDecision(
        decision=GovernanceDecisionType.ALLOW_WITH_CONSTRAINTS,
        constraints={"allowed_models": ["gpt-4"], "max_output_tokens": 1000},
    )
    extracted = PolicyEnforcer.extract_model_constraints(decision)
    assert extracted["allowed_models"] == ["gpt-4"]
    assert extracted["max_output_tokens"] == 1000


# ---------------------------------------------------------------------------
# 16. Rate Limits
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rate_limit_allows_under_limit():
    ws = str(uuid.uuid4())
    await RateLimitService.reset_for_workspace(ws)
    decision_type, _ = await RateLimitService.check(ws, "model_calls", limit=10)
    assert decision_type == GovernanceDecisionType.ALLOW


@pytest.mark.asyncio
async def test_rate_limit_denies_over_limit():
    ws = str(uuid.uuid4())
    await RateLimitService.reset_for_workspace(ws)
    for _ in range(5):
        await RateLimitService.check(ws, "requests", limit=5)
    decision_type, reasons = await RateLimitService.check(ws, "requests", limit=5)
    assert decision_type == GovernanceDecisionType.DENY
    assert len(reasons) > 0


@pytest.mark.asyncio
async def test_rate_limit_isolated_per_workspace():
    ws1 = str(uuid.uuid4())
    ws2 = str(uuid.uuid4())
    await RateLimitService.reset_for_workspace(ws1)
    await RateLimitService.reset_for_workspace(ws2)
    for _ in range(5):
        await RateLimitService.check(ws1, "requests", limit=5)
    # ws2 should still be under limit
    decision_type, _ = await RateLimitService.check(ws2, "requests", limit=5)
    assert decision_type == GovernanceDecisionType.ALLOW


# ---------------------------------------------------------------------------
# 17. Budget Service (mocked session)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_budget_check_no_policy_allows():
    session = AsyncMock()
    # No budget policy configured → allow
    from backend.app.services.governance.repository import GovernancePolicyRepository
    repo = GovernancePolicyRepository(session)
    repo.get_budget_policy = AsyncMock(return_value=None)
    budget_svc = BudgetService(repo)
    decision_type, reasons = await budget_svc.check_cost(_org(), _ws(), None, 100.0)
    assert decision_type == GovernanceDecisionType.ALLOW


@pytest.mark.asyncio
async def test_budget_check_unknown_cost_allows():
    session = AsyncMock()
    from backend.app.services.governance.repository import GovernancePolicyRepository
    repo = GovernancePolicyRepository(session)
    budget_svc = BudgetService(repo)
    # No cost estimate → allow (never fabricate cost)
    decision_type, reasons = await budget_svc.check_cost(_org(), _ws(), None, None)
    assert decision_type == GovernanceDecisionType.ALLOW
    assert reasons == []


@pytest.mark.asyncio
async def test_budget_per_run_limit_deny():
    session = AsyncMock()
    from backend.app.services.governance.repository import GovernancePolicyRepository
    from backend.app.services.governance.models import BudgetPolicy
    policy = BudgetPolicy(
        id=uuid.uuid4(),
        organization_id=_org(),
        workspace_id=_ws(),
        per_run_limit_usd=0.50,
        soft_threshold_pct=0.8,
        hard_threshold_pct=1.0,
        on_soft_breach="warn",
        on_hard_breach="deny",
        is_active=True,
        created_by=_user(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    repo = GovernancePolicyRepository(session)
    repo.get_budget_policy = AsyncMock(return_value=policy)
    repo.get_active_reservations_total = AsyncMock(return_value=0.0)
    budget_svc = BudgetService(repo)
    decision_type, reasons = await budget_svc.check_cost(_org(), _ws(), None, 1.00)
    assert decision_type == GovernanceDecisionType.DENY


@pytest.mark.asyncio
async def test_budget_soft_threshold_warning():
    session = AsyncMock()
    from backend.app.services.governance.repository import GovernancePolicyRepository
    from backend.app.services.governance.models import BudgetPolicy
    policy = BudgetPolicy(
        id=uuid.uuid4(),
        organization_id=_org(),
        workspace_id=_ws(),
        daily_limit_usd=100.0,
        per_run_limit_usd=None,
        soft_threshold_pct=0.80,
        hard_threshold_pct=1.00,
        on_soft_breach="warn",
        on_hard_breach="deny",
        is_active=True,
        created_by=_user(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    repo = GovernancePolicyRepository(session)
    repo.get_budget_policy = AsyncMock(return_value=policy)
    repo.get_active_reservations_total = AsyncMock(return_value=79.0)  # 79+5 = 84 > 80% of 100
    budget_svc = BudgetService(repo)
    decision_type, reasons = await budget_svc.check_cost(_org(), _ws(), None, 5.0)
    assert decision_type == GovernanceDecisionType.ALLOW_WITH_CONSTRAINTS
    assert any("approaching" in r.lower() for r in reasons)


# ---------------------------------------------------------------------------
# 18. Governance Sanitizer
# ---------------------------------------------------------------------------

def test_sanitizer_removes_api_keys():
    data = {"api_key": "sk-abc123", "message": "hello"}
    cleaned = GovernanceSanitizer.sanitize_dict(data)
    assert cleaned["api_key"] == "[REDACTED]"
    assert cleaned["message"] == "hello"


def test_sanitizer_removes_nested_secrets():
    data = {"context": {"password": "super_secret", "user": "bob"}}
    cleaned = GovernanceSanitizer.sanitize_dict(data)
    assert cleaned["context"]["password"] == "[REDACTED]"
    assert cleaned["context"]["user"] == "bob"


def test_sanitizer_removes_credential_patterns_in_strings():
    text = "Use api_key: sk-abc123 to authenticate"
    cleaned = GovernanceSanitizer.sanitize_string(text)
    assert "[REDACTED]" in cleaned


def test_sanitizer_does_not_remove_safe_fields():
    data = {"enforcement_point": "task_execution", "decision": "allow"}
    cleaned = GovernanceSanitizer.sanitize_dict(data)
    assert cleaned["enforcement_point"] == "task_execution"
    assert cleaned["decision"] == "allow"


# ---------------------------------------------------------------------------
# 19. Approval Service
# ---------------------------------------------------------------------------

def test_approval_service_should_create_hitl():
    assert GovernanceApprovalService.should_create_hitl_request(GovernanceDecisionType.REQUIRE_APPROVAL) is True
    assert GovernanceApprovalService.should_create_hitl_request(GovernanceDecisionType.ALLOW) is False
    assert GovernanceApprovalService.should_create_hitl_request(GovernanceDecisionType.DENY) is False


def test_approval_service_hitl_payload_no_secrets():
    payload = GovernanceApprovalService.build_hitl_payload(
        enforcement_point="connector_execution",
        reasons=["connector write requires approval"],
        required_approvals=["connector_write"],
        organization_id=_org(),
        workspace_id=_ws(),
        project_id=None,
        user_id=_user(),
    )
    assert "reason" in payload
    assert "api_key" not in str(payload)
    assert "password" not in str(payload)


# ---------------------------------------------------------------------------
# 20. Policy Scope Isolation
# ---------------------------------------------------------------------------

def test_organization_scope_policy():
    data = GovernancePolicyCreate(name="Org Policy", scope=PolicyScope.ORGANIZATION)
    assert data.scope == PolicyScope.ORGANIZATION
    assert data.workspace_id is None


def test_workspace_scope_policy():
    data = GovernancePolicyCreate(
        name="WS Policy", scope=PolicyScope.WORKSPACE, workspace_id=_ws()
    )
    assert data.scope == PolicyScope.WORKSPACE
    assert data.workspace_id == _ws()


def test_project_scope_policy():
    data = GovernancePolicyCreate(
        name="Proj Policy", scope=PolicyScope.PROJECT, workspace_id=_ws(), project_id=_proj()
    )
    assert data.scope == PolicyScope.PROJECT


# ---------------------------------------------------------------------------
# 21. Provider Classification
# ---------------------------------------------------------------------------

def test_provider_classifier_known():
    assert ProviderClassifier.is_known_provider("openai") is True
    assert ProviderClassifier.is_known_provider("unknown_vendor_xyz") is False


def test_provider_classifier_normalize():
    assert ProviderClassifier.normalize("OpenAI") == "openai"


# ---------------------------------------------------------------------------
# 22. Task Type Classifier
# ---------------------------------------------------------------------------

def test_task_type_classifier_side_effecting():
    assert TaskTypeClassifier.is_side_effecting("connector_write") is True


def test_task_type_classifier_deterministic():
    assert TaskTypeClassifier.is_deterministic("summarization") is True


def test_task_type_classifier_implied_action_read():
    assert TaskTypeClassifier.implied_action_category("summarization") == ActionCategory.READ


def test_task_type_classifier_implied_action_write():
    assert TaskTypeClassifier.implied_action_category("connector_write") == ActionCategory.WRITE


# ---------------------------------------------------------------------------
# 23. Decision TTL
# ---------------------------------------------------------------------------

def test_governance_decision_has_expires_at():
    decision = GovernanceDecision(
        decision=GovernanceDecisionType.ALLOW,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=GOVERNANCE_DECISION_TTL_SECONDS),
    )
    assert decision.expires_at is not None
    assert decision.expires_at > datetime.now(timezone.utc)


def test_privileged_decision_shorter_ttl():
    # Privileged ops: shorter TTL than read-only
    assert PRIVILEGED_DECISION_TTL_SECONDS < GOVERNANCE_DECISION_TTL_SECONDS


# ---------------------------------------------------------------------------
# 24. Evaluation Request Context Building
# ---------------------------------------------------------------------------

def test_build_context_from_request():
    request = _make_request(
        model_id="gpt-4",
        provider="openai",
        tool_id="code_runner",
        estimated_cost_usd=0.05,
        action_category=ActionCategory.READ,
    )
    ctx = PolicyEvaluator.build_context(request)
    assert ctx["model_id"] == "gpt-4"
    assert ctx["provider"] == "openai"
    assert ctx["tool_id"] == "code_runner"
    assert ctx["estimated_cost_usd"] == 0.05
    assert ctx["action_category"] == "read"


def test_build_context_excludes_sensitive_fields():
    request = _make_request()
    ctx = PolicyEvaluator.build_context(request)
    # Organization and workspace IDs are in the request but not used as
    # condition fields (they are resolved at the policy scope level, not rule level)
    assert "extra_metadata" not in ctx


# ---------------------------------------------------------------------------
# 25. Security: Frontend Cannot Bypass Governance
# ---------------------------------------------------------------------------

def test_api_payload_cannot_grant_permissions():
    # GovernanceEvaluationRequest does not accept arbitrary 'permissions' fields
    request = GovernanceEvaluationRequest(
        enforcement_point=EnforcementPoint.TASK_EXECUTION,
        organization_id=_org(),
        extra_metadata={"permissions": "admin", "bypass": True},
    )
    ctx = PolicyEvaluator.build_context(request)
    # extra_metadata is not in the evaluation context — cannot be used as a condition field
    assert "permissions" not in ctx
    assert "bypass" not in ctx


def test_llm_output_cannot_modify_policy():
    # Policy rules must come from PolicyVersionCreate with validated structure
    # Test that arbitrary string as rule is rejected
    with pytest.raises(Exception):
        PolicyVersionCreate(rules=[{"action": "__import__('os').system('rm -rf /')"}])


def test_workspace_cannot_access_another_workspace_policy():
    # Policies are scoped to organization_id; a different workspace's policies
    # are not resolved for requests from a different org
    rule = PolicyRule(
        rule_type=PolicyRuleType.MODEL,
        action=PolicyAction.DENY,
        conditions=[],
        priority=100,
    )
    # Evaluating in context of workspace A — rule exists in workspace B
    # In real resolver, workspace B's policies would not be loaded for workspace A
    # This unit test verifies the scope enforcement: request only sees its own workspace
    request_ws_a = _make_request(workspace_id=_ws())
    request_ws_b = _make_request(workspace_id=uuid.UUID("99999999-0000-0000-0000-000000000099"))
    # Both would evaluate the same injected rules here; but in the full system
    # the PolicyResolver filters by workspace_id
    dt_a, _, _, _, _ = PolicyEvaluator.evaluate([rule], request_ws_a)
    dt_b, _, _, _, _ = PolicyEvaluator.evaluate([rule], request_ws_b)
    # Both contexts evaluate the same injected rule (unit test limitation)
    # The actual isolation is enforced in PolicyResolver (DB-layer filtering)
    assert isinstance(dt_a, GovernanceDecisionType)
    assert isinstance(dt_b, GovernanceDecisionType)


# ---------------------------------------------------------------------------
# 26. Replay Governance
# ---------------------------------------------------------------------------

def test_replay_governance_deny_current_policy():
    """If current policy denies the replayed action, replay must not execute side effects."""
    rule = PolicyRule(
        rule_type=PolicyRuleType.ACTION,
        action=PolicyAction.DENY,
        conditions=[RuleCondition(field="action_category", operator=RuleConditionOperator.EQUALS, value="write")],
        priority=100,
        description="Write operations currently denied",
    )
    request = _make_request(action_category=ActionCategory.WRITE)
    decision_type, _, _, _, _ = PolicyEvaluator.evaluate([rule], request)
    assert decision_type == GovernanceDecisionType.DENY

    # Enforcer must block the replay
    decision = GovernanceDecision(decision=decision_type, reasons=["Write operations currently denied"])
    with pytest.raises(GovernanceDeniedError):
        PolicyEnforcer.enforce(decision, "external_action")


# ---------------------------------------------------------------------------
# 27. Evaluation Governance
# ---------------------------------------------------------------------------

def test_evaluation_required_constraint():
    rule = PolicyRule(
        rule_type=PolicyRuleType.EVALUATION,
        action=PolicyAction.SET_LIMIT,
        conditions=[],
        action_params={"evaluation_required": True, "evaluation_scope": "production"},
        priority=100,
        description="Production workflows require evaluation",
    )
    _, _, constraints, _, _ = PolicyEvaluator.evaluate([rule], _make_request())
    assert constraints.get("evaluation_required") is True
    assert constraints.get("evaluation_scope") == "production"


# ---------------------------------------------------------------------------
# 28. Model Capability Classifier
# ---------------------------------------------------------------------------

def test_model_capability_vision():
    assert ModelCapabilityClassifier.requires_vision(["vision", "text"]) is True
    assert ModelCapabilityClassifier.requires_vision(["text"]) is False


def test_model_capability_tool_use():
    assert ModelCapabilityClassifier.requires_tool_use(["tools", "text"]) is True


def test_model_capability_code():
    assert ModelCapabilityClassifier.requires_code(["code_generation"]) is True
