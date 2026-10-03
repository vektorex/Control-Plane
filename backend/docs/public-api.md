# Public API, Developer Platform & SDK Layer

The Public API layer turns the AI Work Layer platform into a consumable developer substrate, exposing controlled APIs for external applications while preserving all security, tenant isolation, and governance boundaries.

> **Operational Disclaimer:**
> "The Public API provides controlled programmatic access to the platform. API availability, limits, and capabilities are subject to the platform's configured policies and operational state."

---

## 1. Architecture

```
External Application
        ↓
Public API Gateway (/api/v1/)
        ↓
API Authentication (PublicAPIAuthenticator)
        ↓
API Authorization (PublicAPIAuthorizer + ScopeRegistry)
        ↓
Governance (Step 32 PolicyEngine)
        ↓
Rate / Quota Control (Sliding Window + QuotaService)
        ↓
Existing Application Services
        ↓
AI Gateway / Task Execution / Workflows / Connectors
        ↓
Events / Webhooks / Usage Telemetry
```

The Public API layer is strictly an adapter over existing services, NOT a second execution architecture.

---

## 2. API Authentication & Key Security

- Keys are generated with recognizable environment prefixes:
  - `awl_dev_` (Development)
  - `awl_stg_` (Staging)
  - `awl_prod_` (Production)
- **Plaintext Secret Protection**: Plaintext keys are shown **exactly once** upon creation or rotation. The database persists only a deterministic SHA-256 hash and the non-sensitive prefix (`awl_dev_xxxx`).
- No sensitive IDs, user emails, or timestamps are embedded into keys.
- **Rotation**: Supports zero-downtime rotation where the old credential remains functional until explicit revocation or expiration.

---

## 3. Scopes & Privilege Escalation Guardrails

Every credential is restricted to a fixed registry of permission scopes:
- `tasks:read`, `tasks:run`
- `runs:read`
- `workflows:read`, `workflows:run`
- `artifacts:read`, `artifacts:create`
- `documents:read`
- `memory:read`, `memory:write`
- `knowledge:read`
- `prompts:read`
- `evaluations:read`
- `replays:read`
- `connectors:read`
- `models:read`
- `events:read`
- `usage:read`
- `webhooks:manage`
- `applications:manage`

**Privilege Escalation Protection**: An application or key creator cannot grant scopes exceeding their own effective permissions. Sensitive execution and management scopes require explicit organization administrator status.

---

## 4. Environment & Resource Scope Isolation

- **Environment Isolation**: Credentials created for `development` cannot access `staging` or `production` resources. Cross-environment access is denied with `EnvironmentMismatchError`.
- **Resource Scope**: A key can be restricted to a specific workspace or project. Attempting to access outside resources raises `ResourceScopeViolationError`.
- **Tenant Isolation**: Cross-organization requests are strictly blocked.

---

## 5. Rate Limiting & Quotas

- **Multi-Tier Rate Limiting**: Evaluates sliding-window counters across application, credential, and organization tiers.
- Standard headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.
- Breaches return HTTP 429 with `Retry-After`.
- **Volumetric Quotas**: Limits on requests, task runs, workflow runs, and tokens per minute/hour/day/month.

---

## 6. Idempotency

All public mutation endpoints support the `Idempotency-Key` header:
- Repeated requests with identical payload return the cached response with `Idempotent-Replay: true`.
- Repeated requests with mismatched payloads return HTTP 409 `IdempotencyConflictError`.
- Keys expire automatically after 24 hours.

---

## 7. Webhook Signatures & SSRF Protection

- Webhooks deliver notifications for events: `run.completed`, `run.failed`, `workflow.completed`, `workflow.failed`, `artifact.processed`, `evaluation.completed`, `security.incident.created`, `usage.threshold`, `recovery.failure`.
- Deliveries are signed using HMAC-SHA256 (`X-AWL-Signature: t={timestamp},v1={hash}`).
- **SSRF Prevention**: Webhook destinations must use HTTPS (except localhost in development). Private IP ranges (RFC 1918), AWS/cloud metadata IPs (`169.254.169.254`), and loopback addresses are blocked.

---

## 8. Official SDKs

- **JavaScript SDK**: `@ai-work-layer/sdk` (ESM/CJS, plain JavaScript, zero-dependencies).
- **Python SDK**: `ai_work_layer` (Python 3.9+, synchronous and streaming support).
- Both SDKs feature built-in webhook signature verification utilities and structured error handling.
