# Step 39: Multi-User Collaboration, Shared AI Workspaces & Real-Time Co-Execution Layer

> **MANDATORY ARCHITECTURAL PRINCIPLE**
> *"Collaboration provides shared application state and realtime coordination. It does not replace authorization, governance, human approval, or the underlying execution systems."*

---

## 1. Overview & Architecture

The **Multi-User Collaboration & Real-Time Co-Execution Layer** enables multiple authorized humans to work alongside AI on the same tasks, workflows, documents, artifacts, security investigations, evaluation datasets, and recovery exercises.

All authoritative state resides in PostgreSQL. Real-time updates reuse the existing Step 26 Event Bus and Server-Sent Events (SSE) infrastructure without external message brokers (no Redis, Kafka, or WebSocket brokers).

```
   Human A ──┐
   Human B ──┼──> Shared Workspace State (PostgreSQL)
   Human C ──┤           │
   AI Run  ──┘           ▼
                  Collaboration Service
                         │
                         ▼
                    Event Store
                         │
                         ▼
                        SSE
                         │
                         ▼
             Authorized Connected Clients
```

---

## 2. Collaboration Sessions & Resources

A `CollaborationSession` represents a bounded real-time collaboration context. It attaches to an underlying resource without replacing or altering the authoritative data model of that resource.

Supported Resource Types:
- `task`: Orchestrated task runs
- `run`: Execution traces
- `workflow` & `workflow_version`: Workflow authoring (drafts editable; published versions immutable)
- `document` & `artifact`: Shared reviews, highlights, and annotations
- `evaluation`: Dataset cases and regression reviews
- `replay`: Execution replay and trace debugging
- `security_incident`: Security investigation war rooms
- `recovery_exercise`: Disaster recovery exercises
- `marketplace_package`: Community package reviews
- `knowledge_graph`: Graph entities, proposals, and conflicts

---

## 3. Participants & Presence Tracking

### Participant Roles
- `owner`: Session management, decision recording, full editing, run dispatch
- `editor`: Commenting, annotating, state editing, task execution
- `reviewer`: Commenting, annotating, recording review decisions/approvals
- `viewer`: Read-only access to comments, presence, and live execution streams

*Note: Collaboration participant roles are additive and cannot override organization or workspace RBAC (Step 27).*

### Ephemeral Presence
- Lightweight heartbeats with status transitions (`active`, `idle`, `away`, `offline`)
- Automatic TTL expiration after 90 seconds of inactivity
- Sanitized cursor/context tracking; no raw keystrokes or sensitive client inputs are stored
- Rate-limited presence broadcasts to avoid event storms

---

## 4. Discussion, Mentions & Annotations

- **Threaded Comments**: Sanitized markdown discussions with nested replies and audit-preserving soft deletion (`deleted_at`).
- **@Mentions**: Validated against tenant workspace boundaries to prevent private membership enumeration. Mentions dispatch Step 25 notifications.
- **Targeted Annotations**: Targeted anchors for document parts, workflow steps, image regions, table cells, and graph nodes.
- **Actionable Assignments**: Delegation of review, approval, execution, and investigation duties with due dates and statuses (`pending`, `accepted`, `completed`, `cancelled`).

---

## 5. Human + AI Co-Execution & Trust Hierarchy

Collaboration sessions can initiate and inspect AI executions using the platform's existing `TaskExecutionService` and `WorkflowExecutor`.

### Instruction Trust Hierarchy
To prevent prompt injection and unauthorized command execution:
1. **System Security Policies**
2. **Governance Policies & Budget Limits**
3. **Organization / Workspace Project Policies**
4. **Explicit Authorized Task Configuration**
5. **Authorized Human Instructions**
6. **Contextual Comments & Annotations (Supplemental Context Only)**
7. **External Untrusted Data**

*Rules:*
- Comments and annotations are treated as supplemental context and never override authoritative task instructions.
- AI suggestions are explicitly marked (`author_type = "ai"`).
- **AI cannot approve its own work**, and AI suggestions do not fulfill HITL approval requirements.

---

## 6. Optimistic Concurrency & Merge Safety

- Every collaborative state update requires an `expected_version`.
- If `expected_version` does not match the authoritative server version, the server detects a version mismatch, logs a `CollaborationConflict`, and returns **HTTP 409 Conflict**.
- **Merge Safety**: Governance policies, security rules, credentials, RBAC definitions, and published immutable workflow packages **cannot be auto-merged**. Safe metadata may be reconciled through explicit human resolution strategies (`keep_current`, `apply_changes`, `manual_merge`).
- Ephemeral advisory locks (`CollaborationLock`) may be acquired with short TTLs (default 60s) for high-contention resources.

---

## 7. Real-Time SSE Stream Integration

Live collaboration updates are streamed over HTTP using Server-Sent Events (`GET /api/collaboration/sessions/{id}/events`):
- Uses standard `Last-Event-ID` header for seamless auto-reconnect without dropped events.
- Tenant-scoped filtering ensures events are broadcast only to authorized participants within the same organization and workspace.

Event Types:
- `collaboration.session.created`
- `collaboration.participant.joined`
- `collaboration.participant.left`
- `collaboration.presence.updated`
- `collaboration.comment.created`
- `collaboration.comment.updated`
- `collaboration.comment.deleted`
- `collaboration.mention.created`
- `collaboration.assignment.created`
- `collaboration.assignment.updated`
- `collaboration.annotation.created`
- `collaboration.annotation.updated`
- `collaboration.decision.created`
- `collaboration.resource.updated`
- `collaboration.conflict.detected`
- `collaboration.run.started`
- `collaboration.run.updated`
- `collaboration.run.completed`
- `collaboration.run.failed`

---

## 8. Public API & SDK Layer

### Public API Endpoints (`/api/v1/collaboration/...`)
- `POST /api/v1/collaboration/sessions` (scope: `collaboration:write`)
- `GET /api/v1/collaboration/sessions` (scope: `collaboration:read`)
- `GET /api/v1/collaboration/sessions/{id}` (scope: `collaboration:read`)
- `POST /api/v1/collaboration/sessions/{id}/comments` (scope: `collaboration:write`)
- `GET /api/v1/collaboration/sessions/{id}/comments` (scope: `collaboration:read`)
- `GET /api/v1/collaboration/sessions/{id}/events` (scope: `collaboration:read`)
- `POST /api/v1/collaboration/sessions/{id}/assignments` (scope: `collaboration:write`)
- `GET /api/v1/collaboration/sessions/{id}/assignments` (scope: `collaboration:read`)

### JavaScript SDK
```javascript
import { AIWorkLayerClient } from "@aiworklayer/sdk";

const client = new AIWorkLayerClient({ apiKey: "awl_key_..." });

// Create collaboration session
const session = await client.collaboration.sessions.create({
  resource_type: "task",
  resource_id: "task-quarterly-analysis",
});

// Post comment
await client.collaboration.sessions.comments.create(session.id, {
  body: "Please review the updated retrieval parameters.",
});

// Stream real-time events
const events = await client.collaboration.sessions.events(session.id, (event) => {
  console.log("Realtime event received:", event);
});
```

### Python SDK
```python
from ai_work_layer import Client

client = Client(api_key="awl_key_...")

# Create collaboration session
session = client.collaboration.sessions.create(
    resource_type="workflow",
    resource_id="wf-customer-support-v2",
)

# Add comment
client.collaboration.sessions.comments.create(
    session_id=session["id"],
    body="Validated Step 3 against budget constraints.",
)

# Stream live SSE events
for event_line in client.collaboration.sessions.events(session["id"]):
    print("SSE line:", event_line)
```
