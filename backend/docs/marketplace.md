# AI WORKFLOW MARKETPLACE, VERSIONED TEMPLATES & EXTENSION ECOSYSTEM (STEP 38)

> **MANDATORY SECURITY & GOVERNANCE PRINCIPLE:**  
> **"Marketplace packages are reusable platform definitions and configurations. Installation does not automatically grant permissions, credentials, or unrestricted access."**

---

## 1. Executive Summary & Architecture

Step 38 introduces a first-class ecosystem layer where developers, organizations, and internal teams can create, validate, publish, discover, install, version, update, test, and govern reusable AI Work Layer packages without ever compromising isolation, security, or tenant boundaries.

### Core Ecosystem Flow
```
Creator (Builder)
       ↓
Static Schema Validation (PackageValidator)
       ↓
Static Security Scan (MarketplaceSecurityScanner - zero secrets, zero code)
       ↓
Governance Review (HITL if public/sensitive)
       ↓
Semantic Versioning (MAJOR.MINOR.PATCH - Immutable)
       ↓
Marketplace Registry
       ↓
Discovery & Preview (Factual telemetry & metadata)
       ↓
Installation Review (Explicit approval & configuration)
       ↓
Workspace Installation (Tenant-scoped reference)
       ↓
Authoritative Execution (Under existing RBAC, Gateway & Governance)
```

---

## 2. Package Manifest Structure

Marketplace packages are strictly declarative definitions. The manifest explicitly disallows executable Python, JavaScript, shell scripts, or binary payloads.

```json
{
  "schema_version": "1.0",
  "package": {
    "name": "Research Report Work Pack",
    "version": "1.0.0",
    "type": "work_pack"
  },
  "compatibility": {
    "platform_min_version": "1.0.0",
    "platform_max_version": null,
    "model_capabilities": [
      "vision",
      "structured_output"
    ]
  },
  "components": [
    {
      "name": "Deep Research Workflow",
      "type": "workflow",
      "identifier": "wf_deep_research",
      "config": {}
    },
    {
      "name": "Citation Prompt",
      "type": "prompt",
      "identifier": "prompt_citation_eval"
    }
  ],
  "permissions": [
    {
      "scope": "workflows:run",
      "description": "Execute research workflow steps"
    }
  ],
  "dependencies": [
    {
      "dependency_type": "package",
      "dependency_identifier": "pkg_web_scraper",
      "version_constraint": ">=1.0.0"
    }
  ],
  "configuration": {
    "variables": {
      "research_depth": {
        "type": "integer",
        "default": 3,
        "description": "Max depth of recursive queries"
      }
    }
  },
  "documentation": {
    "readme": "Overview of deep research capabilities...",
    "usage": "Configure research_depth and dispatch via orchestrator.",
    "limitations": "Standard platform token quotas apply.",
    "security_notes": "Zero external secrets embedded."
  }
}
```

---

## 3. Supported Component Types

The ecosystem allows composing declarative configurations across existing platform engines:
1. `workflow` - Reference to declarative workflow pipelines.
2. `workflow_step` - Reusable step definition.
3. `prompt` - Prompt template definition.
4. `prompt_version` - Specific prompt template version.
5. `evaluation_dataset` - Benchmark dataset for Evaluation Lab.
6. `evaluation_case` - Specific evaluation assertion cases.
7. `task_template` - Orchestration task template.
8. `tool_definition` - Declarative tool configuration.
9. `connector_template` - Reusable external integration template (credentials strictly excluded).
10. `policy_template` - Governance policy rule template.
11. `ui_metadata` - Presentation layouts.

**Explicitly Forbidden Elements:**
- Arbitrary Python code (`eval`, `exec`, `subprocess`, `os.system`, `__import__`).
- Arbitrary JavaScript code (`child_process`, `eval`, `Function`).
- Shell commands (`curl`, `rm -rf`, `wget`, `bash`).
- Binary executables or untrusted native plugins.
- Embedded credentials, private keys, passwords, API tokens, or secrets.

---

## 4. Verification & Security Scanning Pipeline

Marketplace packages remain completely untrusted until statically validated:
- **`PackageValidator`**: Validates JSON schema conformance, required fields, semantic version format (`X.Y.Z`), reference integrity, and verifies that no code execution keys or patterns are present.
- **`MarketplaceSecurityScanner`**: Reuses Step 33 and 34 security detectors. Scans all strings, configs, and documentation for:
  - Private keys (`-----BEGIN PRIVATE KEY-----`), API tokens (`sk-`, `ghp_`, `xoxb-`), passwords.
  - Shell command patterns (`curl `, `wget `, `rm -rf`, `bash -c`).
  - Path traversal sequences (`../`, `..\\`).
  - SSRF & blocked local networks (`127.0.0.1`, `169.254.169.254`, `localhost`, RFC 1918 subnets).
  - Suspicious prompt injection vectors.
- **`DependencyResolver`**: Validates dependency graphs using depth-first search (DFS) with recursive cycle detection. Circular or missing dependencies cause immediate publication rejection.
- **`CompatibilityChecker`**: Verifies minimum platform version and factual model capabilities (`structured_output`, `vision`, `streaming`, `large_context`). Subjective quality claims are rejected.

---

## 5. Publishing, Immutability & Provenance

### 7-Stage Publishing Pipeline
1. **Static Validation**: Manifest syntax, components, variables, constraints.
2. **Security Scanning**: Credentials, SSRF, path traversal, injection.
3. **Dependency Resolution**: Cycle detection, version satisfiability.
4. **Platform Compatibility**: Compatibility checking against active runtime.
5. **Governance Evaluation**: Step 32 Governance review; triggers Step 18 HITL for public packages or high-risk permissions.
6. **Provenance Recording**: Verifiable origin (`native`, `imported`, `forked`, `derived`), author organization, parent version ID, and immutable SHA-256 content hashes.
7. **Publication Transition**: Version state transitions to `published`.

### Immutability Rule
Once published, a package version can **never** be edited in place. Any modification requires incrementing the semantic version, producing a fresh content hash, and re-running the full 7-stage verification pipeline.

---

## 6. Installation, Updates & Safe Rollback

### Tenant-Scoped Installation
- Installations are strictly scoped to an organization and optionally a workspace.
- The installation record stores the package version reference, content hash, configuration variables, and an installation policy snapshot.
- Credentials and private secrets are never stored inside the installation record.

### Explicit Update Process
- Package updates are **never silently applied**.
- When a newer compatible version is released, the installation enters an `update_available` status.
- Administrators review diffs in permissions, dependencies, workflows, and prompts before confirming the update.

### Safe Rollback
- Installations can be rolled back to a previous valid version.
- Before rollback execution, the system verifies that the target version still exists, is not revoked, and is not security-blocked.
- Rolling back to a known revoked or compromised version is strictly forbidden.

---

## 7. Factual Telemetry & Moderation

- **Factual Analytics**: The platform records installations, runs, updates, uninstalls, and failure counts. No subjective "package quality ranking" is computed.
- **Reviews**: User reviews (1-5 stars) and comments are preserved as factual user-submitted opinions.
- **Review Moderation**: Reviews undergo automated scanning for spam, duplicate submissions, credential leaks, and malicious URLs. Legitimate negative reviews are never suppressed.

---

## 8. Public API & SDK Extensions

### Public API Endpoints (`/api/v1/marketplace/...`)
- `GET /api/v1/marketplace/packages` — Discover packages.
- `GET /api/v1/marketplace/packages/{slug}` — Inspect package details.
- `GET /api/v1/marketplace/packages/{slug}/versions` — List immutable versions.
- `POST /api/v1/marketplace/packages/{id}/installations` — Install package into workspace.
- `GET /api/v1/marketplace/installations` — List workspace installations.
- `GET /api/v1/marketplace/installations/{id}` — Get installation status.
- `POST /api/v1/marketplace/installations/{id}/update` — Explicitly apply version update.
- `POST /api/v1/marketplace/installations/{id}/rollback` — Safely roll back to previous version.
- `POST /api/v1/marketplace/packages/{id}/fork` — Fork package into organization.
- `GET /api/v1/marketplace/packages/{id}/usage` — Retrieve factual telemetry.

### SDK Usage Examples

#### JavaScript SDK
```javascript
import { AIWorkLayerClient } from "@aiworklayer/sdk";

const client = new AIWorkLayerClient({ apiKey: process.env.AWL_API_KEY });

// 1. Discover packages
const packages = await client.marketplace.list({ category: "research" });

// 2. Install package into workspace
const installation = await client.marketplace.install("pkg_research_pack", {
  workspace_id: "ws_primary",
  configuration: { research_depth: 4 },
});

// 3. Inspect and update
await client.marketplace.update(installation.id, {
  target_version_id: "ver_1_1_0",
});

// 4. Rollback if necessary
await client.marketplace.rollback(installation.id, {
  reason: "Reverting due to pipeline customization requirement",
});
```

#### Python SDK
```python
from ai_work_layer import Client

client = Client()

# 1. Discover packages
pkgs = client.marketplace.list(category="automation", package_type="work_pack")

# 2. Install package
inst = client.marketplace.install(
    package_id="pkg_data_pack",
    workspace_id="ws_analytics",
    configuration={"batch_size": 50},
)

# 3. Update
client.marketplace.update(installation_id=inst["id"], target_version_id="ver_2_0_0")

# 4. Rollback
client.marketplace.rollback(
    installation_id=inst["id"],
    reason="Compatibility validation check",
)
```

---

## 9. Cross-Cutting Architectural Integrations

- **Step 18 (HITL)**: Public marketplace publication and sensitive permission grants trigger Human-in-the-Loop review.
- **Step 24 (Jobs)**: Asynchronous background handlers for `marketplace_validation`, `marketplace_security_scan`, `marketplace_publish`, `marketplace_install`, `marketplace_update`, and `marketplace_rollback`.
- **Step 25 (Notifications)**: Multi-channel notifications for security warnings, version revocations, and update notices.
- **Step 26 (Events)**: High-resolution audit events emitted under aggregate `AggregateType.MARKETPLACE`.
- **Step 27 & 37 (RBAC & API Scopes)**: Permissions `marketplace:read`, `marketplace:install`, and `marketplace:manage` integrated with public API tokens and role matrices.
- **Step 32 (Governance)**: Every marketplace lifecycle action (publish, install, update, rollback, fork) is evaluated against organization governance policies.
- **Step 33 (Data Governance)**: Packages cannot contain private tenant data, credentials, or personal memory.
- **Step 34 (Security Detection)**: Static detection of credentials, malicious URLs, command injections, and path traversals.
- **Step 35 (Reliability)**: Idempotency keys on mutating endpoints; bounded retries on read queries.
- **Step 36 (Disaster Recovery)**: Cryptographic integrity checksums and recovery metadata for all marketplace entities.
