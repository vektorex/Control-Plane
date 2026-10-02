# STEP 24: Durable Background Job System Architecture

## 1. Overview & Purpose

The **AI Work Layer Durable Background Job System** decouples long-running AI operations (multi-step workflow executions, batch document chunking and embeddings, trigger event cascades, evaluation lab experiments, recorded execution replays, and external connector operations) from the synchronous lifecycle of incoming HTTP requests.

By shifting execution to a durable, transactional background queue, operations are resilient against HTTP client timeouts, connection drops, worker node failures, and API rate-limiting spikes.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        AI Work Layer Architecture                      │
└────────────────────────────────────────────────────────────────────────┘

HTTP / API / Trigger Webhook
         │
         ▼
    JobService (Workspace Isolation & Idempotency Check)
         │
         ▼
 PostgreSQL Durable Queue (jobs & job_events table with SKIP LOCKED)
         │
         ▼
  JobWorker Pool (Bounded Concurrency & Lease Heartbeats)
         │
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     Authoritative Business Handlers                   │
├───────────────────┬───────────────────┬────────────────────────────────┤
│  WorkflowExecutor │  TriggerExecutor  │  Document Ingestion Pipeline   │
├───────────────────┼───────────────────┼────────────────────────────────┤
│ ExperimentService │   ReplayRunner    │       ConnectorExecutor        │
└───────────────────┴───────────────────┴────────────────────────────────┘
         │
         ▼
Telemetry / Tracer / Cost & Latency Metrics / HITL Review Checkpoints
         │
         ▼
Job Completion & Event Persistence
```

---

## 2. Why PostgreSQL is Used as the Durable Queue

In accordance with strict project constraints, no external broker services (Redis, Celery, RabbitMQ, Kafka, SQS, or paid cloud queues) were introduced. PostgreSQL is used as the durable queue for several key reasons:

1. **Transactional Atomicity (ACID):** Enqueueing a job can occur in the exact same database transaction as the entity state change (e.g. creating a `TriggerRun`, saving a `Document`, or initiating a `WorkflowRun`), completely eliminating dual-write race conditions.
2. **Zero Additional Infrastructure Overhead:** Development, testing, and deployment share a single unified datastore without requiring external broker clustering or state synchronization.
3. **Robust Atomic Locking:** Modern PostgreSQL supports `SELECT ... FOR UPDATE SKIP LOCKED`, which allows multiple concurrent workers to claim distinct queued jobs without contention or lock blocking.
4. **Permanent Audit & Event History:** Retaining `jobs` and `job_events` in the relational database provides rich, queryable SaaS operations metrics and audit timelines.

---

## 3. Atomic Job Claiming & Lease Model

### Claiming Mechanism
A worker claims queued or retrying jobs using atomic row locking:
```sql
SELECT * FROM jobs
WHERE status IN ('queued', 'retrying')
  AND available_at <= NOW()
ORDER BY 
  CASE 
    WHEN priority = 'high' THEN 1 
    WHEN priority = 'normal' THEN 2 
    ELSE 3 
  END, 
  created_at ASC
LIMIT :limit
FOR UPDATE SKIP LOCKED;
```
Once locked, the worker atomically transitions the job to `running` while assigning:
- `lease_owner`: Unique worker hostname and process identifier (`worker_<host>_<pid>_<uuid>`).
- `lease_expires_at`: `NOW() + JOB_LEASE_SECONDS` (default: 300 seconds).
- `heartbeat_at`: `NOW()`.
- `started_at`: `NOW()`.
- `attempts`: `attempts + 1`.

### Heartbeat Renewal
While an asynchronous handler runs, a background heartbeat task periodically updates `lease_expires_at` and `heartbeat_at` every `JOB_HEARTBEAT_SECONDS` (default: 30 seconds).

### Worker Crash Recovery
If a worker crashes, loses power, or suffers an unhandled network partition, its heartbeat ceases:
1. `lease_expires_at` lapses into the past (`lease_expires_at < NOW()`).
2. The `JobLeaseManager` queries all jobs in status `running` with expired leases.
3. If `attempts < max_attempts`, the job is automatically recovered to `retrying` (or `queued`) with an exponential backoff delay.
4. If `attempts >= max_attempts`, the job is marked `failed` with error code `LEASE_EXPIRED_WORKER_CRASHED`.
5. **No job is ever permanently trapped in a running state.**

---

## 4. Retry System & Error Classification

Errors raised during job execution are categorized by `JobRetryPolicy`:

| Classification | Examples | Action |
|---|---|---|
| **Transient** | `503 Service Unavailable`, `429 Rate Limited`, connection resets, provider timeouts | Eligible for retry with jittered exponential backoff |
| **Permanent** | Schema validation error, invalid input, malformed workflow | Immediate transition to `failed` |
| **Policy Blocked** | Secret token in payload, malicious token, destructive command | Immediate transition to `failed` |
| **Authorization Failure** | Connector credentials revoked, invalid API key, workspace permission denied | Immediate transition to `failed` |
| **Cancelled** | Cooperative cancellation requested by user | Transition to `cancelled` |

### Bounded Exponential Backoff with Jitter
For transient errors:
$$\text{delay} = \min(\text{base} \times 2^{\text{attempt} - 1} + \text{jitter}, \text{max\_delay})$$
- Default base delay: 5.0 seconds
- Default max delay: 300.0 seconds
- Jitter: Uniform random float between 0.0 and 1.5 seconds to prevent thundering herd collisions.

---

## 5. Workspace Isolation & Idempotency

### Workspace Multi-Tenant Fairness
- Every job record belongs strictly to a `workspace_id`.
- Every API endpoint (`GET /api/jobs`, `POST /api/jobs/{id}/cancel`, `POST /api/jobs/{id}/retry`) verifies workspace ownership.
- Concurrency limiting: `JobPolicyEngine` ensures no single workspace exceeds `MAX_WORKSPACE_RUNNING_JOBS` (default: 20 concurrent active jobs), preventing one tenant from starving the queue.

### Idempotency Protection
To protect against network retries and duplicate webhook deliveries:
- Callers may provide an `idempotency_key`.
- `JobService` checks for existing jobs with the tuple `(workspace_id, idempotency_key)`.
- If a match is found, the existing `JobResponse` is returned immediately with `is_newly_created = False`. No duplicate job is enqueued.

---

## 6. Cooperative Cancellation & Checkpoints

Cancellation is cooperative and safe:
1. Client issues `POST /api/jobs/{job_id}/cancel`.
2. If the job is `queued` or `retrying`, it transitions immediately to `cancelled` with `cancelled_at = NOW()`.
3. If the job is `running`, an `asyncio.Event` cancellation token is signaled for that specific job.
4. The executing `JobHandler` inspects `cancellation_token.is_set()` before dispatching side effects or heavy AI computation steps.
5. If cancelled, execution stops cleanly at the checkpoint, preventing downstream tool invocations or irreversible side effects.

---

## 7. Security & Payload Sanitization

- **Untrusted Input:** Job payloads are treated as untrusted data.
- **Forbidden Execution Tokens:** `JobPolicyEngine.validate_payload_safety` recursively scans dictionaries and lists for code execution keys (`eval`, `exec`, `__import__`, `subprocess`, `popen`, `system`, `bytecode`). Any match immediately raises `JobValidationError`.
- **Secret & Credential Sanitization:** Payloads are inspected for raw secret keys (`api_key`, `secret_key`, `access_token`, `client_secret`) and bearer tokens. Sensitive credentials must reside in the secure Credential/Secret Store, never in raw job payloads.
- **Fixed Registry:** Only registered handlers in `JobHandlerRegistry` may execute. Arbitrary Python function paths or serialized code expressions are strictly prohibited.

---

## 8. Scaling Limitations & Future Replacement Strategy

### Current PostgreSQL Queue Limits
- **Throughput:** PostgreSQL row locking with `SKIP LOCKED` comfortably handles **1,000 to 5,000 jobs per second** with sub-millisecond lock acquisition on modern database hardware.
- **Table Bloat:** High-throughput job completion creates dead rows; standard PostgreSQL autovacuum settings are configured to maintain indexes.

### Zero-Disruption Future Replacement Strategy
The job system was designed with clean architectural boundaries:
- `JobService` interacts solely with `JobRepository` and `JobQueue`.
- The `JobQueue` class encapsulates queue claiming, priority ordering, and atomic state transitions.
- If system load eventually exceeds 10,000+ jobs/sec, `JobQueue` can be replaced with a Redis Streams, Celery, or Kafka queue adapter without altering any of the business handlers (`WorkflowRunJobHandler`, `TriggerRunJobHandler`, `DocumentProcessingJobHandler`, etc.) or the frontend SaaS Job Center.
