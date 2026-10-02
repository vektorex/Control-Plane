# Workflow Trigger & Event Automation Architecture (Step 23)

## 1. System Overview

The **Workflow Trigger & Event Automation System** provides production-grade event-driven and scheduled automation for AI workflows in the AI Work Layer. It allows users to automatically execute existing workflows without creating a second workflow execution engine or permitting arbitrary code execution.

```
Incoming Event (Webhook / Schedule / GitHub / Manual)
                     ↓
             Trigger Validation
                     ↓
        Authentication & Signature Verification
                     ↓
        Idempotency & Debounce Evaluation
                     ↓
          Deterministic Event Filtering
                     ↓
              Create TriggerRun
                     ↓
         WorkflowExecutor (Authoritative)
                     ↓
   HITL / Tools / Connectors / AI Gateway
                     ↓
              Workflow Result
                     ↓
      Observability & Telemetry Recording
```

---

## 2. Trigger Types Supported

| Trigger Type | Description | Source | Key Configs |
|---|---|---|---|
| `manual` | Executed directly via API or UI button | `manual` | Input payload, user auth |
| `schedule` | Recurring execution via cron or interval format | `schedule` | Cron expression, IANA timezone |
| `webhook` | HTTP POST ingestion with HMAC verification | `webhook` | Public trigger ID, HMAC secret, debounce |
| `connector_event` | Normalized external connector events | `github` | Event type, repository filter |

---

## 3. Core Architecture & Components

### 3.1 `TriggerRegistry`
Maintains an authoritative registry of all supported canonical event types:
- `manual.workflow.run`
- `schedule.workflow.run`
- `webhook.workflow.run`
- `github.issue.created`
- `github.issue.updated`
- `github.pull_request.opened`
- `github.pull_request.updated`

### 3.2 `EventTriggerService`
Normalizes raw, untrusted external webhook payloads into canonical `TriggerEvent` structures:
- GitHub issue created/updated
- GitHub pull request opened/updated
- Generic webhooks
- Safe extraction without dynamic code execution

### 3.3 `TriggerFilterEngine`
Deterministic multi-condition evaluation engine supporting:
- Operators: `equals`, `not_equals`, `contains`, `starts_with`, `ends_with`, `exists`, `greater_than`, `less_than`, `greater_or_equal`, `less_or_equal`.
- Boolean Composition: `AND` (all conditions must match) and `OR` (at least one condition must match).
- Zero `eval` or dynamic code execution. Safe path traversal across payload structures.

### 3.4 `TriggerPayloadMapper`
Reuses the variable resolution mechanism from the existing Workflow Engine:
- Maps `{{payload.repository.full_name}}`, `{{payload.issue.number}}`, `{{payload.issue.title}}` into target workflow inputs.
- Validates mapped values against the workflow's authoritative `input_schema`.

### 3.5 `TriggerDeduplicationService`
- **Idempotency Window**: Configured with `TRIGGER_DEDUPLICATION_WINDOW_SECONDS = 3600`. Prevents duplicate workflow execution by checking `idempotency_key` or `event_id`. First receipt executes; second receipt is recorded as `skipped` (`TRIGGER_DEDUPLICATED`).
- **Debouncing**: Configured with `debounce_seconds` (bounded up to 3600s). Suppresses rapid event bursts for the same trigger within the window, creating a `skipped` run (`TRIGGER_DEBOUNCED`).

### 3.6 `WebhookSecretStore` & `WebhookTriggerService`
- Generates high-entropy secrets and non-guessable `public_trigger_id` tokens (does not reveal workspace, workflow, or user IDs).
- Stores secrets using AES-256-GCM authenticated encryption. Secrets are never exposed in logs or API responses after creation.
- Verifies HMAC-SHA256 signatures (`X-Hub-Signature-256`, `X-Webhook-Signature`, `X-Signature-256`).
- Validates timestamp headers with drift tolerance (`WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS = 300`) for replay protection.
- High-performance ingestion endpoint (`POST /api/webhooks/{public_trigger_id}`) returns HTTP 202 Accepted immediately without synchronous execution.

### 3.7 `TriggerScheduler`
- Database-backed claiming for due trigger records using `with_for_update(skip_locked=True)` to prevent duplicate execution across distributed workers.
- Supports 5-part cron syntax and predefined shortcuts (`@hourly`, `@daily`, `@weekly`).
- Enforces `MAX_SCHEDULED_WORKFLOWS_PER_WORKSPACE = 50` and `MIN_SCHEDULE_INTERVAL_SECONDS = 60`.
- Native timezone support via `zoneinfo.ZoneInfo`. Never silently interprets schedules in UTC when another timezone was specified.

### 3.8 `TriggerPolicyEngine`
- Enforces rate limits: `TRIGGER_RATE_LIMIT_PER_MINUTE = 60` per trigger, per workspace, and per webhook identifier.
- Enforces workspace concurrency: `MAX_TRIGGER_CONCURRENCY_PER_WORKSPACE = 5`.
- Verifies trigger status (`active`) and workflow status (`published` / non-archived).
- Guarantees strict multi-tenant workspace isolation.

### 3.9 `TriggerRetryManager`
- Transient failure classification: retries only provider unavailable, gateway timeouts, temporary network/connector failures (`502`, `503`, `504`).
- Non-retryable: authorization failure, invalid workflow, policy denial, HITL rejection, invalid schema.
- Exponential backoff calculation: `delay = min(base * (factor ** retry_count), max_seconds)`.

---

## 4. Security & Safety Controls

1. **HITL Preservation**: Triggered workflows that encounter steps requiring human approval pause immediately in `waiting_for_approval`. Scheduled or automated execution NEVER grants automatic approval.
2. **Connector & Destructive Action Policies**: Read operations are allowed if authorized; external write/destructive connector operations require explicit human approval according to existing HITL policies.
3. **Memory Safety**: Triggered workflows retrieve memory only according to existing memory policies. Automatic permanent memory creation remains disabled unless explicitly requested by an approved workflow step.
4. **Secret Confidentiality**: Webhook secrets are encrypted at rest using AES-256-GCM. Plaintext secrets are returned strictly once during creation or regeneration, and never logged or exposed in traces or API responses.
5. **No Chain-of-Thought Exposure**: Telemetry only records structured audit events and metadata.

---

## 5. Observability Integration

The following trace events are recorded in `ExecutionTraceEvent`:
- `trigger_received`
- `trigger_validated`
- `trigger_filtered`
- `trigger_skipped`
- `trigger_queued`
- `trigger_started`
- `trigger_completed`
- `trigger_failed`
- `trigger_retry`
- `trigger_rate_limited`

---

## 6. API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/workflows/{workflow_id}/triggers` | POST | Create a new trigger for a workflow |
| `/api/workflows/{workflow_id}/triggers` | GET | List all triggers for a workflow |
| `/api/triggers/{trigger_id}` | GET | Retrieve trigger details |
| `/api/triggers/{trigger_id}` | PATCH | Update trigger configuration |
| `/api/triggers/{trigger_id}` | DELETE | Delete trigger |
| `/api/triggers/{trigger_id}/pause` | POST | Pause trigger |
| `/api/triggers/{trigger_id}/resume` | POST | Resume trigger |
| `/api/triggers/{trigger_id}/test` | POST | Dry-run test mode (filters & mapping) |
| `/api/workflows/{workflow_id}/triggers/{trigger_id}/run` | POST | Manual trigger execution |
| `/api/triggers/{trigger_id}/runs` | GET | List execution history for trigger |
| `/api/trigger-runs/{trigger_run_id}` | GET | Get single trigger run snapshot |
| `/api/triggers/{trigger_id}/webhook/regenerate-secret` | POST | Regenerate webhook HMAC secret |
| `/api/triggers/{trigger_id}/webhook/status` | GET | Get webhook status and public URL |
| `/api/webhooks/{public_trigger_id}` | POST | Public webhook ingestion endpoint |
