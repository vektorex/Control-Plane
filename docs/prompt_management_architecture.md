# STEP 28: Production-Grade Prompt Management, Versioning, Release, and Experimentation Architecture

## 1. Overview & Architecture Target

The Prompt Management System transforms prompts from hard-coded, scattered strings in application code into first-class, version-controlled, auditable, and governed AI assets.

```
Prompt Asset (Key & Metadata)
       ↓
Immutable Prompt Versions (v1, v2, v3...)
       ↓
Environment Releases (development, staging, production)
       ↓
Consumers (Task / Workflow / Evaluator / Planner / Replay)
       ↓
AI Gateway (Centralized Unified Execution)
       ↓
Observability & Evaluation Lab (Telemetry & Automated Metrics)
       ↓
A/B Experimentation & Comparison (Deterministic Variant Allocation)
       ↓
Human-Controlled Promotion (Optional HITL Verification)
```

---

## 2. Core Invariants & Security Boundaries

1. **No Second Model Execution Path**: All preview test executions and runtime prompt executions route strictly through the centralized `default_ai_gateway`. No provider direct calls or unmonitored pathways exist.
2. **Safe Deterministic Variable Rendering**:
   - Variables use the safe syntax `{{namespace.variable_name}}` where `namespace` is strictly constrained to `input`, `task`, `project`, `context`, `workflow`, `memory`, `system`.
   - Single-pass replacement only. Dynamic evaluation (`eval()`, JavaScript, Python, shell scripts, methods, or attribute traversal) is strictly rejected by the validator.
   - Variable values are treated strictly as literal data. Values containing nested template syntax (e.g., `{{system.secret}}`) are inserted as literal strings without a second rendering pass, preventing template injection.
3. **Secret Protection**:
   - Every prompt content modification is scanned against credential patterns (OpenAI, Anthropic, AWS, GitHub, Bearer tokens, private keys, connection strings).
   - Prompts containing detected credentials are automatically rejected before saving to prevent prompt storage from becoming an insecure credential store.
   - Version diff generation automatically masks sensitive patterns.
4. **No Autonomous AI Model Promotion**:
   - Models/LLMs are strictly forbidden from publishing or promoting prompt versions to staging or production environments. Promotion is exclusively a human-authorized operation.
   - High-impact production releases can be configured to require HITL (Human-in-the-Loop) approvals.
5. **Multi-Tenant Isolation & Hierarchical RBAC**:
   - Prompts inherit access boundaries from `Organization -> Workspace -> Project`.
   - Cross-organization and cross-workspace access attempts are strictly blocked.
   - RBAC matrix enforces granular permissions:
     - `prompt.read` (Viewer+)
     - `prompt.create`, `prompt.update` (Member+)
     - `prompt.publish`, `prompt.release`, `prompt.rollback` (Admin+)
     - `prompt.execute`, `prompt.experiment` (Member+)
     - `prompt.archive` (Admin+)

---

## 3. Versioning & Immutability Lifecycle

### Monotonic Version Numbering
- Version numbers increase monotonically (`v1`, `v2`, `v3`...) within the scope of a parent prompt asset.
- Monotonic version generation is executed within a database transaction with row-level locking to prevent race conditions and concurrent duplicate version numbers.

### Immutability Contract
- **Draft Status**: Newly created versions are drafts and can be refined, previewed, and validated.
- **Published Status**: Calling `/api/prompts/{id}/versions/{version_id}/publish` transitions the version to `published` and generates a cryptographic SHA-256 `content_hash`.
- Published versions are **permanently immutable**. Editing a published prompt automatically requires creating a new draft version.
- Deprecated versions retain full historical auditability.

---

## 4. Release Environments, Resolution & Rollback

### Environments
The system defines 3 governed environments:
- `development`
- `staging`
- `production`

Each environment holds at most **one active release** per prompt at any point in time. Historical releases are preserved in `prompt_releases` for a full audit trail.

### Runtime Resolution
Application code references prompts logically using `prompt key + environment`:
```python
resolved = await prompt_resolver.resolve_prompt_for_execution(
    prompt_key="planner.execution_plan",
    environment="production",
    workspace_id=workspace_id,
    project_id=project_id,
)
# Returns the immutable PromptVersion and its SHA-256 content_hash
```

### Rollback
Rollback transitions release an existing published version back to the active slot, preserving the `previous_version_id` link and emitting `prompt.release_changed` and `prompt.rolled_back` events through the Step 26 EventPublisher.

---

## 5. Workflow Pinning Modes

Workflow steps (`generate`, `evaluate`) integrate with managed prompts using two explicit pinning modes:

1. **`PINNED`**:
   - Steps store the exact immutable `prompt_version_id`.
   - Recommended and default for published production workflows to guarantee 100% reproducibility.
2. **`TRACK_RELEASE`**:
   - Steps store `prompt_key` and target `environment` (e.g., `staging` or `production`).
   - Dynamically resolves to the active release of that environment at run execution time.

---

## 6. A/B Experimentation & Deterministic Allocation

### Architecture
Prompt experiments allow factual comparison of multiple prompt versions under live production or staging traffic:
- Neutral labels are strictly enforced (`A`, `B`, `C`, etc. — subjective tags like "winner" or "best" are prohibited).
- Configurable allocation weights (e.g., 50/50, 80/20).

### Deterministic Sticky Hashing
Variant allocation is calculated deterministically:
$$\text{hash} = \text{SHA256}(\text{experiment\_id} + \text{":"} + \text{allocation\_key\_value}) \pmod{10000}$$
- Valid allocation keys: `user_id`, `task_id`, `workflow_run_id`.
- Guarantees the same user or workflow run consistently receives the exact same prompt variant without database locks.
- AI models or subjective heuristics are never used to assign variants.

### Factual Metrics & Human Promotion
Metrics collected:
- Assertion pass/fail counts
- Evaluator findings
- Latency (ms)
- Token consumption (prompt + completion)
- Configured cost ($)
- Schema formatting compliance
- Citation behavior

The system presents purely objective comparisons and allows authorized operators to promote the desired version to staging or production.

---

## 7. Replay & Reproducibility Integration

Step 21 Replay snapshots capture the full prompt execution context:
- `prompt_id`
- `prompt_version_id`
- `content_hash`
- `release_environment`

During replay execution:
- By default, the original snapshot version is re-executed.
- An explicit alternative version can be selected for "what-if" testing.
- The system **never silently substitutes** the current production prompt during a reproducibility replay.

---

## 8. Real-Time Events, Jobs & Notifications

- **Events (Step 26)**:
  - `prompt.created`, `prompt.version_created`, `prompt.version_published`
  - `prompt.release_changed`, `prompt.rolled_back`, `prompt.archived`
  - `prompt.experiment_started`, `prompt.experiment_paused`, `prompt.experiment_completed`
- **Notifications (Step 25)**: Emitted on production release, rollback, and experiment completion.
- **Job Queue (Step 24)**: Background execution of bulk Evaluation Lab prompt experiment runs using `JobType.PROMPT_EXPERIMENT`.
- **SSE Streams**: UI updates instantaneously via the unified Server-Sent Events bus.

---

## 9. Concrete Prompt Examples

### Task Prompt: `task.summarize`
```
Key: task.summarize
Type: task
Variable Schema:
{
  "task.title": { "type": "string", "required": true },
  "input.content": { "type": "string", "required": true },
  "input.max_bullet_points": { "type": "number", "required": false }
}

Content:
Summarize the following material for task '{{task.title}}'.
Highlight key decisions, risks, and next steps in a concise bulleted list.

Content to analyze:
{{input.content}}
```

### Planner Prompt: `planner.execution_plan`
```
Key: planner.execution_plan
Type: planner
Variable Schema:
{
  "task.description": { "type": "string", "required": true },
  "context.content": { "type": "string", "required": false }
}

Content:
You are an expert AI orchestrator. Given the task instructions, decompose the objective into sequential and parallel steps.

Task:
{{task.description}}

Available Context:
{{context.content}}
```

### Evaluator Prompt: `evaluation.grounding`
```
Key: evaluation.grounding
Type: evaluator
Variable Schema:
{
  "context.source_text": { "type": "string", "required": true },
  "input.candidate_text": { "type": "string", "required": true }
}

Content:
Evaluate whether all assertions in the candidate text are grounded strictly in the source text.

Source Text:
{{context.source_text}}

Candidate Text:
{{input.candidate_text}}
```

### Workflow Prompt: `workflow.document_analysis`
```
Key: workflow.document_analysis
Type: workflow
Variable Schema:
{
  "project.name": { "type": "string", "required": true },
  "workflow.input": { "type": "string", "required": true }
}

Content:
Analyze the input document as part of project '{{project.name}}'.
Extract compliance indicators, contract obligations, and deliverables.

Input:
{{workflow.input}}
```

---

## 10. Verification & Test Suite Summary

- **Backend Unit & Integration Tests**: `backend/tests/test_prompts.py` (13 tests passed)
  - Safe deterministic rendering & schema validation
  - Forbidden namespace rejection
  - Arbitrary code / eval syntax rejection
  - Single-pass template injection prevention
  - Secret scanning & credential rejection
  - Secret masking in version diffs
  - Role matrix permissions enforcement
  - Version creation, monotonic numbering, and permanent immutability
  - Preview execution without model invocation
  - Release promotion & non-destructive rollback
  - Deterministic sticky A/B variant allocation
  - Strict tenant isolation across organizations
- **Regression Tests (Steps 23-27)**:
  - `backend/tests/test_access_control.py` passed
  - `backend/tests/test_events.py` passed
  - `backend/tests/test_jobs.py` passed
  - `backend/tests/test_replay.py` passed
  - `backend/tests/test_workflows.py` passed
  - `backend/tests/test_evaluation.py` passed (22 passed)
- **Frontend Quality Assurance**:
  - `npm run lint` passed with **0 errors and 0 warnings**.
