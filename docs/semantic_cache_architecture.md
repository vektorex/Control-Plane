# STEP 31: Production-Grade Semantic Cache and Intelligent Reuse Layer Architecture

## 1. Overview & Architecture Target

The Semantic Cache and Intelligent Reuse Layer provides deterministic exact reuse and embedding-backed semantic reuse across the AI Work Layer. It optimizes token usage, eliminates redundant model computation, and slashes execution latency while strictly preserving correctness, data freshness, tenant isolation, and cryptographic reproducibility.

```
Task Execution / Workflow Step
        ↓
Task Intelligence (Requirement & Capability Extraction)
        ↓
Cache Eligibility Check (Safety, Determinism, Mutation Filters)
        ↓
Deterministic Fingerprint Computation (Request + Context + Prompt + Model + State)
        ↓
Cache Lookup
 ├── Exact Key Match
 └── Semantic Embedding Search (Hybrid Mode with Cosine Similarity Threshold)
        ↓
 [Cache Hit Evaluation]
   ├── Authorization Verification (Current tenant, project, user access)
   ├── Freshness & TTL Verification
   │    ├── Fresh: Return Cached Result (Mark source: "cache")
   │    └── Stale: If eligible for Stale-While-Revalidate:
   │          ├── Return Cached Result (Async Refresh Enqueued)
   │          └── Enqueue `cache_refresh` Job to Job Queue
   └── Incompatible/Expired: Proceed to AI Execution
        ↓
 [Cache Miss Flow]
   ├── Existing AI Execution (Orchestrator → AI Gateway → Model Execution)
   ├── Automated Evaluation / Verification Gate
   ├── Secret Sanitization & Chain-of-Thought Scrubbing
   └── Cache Admission (Capacity & LRU Eviction → Vector Embedding → PostgreSQL `cache_entries`)
```

---

## 2. Core Invariants & Security Boundaries

1. **Zero External Infrastructure Dependency**: Uses existing PostgreSQL with `pgvector` (`VectorType(1536)`) for vector similarity. No Redis, Memcached, or external paid caching services are introduced. Pure-Python cosine fallback ensures seamless execution in local/SQLite test environments.
2. **Never Bypass the AI Gateway on Cache Misses**: On a cache miss or cache bypass, execution flows through the standard AI Orchestrator and AI Gateway. No rogue LLM execution pathways exist.
3. **No Automatic Semantic Equivalence**: High vector similarity alone does not grant reuse. Candidate entries are rejected if prompt versions, models, execution configs, context items, multimodal artifacts, knowledge graph nodes, or memory states do not strictly match.
4. **Side-Effect & Mutation Protection**:
   - Cache hits NEVER replace operations with external side effects, destructive tools, connector mutations, transactions, HITL approvals, or live state verification.
   - Operations classified as mutating or side-effecting are flagged as non-cacheable by `CacheEligibilityService`.
5. **Multi-Tenant & Namespace Isolation**:
   - Every cache entry belongs to an authorized namespace: `workspace`, `project`, `user`, or `global`.
   - Cross-tenant and cross-workspace cache access is strictly impossible.
   - `user`-scoped data remains user-scoped and is never promoted to workspace or global scopes.
   - Global namespace is restricted to universal public read-only templates approved by workspace policy.
6. **No Secret or Chain-of-Thought Caching**:
   - Before admission, `CacheSanitizer` scrubs API keys, bearer tokens, passwords, connector credentials, private webhook secrets, and chain-of-thought blocks (`<thought>`, `Thinking Process:`).
   - Sanitization produces a clean, reusable response payload without mutating the caller's live runtime output.
7. **Cache Stampede Prevention**:
   - In-memory `asyncio.Lock` request coalescing ensures that concurrent identical requests in the same workspace execute only once; subsequent callers await and consume the generated cache entry.
8. **Graceful Cache Failure**:
   - Cache lookup or admission failures never fail the caller's AI request. If a cache query encounters a transient database issue, execution safely falls back to standard AI Gateway execution.

---

## 3. Cache Entry Schema & Cryptographic Fingerprinting

### Cache Entry Model (`cache_entries`)
- `id` (UUID, Primary Key)
- `organization_id`, `workspace_id`, `project_id` (Nullable), `user_id` (Nullable)
- `namespace` (`workspace`, `project`, `user`, `global`)
- `cache_key` (Deterministic SHA-256 string)
- `semantic_embedding` (`vector(1536)`)
- `normalized_request` (Canonical text representation)
- `request_fingerprint` (SHA-256 of normalized request)
- `response_content` (Sanitized text response)
- `response_metadata` (JSONB)
- `source_snapshot` (JSONB: original task ID, run ID, trace ID)
- `prompt_id`, `prompt_version_id` (Foreign Key / UUID)
- `model_id`, `model_provider` (String)
- `execution_config_hash` (SHA-256 of temperature, max_tokens, tools, response format)
- `context_hash` (SHA-256 of context items, chunk IDs, source revisions)
- `artifact_hash` (SHA-256 of multimodal artifact IDs, content hashes, parts)
- `graph_snapshot_hash` (SHA-256 of entity IDs, relations, traversal config)
- `memory_snapshot_hash` (SHA-256 of memory items, user session hashes)
- `status` (`active`, `expired`, `invalidated`, `blocked`)
- `created_at`, `accessed_at`, `expires_at`, `invalidated_at`, `last_hit_at`
- `hit_count` (Integer)

### Deterministic Fingerprint Composition
The exact `cache_key` is calculated using canonical JSON serialization (sorted keys, compact delimiters) and SHA-256:

```python
cache_key = sha256(
    normalized_request
    + ":" + prompt_version_id
    + ":" + model_id
    + ":" + execution_config_hash
    + ":" + context_hash
    + ":" + artifact_hash
    + ":" + graph_snapshot_hash
    + ":" + memory_snapshot_hash
    + ":" + namespace
    + ":" + scope_id
)
```

---

## 4. Matching Modes & Semantic Similarity Engine

### Supported Match Modes
1. **`exact`**: Strictly queries by `cache_key`. Fastest execution (`O(1)` index lookup), zero vector overhead.
2. **`semantic`**: Computes text embedding for the normalized request, runs vector cosine similarity query against candidate entries, and verifies all cryptographic compatibility dimensions.
3. **`hybrid` (Default)**: Attempts exact matching first. If an exact match is found and valid, returns immediately. Otherwise, falls back to semantic vector lookup.

### Semantic Compatibility Matrix
A semantic candidate entry (`cosine_similarity >= CACHE_SEMANTIC_THRESHOLD`) is reusable **only** if all 7 compatibility checks evaluate to `true`:

| Compatibility Dimension | Validation Logic |
| :--- | :--- |
| **Scope Authorization** | Candidate `organization_id` == current org, and namespace scope matches current caller (`workspace`, `project`, or `user`). |
| **Prompt Version** | Candidate `prompt_version_id` == current `prompt_version_id`. Published prompt changes invalidate previous outputs. |
| **Model Compatibility** | If workspace `allow_cross_model_cache == False`, candidate `model_id` == current `model_id`. |
| **Execution Config** | Candidate `execution_config_hash` == current `execution_config_hash` (temperature, max tokens, tool schemas). |
| **Context State** | Candidate `context_hash` == current `context_hash` (retrieved document chunks, web excerpts). |
| **Multimodal Artifacts**| Candidate `artifact_hash` == current `artifact_hash` (image, audio, spreadsheet content hashes). |
| **Graph & Memory** | Candidate `graph_snapshot_hash` and `memory_snapshot_hash` match active states. |

---

## 5. Cache Eligibility & Policy Engine

### Deterministic vs. Non-Cacheable Classifications

#### Eligible for Reuse (Safe & Deterministic):
- Deterministic text transformations (translation, markdown formatting, syntax conversion)
- Document summarization and Q&A over static documents
- Information extraction and classification (entity tagging, sentiment analysis, schema extraction)
- Structured JSON transformations
- Read-only code and log analysis
- Stable research outputs over unchanging source datasets

#### Ineligible for Reuse (Bypassed & Rejected):
- Workflows with external side effects (HTTP POST/PUT/DELETE, notifications)
- Destructive tools (file writes, database mutations, infrastructure commands)
- Connector write operations (Salesforce, HubSpot, Jira, Slack messages)
- Human-in-the-Loop (HITL) approval decisions
- Security and permission policy decisions
- Credential management operations
- Real-time/time-sensitive actions
- Requests explicitly marked with `cache_mode="refresh"` or `cache_mode="disabled"`

### Workspace Cache Policy Settings
Configured via `GET /api/cache/policy` and `PUT /api/cache/policy`:
- `enabled`: Global toggle for workspace caching (`true`/`false`).
- `default_mode`: `auto`, `enabled`, `disabled`, or `refresh`.
- `semantic_enabled`: Enables vector semantic candidate matching (`true`/`false`).
- `semantic_threshold`: Float bounded strictly between `0.70` and `0.99` (default: `0.88`).
- `default_ttl`: Time-to-live in seconds (default: `86400` / 24 hours).
- `max_entry_size`: Byte limit for cached response payloads (default: `500,000` bytes).
- `allow_cross_model_cache`: Disallow cross-model reuse by default (`false`).
- `stale_while_revalidate`: Allow serving slightly expired entries while queuing a background refresh (`true`/`false`).
- `max_namespace_entries`: Maximum active entries per namespace before LRU eviction triggers (default: `5000`).

---

## 6. Freshness, Invalidation, and Background Refresh

### Freshness Lifecycle
- **Fresh**: `now < expires_at`. Cache hit returned immediately.
- **Stale-While-Revalidate**: `expires_at <= now < expires_at + grace_period` (and operation is safe/read-only). Entry is returned to client with `stale: true`, and a `cache_refresh` job is enqueued to the durable Job Queue.
- **Expired**: `now >= expires_at + grace_period`. Entry is marked expired and bypassed.

### Event-Driven Cache Invalidation
Registered consumers on the centralized `EventBus` (`EventPublisher`) invalidate affected entries surgically:

| Domain Event | Invalidation Target | Scope |
| :--- | :--- | :--- |
| `prompt.release_changed`, `prompt.rolled_back` | Entries matching `prompt_id` or `prompt_version_id` | Prompt Scope |
| `artifact.processing_completed` | Entries referencing modified artifact ID or content hash | Artifact Scope |
| `document.updated` | Entries with matching document content hash | Context Scope |
| `graph.entity_updated`, `graph.relationship_*` | Entries referencing affected entity or relation IDs | Graph Scope |
| `memory.updated` | User-scoped entries for the specific modified memory | User Memory Scope |
| `workflow.updated` | Entries generated by the modified workflow version | Workflow Scope |
| `connector.updated` | Connector-derived entries whose data source changed | Connector Scope |

### Administrative Invalidation API
`POST /api/cache/invalidate`:
```json
{
  "mode": "prompt",
  "workspace_id": "893c52a0-43e8-4623-bc97-8a8b1ef38057",
  "target_id": "prompt-asset-uuid",
  "reason": "Production prompt prompt-v4 released with new schema"
}
```

---

## 7. Concrete Real-World Examples

### 1. Document Q&A Reuse
- **Scenario**: User asks "What is the termination clause in the 2025 Vendor Agreement?"
- **Context**: Context Engine retrieves 3 chunks from `doc_vendor_agreement_2025.pdf` (Content Hash: `e3b0c44...`).
- **Cache Check**: Exact hit on request + document chunk hash + prompt version `v2`.
- **Result**: Immediate hit returned in 12ms (saving 1,450 tokens and $0.02).
- **Subsequent Action**: Vendor agreement is re-indexed with an addendum. Event `document.updated` fires. Relevant cache entry is invalidated. Next Q&A triggers a fresh AI execution.

### 2. Research Summary with Stale-While-Revalidate
- **Scenario**: Scheduled workflow generates "Daily Market Tech Summary".
- **Policy**: `freshness_policy="relaxed"`, `default_ttl=43200` (12 hours), `stale_while_revalidate=true`.
- **Cache Check**: Cache entry is 12.5 hours old (within 2-hour grace period).
- **Result**: Summary returned to user in 8ms with `source="cache"` and `fresh=false`. Background job `cache_refresh` is enqueued, executes via `TaskExecutionService`, and updates the cache entry transparently.

### 3. Image Analysis (Multimodal Artifact Integration)
- **Scenario**: Image defect detector evaluates `part_inspection_092.png`.
- **Artifact State**: Artifact ID `art-102` with image perceptual/SHA-256 hash `a1b2c3d4...`.
- **Cache Check**: Evaluates normalized instruction "Detect surface fractures" + artifact content hash.
- **Result**: Identical image uploaded later matches `artifact_hash` → cache hit. If a different image is analyzed under the same prompt, `artifact_hash` differs → cache miss, full vision model execution.

### 4. Spreadsheet Analysis (Multimodal Table Integration)
- **Scenario**: Financial pipeline runs automated ratio calculations on `q3_financials.csv`.
- **Artifact State**: Artifact table with parts `table_rows_1_100`.
- **Cache Check**: Request fingerprint incorporates `artifact_id` + part IDs + table schema hash.
- **Result**: Results cached at `project` namespace. Concurrent analysts querying identical spreadsheet metrics receive instantaneous cached results without re-running code analysis.

### 5. Workflow Step Generation
- **Scenario**: Multi-step pipeline with steps `[step1: summarize_brief, step2: generate_proposal, step3: send_slack_notification]`.
- **Workflow Cache Policy**: `safe`.
- **Execution**:
  - `step1` (`generate`): Eligible → Cache hit.
  - `step2` (`generate`): Eligible → Executed & Admitted to cache.
  - `step3` (`tool` / Slack notification): Mutating connector tool → Cache bypassed. Execution mandatory.

### 6. Stable Data Transformation
- **Scenario**: Extract customer JSON schema from raw support transcripts.
- **Eligibility**: Classified as `deterministic_transformation`.
- **Cache Check**: Exact request fingerprint matches. Prompt version `v1` intact.
- **Result**: Immediate sanitized JSON return. Sanitizer ensures customer email credentials or internal bearer tokens present in prompt context were scrubbed before storage.
