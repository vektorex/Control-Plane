# Step 43: AI Outcome Intelligence & Work Impact Layer Architecture

## 1. Executive Summary

The **AI Outcome Intelligence & Work Impact Layer** advances the platform from tracking merely *whether an AI generated an output* to evaluating *whether the work produced the intended business, product, or operational outcome*.

The system tracks the full factual lifecycle:
```
Objective
  → Target (Key Result)
    → Milestone
      → Work (Task, Workflow, Agent Team)
        → Execution (Run, Telemetry, Trace)
          → Evidence (Execution Result, Artifact, Review)
            → Deliverable
              → Outcome
                → Deterministic Verification
                  → Measurement (Factual Metrics)
                    → Impact Analysis (Before vs After)
```

### Core Design Principles
1. **Zero Fabricated Metrics**: No imaginary business metrics or synthetic progress numbers.
2. **Zero Fabricated Savings**: Monetary or time savings are never claimed without explicit, pre-existing baseline measurements. Missing baselines report observed values with explicit limitations.
3. **No Subjective AI Intelligence Scores**: Prohibits opaque quality scores (e.g. arbitrary "Agent IQ = 94"). Quality is evaluated via factual assertions, test passes, format compliance, and grounded evaluations.
4. **Evidence-Backed Attribution Safety**: Distinguishes `observed`, `estimated`, and `inferred` connections. Never claims "Agent X caused outcome Y" without explicit causal evidence; defaults to "contributed to".
5. **Deterministic Verification Engine**: An outcome cannot transition to `VERIFIED` without satisfying configured requirements and required human confirmation. LLMs alone cannot declare business success.
6. **Decision Provenance Transparency**: AI-assisted and agent decisions are tracked with full model, prompt, run, evaluation, and approval provenance, and cannot impersonate human decisions.

---

## 2. Domain Model Architecture

### 2.1 Strategic Objective (`Objective`)
Represents an intended business or product result.
- **Fields**: `id`, `workspace_id`, `project_id`, `name`, `description`, `objective_type`, `status`, `priority`, `owner_user_id`, `created_by`, `start_at`, `target_at`, `completed_at`, `requirements`, `created_at`, `updated_at`.
- **Types**: `business`, `product`, `engineering`, `research`, `operations`, `security`, `compliance`, `personal`, `project`.
- **Statuses**: `draft`, `active`, `at_risk`, `completed`, `cancelled`, `archived`.

### 2.2 Key Result / Target (`OutcomeTarget`)
Measurable targets bound to an objective.
- **Fields**: `id`, `objective_id`, `name`, `description`, `metric_type`, `target_value`, `target_unit`, `baseline_value`, `current_value`, `target_date`, `measurement_source`, `status`, `created_at`, `updated_at`.
- **Metric Types**: `count`, `percentage`, `duration`, `currency`, `boolean`, `rate`, `ratio`, `custom`.
- **Measurement Sources**: `manual`, `system`, `connector`, `workflow`, `evaluation`, `event`, `artifact`, `document`, `external_reference`.

### 2.3 Strategic Milestone (`OutcomeMilestone`)
Checkpoints across work execution phases.
- **Fields**: `id`, `objective_id`, `name`, `description`, `status`, `due_at`, `completed_at`, `owner_user_id`, `connected_resource_type`, `connected_resource_id`, `created_at`, `updated_at`.
- **Statuses**: `planned`, `in_progress`, `blocked`, `completed`, `missed`, `cancelled`.

### 2.4 Outcome Deliverable (`Outcome`)
Concrete result or deliverable produced by AI work.
- **Fields**: `id`, `workspace_id`, `project_id`, `objective_id`, `name`, `description`, `outcome_type`, `status`, `confidence`, `owner_user_id`, `created_by`, `requirements`, `observed_at`, `verified_at`, `verified_by`, `created_at`, `updated_at`.
- **Types**: `deliverable`, `decision`, `resolution`, `optimization`, `risk_reduction`, `issue_resolution`, `research_finding`, `automation`, `approval`, `milestone`, `customer_outcome`, `operational_outcome`, `security_outcome`.
- **Statuses**: `planned`, `in_progress`, `observed`, `verified`, `disputed`, `failed`, `cancelled`.
- **Confidence States**: `unverified`, `supported`, `strongly_supported`, `verified`, `disputed`.

### 2.5 Work-to-Outcome Link (`OutcomeWorkLink`)
Connects outcomes to underlying execution resources:
- `Task`, `Run`, `Workflow`, `WorkflowRun`, `AgentRun`, `AgentTeamRun`, `Document`, `Artifact`, `EvaluationRun`, `SimulationRun`, `Decision`, `CollaborationSession`.
- **Relationships**: `contributes_to`, `produced`, `supports`, `validated_by`, `blocked_by`, `derived_from`, `measures`, `implements`.

### 2.6 Outcome Evidence (`OutcomeEvidence`)
Provenance snapshots substantiating outcome claims.
- **Fields**: `id`, `outcome_id`, `source_type`, `source_id`, `evidence_type`, `description`, `snapshot`, `status`, `is_human_confirmed`, `is_ai_generated`, `observed_at`, `created_at`.
- **Types**: `execution_result`, `evaluation_result`, `human_confirmation`, `artifact`, `document`, `connector_record`, `workflow_result`, `metric_observation`, `security_event`, `simulation_result`, `collaboration_decision`, `external_reference`.
- **Statuses**: `unreviewed`, `supported`, `rejected`, `superseded`.

### 2.7 Factual Measurement (`OutcomeMeasurement`)
Empirical observations tied to targets or outcomes.
- **Fields**: `id`, `outcome_id`, `target_id`, `metric_name`, `value`, `unit`, `measurement_source`, `observed_at`, `evidence_id`, `created_at`.

### 2.8 Work Decision (`WorkDecision`)
Governs human, policy, and AI-assisted decisions.
- **Fields**: `id`, `workspace_id`, `project_id`, `objective_id`, `outcome_id`, `title`, `description`, `decision_type`, `status`, `decision_owner`, `evidence_ids`, `provenance`, `created_at`, `updated_at`.
- **Decision Types**: `human`, `AI_assisted`, `policy`, `workflow`, `agent`, `team`.
- **Provenance**: `agent_id`, `agent_version_id`, `run_id`, `model_provider`, `prompt_version`, `evidence_ids`, `evaluation_id`, `approval_id`.

### 2.9 Attribution (`OutcomeAttribution`)
- **Fields**: `id`, `outcome_id`, `resource_type`, `resource_id`, `attribution_type`, `evidence_ids`, `explanation`, `attribution_source`, `attribution_confidence`, `created_at`.
- **Attribution Types**: `direct`, `supporting`, `contributing`, `blocking`, `unknown`.
- **Attribution Sources**: `deterministic`, `human`, `AI_GENERATED_ATTRIBUTION`.
- **Confidence**: `observed`, `estimated`, `inferred`.

### 2.10 Impact Analysis (`ImpactAnalysis`)
- **Fields**: `id`, `outcome_id`, `analysis_type`, `summary`, `evidence_ids`, `observations`, `limitations`, `attribution_confidence`, `baseline_value`, `observed_value`, `difference_value`, `unit`, `created_at`.
- **Types**: `time_saved`, `cost_change`, `risk_change`, `quality_change`, `throughput_change`, `resolution_change`, `process_change`, `operational_change`.

---

## 3. Verification & Safety Policies

### 3.1 Verification Requirements Flow
An outcome cannot be marked `VERIFIED` unless deterministic checks succeed:
1. **Evidence Check**: At least one supporting evidence record is present and unrejected.
2. **Evaluation Check**: Associated evaluation lab assertions passed if `required_evaluation` configured.
3. **Approval Check**: Governance approval record attached if `required_approval` configured.
4. **Human Sign-off**: Explicit human sign-off required if `required_human_confirmation` configured.

### 3.2 Attribution Causality Rules
- Direct causation (`direct`) requires verified causal evidence records.
- If evidence is partial or timestamps correlate without deterministic causality proof, attribution defaults to `contributing` or `supporting`.
- AI Gateway attribution suggestions are strictly tagged with `AI_GENERATED_ATTRIBUTION` and `inferred` confidence; they never graduate to verified attribution without human confirmation.

### 3.3 Explainable Health Rules
Objective and Outcome health is evaluated strictly with deterministic rules:
- **`HEALTHY`**: All milestones on schedule, targets progressing within windows, evidence attached.
- **`AT_RISK`**: Milestone overdue, target deadline passed without achievement, or missing required evidence.
- **`BLOCKED`**: Any milestone or dependency is explicitly flagged as `BLOCKED`.
- **`STALE`**: No updates or new evidence recorded for > 30 days.

---

## 4. Work-to-Outcome Bounded Graph Traversal

The `OutcomeGraphService` integrates with the Step 29 Knowledge Graph without introducing external graph databases:
- **Entities**: `objective`, `outcome`, `outcome_target`, `milestone`, `decision`, `measurement`.
- **Relationships**: `supports`, `contributes_to`, `achieves`, `measures`, `blocks`, `depends_on`, `decided_by`, `validated_by`, `derived_from`.
- **Bounded Traversal**: Strictly enforced between 1 and 3 hops (default: 2 hops) to prevent unbounded recursive loops.

---

## 5. Security, Governance, and Multi-Tenancy

- **Tenant Isolation**: Every database query, repository lookup, and API handler enforces `workspace_id` matching via `OutcomePolicyEngine.enforce_tenant_isolation`.
- **RBAC & Developer Platform Scopes**:
  - `objectives:read`, `objectives:write`
  - `outcomes:read`, `outcomes:write`, `outcomes:verify` (marked `SENSITIVE`)
  - `decisions:read`, `decisions:write`
- **Data Governance (Step 33)**: All outcome, evidence, decision, and impact entities are subject to data retention policies, classification, legal hold, export, and soft deletion.
- **Security Operations (Step 34)**: Detects and audits attempts to tamper with evidence, manipulate measurements, or impersonate human reviewers.

---

## 6. Public API & SDK Reference

### 6.1 Public Endpoints (`/api/v1`)
| Method | Endpoint | Description | Scope |
|---|---|---|---|
| POST | `/api/v1/objectives` | Create objective | `objectives:write` |
| GET | `/api/v1/objectives` | List objectives | `objectives:read` |
| GET | `/api/v1/objectives/{id}` | Get objective | `objectives:read` |
| PATCH | `/api/v1/objectives/{id}` | Update objective | `objectives:write` |
| DELETE | `/api/v1/objectives/{id}` | Delete objective | `objectives:write` |
| POST | `/api/v1/objectives/{id}/targets` | Create target | `objectives:write` |
| GET | `/api/v1/objectives/{id}/targets` | List targets | `objectives:read` |
| POST | `/api/v1/objectives/{id}/milestones`| Create milestone | `objectives:write` |
| GET | `/api/v1/objectives/{id}/milestones`| List milestones | `objectives:read` |
| GET | `/api/v1/objectives/{id}/health` | Objective health diagnostics | `objectives:read` |
| GET | `/api/v1/objectives/{id}/work-map` | Visual work map graph | `objectives:read` |
| POST | `/api/v1/outcomes` | Create outcome deliverable | `outcomes:write` |
| GET | `/api/v1/outcomes` | List outcomes | `outcomes:read` |
| GET | `/api/v1/outcomes/{id}` | Get outcome details | `outcomes:read` |
| PATCH | `/api/v1/outcomes/{id}` | Update outcome | `outcomes:write` |
| POST | `/api/v1/outcomes/{id}/evidence` | Attach evidence | `outcomes:write` |
| GET | `/api/v1/outcomes/{id}/evidence` | List evidence | `outcomes:read` |
| POST | `/api/v1/outcomes/{id}/measurements` | Add factual measurement | `outcomes:write` |
| GET | `/api/v1/outcomes/{id}/measurements` | List measurements | `outcomes:read` |
| POST | `/api/v1/outcomes/{id}/verify` | Verify outcome deliverable | `outcomes:verify` |
| POST | `/api/v1/outcomes/{id}/dispute` | Dispute outcome claim | `outcomes:write` |
| GET | `/api/v1/outcomes/{id}/work` | List linked work resources | `outcomes:read` |
| GET | `/api/v1/outcomes/{id}/impact` | List impact analyses | `outcomes:read` |
| GET | `/api/v1/outcomes/{id}/graph` | Get attribution graph | `outcomes:read` |
| POST | `/api/v1/decisions` | Propose work decision | `decisions:write` |
| GET | `/api/v1/decisions` | List work decisions | `decisions:read` |
| GET | `/api/v1/decisions/{id}` | Get decision with provenance | `decisions:read` |
| POST | `/api/v1/decisions/{id}/approve` | Approve decision | `decisions:write` |
| POST | `/api/v1/decisions/{id}/reject` | Reject decision with reason | `decisions:write` |

### 6.2 Python SDK
```python
from ai_work_layer import Client

client = Client(api_key="awl_dev_...")

# Strategic Objectives
obj = client.objectives.create({
    "name": "Accelerate Incident Resolution",
    "objective_type": "engineering",
    "priority": "high",
})

# Outcome Deliverables
outcome = client.outcomes.create({
    "name": "Automated Remediation Plan",
    "objective_id": obj["id"],
    "outcome_type": "deliverable",
})

# Attach Evidence
client.outcomes.add_evidence(outcome["id"], {
    "evidence_type": "execution_result",
    "description": "Benchmark run logs confirmed 45min MTTR reduction",
    "snapshot": {"observed_mttr_minutes": 45},
})

# Verify Deliverable
client.outcomes.verify(outcome["id"], {"notes": "Verified by engineering lead"})
```

### 6.3 JavaScript SDK
```javascript
import { AIWorkLayerClient } from "@ai-work-layer/sdk";

const client = new AIWorkLayerClient({ apiKey: "awl_dev_..." });

// Create Objective
const objective = await client.objectives.create({
  name: "Documentation Quality Overhaul",
  objective_type: "product",
});

// Attach Evidence & Verify
await client.outcomes.addEvidence(outcomeId, {
  evidence_type: "artifact",
  description: "Public API reference guides updated and committed",
});

await client.outcomes.verify(outcomeId);
```
