# Memory & Persistent Context Intelligence System (Step 17)

The **AI Work Layer** persistent memory architecture allows the platform to retain useful, user-approved knowledge, technical facts, preferences, and architectural decisions across tasks and workflows, retrieve relevant context boundedly when needed, and strictly prevent irrelevant, arbitrary, or sensitive information from ever being retained.

---

## 1. ⚠️ Memory is Not Conversation History

> **Critical Distinction**:
> **Memory is NOT conversation history.**
> **Memory is NOT raw prompt or chat transcript storage.**
> **The platform NEVER automatically stores everything users say.**

In the AI Work Layer, conversational turns and raw chat logs are transient execution artifacts. Persistent memory represents **curated, structured, high-value knowledge**:
- Explicit preferences approved by the user (e.g., "Use JavaScript instead of TypeScript for fast frontend prototypes").
- Verified technical facts (e.g., "PostgreSQL pgvector extension installed in production cluster").
- Architectural decisions (e.g., "Use AES-256-GCM authenticated encryption for third-party connector tokens").
- Reusable project standards and instructions.

Raw user banter, prompt boilerplate, transient debugging sessions, unconfirmed AI thoughts, and chain-of-thought traces are **never** persisted into the memory store.

---

## 2. 🛡️ Trust Hierarchy & Security Boundaries

Persistent memory is one context source among many and **must never override application policy, system security, or tool permissions**. The system enforces the following deterministic trust hierarchy:

```
  ┌────────────────────────────────────────────────────────┐
  │                 1. System Policy                       │  (Immutable platform boundaries)
  ├────────────────────────────────────────────────────────┤
  │              2. Application Policy                     │  (Workspace-level rules & RBAC)
  ├────────────────────────────────────────────────────────┤
  │               3. Security Policy                       │  (Secret & PII filter, rate limits)
  ├────────────────────────────────────────────────────────┤
  │               4. Workflow Policy                       │  (Execution step constraints)
  ├────────────────────────────────────────────────────────┤
  │             5. Explicit User Context                   │  (Task instructions & direct input)
  ├────────────────────────────────────────────────────────┤
  │              6. Persistent Memory                      │  (Curated preferences & decisions)
  ├────────────────────────────────────────────────────────┤
  │           7. Retrieved External Data                   │  (Documents, Connectors, Web Search)
  └────────────────────────────────────────────────────────┘
```

### Safety Rules:
1. **No Silent Persistence**: External connector content, document uploads, and arbitrary web search results must **NEVER** automatically become persistent memory.
2. **Attribution Preservation**: When a user explicitly chooses *"Save this snippet as memory"* from a connector or document, the system records `source_type="connector"` or `"document"` with `source_id`, verifies trust, and cleans the text.
3. **No Chain-of-Thought Exposure**: Memory suggestions extracted by the AI include only concise, user-safe explanations (e.g. *"Looks like a recurring preference that may be useful in future tasks"*). Internal chain-of-thought reasoning is completely omitted.
4. **Secret Scrubbing**: Raw credentials, private keys, JWTs, and database URIs are automatically scrubbed or rejected; errors never echo raw secrets back to the user.

---

## 3. 🌐 Memory Scopes & Strict Isolation

Every memory belongs to an explicit scope that guarantees multi-tenant isolation:

| Scope | Visibility | Isolation Boundary |
| :--- | :--- | :--- |
| **`user`** | Private to the creating user | Inaccessible to other workspace members or projects. |
| **`workspace`** | Accessible to all authenticated members of that workspace | Isolated strictly to that workspace ID; never leaks across tenants. |
| **`project`** | Accessible only to tasks & workflows inside that project | Inaccessible to other projects even within the same workspace. |

---

## 4. 🏷️ Memory Types & Lifecycle States

### Memory Types:
- `preference`: User preferences (frameworks, coding conventions, styling choices).
- `technical_fact`: Concrete platform or environment facts (database versions, cluster endpoints).
- `instruction`: Operational guidelines (review standards, testing requirements).
- `project_context`: Scoped domain knowledge for a specific project.
- `workflow_context`: Context specific to multi-step orchestration workflows.
- `reference`: Useful specifications, API documentation references, or schema links.
- `decision`: Architecture decisions (ADRs, team agreements, design approvals).

### Lifecycle States:
```
               [AI / Task / Workflow]
                         │
                         ▼
               ┌───────────────────┐
               │ Candidate State   │  (Pending explicit user confirmation)
               └─────────┬─────────┘
                         │
         ┌───────────────┴───────────────┐
         ▼ Accept                        ▼ Reject / Dismiss
┌───────────────────┐           ┌───────────────────┐
│   Active Memory   │           │     Discarded     │
└────────┬──────────┘           └───────────────────┘
         │
         ├── Archive ──────────────► [Archived] (Excluded from retrieval)
         ├── Conflict Detected ────► [MemoryConflict] (Tracked & resolved)
         └── Expiration Date ──────► [Expired] (Automatically purged)
```

---

## 5. 🔍 Bounded Memory Retrieval & ContextEngine Integration

Memory retrieval integrates directly with the existing vector infrastructure (`PostgreSQL + pgvector` via `VectorType` and `EmbeddingProvider`).

### Bounded Limits:
- `MAX_MEMORY_RESULTS = 10`
- `MAX_MEMORY_CONTEXT_TOKENS = 3000`

### Retrieval Modes:
- **`auto`**: Retrieval Router dynamically decides whether memory retrieval is required based on task intent and historical utility.
- **`always`**: Force memory retrieval for all task executions in the workspace.
- **`never`**: Memory retrieval is disabled; tasks execute strictly with manual context and external documents.

Memories are transformed into normalized `ContextItem` objects with `source_type: "memory"`, `priority: 75`, and `trust_level: "trusted_user_context"`, fed through the existing `ContextEngine` pipeline.

---

## 6. ⚔️ Deduplication & Conflict Handling

### Deduplication:
When a new memory is proposed, the system performs a SequenceMatcher similarity check on active memories in the same scope. If content similarity exceeds **0.90**, the system touches `last_used_at` rather than creating a redundant clone.

### Conflict Detection & Resolution:
When two memories share the same topic or title (similarity ≥ 0.60) but express opposing directives (content similarity < 0.88), the system creates a `MemoryConflict` record:
- **`keep_winner`**: The user picks the preferred directive (Memory A or Memory B); the other is archived.
- **`merge`**: The directives are merged into a synthesized standard.
- **`dismiss`**: Both directives remain active without further warnings.

---

## 7. 🔒 Centralized Secret Detection Patterns

The `SecretDetector` scans all memory titles, contents, and metadata fields for high-entropy patterns before persistence:
- **OpenAI / Anthropic Keys**: `sk-proj-`, `sk-ant-`
- **GitHub Tokens**: `ghp_`, `gho_`, `github_pat_`
- **Bearer Tokens / JWTs**: `Bearer eyJ...`
- **Private RSA / OpenSSH Keys**: `-----BEGIN RSA PRIVATE KEY-----`
- **Database Connection URIs**: `postgres://user:pass@host:port/db`
- **Cloud Credentials**: `AKIA[0-9A-Z]{16}`, AWS secret patterns

If detected, memory creation is immediately rejected with a safe warning, ensuring credentials are never saved or echoed back.

---

## 8. 🎛️ Privacy Controls & Bulk Purge

Through `/app/settings/memory` or the REST API:
- **Delete All Project Memories**: Purges all memories tied to a specific project.
- **Delete All Workspace Memories**: Purges all workspace-level memories and conflicts.
- **Inspect & Edit**: Users can inspect, modify, archive, or permanently delete any individual memory.
- **Security Notice**: Security filtering and secret detection can never be disabled by user settings.

---

## 9. 🔌 System Integrations

### Workflow System:
Workflows support a native `memory` step with operations:
- `retrieve`: Searches memories using a query template (e.g. `{{input.topic}}`).
- `save_candidate`: Generates a suggestion that queues in the Memory Center for confirmation.
- `create_explicit`: Persists explicit workspace knowledge.

### Task Execution:
Tasks support Memory mode controls (`Auto`, `Enabled`, `Disabled`). When memories are used during execution, citations are rendered (`"Used from memory: X items"`) in the Run detail view and Execution Trace, and recorded in telemetry without leaking private contents.
