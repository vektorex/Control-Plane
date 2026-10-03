"""
Constants and Enums for Step 32: AI Governance, Policy Control Plane, and Safety Guardrails.
"""
from enum import Enum


class GovernanceDecisionType(str, Enum):
    ALLOW = "allow"
    ALLOW_WITH_CONSTRAINTS = "allow_with_constraints"
    REQUIRE_APPROVAL = "require_approval"
    REQUIRE_VERIFICATION = "require_verification"
    DENY = "deny"


class PolicyStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    ARCHIVED = "archived"


class PolicyVersionStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class PolicyScope(str, Enum):
    ORGANIZATION = "organization"
    WORKSPACE = "workspace"
    PROJECT = "project"


class PolicyRuleType(str, Enum):
    MODEL = "model"
    PROVIDER = "provider"
    TOOL = "tool"
    CONNECTOR = "connector"
    WORKFLOW = "workflow"
    PROMPT = "prompt"
    ARTIFACT = "artifact"
    DATA = "data"
    ACTION = "action"
    COST = "cost"
    RATE_LIMIT = "rate_limit"
    CACHE = "cache"
    APPROVAL = "approval"
    EVALUATION = "evaluation"
    RETENTION = "retention"


class RuleConditionOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    NOT_IN = "not_in"
    EXISTS = "exists"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_OR_EQUAL = "less_or_equal"
    MATCHES_ENUM = "matches_enum"


class PolicyAction(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    REQUIRE_VERIFICATION = "require_verification"
    SET_LIMIT = "set_limit"
    RESTRICT = "restrict"
    FORCE = "force"
    DISABLE = "disable"


class DataClassification(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class ClassificationSource(str, Enum):
    SYSTEM = "system"
    ORGANIZATION_POLICY = "organization_policy"
    WORKSPACE_POLICY = "workspace_policy"
    PROJECT_POLICY = "project_policy"
    USER_EXPLICIT = "user_explicit"


class ActionCategory(str, Enum):
    READ = "read"
    WRITE = "write"
    DESTRUCTIVE = "destructive"
    FINANCIAL = "financial"
    COMMUNICATION = "communication"
    AUTHENTICATION = "authentication"
    CONFIGURATION = "configuration"


class EnforcementPoint(str, Enum):
    REQUEST_START = "request_start"
    TASK_EXECUTION = "task_execution"
    MODEL_EXECUTION = "model_execution"
    TOOL_EXECUTION = "tool_execution"
    CONNECTOR_EXECUTION = "connector_execution"
    WORKFLOW_STEP = "workflow_step"
    EXTERNAL_ACTION = "external_action"
    PROMPT_RELEASE = "prompt_release"
    CACHE_REUSE = "cache_reuse"
    ARTIFACT_ACCESS = "artifact_access"
    JOB_EXECUTION = "job_execution"


class VerificationRequirement(str, Enum):
    GROUNDING_REQUIRED = "grounding_required"
    CITATION_REQUIRED = "citation_required"
    SCHEMA_VALIDATION_REQUIRED = "schema_validation_required"
    HUMAN_REVIEW_REQUIRED = "human_review_required"
    ARTIFACT_EVIDENCE_REQUIRED = "artifact_evidence_required"


class BudgetReservationStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SETTLED = "settled"
    RELEASED = "released"
    EXPIRED = "expired"


# Policy precedence order (lower number = higher authority)
POLICY_PRECEDENCE = {
    "system_security": 0,
    PolicyScope.ORGANIZATION.value: 1,
    PolicyScope.WORKSPACE.value: 2,
    PolicyScope.PROJECT.value: 3,
    "user_preferences": 4,
}

# System-level immutable security constraints
SYSTEM_SECURITY_CONSTRAINTS = {
    "max_semantic_threshold_override": 0.99,
    "min_semantic_threshold_override": 0.70,
    "deny_overwrites_allow": True,
    "user_cannot_weaken_security": True,
    "restricted_requires_explicit_provider": True,
}

# Default policy decision TTL seconds (must be rechecked after this)
GOVERNANCE_DECISION_TTL_SECONDS = 300  # 5 minutes

# Decision TTL for privileged/destructive operations
PRIVILEGED_DECISION_TTL_SECONDS = 60  # 1 minute

# Maximum budget reservation hold (seconds)
MAX_BUDGET_RESERVATION_SECONDS = 3600  # 1 hour

# Default fail-safe for unknown governance state
FAIL_SAFE_DEFAULT_PRIVILEGED = GovernanceDecisionType.DENY
FAIL_SAFE_DEFAULT_READ_ONLY = GovernanceDecisionType.ALLOW

# Rate limit window (seconds)
RATE_LIMIT_WINDOW_SECONDS = 60

# Maximum active policies per workspace
MAX_POLICIES_PER_WORKSPACE = 100

# Maximum rules per policy version
MAX_RULES_PER_POLICY = 50
