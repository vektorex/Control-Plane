# Step 36: Disaster Recovery, Backup & Business Continuity Layer

> **MANDATORY SYSTEM DISCLAIMER**
> *"This system provides application-level backup, restore orchestration, and recovery-readiness controls. It does not by itself guarantee infrastructure-level disaster recovery, availability, uptime, or contractual RTO/RPO."*

---

## 1. Overview & Architecture

Modern AI applications contain heterogeneous persistent and runtime state: organizations, workspaces, projects, tasks, workflows, triggers, documents, artifacts, prompts, evaluation datasets, semantic memories, knowledge graphs, background jobs, and audit logs. Infrastructure-level database backups (such as PostgreSQL WAL archiving or EBS snapshots) are critical for hardware failures, but cannot solve application-level disaster recovery challenges:
- Selective resource recovery (e.g. restoring a single workspace, prompt release, or workflow version).
- Cross-tenant data isolation and boundary enforcement during restore.
- Secret redaction preventing stale or revoked API credentials from silent resurrection.
- Respecting data governance lifecycles (preventing the resurrection of legally deleted customer data under Step 33).
- Enforcement of Step 32 Governance and Step 18 Human-in-the-Loop (HITL) approval when replacing existing production resources.
- Factual tracking of Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO) without marketing guarantees.

```
                    ┌─────────────────────────┐
                    │    Application State    │
                    │ (PostgreSQL, Files, DB) │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │      Backup Policy      │
                    │  (Scope, Retention, RPO)│
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │      Backup Planner     │
                    │ (Dependencies, Topology)│
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Consistent Snapshot    │
                    │ (Logical JSON Package)  │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Integrity Verification  │
                    │  (SHA-256 Content/Meta) │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     Backup Manifest     │
                    │  (Inventory, Signatures)│
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │      Restore Plan       │
                    │ (Dry-Run Conflict Eval) │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │    Governance + HITL    │
                    │ (Elevated Authorization)│
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Authorized Restore Run  │
                    │ (Sandbox or Production) │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   Recovery Evidence     │
                    │  (Step 33 Hash Chaining)│
                    └─────────────────────────┘
```

---

## 2. Backup Content Format & Serialization

Backups utilize a versioned, deterministic logical format (`json_logical`):
- **Version**: `1.0`
- **Root Packaging**: Contains metadata describing application version, schema version, organization ID, and timestamp.
- **Resource Buckets**: Categorized by architectural domain:
  - `organizations/`, `workspaces/`, `projects/`, `tasks/`, `runs/`
  - `workflows/`, `prompts/`, `documents/`, `artifacts/`
  - `memories/`, `graph/`, `evaluations/`
  - `governance/`, `security/`, `reliability/`, `compliance/`

Every resource snapshot records its `resource_type`, `resource_id`, `tenant`, `classification`, `dependencies`, and `content_hash`.

---

## 3. Storage Abstraction & Encryption

### Storage Provider Abstraction
The `BackupStorageProvider` abstract base class decouples persistence from physical media:
- `put(key, data, metadata) -> str`
- `get(key) -> bytes`
- `exists(key) -> bool`
- `delete(key) -> bool`
- `list(prefix) -> List[str]`
- `get_metadata(key) -> dict`

The default implementation is `LocalBackupStorageProvider`, which enforces strict path sanitization against directory traversal (`..`).

### Encryption at Rest
The `BackupEncryptionProvider` encrypts sensitive backup payloads before writing to disk using standard Fernet (AES-128-CBC with HMAC-SHA256 authenticated encryption).
- **Classification Inheritance**: Backups inherit the highest classification of their constituent assets (`public` $\to$ `internal` $\to$ `confidential` $\to$ `restricted`).
- **Mandatory Encryption**: Any backup containing `confidential` or `restricted` resources is encrypted before persistent storage.
- **Key Isolation**: Encryption keys are never written to the backup payload or stored in manifest files.

---

## 4. Manifest & Cryptographic Integrity

Each backup snapshot is accompanied by a cryptographic `BackupManifest`:
- **Content Hash**: `SHA-256` digest computed across the raw binary/encrypted archive payload.
- **Manifest Hash**: Deterministic `SHA-256` digest computed across canonical manifest metadata.
- **Previous Manifest Hash**: Optional hash chaining linking sequential backup generations.
- **Tenant Validation**: Strict assertion verifying that all resources in the manifest match the organization's tenant boundary.

If any hash mismatch is detected, the `BackupIntegrityService` marks the package invalid and raises `ManifestTamperedError` or `BackupIntegrityError`.

---

## 5. Multi-Phase Backup Verification

A backup marked "completed" is not assumed to be restorable. The `BackupVerificationService` executes a multi-phase battery:
1. **Manifest Integrity**: Validates manifest hash matches content structure.
2. **Cryptographic Content**: Verifies SHA-256 payload checksum and tenant boundaries.
3. **Schema Compliance**: Confirms package version and format match platform capabilities.
4. **Dependency Consistency**: Resolves internal foreign key and parent/child references.
5. **Dry-Run Restore Simulation**: Decrypts and deserializes payload into memory, verifying state completeness without modifying production data.

Only when all checks pass is the manifest certified with `verification_status = "verified"`.

---

## 6. Restore Planning, Modes & Safety Constraints

### Restore Modes
- `dry_run` (default): Simulates restoration, evaluates schema compatibility, identifies conflicting resources, and outputs a blast radius assessment without writing data.
- `sandbox`: Restores resources into an isolated non-production workspace for inspection and validation.
- `authorized_restore`: Restores resources into designated active environments.

### Conflict Policies
- `fail`: Abort if any target resource already exists.
- `skip_existing`: Leave existing resources untouched and restore only missing entities.
- `restore_missing`: Restore only absent records and log existing records.
- `replace_existing`: Overwrite existing target records with snapshot data.

### Critical Safety Protections
1. **Cross-Tenant Block**: Restoring organization A's backup into organization B is strictly blocked (`CrossTenantRestoreBlockedError`).
2. **Elevated Privilege + HITL**: `replace_existing` or production restoration requires administrative roles (`admin` or `owner`) plus explicit Step 18 Human-in-the-Loop approval.
3. **No Plaintext Secret Restoration**: Third-party API keys, OAuth tokens, and webhook secrets are never restored as plaintext active credentials; references are preserved and require explicit credential re-authentication.
4. **Data Governance Lifecycle (Step 33)**: Data that was legally deleted cannot be resurrected from historical backups (`DeletedDataResurrectionBlockedError`). Assets under active legal hold cannot be overwritten during restore.
5. **Security State (Step 34)**: Historical security incidents and containment logs are restored as immutable historical records, never as active alerts.
6. **Reliability Resumption (Step 35)**: Historical background jobs and workflow runs are restored as completed or failed records; stale jobs are not re-executed automatically without validation.

---

## 7. Dependency-Aware Restoration Ordering

Resource restoration follows a topological dependency order to avoid foreign key and reference violations:
1. `organization` $\to$ `workspace` $\to$ `project`
2. `governance_policy` $\to$ `governance_policy_version`
3. `prompt` $\to$ `prompt_version` $\to$ `prompt_release`
4. `document` $\to$ `document_chunk` $\to$ `artifact`
5. `workflow` $\to$ `workflow_version` $\to$ `task` $\to$ `run`
6. `evaluation_dataset` $\to$ `evaluation_case` $\to$ `evaluation_experiment`
7. `memory` $\to$ `knowledge_graph_entity` $\to$ `knowledge_graph_relationship`
8. `trigger` $\to$ `trigger_run` $\to$ `job` $\to$ `notification`

---

## 8. Recovery Objectives (RTO/RPO) & Readiness

- **Recovery Time Objective (RTO)**: Target maximum duration required to restore operational capability (e.g. 2 hours).
- **Recovery Point Objective (RPO)**: Target maximum tolerable data loss window (e.g. 24 hours).
- **Readiness Tracking**: Evaluates factual operational parameters:
  - `observed_backup_age_seconds`: Elapsed time since the latest completed backup.
  - `verification_status`: Status of the most recent integrity check.
  - `restore_test_status`: Result of the most recent dry-run or sandbox restore simulation.
  - `overall_status`: Factual readiness state (`ready`, `needs_attention`, `blocked`, `unknown`).

---

## 9. Business Continuity Planning & Exercises

### Business Continuity Plans
Enables organizations to document critical service tiers, dependency graphs, fallback modes, owner escalations, and ordered restoration sequences:
`database` $\to$ `authentication` $\to$ `governance` $\to$ `security` $\to$ `ai_gateway` $\to$ `jobs` $\to$ `events` $\to$ `workflows` $\to$ `connectors` $\to$ `notifications`

### Safe Disaster Recovery Exercises
Supports simulated drill scenarios (`database_restore_simulation`, `workflow_recovery`, `provider_outage_recovery`):
- **Allowed Environments**: `test`, `staging`, `sandbox`.
- **Production Guardrails**: Production exercises are disabled by default. Running an exercise against production raises `ProductionExerciseBlockedError` unless explicit Step 32 Governance clearance and Step 18 HITL approval are granted.
- **Zero Real Side-Effects**: Drills never delete production records, revoke live credentials, or deliver real notifications.

---

## 10. Audit, Evidence & Notifications

- **Compliance Evidence**: Reuses Step 33 `ComplianceEvidence` with SHA-256 hash chaining to log `backup_created`, `backup_verified`, `restore_planned`, `restore_approved`, `restore_executed`, and `recovery_exercise_completed`.
- **Security Operations Bridge**: Failed manifest verifications, cross-tenant restore attempts, or data resurrection violations create `SecuritySignal` entries in Step 34.
- **Event Bus Integration**: Emits sanitized tenant-scoped events (`recovery.backup.*`, `recovery.restore.*`, `recovery.exercise.*`).
- **Notifications**: Alerts administrators when backups become stale, integrity checks fail, or restore operations encounter blockers.

---

## 11. System Limitations

1. **Application-Level Scope**: This layer orchestrates logical resource backups and recovery readiness. It does not replace infrastructure-level PostgreSQL WAL replication, disk mirroring, or multi-region cloud disaster recovery.
2. **Local Storage Single Point of Failure**: When configured with the default local filesystem provider, backups reside on the host system. High-availability production deployments must attach distributed, resilient storage volumes.
3. **Secret Re-Authentication**: By design, third-party API credentials and external OAuth tokens are not preserved in plaintext; recovered connectors require administrative re-authentication.
