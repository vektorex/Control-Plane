# Multi-Tenant Organizations, Teams, Roles & Access Control Architecture (Step 27)

## 1. Architectural Overview & Tenant Hierarchy

The AI Work Layer implements a strict, server-side hierarchical multi-tenant architecture designed to guarantee cryptographic and logical isolation across organizations, teams, workspaces, projects, and resources:

```
User (Authenticated Supabase Identity)
  ↓
Organization (Tenant Boundary & Quota Domain)
  ↓
Membership (Organization Role: Owner, Admin, Member, Viewer)
  ↓
Workspace (Execution & Credential Boundary)
  ↓
Workspace Membership (Workspace Role: Admin, Member, Viewer)
  ↓
Project (Knowledge Context & Toolset Domain: Workspace or Restricted Mode)
  ↓
Project Membership (Project Role: Editor, Viewer)
  ↓
Resources (Tasks, Workflows, Jobs, Events, Connectors, Memory, HITL, Replays, Evaluations)
```

### Hierarchy Constraints
1. **User Identity**: Supabase JWT authentication provides cryptographically verified user identity. Frontend claims are never trusted for authorization.
2. **Organization**: The top-level tenant boundary. Each user belongs to at least one organization (personal organization created automatically on first login).
3. **Workspace**: Encapsulates external credentials, active worker leases, and vector stores. Every workspace belongs to an organization.
4. **Project**: Groups related workloads. Projects operate in either **Workspace Mode** (accessible to all authorized workspace members) or **Restricted Mode** (accessible only to explicitly assigned project members and workspace/org admins).
5. **Resources**: Tasks, workflows, runs, triggers, connectors, memory, jobs, and evaluations inherit tenant context and must never be accessed without parent authorization verification.

---

## 2. Server-Side Authorization Model & Intersection Rule

Authorization decisions are strictly evaluated server-side by the `AuthorizationService` and `PolicyEngine`.

### Effective Permission Resolution
Effective permissions are derived through the strict **mathematical intersection** of applicable role levels:

$$\text{Effective Permissions} = \text{Org Role Permissions} \cap \text{Workspace Role Permissions} \cap \text{Project Role Permissions}$$

**Core Security Rule**: A lower-level role cannot elevate a higher-level restriction. For example:
- An Organization **Viewer** assigned as Workspace **Admin** remains read-only for destructive or execution actions (cannot run workflows or execute connectors).
- An Organization **Member** assigned as Workspace **Viewer** is restricted to read-only within that workspace.

---

## 3. Comprehensive Permission Matrix

| Permission Key | Description | Owner | Admin | Member | Viewer |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `organization.read` | View organization profile and status | ✅ | ✅ | ✅ | ✅ |
| `organization.update` | Edit organization name, slug, settings | ✅ | ✅ | ❌ | ❌ |
| `organization.delete` | Soft-delete / archive organization | ✅ | ❌ | ❌ | ❌ |
| `member.read` | List organization members and roles | ✅ | ✅ | ✅ | ✅ |
| `member.invite` | Send cryptographically signed invitations | ✅ | ✅ | ❌ | ❌ |
| `member.update` | Modify member role or suspension status | ✅ | ✅ | ❌ | ❌ |
| `member.remove` | Remove member from organization | ✅ | ✅ | ❌ | ❌ |
| `workspace.create` | Provision new workspace in organization | ✅ | ✅ | ❌ | ❌ |
| `workspace.read` | View workspace metadata and list | ✅ | ✅ | ✅ | ✅ |
| `workspace.update` | Edit workspace details and settings | ✅ | ✅ | ❌ | ❌ |
| `workspace.delete` | Archive / delete workspace | ✅ | ✅ | ❌ | ❌ |
| `project.create` | Create projects within workspace | ✅ | ✅ | ✅ | ❌ |
| `project.read` | View project metadata | ✅ | ✅ | ✅ | ✅ |
| `project.update` | Update project configuration and access mode | ✅ | ✅ | ✅ | ❌ |
| `project.delete` | Delete project | ✅ | ✅ | ❌ | ❌ |
| `task.read` | View task definitions and status | ✅ | ✅ | ✅ | ✅ |
| `task.create` | Create and define tasks | ✅ | ✅ | ✅ | ❌ |
| `task.update` | Update task specifications | ✅ | ✅ | ✅ | ❌ |
| `task.delete` | Delete tasks | ✅ | ✅ | ❌ | ❌ |
| `task.run` | Dispatch and execute tasks | ✅ | ✅ | ✅ | ❌ |
| `workflow.read` | Inspect workflow pipelines and DAGs | ✅ | ✅ | ✅ | ✅ |
| `workflow.create` | Design workflow pipelines | ✅ | ✅ | ✅ | ❌ |
| `workflow.update` | Modify workflow definitions | ✅ | ✅ | ✅ | ❌ |
| `workflow.delete` | Delete workflows | ✅ | ✅ | ❌ | ❌ |
| `workflow.publish` | Publish workflow versions | ✅ | ✅ | ✅ | ❌ |
| `workflow.run` | Trigger workflow pipeline executions | ✅ | ✅ | ✅ | ❌ |
| `trigger.read` | View webhook and cron triggers | ✅ | ✅ | ✅ | ✅ |
| `trigger.create` | Register new automated triggers | ✅ | ✅ | ✅ | ❌ |
| `trigger.update` | Edit trigger configurations | ✅ | ✅ | ✅ | ❌ |
| `trigger.delete` | Remove triggers | ✅ | ✅ | ❌ | ❌ |
| `trigger.run` | Manually fire or test triggers | ✅ | ✅ | ✅ | ❌ |
| `job.read` | Inspect durable background job states | ✅ | ✅ | ✅ | ✅ |
| `job.cancel` | Cancel in-flight jobs and releases leases | ✅ | ✅ | ✅ | ❌ |
| `job.retry` | Retry failed background jobs | ✅ | ✅ | ✅ | ❌ |
| `connector.read` | Inspect configured connectors | ✅ | ✅ | ✅ | ✅ |
| `connector.configure`| Store or update connector credentials | ✅ | ✅ | ❌ | ❌ |
| `connector.execute` | Invoke connector external actions | ✅ | ✅ | ✅ | ❌ |
| `memory.read` | Read memories and user preferences | ✅ | ✅ | ✅ | ✅ |
| `memory.create` | Create memory items | ✅ | ✅ | ✅ | ❌ |
| `memory.update` | Update memory entries | ✅ | ✅ | ✅ | ❌ |
| `memory.delete` | Delete memory entries | ✅ | ✅ | ❌ | ❌ |
| `evaluation.read` | View evaluation datasets & experiment results | ✅ | ✅ | ✅ | ✅ |
| `evaluation.create` | Create evaluation experiments | ✅ | ✅ | ✅ | ❌ |
| `evaluation.run` | Execute evaluations | ✅ | ✅ | ✅ | ❌ |
| `replay.read` | Inspect recorded execution traces | ✅ | ✅ | ✅ | ✅ |
| `replay.create` | Re-run past execution replays | ✅ | ✅ | ✅ | ❌ |
| `notification.read`| View in-app and delivery notifications | ✅ | ✅ | ✅ | ✅ |
| `notification.configure` | Configure webhook and alert routing | ✅ | ✅ | ❌ | ❌ |
| `webhook.read` | View webhook endpoints | ✅ | ✅ | ✅ | ✅ |
| `webhook.configure` | Generate or rotate webhook secrets | ✅ | ✅ | ❌ | ❌ |
| `approval.read` | Review pending human approval requests | ✅ | ✅ | ✅ | ✅ |
| `approval.respond` | Approve or reject human-in-the-loop requests | ✅ | ✅ | ✅ | ❌ |
| `analytics.read` | View token usage and performance metrics | ✅ | ✅ | ✅ | ❌ |
| `event.read` | Stream and inspect SSE audit events | ✅ | ✅ | ✅ | ✅ |
| `audit.read` | Inspect security audit trails | ✅ | ✅ | ❌ | ❌ |

---

## 4. Cryptographic Invitation Lifecycle

Invitations enable controlled team onboarding with defense-in-depth against credential theft:

1. **Invitation Creation**:
   - The inviter (Owner/Admin) specifies recipient email and assigned role.
   - The backend generates a 256-bit cryptographically secure random token (`secrets.token_urlsafe(32)`).
   - Only the **SHA-256 hash** of the token is stored in the PostgreSQL database (`OrganizationInvitation.token_hash`).
   - The raw token is returned once for transmission via email or link.
2. **Acceptance Verification**:
   - The recipient submits the token to `POST /api/invitations/{token}/accept`.
   - The backend hashes the provided token and performs an atomic lookup.
   - Validation checks: Token exists, unexpired (default 7 days), unrevoked (`revoked_at IS NULL`), and unaccepted (`accepted_at IS NULL`).
   - On success, creates `OrganizationMember(role=inv.role, status='active')` and records `accepted_at`.
3. **Replay & Brute-Force Protection**:
   - Accepting an already accepted token raises `HTTP 400 Bad Request`.
   - Revoked tokens raise `HTTP 400 Bad Request`.
   - Sliding-window rate limiting prevents brute-force token enumeration.

---

## 5. Atomic Ownership Transfer

Primary tenant ownership is safeguarded with transactional consistency:

- **Endpoint**: `POST /api/organizations/{org_id}/transfer-ownership`
- **Validation Rules**:
  - Requesting user must be the current authenticated Owner.
  - Target user must be an existing, active member of the organization.
  - Self-transfer is disallowed.
- **Transaction**:
  - Within an atomic database transaction:
    - Target member's role is updated to `owner`.
    - Previous owner's role is demoted to `admin`.
    - Organization `owner_user_id` is updated.
    - Security audit record `ownership.transferred` is published.

---

## 6. Real-Time SSE & Event Isolation

Event streaming over Server-Sent Events (SSE) from Step 26 enforces tenant isolation:

1. **Stream Scoping**: The client connects to `GET /api/events/stream?workspace_id=...`. The backend validates active workspace membership in the database before initializing the connection.
2. **Immediate Disconnect on Revocation**:
   - Active SSE connections track `(workspace_id, user_id)`.
   - When a member is suspended or removed from an organization or workspace, `EventStreamHub.disconnect_user(user_id)` immediately closes all active sockets for that user.
   - Subsequent event broadcasts are never delivered to unauthorized clients.

---

## 7. Security Hardening & Isolation Protections

- **IDOR Defense**: All resource operations (tasks, projects, workflows, connectors) resolve through the authenticated tenant chain (`User -> Organization -> Workspace -> Project -> Resource`).
- **No Role Tampering**: Role modification checks prohibit non-owners from assigning the Owner role and prevent viewers from updating roles.
- **Header Spoofing Resistance**: While `X-Organization-Id` and `X-Workspace-Id` can be supplied by the frontend for UI context, the backend validates actual database membership for every request.
- **Secret Scrubbing**: Audit logs, invitations, and capability payloads redact tokens, hashes, API keys, and connector credentials.
