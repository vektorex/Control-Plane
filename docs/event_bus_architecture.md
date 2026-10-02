# Step 26: Unified Event Bus & Real-Time Execution Updates Architecture

## 1. Overview & System Topology

The **Unified Event Bus & Real-Time Execution Updates layer** serves as the authoritative, durable event backbone for the AI Work Layer. It unifies state transitions across long-running background jobs, workflows, human-in-the-loop approvals, triggers, evaluation experiments, historical replays, document indexing, and connector syncs into a single, transactional event store backed by **PostgreSQL**.

Events are safely persisted before distribution and broadcast to:
1. **Server-Sent Events (SSE)** for immediate, real-time reactive UI updates in the browser.
2. **Notification Subsystem** for in-app alert badges and external deliveries (Webhooks/Email).
3. **Observability & Telemetry** for distributed trace correlation and audit logging.
4. **Future consumers** via isolated, extensible consumer plugins.

```
Existing Service (Workflow / Job / Trigger / HITL / etc.)
        ↓
EventPublisher
        ↓
PostgreSQL Event Store (Transactionally persisted with state change)
        ↓
EventDispatcher (Failure-isolated dispatch)
        ├── RealtimeEventConsumer → SSEConnectionManager → Browser EventSource
        ├── NotificationEventConsumer → Step 25 NotificationService
        ├── ObservabilityEventConsumer → Step 14 Telemetry & Distributed Traces
        └── AuditEventConsumer → Audit Trail
```

---

## 2. Event Contract Specification

Every event adheres to a strict, standardized contract:

```json
{
  "id": "e5b871c8-2bb1-419b-a320-1a76f28b7e29",
  "type": "workflow.completed",
  "timestamp": "2026-10-03T00:30:00.123456+00:00",
  "workspace_id": "a3bb189e-8bf9-3888-9912-ace4e6543002",
  "project_id": "b1c2d3e4-f5a6-7890-bcde-f12345678901",
  "actor": {
    "type": "system",
    "id": null
  },
  "aggregate": {
    "type": "workflow",
    "id": "wf_run_9823412"
  },
  "parent_event_id": "c1a2b3d4-e5f6-7890-abcd-ef0123456789",
  "correlation_id": "corr_wf_batch_001",
  "causation_id": "evt_step_transform_completed",
  "sequence_number": 4,
  "data": {
    "title": "Workflow Ingestion Pipeline Completed",
    "status": "completed",
    "duration_ms": 1420,
    "steps_count": 3
  },
  "metadata": {
    "environment": "production"
  }
}
```

### Security Boundary & Sanitization
Before an event is persisted to PostgreSQL or emitted over SSE:
- Any keys matching sensitive terms (`api_key`, `token`, `secret`, `password`, `authorization`, `cookie`, `credential`, `database_url`) are automatically masked as `"[REDACTED]"`.
- Internal model thoughts, `chain_of_thought`, and `hidden_prompt` are scrubbed.
- Oversized individual string values exceeding 8 KB are truncated with `"... [TRUNCATED]"`.
- Total payload byte size is constrained to `EVENT_MAX_PAYLOAD_BYTES` (default 64 KB).

---

## 3. Supported Event Types (Centralized Registry)

The system registers 38+ core event types in `EventRegistry`:

| Category | Event Type | Description |
|---|---|---|
| **JOB** | `job.created` | Background job persisted |
| | `job.queued` | Job enqueued for worker claiming |
| | `job.started` | Job claimed by worker; execution begun |
| | `job.progress` | Incremental progress percentage or status message |
| | `job.retrying` | Transient error encountered; backoff scheduled |
| | `job.cancel_requested` | Cancellation signal issued |
| | `job.cancelled` | Job cancelled and worker lease released |
| | `job.completed` | Job succeeded |
| | `job.failed` | Job failed permanently |
| | `job.recovered` | Job recovered from expired worker lease |
| **WORKFLOW** | `workflow.started` | Workflow execution started |
| | `workflow.step_started` | Individual workflow step started |
| | `workflow.step_completed` | Workflow step finished |
| | `workflow.waiting_for_approval` | Workflow paused for human decision |
| | `workflow.resumed` | Workflow resumed after decision |
| | `workflow.completed` | Workflow finished successfully |
| | `workflow.failed` | Workflow terminated with error |
| **TRIGGER** | `trigger.created` | Trigger configured |
| | `trigger.updated` | Trigger settings changed |
| | `trigger.paused` / `resumed` | Automation schedule toggled |
| | `trigger.fired` | Trigger evaluated positive and fired |
| | `trigger.completed` / `failed` | Trigger dispatch result |
| **HITL** | `approval.requested` | Human intervention requested |
| | `approval.approved` / `rejected` | Review decision recorded |
| | `approval.expired` | Review window timed out |
| **NOTIFICATION** | `notification.created` | In-app notification available |
| | `notification.delivery_started` | External webhook/email dispatch initiated |
| | `notification.delivery_completed` | External transmission succeeded |
| | `notification.delivery_failed` | External delivery failed |
| **SYSTEM** | `system.warning` | Capacity or threshold warning |
| | `system.error` | Critical system error |

---

## 4. Ordering, Correlation & Idempotency

### Monotonic Aggregate Sequencing
Within any domain aggregate `(workspace_id, aggregate_type, aggregate_id)`:
- Sequence numbers are strictly incrementing integers (`sequence_number = 1, 2, 3, ...`).
- Global ordering across independent workspaces is intentionally not required, ensuring high-throughput partition isolation.

### Distributed Tracing & Causation
- `correlation_id`: Propagated from initial user request or root workflow run through all child jobs, model calls, and evaluations.
- `causation_id`: Points to the specific previous event that triggered the current operation.

### Idempotency Deduplication
- Database unique constraint: `(workspace_id, idempotency_key)`.
- If a worker retries an operation after a timeout, the re-published event returns the existing event record with `is_new=False` without creating duplicate events or repeating consumer side-effects.

---

## 5. Server-Sent Events (SSE) Protocol & Reconnect

### Endpoint
```http
GET /api/events/stream?workspace_id={id}&event_type=job.*
```

### Protocol Headers
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
```

### Frame Formatting
```
event: job.progress
id: 550e8400-e29b-41d4-a716-446655440000
data: {"id":"550e8400...","type":"job.progress",...}

```

### Heartbeats
To prevent intermediate proxies or reverse proxies from dropping idle connections:
```
event: heartbeat
data: {}

```
Emitted every 15 seconds without polluting the database event store.

### Reconnection with `Last-Event-ID`
When a browser disconnects and reconnects:
1. The browser passes `Last-Event-ID` in the request header (or `?after=<id>` query parameter).
2. The server queries the PostgreSQL event store for up to 50 missed events (`created_at > after.created_at`) and flushes them immediately before resuming the real-time stream.

---

## 6. Backpressure & Multi-Worker Architecture

### Backpressure Handling
- Each active SSE client connection possesses a bounded async queue (`SSE_CLIENT_BUFFER_SIZE = 100`).
- If a slow client stalls or network degrades and the buffer overflows, the connection is closed safely (`is_active = False`) to prevent memory leaks in application workers.

### Multi-Worker Synchronization
- PostgreSQL is the durable source of truth.
- When multiple FastAPI worker processes run, newly persisted events can be replayed by any worker using `Last-Event-ID`.
- Client-side event clients automatically fallback to bounded polling if an SSE stream drops.

---

## 7. Frontend Integration & Polling Fallback

The client library (`@/lib/events`) provides:
- `useEventStream`: React hook managing real-time connections, event filtering, and unmount cleanup.
- **Adaptive Polling Fallback**:
  - When SSE is **Connected** (`LIVE SSE`): Background polling is suppressed, saving server bandwidth and database IO.
  - When SSE is **Disconnected / Error**: Reconnects with exponential backoff and jitter.
  - If 5 consecutive reconnection attempts fail: Transitions to **Fallback Mode** (`POLLING FALLBACK`), activating bounded interval polling until SSE connectivity is restored.

---

## 8. Security & Multi-Tenant Authorization

1. **Workspace Boundary Enforcement**: The stream endpoint strictly validates that the requesting user belongs to the requested workspace. Attempting to stream another workspace (`?workspace_id=other`) returns HTTP 403 Forbidden.
2. **Actor Sanitization**: Actor types are restricted to validated system roles (`user`, `system`, `worker`, `connector`, `scheduler`).
3. **No Dynamic Code Handlers**: Event consumers are compile-time registered singletons. Client input or model output cannot register dynamic or arbitrary event listeners.
4. **Filter Defense**: Filter patterns are validated against strict regex (`^[a-z0-9_]+(\.\*|\.[a-z0-9_]+)?$`) preventing SQL injection or regex DoS.
