# Step 25: Notifications & External Delivery Layer Architecture

## 1. Overview & Architecture

The **Notifications & External Delivery Layer** is a production-grade, multi-tenant notification system that unifies system events, workflow completions, approvals (HITL), job failures, evaluation regressions, and connector updates into a secure, asynchronous delivery pipeline.

All external deliveries (Webhooks, Email) are processed **asynchronously** via the durable background Job Queue implemented in **STEP 24** (`JobType.NOTIFICATION_DELIVERY`), ensuring that fast HTTP request lifecycles and workflow executions are never blocked by external network latency or downstream endpoint failures.

```
Existing System Event (Workflow / HITL / Job / Trigger / etc.)
        ↓
NotificationEventBus.publish(...)
        ↓
NotificationService (Event validation & DB record creation)
        ↓
NotificationPolicyEngine & RecipientResolver
        ↓
NotificationPreferenceService (User / Workspace / Mandatory rules)
        ↓
NotificationDelivery (Status: queued)
        ↓
JobService.enqueue_job(job_type="notification_delivery")
        ↓
JobWorker (STEP 24 PostgreSQL durable worker)
        ↓
NotificationDeliveryJobHandler → DeliveryDispatcher.execute_delivery(...)
        ↓
DeliveryChannel (In-App / Webhook / Email)
        ↓
DeliveryResult (Success / Transient Retry / Permanent Failure)
        ↓
Audit Log & Observability (OpenTelemetry / Step 14 Metrics)
```

---

## 2. Supported Event Types (17 Core Events)

The system defines 17 first-class events registered in `NotificationRegistry`:

| Event Type | Default Severity | Category | Description |
|---|---|---|---|
| `workflow.completed` | `success` | Workflow | Workflow run executed to successful completion |
| `workflow.failed` | `error` | Workflow | Workflow execution failed or timed out |
| `workflow.waiting_for_approval` | `warning` | HITL | Workflow execution paused pending human decision |
| `trigger.completed` | `info` | Automation | Automation trigger fired and dispatched successfully |
| `trigger.failed` | `error` | Automation | Automation trigger failed evaluation or execution |
| `job.completed` | `info` | Jobs | Asynchronous durable background job succeeded |
| `job.failed` | `error` | Jobs | Durable background job reached permanent failure |
| `job.retrying` | `warning` | Jobs | Durable job encountered transient error; retry queued |
| `document.processing_completed` | `success` | Document | Document extraction & chunking completed |
| `document.processing_failed` | `error` | Document | Document extraction or ingestion error |
| `evaluation.completed` | `info` | Evaluation | Benchmark experiment run completed |
| `evaluation.regression_detected` | `warning` | Evaluation | Evaluation metric regressed beyond baseline threshold |
| `replay.completed` | `info` | Replay | Workflow execution historical replay finished |
| `replay.failed` | `error` | Replay | Replay divergence or execution failure |
| `connector.completed` | `info` | Connectors | External connector sync completed |
| `connector.failed` | `error` | Connectors | External connector synchronization failed |
| `system.warning` | `warning` | System | Critical system threshold or security notification |

---

## 3. Delivery Channels

### 3.1 `in_app`
- **Behavior**: Persisted directly in the database (`notifications` table). Available immediately to authenticated users via REST endpoints (`/api/notifications`, `/api/notifications/unread-count`).
- **Supports Rich Content**: Yes (formatted markdown body, structured metadata).
- **Mandatory Enforcement**: Security notifications (`system.warning`) and human-in-the-loop approvals (`workflow.waiting_for_approval`) **cannot** be disabled for in-app delivery.

### 3.2 `webhook`
- **Behavior**: Dispatched as an HTTPS POST request signed with HMAC-SHA256.
- **SSRF Protection**: Destination URLs are resolved and validated against loopback, private IPv4/IPv6, link-local, and cloud metadata IPs (`169.254.169.254`).
- **Redirects**: HTTP redirect chains are rejected (`follow_redirects=False`) to prevent open-redirect SSRF bypasses.

### 3.3 `email`
- **Behavior**: Provider-agnostic abstraction (`EmailDeliveryProvider`). Configured via environment variables:
  - `EMAIL_PROVIDER`: e.g. `smtp`, `sendgrid`, `resend`, `mock`
  - `EMAIL_FROM`: sender email address
  - `EMAIL_API_KEY`: API key or credentials
- **Unconfigured State**: If no email provider is configured, the channel reports `ChannelNotConfiguredError` (503) rather than faking successful delivery.

---

## 4. Webhook Authentication & Deterministic HMAC Signing

Every outbound webhook delivery includes 3 standard HTTP headers:

```http
X-AI-Work-Event: workflow.completed
X-AI-Work-Timestamp: 1727800000
X-AI-Work-Signature: sha256=a1b2c3d4e5f6...
```

### Signature Construction
1. Construct the signing string: `{timestamp}.{payload_json}` where `payload_json` is the minified UTF-8 JSON payload.
2. Compute the HMAC using the endpoint's secret and `SHA-256`:
   ```python
   signing_payload = f"{timestamp}.{payload_json}".encode("utf-8")
   signature = hmac.new(secret.encode("utf-8"), signing_payload, hashlib.sha256).hexdigest()
   header_value = f"sha256={signature}"
   ```
3. Timestamp anti-replay: Receivers should reject requests where `abs(now - timestamp) > 300` seconds.

### Example Webhook Receiver (Python / FastAPI)

```python
import hmac
import hashlib
import time
from fastapi import FastAPI, Request, HTTPException, Header

app = FastAPI()
WEBHOOK_SECRET = "your_webhook_endpoint_secret"

@app.post("/webhook-receiver")
async def receive_webhook(
    request: Request,
    x_ai_work_event: str = Header(..., alias="X-AI-Work-Event"),
    x_ai_work_timestamp: str = Header(..., alias="X-AI-Work-Timestamp"),
    x_ai_work_signature: str = Header(..., alias="X-AI-Work-Signature"),
):
    # 1. Anti-replay verification (5-minute tolerance)
    now = int(time.time())
    if abs(now - int(x_ai_work_timestamp)) > 300:
        raise HTTPException(status_code=400, detail="Timestamp out of tolerance window")

    # 2. Reconstruct signature
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")
    signing_payload = f"{x_ai_work_timestamp}.{body_str}".encode("utf-8")
    expected_hex = hmac.new(WEBHOOK_SECRET.encode("utf-8"), signing_payload, hashlib.sha256).hexdigest()
    expected_sig = f"sha256={expected_hex}"

    # 3. Constant-time signature comparison
    if not hmac.compare_digest(x_ai_work_signature, expected_sig):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()
    print(f"Verified event {x_ai_work_event} from workspace {payload['workspace_id']}")
    return {"status": "accepted"}
```

---

## 5. Webhook Payload Format & Sanitization

Outbound payloads adhere to a deterministic, scrubbed schema:

```json
{
  "id": "evt_9b1deb4d3b7d4e89",
  "type": "workflow.completed",
  "timestamp": "1727800000",
  "workspace_id": "a3bb189e-8bf9-3888-9912-ace4e6543002",
  "source": {
    "type": "workflow_run",
    "id": "run_01j7..."
  },
  "data": {
    "title": "Workflow 'Data Extraction' Completed",
    "body": "Workflow run run_01j7... finished successfully.",
    "execution_time_ms": 1420
  }
}
```

### Sanitization Rules (`NotificationSanitizer`)
- Automatically scrubs any field matching sensitive keys (`api_key`, `token`, `password`, `secret`, `authorization`, `private_key`, `credential`) with `"[REDACTED]"`.
- Truncates oversized string fields (> 16 KB) with `"[TRUNCATED]"` to prevent downstream buffer overflow attacks.
- Strips internal execution internals, raw prompt chains, and model thoughts.

---

## 6. SSRF Protection (`SSRFValidator`)

All outbound webhook destinations must pass strict validation before saving and prior to each transmission:

1. **Protocol Check**: Only `https://` is allowed (or `http://` in local development mode). `file://`, `ftp://`, `gopher://` are rejected.
2. **DNS Resolution**: Resolves all A/AAAA records for the hostname.
3. **Forbidden Networks**: Rejects any address falling into:
   - `127.0.0.0/8` (IPv4 Loopback)
   - `::1/128` (IPv6 Loopback)
   - `10.0.0.0/8` (Private RFC1918)
   - `172.16.0.0/12` (Private RFC1918)
   - `192.168.0.0/16` (Private RFC1918)
   - `169.254.0.0/16` (IPv4 Link-Local & AWS/GCP Metadata `169.254.169.254`)
   - `fe80::/10` (IPv6 Link-Local)
   - `fc00::/7` (IPv6 Unique Local)
4. **Follow Redirects Disabled**: Set to `follow_redirects=False` to prevent DNS rebinding or redirect-based network infiltration.

---

## 7. Retry Behavior & Error Handling

Deliveries follow the resilient failure-handling semantics established in Step 24:

### Error Classification
- **Transient Failures (Retried)**:
  - Network timeouts & connection resets (`ConnectTimeout`, `ReadTimeout`)
  - HTTP `429 Too Many Requests`
  - HTTP `5xx Internal Server Error / Bad Gateway / Gateway Timeout`
- **Permanent Failures (Not Retried)**:
  - HTTP `400 Bad Request`
  - HTTP `401 Unauthorized` / `403 Forbidden`
  - HTTP `404 Not Found`
  - SSRF validation failure (`SSRFSecurityError`)
  - Disabled or deleted endpoint

### Exponential Backoff with Jitter
- Formula: `min(max_delay, base_delay * (2 ** attempt)) * uniform(0.8, 1.2)`
- Default attempts: 3 (configurable up to 5)

---

## 8. Delivery Idempotency

1. **Database-Level Idempotency**:
   - `NotificationDelivery` checks `(notification_id, channel, destination)` before queueing to ensure no duplicate active records exist for a single notification event.
2. **Webhook Deduplication**:
   - `(event_id, endpoint_id)` tracking guarantees that concurrent event dispatches or re-evaluations do not emit duplicate webhook HTTP POST requests.

---

## 9. Notification Preferences & Recipient Resolution

### Resolution Hierarchy
When an event occurs, recipient preferences are resolved in order:
1. Explicit User Preference (`user_id + event_type + channel`)
2. User Global Preference (`user_id + * + channel`)
3. Workspace Preference (`workspace_id + event_type + channel`)
4. Workspace Global Preference (`workspace_id + * + channel`)
5. System Default:
   - `in_app`: **Enabled** by default
   - `webhook`: **Enabled** if endpoint is active and subscribed
   - `email`: **Disabled** until explicitly enabled

### Recipient Authority
`RecipientResolver` resolves recipients exclusively through verified system relationships:
- Task or workflow run owner
- Project members
- Workspace owner
- Model outputs **cannot** inject arbitrary email addresses or user IDs into delivery destinations.

---

## 10. Rate Limiting

Multi-tenant protection via sliding-window limiter (`NotificationRateLimiter`):
- `NOTIFICATION_MAX_DELIVERIES_PER_MINUTE`: 120 per workspace
- `WEBHOOK_MAX_DELIVERIES_PER_MINUTE`: 60 per workspace
- `EMAIL_MAX_DELIVERIES_PER_MINUTE`: 30 per workspace

Workspaces exceeding quotas receive HTTP 429 (`RateLimitExceededError`) and excess dispatches are throttled.

---

## 11. Security Model Summary

- **Secret Masking**: Webhook secrets are returned **only once** upon creation or rotation (`/rotate-secret`). They are never exposed in listing or detail APIs.
- **Multi-Tenant Isolation**: All database queries strictly scope by `workspace_id` from the verified session header (`X-Workspace-Id`). Cross-workspace access returns HTTP 404.
- **No Arbitrary Code Execution**: Templates use strict regex variable lookup (`{{var.name}}`). Code evaluation like `{{7*7}}` or `{{__import__('os')}}` is strictly ignored and rendered as literal text.
- **Safe Test Delivery**: `POST /api/webhooks/{id}/test` dispatches only synthetic fixture data; real execution logs or user data are never transmitted during testing.
