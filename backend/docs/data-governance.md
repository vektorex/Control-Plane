# Step 33: Data Governance, Privacy & Compliance Evidence Layer

> **DISCLAIMER:**
> **This system provides technical data-governance and privacy controls. It does not by itself establish legal or regulatory compliance.** Compliance certifications (GDPR, HIPAA, SOC 2, CCPA, etc.) require institutional policies, administrative safeguards, legal counsel, and independent audits outside the scope of this software layer.

---

## 1. System Architecture & Objectives

The **Data Governance, Privacy & Compliance Evidence Layer** establishes a unified, multi-tenant control plane across all logical data assets created and orchestrated within the platform. It operates alongside Step 32 (AI Governance & Safety Guardrails) without duplicating authorization logic or creating secondary policy silos.

```
                      User / External Ingestion
                                 │
                                 ▼
                         Data Inventory
                                 │
                                 ▼
                      Classification Engine
              (Public | Internal | Confidential | Restricted)
                                 │
                                 ▼
                     Lineage & Provenance DAG
                                 │
                                 ▼
                   Step 32 Policy Authorization
                                 │
                                 ▼
                         Retention Policy
                                 │
                                 ▼
                         Lifecycle Engine
        ┌──────────────┬──────────────┬──────────────┬──────────────┐
        ▼              ▼              ▼              ▼              ▼
     Retain         Archive       Anonymize        Delete      Legal Hold
                                                     │              │
                                                     ▼              ▼
                                                Verification     Blocks
                                                     │         Destruction
                                                     ▼
                                            Immutable Evidence
                                         (SHA-256 Hash Chained)
                                                     │
                                                     ▼
                                          Events & Audit Logs
```

---

## 2. Core Pillars & Capabilities

### 2.1 Logical Data Inventory (`DataAsset`)
Logical assets are tracked without exposing raw payloads or storing plaintext credentials.
- **Tracked Asset Types:** `document`, `document_chunk`, `artifact`, `memory`, `knowledge_graph_entity`, `knowledge_graph_relationship`, `prompt`, `prompt_version`, `workflow`, `workflow_run`, `task`, `run`, `replay_snapshot`, `cache_entry`, `job`, `event`, `audit_record`.
- **Properties:**
  - `storage_location`: Descriptive logical reference only (e.g. `logical:s3/reports`, `logical:db/table`).
  - `contains_personal_data`: Boolean flag populated by deterministic scanner.
  - `contains_secrets`: Boolean flag for detected API keys, JWTs, or cloud credentials.
  - **Zero Secrets Rule:** Plaintext credentials are strictly prohibited from being persisted in the inventory metadata.

### 2.2 Classification Lifecycle & Downgrade Prevention
Reuses Step 32 classifications:
- `public`: Freely shareable externally.
- `internal`: Workspace and tenant scope.
- `confidential`: Sensitive business or task execution context.
- `restricted`: Highly sensitive or regulated; requires elevated authorization.

**Downgrade Barrier:**
- Automated background classification (rules, connectors, regex scanners) cannot silently downgrade data classified as `confidential` or `restricted`.
- Only explicit, authorized review actions (`POST /api/data-governance/classifications/review`) by authorized administrators can lower classification tiers, and each change is permanently logged in `compliance_evidence`.

### 2.3 Deterministic PII & Secret Redaction
The engine detects high-risk patterns using deterministic scanners:
- **Patterns Detected:**
  - Emails (`[EMAIL_REDACTED]` or `ra***@domain.com` preview)
  - Phone numbers (`[PHONE_REDACTED]`)
  - IPv4 / IPv6 addresses (`[IP_REDACTED]`)
  - URLs (`[URL_REDACTED]`)
  - Credit-card-like strings (`[CARD_REDACTED]`)
  - Government ID / SSN patterns (`[GOV_ID_REDACTED]`)
  - API Keys: OpenAI (`sk-...`), Anthropic (`sk-ant-...`), AWS (`AKIA...`), GitHub (`ghp_...`), Bearer & JWT tokens.
- **Redaction Strategies:** `mask`, `hash`, `remove`, `tokenize_placeholder`.
- **Limitation Notice:** Deterministic regex scanning cannot detect 100% of unstructured or contextual PII. It serves as a defensive technical filter.

### 2.4 Cryptographic Provenance Lineage (`DataLineageEdge`)
A directed acyclic graph (DAG) tracking data relationships:
- **Relationships:** `derived_from`, `copied_from`, `embedded_from`, `retrieved_from`, `generated_from`, `summarized_from`, `evaluated_from`, `cached_from`, `exported_from`, `imported_from`, `redacted_from`, `deleted_from`.
- **Transformations:** `direct`, `chunked`, `embedded`, `summarized`, `generated`, `transformed`, `aggregated`, `redacted`, `exported`, `imported`.
- **Bounded Traversal:** Lineage inspection is bounded by a maximum depth (default: 3 hops) to avoid unbounded recursion. No raw sensitive payload is exposed through the lineage endpoints.

### 2.5 Protective Legal Holds (`LegalHold`, `LegalHoldAsset`)
- Authorized legal holds place an irrevocable freeze on bound assets.
- If an asset is covered by an active hold, any automated retention deletion, manual deletion request, or lifecycle sweep is immediately **BLOCKED**.
- Attempted deletions of held data generate high-priority security notifications and immutable evidence logs.
- Releasing a legal hold requires explicit administrative justification and records full audit evidence.

### 2.6 Safe Deletion & Verification (`SafeDeletionEngine`)
Massive or destructive deletions are never executed synchronously in request cycles.
1. **Pre-flight Checks:**
   - Resolve Step 32 Governance authorization.
   - Verify absence of active legal holds.
   - Resolve dependency tree (documents, chunks, embeddings, cache entries).
2. **Execution:**
   - Soft-delete asset and associated chunks.
   - Invalidate dependent Step 31 semantic cache entries.
   - Clean up derived memory embeddings and graph edges.
3. **Post-deletion Verification:**
   - Re-queries the storage target to verify records are unsearchable and status marked `deleted`.
   - Records verification status (`verified`, `failed`) and summary.
4. **Immutable Evidence Record:**
   - SHA-256 hash appended to the audit chain.

### 2.7 Sanitized Data Exports (`DataExportEngine`)
Multi-format exports (`json`, `jsonl`, `csv`) generated via asynchronous Step 24 background jobs.
- **Sanitization Guarantee:** All API credentials, JWTs, cloud access keys, and passwords are unconditionally stripped prior to bundle creation.
- **Manifest:** Includes export metadata, asset counts, format, lineage references, and cryptographic verification hash.
- **Path-traversal Protection:** Scope targets and export paths are strictly validated to prevent filesystem directory traversal attacks.

### 2.8 Platform Privacy Requests (`PrivacyRequestService`)
Provides structured workflows for tenant privacy requests:
- **Types:** `access`, `export`, `deletion`, `correction`, `restriction`.
- **Statuses:** `pending`, `in_review`, `completed`, `rejected`.
- **Verification:** Requests require identity verification prior to executing underlying data access or deletion jobs.

### 2.9 Tamper-Evident Compliance Evidence (`ComplianceEvidenceService`)
Provides cryptographic proof of governance decisions and lifecycle actions.
- **Chained Hash Formula:**
  $$\text{current\_hash} = \text{SHA256}(\text{previous\_hash} + \text{canonical\_json}(\text{payload}))$$
- **Immutability:** Evidence records cannot be edited or deleted. Corrective adjustments append new evidence records into the chain.
- **Chain Verification:** The `/api/data-governance/overview` endpoint verifies the entire cryptographic chain and flags any divergence or tampering.

---

## 3. Integration Points

| Subsystem | Integration Behavior |
|:---|:---|
| **Step 32 AI Governance** | Evaluates policy authorization before any destructive lifecycle action, classification downgrade, or export. Injects policy evidence snapshots via `PolicyEvidenceRecorder`. |
| **Step 27 Access Control** | Enforces tenant boundary (`organization_id`, `workspace_id`) and role permissions (`data_governance:read`, `data_governance:write`, `data_governance:admin`, `data_governance:export`, `data_governance:delete`, `data_governance:legal_hold`). |
| **Step 24 Durable Jobs** | Asynchronously executes `data_retention_scan`, `data_deletion`, `data_export`, `data_anonymization`, `data_archive`, and `privacy_request`. |
| **Step 26 Event Bus** | Dispatches 17 granular telemetry events under the `DATA_GOVERNANCE` aggregate (e.g. `data.asset.created`, `data.deletion.blocked`, `data.evidence.created`). |
| **Step 25 Notifications** | Dispatches alerts for blocked deletions, legal hold actions, export readiness, and retention failures. |
| **Step 31 Semantic Cache** | Automatically purges and invalidates cached prompt/response entries tied to deleted or redacted assets. |
| **Step 21 Replay Engine** | Displays "Data Redacted" or "Data Deleted" markers when replaying executions whose source assets were purged, preventing zombie resurrection of sensitive content. |

---

## 4. API Reference Summary

All endpoints are authenticated under `/api/data-governance` with Bearer token:

### Assets & Lineage
- `GET /api/data-governance/assets`: List logical assets with classification and privacy filters.
- `POST /api/data-governance/assets`: Register a logical asset and scan for PII/secrets.
- `GET /api/data-governance/assets/{id}`: Inspect single asset metadata and sensitive findings.
- `PATCH /api/data-governance/assets/{id}`: Update asset metadata.
- `GET /api/data-governance/assets/{id}/lineage`: Get bounded DAG of provenance nodes and edges.
- `POST /api/data-governance/lineage`: Record a directed data lineage edge.
- `GET /api/data-governance/assets/{id}/access-history`: Audit logs of reads, writes, and executions.

### Classifications
- `GET /api/data-governance/classifications`: List classification audit history.
- `POST /api/data-governance/classifications/review`: Authoritatively reclassify an asset with audit reasoning.

### Retention & Lifecycle
- `GET /api/data-governance/retention-policies`: List active retention rules.
- `POST /api/data-governance/retention-policies`: Create a new retention policy.
- `PATCH /api/data-governance/retention-policies/{id}`: Update retention parameters or grace periods.
- `DELETE /api/data-governance/retention-policies/{id}`: Soft-delete/disable retention rule.

### Legal Holds
- `GET /api/data-governance/legal-holds`: List active and released holds.
- `POST /api/data-governance/legal-holds`: Create a legal hold and bind protected assets.
- `PATCH /api/data-governance/legal-holds/{id}/release`: Release a hold with recorded justification.

### Deletions & Exports
- `POST /api/data-governance/deletions`: Submit a safe deletion request.
- `GET /api/data-governance/deletions`: List deletion requests and verification states.
- `GET /api/data-governance/deletions/{id}`: Inspect specific deletion details.
- `POST /api/data-governance/exports`: Queue sanitized multi-format data export.
- `GET /api/data-governance/exports`: List exports.
- `GET /api/data-governance/exports/{id}`: Inspect export details and sanitization manifest.

### Privacy Requests
- `POST /api/data-governance/privacy-requests`: Submit platform privacy workflow.
- `GET /api/data-governance/privacy-requests`: List privacy requests.
- `GET /api/data-governance/privacy-requests/{id}`: Get privacy request details.
- `PATCH /api/data-governance/privacy-requests/{id}`: Update verification status or complete request.

### Compliance Evidence & Reports
- `GET /api/data-governance/evidence`: List chronological immutable audit records.
- `GET /api/data-governance/evidence/{id}`: Inspect single evidence snapshot with SHA-256 hash.
- `GET /api/data-governance/overview`: Summary metrics, classification counts, and chain verification status.
- `GET /api/data-governance/reports/retention`: Operational retention forecast and expired count.
- `GET /api/data-governance/reports/classification`: Factual classification distribution.
- `GET /api/data-governance/reports/access`: Access frequency by actor type and result.
- `GET /api/data-governance/reports/deletion`: Verified vs blocked deletion breakdown.
- `GET /api/data-governance/reports/evidence`: Evidence volume grouped by action type.

---

## 5. Fail-Safe Operational Constraints

1. **Governance Failure = Abort:** If Step 32 Policy Engine evaluation times out or fails, destructive deletion is aborted.
2. **Uncertain Hold State = Abort:** If active legal holds cannot be verified with 100% confidence, deletion is blocked.
3. **Evidence Write Failure = Abort:** If the cryptographic evidence chain cannot write a deletion confirmation record, the destructive transaction is rolled back.
4. **Sanitization Failure = Abort:** If the export engine encounters an error while stripping secrets, the export artifact is discarded and marked `failed`.
5. **No Cross-Tenant Lineage:** Lineage edges spanning disparate `organization_id` tenants are rejected at validation time.
