# AI Governance, Policy Control Plane, and Safety Guardrails Architecture (Step 32)

## 1. Executive Summary & Purpose

The **AI Governance, Policy Control Plane, and Safety Guardrails** layer provides centralized, deterministic policy enforcement and safety constraints across the AI Work Layer. As organizations scale generative AI and agentic execution pipelines, critical operations—including frontier model invocation, privileged tool execution, external connector writes, semantic cache access, and high-volume background jobs—must operate within explicit compliance, data privacy, and budgetary boundaries.

This control plane serves as the authoritative evaluation engine for:
- Pre-execution validation of task dispatch, agent tool use, and workflow steps.
- Scoped guardrail evaluation adhering to strict hierarchical precedence: **System &rarr; Organization &rarr; Workspace &rarr; Project**.
- Data classification and privacy guardrails protecting PHI, PII, financial data, and credentials.
- Financial budget enforcement (per-run cost caps, periodic spend limits, and token thresholds).
- Immutable, tamper-evident audit logging for forensic traceability and compliance reporting.

Importantly, this subsystem centralizes policy evaluation **without duplicating** existing specialized subsystems (such as RBAC access control, HITL review tables, or AI Gateway routing); instead, it evaluates policies across these domains and supplies authoritative constraints.

---

## 2. Architecture & Component Topology

```
                   +--------------------------------------------+
                   |           Client Applications              |
                   |   (Dashboard, Policy Editor, Simulator)    |
                   +---------------------+----------------------+
                                         |
                                         v
                   +--------------------------------------------+
                   |       FastAPI /governance/* Endpoints       |
                   | (Policy CRUD, Versioning, Evaluate, Sim)   |
                   +---------------------+----------------------+
                                         |
                                         v
                   +--------------------------------------------+
                   |            GovernanceService               |
                   |   (Unified Facade & Policy Coordinator)    |
                   +---------------------+----------------------+
                                         |
       +---------------------------------+---------------------------------+
       |                                 |                                 |
       v                                 v                                 v
+--------------+                +------------------+             +-------------------+
| PolicyEngine |                |  Sanitizer &     |             |   BudgetService   |
| (Precedence  |                |  Data Classifier |             |  & Rate Limiter   |
|  Evaluator)  |                +------------------+             +-------------------+
+-------+------+
        |
        +--------> Evaluates Hierarchical Policies (System -> Org -> WS -> Proj)
        |
        +--------> Applies Rule Condition Matching (Regex, Sets, Comparators)
        |
        +--------> Enforces Fail-Safe Behavior (Fail-Closed default)
        |
        +--------> Emits Bounded Decisions (TTL: 300s general, 60s privileged)
        |
        +--------> Logs to Immutable `governance_decisions` Table
```

---

## 3. Hierarchical Scope & Precedence Ordering

Policies are organized into four hierarchically nested scopes:
1. **System Scope (`system`)**: Platform-wide baseline safety guardrails defined at system boot (e.g. blocking destructive shell commands, enforcing secret redaction, credential protection). System rules evaluate first and **cannot be overridden** by downstream scopes to grant permissions blocked by the platform.
2. **Organization Scope (`organization`)**: Enterprise compliance rules applicable across all workspaces within a tenant (e.g. restricting frontier models, enforcing specific model providers, mandatory audit logging).
3. **Workspace Scope (`workspace`)**: Team and environment constraints tailored to daily operational boundaries (e.g. workspace budget limits, cache semantic matching restrictions for sensitive projects).
4. **Project Scope (`project`)**: Granular project guardrails (e.g. enforcing read-only connectors, requiring HITL approval for deployment tools).

### Precedence Algorithm
During policy evaluation, rules are aggregated in precedence order:
$$\text{System} \succ \text{Organization} \succ \text{Workspace} \succ \text{Project}$$

Within a scope, rules are ordered by **Priority** (descending numerical value, higher runs first). The first rule whose conditions match the execution context determines the intermediate action:
- **DENY**: Immediately short-circuits evaluation. Denials at higher scopes cannot be overridden by lower scopes.
- **REQUIRE_APPROVAL**: Elevates the execution requirement to human-in-the-loop review.
- **ALLOW_WITH_CONSTRAINTS**: Records mandatory runtime constraints (e.g. allowed models, redacted fields, exact-only cache mode).
- **ALLOW**: Permits execution unless subsequent, higher-priority rules intervene.

---

## 4. Policy Rules & Condition Schema

A policy version contains an immutable array of `PolicyRule` objects conforming to the following schema:

```json
{
  "rule_id": "rule_frontier_model_guardrail",
  "rule_type": "model",
  "action": "deny",
  "priority": 100,
  "description": "Deny unapproved frontier models in production workspaces",
  "conditions": [
    {
      "field": "model_id",
      "operator": "IN_LIST",
      "value": ["unapproved-frontier-v1", "experimental-model"]
    },
    {
      "field": "environment",
      "operator": "EQUALS",
      "value": "production"
    }
  ],
  "constraints": {
    "suggested_alternative": "gpt-4o"
  }
}
```

### Supported Rule Types
| Rule Type | Description & Enforcement Domain |
| :--- | :--- |
| `model` | Restricts or permits specific model identifiers and model capabilities. |
| `provider` | Controls approved AI providers (e.g. OpenAI, Anthropic, Google, Ollama). |
| `tool` | Restricts execution of side-effecting, destructive, or write-oriented tools. |
| `connector` | Regulates external connector operations, read vs. write authorizations. |
| `workflow` | Controls multi-step workflow pipeline execution and step dispatch. |
| `prompt` | Enforces prompt release status, template approval, or environment tags. |
| `artifact` | Regulates multimodal artifact generation, storage, and classification. |
| `data` | Enforces data classification boundaries (Public, Internal, Confidential, Restricted). |
| `cache` | Governs cache admission, disables semantic matching for restricted data. |
| `hitl` | Triggers Human-in-the-Loop review gates for sensitive operations. |
| `budget` | Enforces maximum per-run and periodic cost caps. |
| `rate_limit` | Governs requests per minute/hour per workspace or user. |

### Supported Condition Operators
- `EQUALS` / `NOT_EQUALS`: Strict string, numerical, or boolean equality.
- `CONTAINS` / `NOT_CONTAINS`: Substring matching or collection inclusion.
- `IN_LIST` / `NOT_IN_LIST`: Set membership validation against string or enum arrays.
- `GREATER_THAN` / `LESS_THAN`: Numerical threshold comparison (costs, tokens, latencies).
- `MATCHES_REGEX`: Regular expression pattern matching on string payloads.

---

## 5. Enforcement Points & Integration

The governance control plane establishes checkpoints at 8 critical execution phases:

1. **`TASK_EXECUTION`**: Pre-execution checkpoint in `TaskExecutionService`. Evaluates model, tools, and budget before orchestration begins.
2. **`ORCHESTRATION_DISPATCH`**: Evaluates multi-agent delegation and plan step dispatch.
3. **`MODEL_INVOCATION`**: AI Gateway checkpoint validating token count, streaming options, and provider health.
4. **`TOOL_EXECUTION`**: Evaluates individual tool calls during bounded agentic execution loops.
5. **`CONNECTOR_CALL`**: Validates external third-party API mutations and data egress.
6. **`WORKFLOW_STEP`**: WorkflowExecutor step checkpoint before executing step dispatch.
7. **`CACHE_READ`**: Validates semantic cache lookup eligibility and prevents data leaks across classifications.
8. **`CACHE_WRITE`**: Validates semantic cache admission gate for executed run responses.

---

## 6. Budget & Spend Control Plane

Financial governance is managed via `BudgetService`, offering:
- **Per-Run Cost Caps**: Immediate validation of estimated cost before launching LLM calls.
- **Periodic Aggregate Spend Limits**: Cumulative daily, weekly, or monthly tracking.
- **Soft Threshold Alerts**: Emits warning notifications when spend reaches 70–90% of threshold.
- **Hard Limit Enforcement**:
  - `deny`: Hard failure, rejecting further executions until the period resets.
  - `require_approval`: Routes requests to HITL for budget override authorization.
  - `notify`: Emits an alert while permitting execution.
- **Budget Reservations**: Atomic reservation and settlement model preventing race conditions during concurrent runs.

---

## 7. Fail-Safe Model & Resilience

AI systems must operate predictably even under external failure conditions:
- **`fail_closed` (Default)**: If governance policy resolution encounters database connectivity failure, malformed rules, or state corruption, **privileged and side-effecting operations are strictly DENIED**. Read-only queries with low risk are allowed with a warning flag.
- **`fail_open`**: Optional mode for non-critical developer environments where continuity is prioritized over strict blocking, logging high-priority audit events for post-hoc review.
- **Bounded Decision TTL**: Decisions carry strict time-to-live timestamps:
  - Standard decisions: 300 seconds.
  - Privileged/side-effecting decisions: 60 seconds.
  Decisions cannot be cached or reused past their expiration.

---

## 8. Database Schema & Migration (029)

The governance control plane introduces 5 relational tables via Alembic migration `029_governance.py`:

```sql
-- Core policy definition
CREATE TABLE governance_policies (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL,
    workspace_id UUID,
    project_id UUID,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    scope VARCHAR(50) NOT NULL,
    policy_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    fail_safe_mode VARCHAR(50) NOT NULL DEFAULT 'fail_closed',
    tags JSONB,
    active_version_id UUID,
    created_by UUID,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    deleted_at TIMESTAMPTZ
);

-- Versioned immutable ruleset
CREATE TABLE governance_policy_versions (
    id UUID PRIMARY KEY,
    policy_id UUID NOT NULL REFERENCES governance_policies(id),
    version_number INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    rules JSONB NOT NULL,
    change_summary TEXT,
    created_by UUID,
    activated_by UUID,
    activated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL
);

-- Spend & token guardrails
CREATE TABLE budget_policies (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL,
    workspace_id UUID,
    project_id UUID,
    scope VARCHAR(50) NOT NULL,
    max_cost_per_run DOUBLE PRECISION,
    max_cost_per_period DOUBLE PRECISION,
    max_tokens_per_run INTEGER,
    period VARCHAR(50) NOT NULL DEFAULT 'monthly',
    hard_limit_action VARCHAR(50) NOT NULL DEFAULT 'deny',
    soft_threshold_percent INTEGER NOT NULL DEFAULT 80,
    created_by UUID,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

-- Atomic budget reservations
CREATE TABLE budget_reservations (
    id UUID PRIMARY KEY,
    budget_policy_id UUID NOT NULL REFERENCES budget_policies(id),
    run_id UUID,
    amount DOUBLE PRECISION NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    settled_at TIMESTAMPTZ
);

-- Immutable audit decision log
CREATE TABLE governance_decisions (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL,
    workspace_id UUID,
    project_id UUID,
    user_id UUID,
    enforcement_point VARCHAR(100) NOT NULL,
    decision VARCHAR(50) NOT NULL,
    reasons JSONB NOT NULL,
    matched_policies JSONB NOT NULL,
    constraints JSONB NOT NULL,
    sanitized_context JSONB NOT NULL,
    evaluation_duration_ms INTEGER NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
```

---

## 9. Verification & Test Suite

The implementation is verified by an extensive 100-test suite in `backend/tests/test_governance.py`:
- **Policy Precedence & Scoping**: Tests verify system > org > workspace > project hierarchy.
- **Rule Evaluator & Operators**: Thorough coverage of all 9 operators and condition combinations.
- **Classifiers**: Model capability, provider normalization, tool destructiveness, artifact risk.
- **Enforcement Gating**: DENY raises `GovernanceDeniedError`, ALLOW permits, ALLOW_WITH_CONSTRAINTS filters tools.
- **Secret Sanitization**: Regex redaction for OpenAI, Anthropic, AWS, GitHub tokens, JWTs, and passwords.
- **Budget Guardrails**: Per-run limit denial, soft threshold alerting, reservation lifecycle.
- **Fail-Safe Robustness**: Verifies fail-closed behavior for privileged actions on unexpected exceptions.
- **Cross-Tenant Isolation**: Confirms workspace $A$ cannot query or manipulate workspace $B$ policies.
