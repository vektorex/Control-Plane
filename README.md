# AI Work Layer (LLM-Work-Orchestration-Layer)

> **"One workspace for getting real work done with LLMs."**

A universal, production-oriented LLM work orchestration platform that accepts complex user tasks and coordinates optimal LLMs, context sources, an intelligent retrieval router, hybrid retrieval strategies (Vector + Keyword Search + Multi-Query + Reranking), persistent project data, multi-tenant workspace isolation, and specialized execution tools.

---

## 🏛️ System Architecture

```
User Task
   ↓
Task Understanding
   ↓
Retrieval Router (RuleBasedDecisionProvider / Pluggable LLMDecisionProvider)
   ↓
┌─────────────────────────────────────────┐
│ No Retrieval (Direct LLM Directive)     │
│ Vector Retrieval (Semantic Concepts)    │
│ Keyword Retrieval (Exact BM25 Match)    │
│ Hybrid Retrieval (Vector + BM25 + RRF)  │
│ Multi-Query Retrieval (Query Expansion) │
└─────────────────────────────────────────┘
   ↓
Decision (RetrievalDecision: required, strategy, scope, top_k, reason, confidence)
   ↓
Retriever (Dispatched Strategy)
   ↓
ContextEngine
   ├── TaskContextProvider     (Task title, instructions, baseline context)
   ├── ManualContextProvider   (User-attached task notes, guidelines, constraints)
   └── RAGContextProvider      (Consumes RetrievalDecision & grounded chunks)
   ↓
ContextPackage (Budget-Enforced & Prioritized)
   ↓
LLM Abstraction (OpenAI, Anthropic, Mock Providers)
```

---

## 🛠️ Tool System & Web Search Grounding (Step 9)

Step 9 establishes a **Provider-Independent Tool System** and integrates live **Web Search** as the first external grounding tool.

### 1. Tool Architecture

```
Task
 ↓
Tool Registry (Centralized registration & validation)
 ↓
Tool Executor (Permissions, timeout, error normalization, latency tracking)
 ↓
Web Search Provider (DuckDuckGo, Tavily, Serper, Mock)
 ↓
Normalized Tool Result ({ title, url, snippet, source, published_at, metadata })
 ↓
WebContextProvider (Untrusted data demarcation & token estimation)
 ↓
ContextEngine (Budget enforcement & priority sorting)
 ↓
LLM Generation
```

### 2. Provider-Independent Tool Interface
Every tool implements the `BaseTool` interface:
- **`name`**: Unique identifier (e.g. `web_search`)
- **`description`**: Human-readable explanation of tool behavior
- **`input_schema`**: Pydantic input model validating all user parameters
- **`requires_auth`**: Server-side enforcement flag (default `true`)
- **`execute(input)`**: Asynchronous execution returning structured data
- **`check_permission(raw_input, user, **kwargs)`**: Backend permission verification

### 3. Tool Registry & Executor
- **`ToolRegistry`**: Centralized registry managing tool lifecycle, validation against Pydantic models, and metadata discovery.
- **`ToolExecutor`**: Safe execution wrapper that:
  1. Resolves requested tool from registry
  2. Enforces authentication and contextual permissions
  3. Validates input schemas
  4. Enforces timeouts (`WEB_SEARCH_TIMEOUT_SECONDS`)
  5. Measures latency in milliseconds
  6. Catches all exceptions and returns normalized `ToolResult` (never exposing raw internal stacktraces)

### 4. Pluggable Web Search Providers
Search APIs are abstracted behind `WebSearchProvider`:
- **`DuckDuckGoSearchProvider`**: Zero-key out-of-the-box search provider
- **`TavilySearchProvider`**: AI-optimized search with native snippets and dates
- **`SerperSearchProvider`**: Google Search API adapter
- **`MockWebSearchProvider`**: Deterministic test provider for CI/CD

### 5. Untrusted Data Boundary & Prompt Injection Safety
Web search content is strictly treated as **UNTRUSTED EXTERNAL DATA**:
```
System Instructions (Highest Trust)
      ↓
User Task & Instructions (Trusted User Input)
      ↓
Application & Workspace Context (Trusted Context)
      ↓
[EXTERNAL UNTRUSTED WEB CONTENT - FACTUAL REFERENCE ONLY] (Untrusted External Data)
      ↓
LLM Execution
```
- External web snippets are demarcated with clear boundary headers.
- Untrusted content is forbidden from overriding system directives, modifying tool permissions, or accessing private tenant resources.

---

## 🧭 Intelligent Retrieval Router (Step 8)

Step 8 adds an **Intelligent Retrieval Router** that analyzes task instructions and directives to determine whether external knowledge is needed, what scope boundary to query, and which retrieval strategy should be deployed.

### 1. Retrieval Decision Model
The router outputs a structured, deterministic `RetrievalDecision`:
```json
{
  "retrieval_required": true,
  "strategy": "hybrid",
  "scope": "project",
  "top_k": 8,
  "query": "What does our authentication implementation do?",
  "reason": "Task requires factual knowledge grounding against project documentation and codebase.",
  "confidence": 0.90,
  "generated_queries": []
}
```

### 2. Supported Retrieval Modes (User Overrides)
Users can configure how retrieval decisions are governed:
- **`auto` (Automatic)**: The router inspects instructions, intent, factual grounding signals, and context availability to make the optimal routing decision.
- **`always` (Always Retrieve)**: Forces knowledge retrieval whenever project or workspace knowledge exists.
- **`never` (Never Retrieve)**: Bypasses external document retrieval completely for closed-form generation.

### 3. Supported Strategies
- **`none`**: Closed-form summarization, conversational directives, or arithmetic requiring zero external lookup.
- **`keyword`**: BM25 lexical term coverage and exact verbatim phrase lookup (e.g. `Find the exact phrase 'refresh token' in documentation`).
- **`vector`**: Dense embedding cosine similarity for high-level semantic concepts and conceptual understanding (e.g. `Explain the concepts related to authentication`).
- **`hybrid`**: Reciprocal Rank Fusion (RRF) combining vector similarity and keyword search for factual project inquiries and codebase comparisons (e.g. `What does our authentication implementation do?`).
- **`multi_query`**: LLM query expansion generating multi-angle search queries, executing parallel hybrid retrievers, deduplicating candidate chunks, and applying local reranking for multi-faceted tasks.

---

## 📚 Document Ingestion & Hybrid RAG Pipeline (Step 7)

- **PDF, Markdown, TXT, DOCX Extraction**: Built-in extractors with page retention and format validation.
- **Storage Abstraction**: `.storage/documents` local storage with S3/R2 cloud storage readiness.
- **Structure-Aware Chunking**: Natural paragraph and boundary splitting with configurable token overlap.
- **Batch Embeddings**: `OpenAIEmbeddingProvider` (`text-embedding-3-small`, 1536d) & `MockEmbeddingProvider` (128d).
- **Reciprocal Rank Fusion**: $RRF(d) = \sum \frac{w_i}{60 + \text{rank}_i(d)}$.
- **Local Reranker**: Query term density and leading chunk alignment.

---

## 🧠 Production Orchestration Engine Architecture (Step 10)

The AI Work Layer features a production-oriented Orchestration Engine that coordinates task configuration, context, retrieval, tools, and LLM generation through a deterministic, observable execution plan.

```
Task
 ↓
Orchestrator
 ↓
Execution Planner (Deterministic)
 ↓
Execution Plan (Validated)
 ↓
Orchestration Executor
 ├── Step 1: Context Assembly / Hybrid Retrieval
 ├── Step 2: Tool Execution (Web Search)
 └── Step 3: Final Context Merging & LLM Generation
 ↓
Execution Results
 ↓
Final LLM Response
 ↓
Run (with Step Records & Telemetry)
```

### 1. Structured Execution Plan (`ExecutionPlan`)
Each execution plan is structured, deterministic, and validated prior to execution:
```json
{
  "id": "plan_9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "task_id": "c1f72782-b4ea-4c46-953e-2faec03df6dc",
  "steps": [
    {
      "id": "step_1",
      "type": "retrieve",
      "strategy": "hybrid",
      "scope": "project",
      "required": false
    },
    {
      "id": "step_2",
      "type": "tool",
      "tool": "web_search",
      "input": { "query": "Latest React changes", "limit": 5 },
      "required": false
    },
    {
      "id": "step_3",
      "type": "generate",
      "model": "gpt-4o",
      "temperature": 0.2,
      "required": true
    }
  ],
  "max_steps": 10,
  "timeout_seconds": 60.0
}
```

### 2. Supported Step Types & Extensibility
- `context`: Assembles manual and task baseline context items.
- `retrieve`: Dispatches intelligent knowledge search (`hybrid`, `vector`, `keyword`, `multi_query`).
- `tool`: Invokes registered provider-independent tools (e.g. `web_search`).
- `generate`: Merges accumulated context via `ContextEngine` and executes LLM generation.
- *Extensible for future*: `transform`, `evaluate`, `retry`, `human_approval`.

### 3. Server-Side Safety & Execution Limits
- `MAX_PLAN_STEPS=10`
- `MAX_TOOL_CALLS_PER_PLAN=5`
- `MAX_RETRIEVAL_CALLS_PER_PLAN=3`
- `MAX_CONTEXT_TOKENS=16000`
- `MAX_EXECUTION_TIME_SECONDS=60.0`

### 4. Failure & Fallback Policies
- **Strict Mode**: If any required step fails, execution halts and the run is marked as failed.
- **Configurable Fallback Mode**: If an optional retrieval or web search step fails (e.g. provider downtime), the executor logs the failure in `ExecutionStepRecord`, attaches the diagnostic to state, and safely proceeds with the remaining available context.
- **Generation Failure**: Immediately records the failure and marks the run failed.

---

## 🔐 Multi-Tenant Security & Isolation

Every document, chunk, context item, and task execution strictly enforces multi-tenant ownership:
$$\text{User} \longrightarrow \text{Workspace} \longrightarrow \text{Project} \longrightarrow \text{Document} \longrightarrow \text{DocumentChunk}$$

- **Cross-Tenant Isolation**: User A can NEVER search, retrieve, preview, plan, execute tools, or access runs across User B's boundaries.
- **Tenant Scope Enforcement**: All SQL queries, tool calls, vector searches, and execution plans filter on `workspace_id` and `project_id` at the database layer.
- **Untrusted Web Content Demarcation**: All search engine snippets and external text are flagged as untrusted context to prevent prompt injection.

---

## 📡 API Reference

### Orchestration & Task Execution (Step 10)
- `POST /api/tasks/{task_id}/plan` — Preview the deterministic `ExecutionPlan` without executing the task.
- `POST /api/tasks/{task_id}/run` — Execute task through the Orchestrator pipeline, persisting `execution_plan`, `execution_steps`, and full telemetry on the `Run`.
- `POST /api/tasks/{task_id}/run/stream` — Execute task with real-time SSE streaming for `plan_generated`, `step_start`, `step_completed`, `step_failed`, `content_delta`, and `run_completed` events.

### Tools & Web Search (Step 9)
- `GET  /api/tools` — List registered tools available to the authenticated user.
- `POST /api/tools/{tool_name}/execute` — Direct testing/execution endpoint returning normalized `ToolResult`.

### Retrieval Router & Preview (Step 8)
- `POST /api/tasks/{task_id}/retrieval/preview` — Inspect the structured `RetrievalDecision` for a task.

### Document Management & Uploads (Step 7)
- `POST   /api/workspaces/{workspace_id}/documents` — Multipart upload for PDF, TXT, Markdown, DOCX with background ingestion.
- `GET    /api/workspaces/{workspace_id}/documents` — List workspace documents with project and status filters.
- `GET    /api/documents/{document_id}` — Get document status, metadata, and chunk count.
- `GET    /api/documents/{document_id}/chunks` — Inspect indexed vector chunks for a document.
- `DELETE /api/documents/{document_id}` — Delete document, vector chunks, and stored file.

### Tasks, Context & Hybrid AI Execution
- `POST   /api/projects/{project_id}/tasks` — Create task.
- `GET    /api/projects/{project_id}/tasks` — List tasks.
- `GET    /api/tasks/{task_id}` — Get task.
- `PATCH  /api/tasks/{task_id}` — Update task.
- `DELETE /api/tasks/{task_id}` — Delete task.
- `POST   /api/tasks/{task_id}/context` — Create manual context item.
- `GET    /api/tasks/{task_id}/context` — List context items.
- `GET    /api/tasks/{task_id}/context/inspect` — Debug view of assembled ContextPackage & prompt.

---

## 🚀 Local Development Setup

---

## 🤖 LLM-Assisted Planning & Bounded Agentic Loop (Step 11)

Step 11 upgrades the deterministic `ExecutionPlanner` into an **LLM-Assisted Planning System** capable of analyzing a task, evaluating available capabilities, and proposing an execution plan while strictly enforcing safety boundaries.

> **Core Principle**: The LLM may **PLAN**. The application decides whether the plan is **SAFE and VALID**. The executor performs only validated actions. The LLM NEVER directly controls tools or arbitrary code execution.

### 1. Planning Architecture

```
                 TASK
                   ↓
             Hybrid Planner
              ↙         ↘
       Deterministic      LLM (1 controlled repair attempt)
              ↘         ↙
              Proposed Plan
                    ↓
              Plan Validator (6-Layer Security & Bounds)
                    ↓
              Approved Plan
                    ↓
                 Execute (Retrieval / Web Search / Context)
                    ↓
                 Observe Evidence
                    ↓
             Completion Evaluator (Structured LLM Check)
              ↙          ↘
          Complete      Continue (Missing Info)
             ↓             ↓
       Final Generate   Re-plan (Anti-Loop Detection)
                           ↓
                        Execute
```

### 2. Planning Modes
- **`hybrid` (Automatic - Default)**: Deterministic planner establishes a safe baseline, LLM proposes a richer plan, `PlanValidator` verifies it, and the system automatically falls back to the deterministic baseline if LLM planning fails.
- **`deterministic`**: Pure rule-based execution pipeline without LLM planning overhead.
- **`llm`**: Direct LLM planning with schema/policy validation, one repair attempt, and safe failure.

### 3. Dedicated Planning Prompt & Strict Trust Boundaries
- **TRUSTED Input**: System rules, application policies, registered capabilities, task configuration.
- **UNTRUSTED Data**: Web search content, retrieved document chunks, external tool outputs.
- Prompt injection protection prevents untrusted documents or web content from executing arbitrary tools or altering permissions.

### 4. 6-Layer Plan Validation
Every proposed plan undergoes strict validation before any action executes:
1. **Layer 1: Schema Validation**: Validates step structures, required types, and IDs against Pydantic models.
2. **Layer 2: Capability Validation**: Rejects invented tools, unknown retrieval strategies, or unconfigured providers.
3. **Layer 3: Permission Validation**: Verifies user permissions and workspace ownership for all requested actions.
4. **Layer 4: Security Policy Validation**: Rejects arbitrary code, shell commands, and untrusted tool creation.
5. **Layer 5: Execution Limits**: Enforces `MAX_PLAN_STEPS=10`, `MAX_TOOL_CALLS_PER_PLAN=5`, `MAX_RETRIEVAL_CALLS_PER_PLAN=3`.
6. **Layer 6: Task Configuration Validation**: Ensures tools or retrieval are enabled in task settings before allowing them in steps.

### 5. Plan Repair Mechanism
If the LLM generates an invalid plan:
- The system performs at most **ONE** controlled repair attempt providing explicit validation error diagnostics.
- If the repaired plan is valid, it proceeds to validation and execution.
- If the second attempt fails, it falls back safely (in hybrid mode) or halts execution without looping.

### 6. Bounded Agentic Loop & Anti-Loop Protection
- **Bounded Iterations**: Hard-capped at `MAX_AGENT_ITERATIONS=3` (hard upper limit 5).
- **CompletionEvaluator**: Structured evaluation determining if sufficient evidence exists to answer the task or identifying specific missing information.
- **AntiLoopDetector**: Tracks action signatures (`tool + normalized input`, `retrieval strategy + query`). If an action is repeated identically, execution terminates immediately with a partial/completed result.

---

### 1. Backend Setup & Database Migrations

```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Configure environment
cp backend/.env.example backend/.env

# 3. Apply Alembic database migrations (up to revision 009)
python -m alembic -c backend/alembic.ini upgrade head

# 4. Run full test suite (172 passing unit, integration, and security tests)
python -m pytest -v

# 5. Start FastAPI backend server
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup & Build

```bash
# 1. Install dependencies
npm install

# 2. Run production build validation (Pure JavaScript Next.js App Router)
npm run build

# 3. Start development server
npm run dev
```

---

## 🧠 Step 12: Model Intelligence & Model Router Layer

Step 12 introduces a centralized, deterministic **Model Intelligence and Model Router Layer** that selects the most appropriate Large Language Model for both planning and generation stages based on normalized task requirements and configured policies.

```
Task
 ↓
Execution Plan
 ↓
Model Requirement Analyzer
 ↓
Model Requirements
 ↓
Model Router (Deterministic Scoring & Capability Matching)
 ↓
Model Selection (Primary Candidate + Compatible Fallbacks)
 ↓
LLM Abstraction Layer
 ↓
Provider Adapter (with Multi-Provider Fallback & Failover)
```

### Key Components

1. **Normalized Model Capabilities (`ModelCapability`)**:
   - Normalized flags: `text_generation`, `reasoning`, `structured_output`, `tool_calling`, `vision`, `long_context`, `streaming`, `embeddings`.
   - Applications depend on capabilities rather than provider-specific model IDs.

2. **Central Model Registry (`ModelRegistry`)**:
   - Manages rich metadata per model: `provider`, `model_id`, `display_name`, `capabilities`, `context_window`, `supports_streaming`, `supports_tools`, `supports_structured_output`, `supports_vision`, `enabled`, `cost_metadata` (`cost_class`, `input_cost_per_million`, `output_cost_per_million`), and `latency_class`.
   - Never exposes API keys, credentials, or sensitive infrastructure to the frontend.

3. **Deterministic Model Requirements Extraction (`ModelRequirementAnalyzer`)**:
   - Fast, local, rule-based extraction analyzing task configuration, context budget, execution plan steps, and enabled tools.
   - Requires zero external LLM calls or network latency for requirement analysis.

4. **Deterministic Model Router (`ModelRouter`)**:
   - Capability filtering ensures incompatible models are immediately disqualified.
   - Weighted scoring computes optimal candidate based on capability match, context window capacity, streaming support, tool support, and configured latency/cost preferences (`low`, `balanced`, `quality`).
   - Generates factual, audit-ready justifications without marketing superlatives.

5. **Multi-Provider Fallback & Failover**:
   - Resilient execution path: `Primary Candidate → Compatible Fallback Candidate → Final Failure`.
   - Fallback candidates are strictly pre-filtered to satisfy all task requirements and allowed server policies.
   - Configurable maximum fallback attempts (`MAX_FALLBACK_ATTEMPTS=2`).

6. **Separate Planner vs. Generation Model Modes**:
   - Dedicated configuration for planning (`PLANNER_MODEL_MODE`, `PLANNER_MODEL`, `PLANNER_MODEL_PROVIDER`) and generation (`GENERATION_MODEL_MODE`).

7. **Task Model Preference Modes**:
   - `model_mode = "auto"`: ModelRouter dynamically selects the optimal model.
   - `model_mode = "manual"`: User selects from server-approved enabled models; server validates compatibility against required capabilities.

8. **Accurate Usage Tracking & Cost Estimation**:
   - Tracks exact `input_tokens`, `output_tokens`, `total_tokens`, `latency_ms`, and `estimated_cost` calculated from verified pricing metadata (or `null` if unconfigured; never invents pricing).

---

## ✅ Step 12 Verification Checklist

- [x] Central `ModelRegistry` with normalized capabilities, context window, cost metadata, and latency classes.
- [x] Multi-vendor model catalog supporting OpenAI, Anthropic, Google Gemini, and Mock providers.
- [x] Deterministic `ModelRequirementAnalyzer` extracting requirements from task parameters, context size, and tool steps.
- [x] Deterministic `ModelRouter` scoring and filtering compatible models with factual justification.
- [x] Multi-provider resilient fallback & failover (`primary -> fallback -> final failure`) up to configured max attempts.
- [x] Task model mode support (`auto` vs `manual` model override with capability validation).
- [x] Separate planner and generation model routing configuration.
- [x] Orchestrator integration passing normalized `ModelSelection` to LLM abstraction.
- [x] API endpoints: `GET /api/models`, `POST /api/models/route`, and `POST /api/tasks/{task_id}/model-preview`.
- [x] Next.js task UI (`/app/tasks/[taskId]`) with Automatic vs Manual model selection, requirement pill checklist, routing reason preview, and cost/telemetry display.
- [x] Live SSE failover notification banner for stream execution.
- [x] Usage tracking with token metrics and `estimated_cost` (or `None` when unconfigured).
- [x] 199/199 passing backend tests (100% pass rate).
- [x] Next.js production build passing with pure JavaScript.

---

## 🔍 Step 13: Evaluation & Verification Engine

Step 13 introduces an enterprise-grade **Evaluation & Verification Engine** that evaluates task output quality, grounding, completeness, citation validity, format compliance, and policy safety through observable, structured verification checks.

```
Task
 ↓
Orchestrator
 ↓
Execution
 ↓
Draft Output
 ↓
Evaluation Engine
 ├── Grounding Check (Factual claims vs contextual evidence)
 ├── Completeness Check (Explicit task requirement coverage)
 ├── Citation / Evidence Check (Source verification & URL validation)
 ├── Format Check (JSON schema, markdown tables, sections, code)
 └── Safety / Policy Check (Secret redaction & dangerous command guards)
 ↓
Evaluation Result ({ status: passed | warning | failed, checks: [...], recommendation: accept | revise | fail })
 ↓
Orchestrator
 ├── Accept (Final output accepted and persisted)
 ├── Revise (Bounded revision prompt up to MAX_REVISION_ATTEMPTS=2)
 └── Fail safely (Partial output with clear audit diagnostics)
 ↓
Final Output
```

### Key Components

1. **Evaluation Engine Architecture (`EvaluationEngine`)**:
   - Accepts task definition, draft output, and trusted context items with stable evidence IDs.
   - Coordinates deterministic checks and pluggable structured LLM evaluators.
   - Computes overall status (`passed`, `warning`, `failed`) and actionable recommendation (`accept`, `revise`, `fail`) without generating arbitrary single numeric quality scores.
   - Evaluator engine never modifies output directly and never executes arbitrary external tools.

2. **Evaluator Suite**:
   - **`GroundingEvaluator`**: Compares factual assertions against retrieved project documents and web sources. Flags unsupported claims with stable evidence citations (`[doc:...]`, `[web:...]`). Does not assert probabilistic claims as absolute certainty.
   - **`CompletenessEvaluator`**: Evaluates observable requirement adherence against task instructions (e.g. multi-dimensional comparisons) and catches empty or truncated outputs.
   - **`CitationEvaluator`**: Validates that all cited sources in markdown link references correspond to actual retrieved context, verifies URL syntax, and detects hallucinated sources. Does not falsely require citations if no external retrieval was performed.
   - **`FormatEvaluator`**: Deterministically verifies structural constraints including valid JSON syntax, markdown tables, bullet lists, code fences, and required headers/sections.
   - **`SafetyEvaluator`**: Detects sensitive credentials, exposed API keys, private tokens, and hazardous shell patterns (`rm -rf`, raw DROP statements) before persistence.

3. **Hybrid Evaluation Abstraction (`Evaluator` -> `DeterministicEvaluator` / `LLMEvaluator`)**:
   - High-throughput deterministic checks run instantly with zero LLM overhead.
   - Semantic evaluators utilize structured Pydantic schemas (`PydanticOutputParser`) via configurable evaluator models (`EVALUATOR_MODEL_PROVIDER`, `EVALUATOR_MODEL`).
   - Private chain-of-thought and internal evaluator prompts are strictly prevented from leaking to user responses.

4. **Configurable Evaluation Policies (`EvaluationPolicy`)**:
   - **`off`**: Bypasses evaluation for high-throughput batch operations.
   - **`basic`**: Runs fast deterministic format, completeness, and safety checks.
   - **`standard`** (Default): Full evaluation suite with warnings allowing completion if critical requirements are met.
   - **`strict`**: Strict compliance mode where warnings trigger automated revision or failure.

5. **Controlled Bounded Revision Loop (`ControlledReviser`)**:
   - When evaluation recommends `revise`, the orchestrator invokes a revision cycle passing the original task, draft output, observable evaluator findings, and trusted context.
   - Hard bounded limit (`MAX_REVISION_ATTEMPTS = 2`) prevents runaway loops.
   - Revised outputs are re-evaluated through the verification engine.

6. **Strict Trust Boundaries & External Injection Defense**:
   - External retrieved documents and web pages are treated strictly as **UNTRUSTED EXTERNAL DATA**.
   - External content cannot modify evaluation policy, disable evaluators, grant tool access, or elevate model permissions.

7. **Data Model & Telemetry Records**:
   - **`EvaluationRun`**: Records `run_id`, `status`, `evaluator_type`, `started_at`, `completed_at`, and `duration_ms`.
   - **`EvaluationFinding`**: Records `check_type`, `status`, `confidence`, `description`, and `evidence_ids`.
   - **`Run`**: Extended with `evaluation_status`, `evaluation_mode`, `evaluation_duration_ms`, `evaluation_attempts`, and `revision_attempts`.

8. **Next.js Verification UI & APIs**:
   - Verification checklist card displaying individual check badges (Grounding, Completeness, Citation coverage, Format, Safety).
   - Observable findings and evidence references without exposing raw prompts or CoT.
   - Revision banner with `[ Improve Answer ]` manual action and live SSE "AI revision in progress..." status indicators.
   - API endpoints: `POST /api/tasks/{task_id}/evaluate` and `GET /api/runs/{run_id}/evaluation`.

---

## ✅ Step 13 Verification Checklist

- [x] Independent `EvaluationEngine` coordinating Grounding, Completeness, Citation, Format, and Safety evaluators.
- [x] Structured `EvaluationResult` with deterministic aggregation (`passed`, `warning`, `failed`) and recommendation (`accept`, `revise`, `fail`).
- [x] Zero exposure of chain-of-thought or raw internal evaluator prompts.
- [x] Grounding evaluator verifying claims against stable evidence IDs.
- [x] Completeness evaluator verifying observable task requirements.
- [x] Citation evaluator verifying retrieved sources and valid URLs without hallucinating citations.
- [x] Format evaluator deterministically validating JSON, tables, bullet lists, code fences, and sections.
- [x] Safety evaluator detecting credential leaks and dangerous shell patterns.
- [x] Structured LLM evaluators using Pydantic output validation.
- [x] Configurable evaluation policies (`off`, `basic`, `standard`, `strict`).
- [x] Bounded revision loop in Orchestrator (`MAX_REVISION_ATTEMPTS = 2`) with re-evaluation.
- [x] Strict trust boundary preventing external content from modifying policies or executing tools.
- [x] Extended `Run` database model with `EvaluationRun` and `EvaluationFinding` persistence and Alembic migrations.
- [x] Authenticated APIs: `POST /api/tasks/{task_id}/evaluate` and `GET /api/runs/{run_id}/evaluation`.
- [x] Next.js task UI (`/app/tasks/[taskId]`) with Verification Findings card, policy selector, and `[ Improve Answer ]` revision action.
- [x] 221/221 passing backend tests across all project modules.
- [x] Next.js production build passing with 100% pure JavaScript.

---

## 📊 Observability, Usage & Cost Intelligence (Step 14)

Step 14 introduces a production-grade, internal **Observability, Usage & Cost Intelligence Layer** that captures structured execution telemetry, granular token accounting, multi-stage latency distributions, model operational data, and end-to-end execution traces across planning, retrieval, tools, generation, evaluation, and revision.

### 1. Telemetry & Observability Architecture

```
Task Execution / Streaming Run
 ├── Stage 1: Planning   ──> TraceEvent [planning_started, planning_completed]
 ├── Stage 2: Retrieval  ──> TraceEvent [retrieval_started, retrieval_completed]
 ├── Stage 3: Tools      ──> TraceEvent [tool_started, tool_completed]
 ├── Stage 4: Generation ──> TraceEvent [generation_started, generation_completed]
 ├── Stage 5: Evaluation ──> TraceEvent [evaluation_started, evaluation_completed]
 └── Stage 6: Revision   ──> TraceEvent [revision_started, revision_completed]
       ↓
 ExecutionTracer (Buffered sequential events with auto-sequence numbering)
       ↓
 ObservabilityService (Fail-Safe Telemetry Engine)
       ├── ExecutionTraceEvent (Ordered, sanitized event stream)
       ├── UsageRecord         (Granular operation token usage & cost)
       └── RunTelemetry        (Consolidated execution summary & metrics)
       ↓
 UsageAnalyticsService (Multi-dimensional tenant-isolated aggregations)
       ├── Overview Analytics   (Runs, tokens, cost, latency, eval passes)
       ├── Usage Analytics      (Time-series token and cost trends)
       ├── Model Analytics      (Factual operational metrics per model)
       ├── Provider Analytics   (Usage share and performance by provider)
       └── Latency Analytics    (End-to-end & per-stage p50/p95 distributions)
```

### 2. Execution Trace Event Lifecycle

Every AI task execution records an ordered trace stream with zero risk to pipeline execution:
1. `run_started`: Run initialization, routed model preferences, task metadata
2. `planning_started` / `planning_completed`: Decomposition, strategy selection, plan validation
3. `retrieval_started` / `retrieval_completed`: Query expansion, vector/BM25 retrieval, reranked chunks
4. `tool_started` / `tool_completed`: Tool invocation, input validation, execution latency
5. `generation_started` / `generation_completed`: Prompt rendering, LLM invocation, token output
6. `evaluation_started` / `evaluation_completed`: Verification check results and findings
7. `revision_started` / `revision_completed`: Bounded revision loops and corrective improvements
8. `run_completed` / `run_failed`: Terminal execution status with elapsed latency and safe error codes

### 3. Usage & Cost Intelligence Formulas

Cost calculations adhere to standardized per-1M token pricing formulas configured in the model catalog:

$$\text{Input Cost} = \frac{\text{Input Tokens}}{1,000,000} \times \text{Input Price per 1M Tokens}$$

$$\text{Output Cost} = \frac{\text{Output Tokens}}{1,000,000} \times \text{Output Price per 1M Tokens}$$

$$\text{Total Run Cost} = \text{Input Cost} + \text{Output Cost}$$

- **Unconfigured Pricing**: If a model has no pricing metadata configured, `estimated_cost` returns `null` (never invented pricing).
- **Provider Usage Normalization**: Provider usage is normalized into `{ input_tokens, output_tokens, total_tokens, cached_input_tokens, estimated_cost }` with source flags (`provider`, `estimated`, `unavailable`).

### 4. Security, Sanitization & Privacy Safeguards

- **Telemetry Sanitizer (`sanitize_metadata`)**: Centralized sanitization scrubs API keys, bearer tokens, authorization headers, cookies, passwords, and secrets before persistence.
- **No Chain-of-Thought**: Private model reasoning and internal prompts are strictly excluded from persisted telemetry.
- **Bounded Payloads**: Metadata sizes are strictly capped (`MAX_TRACE_METADATA_BYTES=10240`) to prevent oversized database writes.
- **Fail-Safe Observability**: All telemetry recording operations run within fail-safe handlers so observability errors never cause AI task execution to fail.

### 5. Multi-Tenant Workspace Isolation

All telemetry, trace events, usage records, and analytics queries strictly enforce workspace boundary ownership. No workspace can ever inspect, aggregate, or delete another workspace's telemetry data.

### 6. Observability Retention & Cleanup

- System configuration: `OBSERVABILITY_RETENTION_DAYS=30` (configurable).
- Admin endpoint: `POST /api/admin/observability/cleanup?retention_days=30` safely purges old `ExecutionTraceEvent`, `UsageRecord`, and `RunTelemetry` rows without ever deleting `Task`, `Run`, `Document`, or `Evaluation` records.

### 7. Authenticated Analytics & Trace Endpoints

- `GET /api/analytics/overview` - Executive overview (runs, tokens, cost, latency, eval passes)
- `GET /api/analytics/usage` - Time-series token and cost trends by day/week/month
- `GET /api/analytics/models` - Factual operational telemetry per model
- `GET /api/analytics/providers` - Provider distribution and market share
- `GET /api/analytics/latency` - End-to-end and per-stage latency distributions
- `GET /api/analytics/evaluations` - Verification pass/fail rates and policy compliance
- `GET /api/runs/{run_id}/trace` - Sequential execution trace event timeline
- `GET /api/runs/{run_id}/usage` - Granular usage records for an execution run
- `GET /api/runs/{run_id}/telemetry` - Consolidated RunTelemetry record
- `POST /api/admin/observability/cleanup` - Retention cleanup execution

---

## ⚡ Workflow System (Step 15)

Step 15 introduces a **Production-Grade Workflow System** that enables users to build, validate, publish, template, and execute reusable multi-step AI orchestration pipelines leveraging existing context, retrieval, tools, model routing, evaluation, and observability layers.

### 1. Workflow Architecture & Lifecycle

```
Workflow Definition
      ↓
WorkflowValidator (Limits, schemas, DAG cycles, branching targets)
      ↓
Workflow Publishing (Creates immutable snapshot in WorkflowVersion)
      ↓
WorkflowRun Trigger
      ↓
Runtime Input Validation (Validates against workflow.input_schema)
      ↓
WorkflowExecutor
      ├── WorkflowExecutionState (input, context, retrieval, tool_results, outputs, evaluations)
      ├── Sequential Step Dispatch (input, context, retrieve, tool, generate, evaluate, transform, condition, output)
      ├── Safe Variable Interpolation ({{input.key}}, {{steps.step_id.output}})
      ├── Step Retry/Skip Resilience (max_retries <= 2 on transient failures)
      └── Observability Tracing (Step-by-step ExecutionTraceEvent telemetry)
      ↓
Final Output & Persisted WorkflowRun
```

### 2. Workflow Step Types

| Step Type | Description & Underlying Service Integration | Configuration Highlights |
|---|---|---|
| `input` | Captures and validates runtime parameters against the typed `input_schema` | Key mappings, parameter declarations |
| `context` | Injects workspace/project knowledge and conversational memory via `ContextEngine` | `max_tokens`, `include_workspace_context` |
| `retrieve` | Executes semantic, keyword, or hybrid document retrieval via `RetrievalRouter` | `mode`, `top_k`, `query` (supports variables) |
| `tool` | Dispatches external tools (e.g. `web_search`) via `ToolRegistry` and `ToolExecutor` | `tool`, `parameters`, `max_retries` |
| `generate` | Synthesizes responses via `ModelRouter` and LLM abstraction | `mode`, `preferred_model`, `temperature`, `prompt_template` |
| `evaluate` | Validates grounding, completeness, or factual correctness via `EvaluationEngine` | `mode`, `threshold`, `target`, `context_source` |
| `transform` | Safe structured data manipulation with zero code execution | `operation` (`select`, `rename`, `join`, `truncate`, `filter`), `source`, `fields` |
| `condition` | Server-side deterministic branching based on state values | `left`, `operator` (`==`, `!=`, `>`, `>=`, `<`, `<=`, `exists`), `right`, `if_true`, `if_false` |
| `output` | Formats and emits the terminal response | `output_template`, `format` (`markdown`, `json`, `text`) |

### 3. Built-In Workflow Templates

Workflows include four pre-configured production templates that can be installed directly into any workspace:
1. **Research Assistant**: `Input` → `Web Search` → `Context/Retrieve` → `Generate Answer` → `Evaluate Grounding` → `Output`.
2. **Document Q&A**: `Input` → `Hybrid Document Retrieval` → `Generate Response` → `Grounding Evaluation` → `Output`.
3. **Summarize & Verify**: `Input` → `Generate Summary` → `Evaluate Completeness` → `Condition (if warning revise)` → `Output`.
4. **Research Report**: `Input` → `Web Search` → `Document Retrieval` → `Generate Draft` → `Evaluate` → `Revise` → `Output`.

### 4. Versioning & Immutability Rules

- **Draft Workflows**: Editable in-place; can be modified, re-ordered, tested, and validated.
- **Published Workflows**: Publishing creates an immutable snapshot in `WorkflowVersion`. Once published, the version cannot be mutated.
- **Draft Forking on Edit**: Editing a published workflow automatically increments the version counter and sets the status back to `draft`.
- **Reproducible Execution**: Historical `WorkflowRun` records always store the exact version snapshot executed, guaranteeing full reproducibility.

### 5. Security & Isolation Safeguards

- **No Arbitrary Code Execution**: Step transforms and conditions are strictly declarative and executed through safe deterministic parsers.
- **Safe Variable Interpolation**: Resolves paths (`{{input.key}}`, `{{steps.id.output}}`) safely against validated execution state dictionaries.
- **Multi-Tenant Workspace Isolation**: Every workflow, step, version, and run is strictly partitioned by `workspace_id`.
- **Privacy & Telemetry**: Internal chain-of-thought and private model reasoning are never exposed.

### 6. Workflow API Endpoints

- `POST /api/workflows` - Create a new workflow draft
- `GET /api/workflows` - List workflows (filtered by workspace, project, status)
- `GET /api/workflows/{workflow_id}` - Retrieve workflow entity and metadata
- `PATCH /api/workflows/{workflow_id}` - Update workflow metadata
- `DELETE /api/workflows/{workflow_id}` - Delete workflow
- `GET /api/workflows/{workflow_id}/definition` - Get full definition (steps, schema)
- `PATCH /api/workflows/{workflow_id}/definition` - Update definition steps & schema
- `POST /api/workflows/{workflow_id}/validate` - Validate rules, constraints, and branch targets
- `POST /api/workflows/{workflow_id}/publish` - Publish workflow version (creates immutable snapshot)
- `POST /api/workflows/{workflow_id}/duplicate` - Clone workflow into a new draft
- `POST /api/workflows/{workflow_id}/run` - Trigger workflow run with input parameters
- `GET /api/workflows/{workflow_id}/runs` - List historical runs for a workflow
- `GET /api/workflow-runs/{run_id}` - Get execution run details and step results
- `GET /api/workflow-runs/{run_id}/trace` - Get execution observability trace events
- `GET /api/workflow-templates` - List built-in templates
- `POST /api/workflow-templates/{template_id}/install` - Install template into workspace

---

## ✅ Step 15 Verification Checklist

- [x] Complete domain models `Workflow`, `WorkflowStep`, `WorkflowVersion`, and `WorkflowRun` with compound indexes.
- [x] Alembic migration `013_workflow_system.py` generated and applied.
- [x] `WorkflowValidator` enforcing step limits, type validation, schema checks, branch targets, and depth limits.
- [x] All 9 deterministic step types (`input`, `context`, `retrieve`, `tool`, `generate`, `evaluate`, `transform`, `condition`, `output`) reusing existing backend engines.
- [x] Safe variable interpolation (`{{input.field}}`, `{{steps.step_id.output}}`) with no arbitrary code execution.
- [x] Deterministic conditional branching (`==`, `!=`, `>`, `>=`, `<`, `<=`, `exists`).
- [x] Safe structured data transformations (`select`, `rename`, `join`, `truncate`, `filter`).
- [x] Built-in templates registry with 4 initial production pipelines (`Research Assistant`, `Document Q&A`, `Summarize & Verify`, `Research Report`).
- [x] Versioning and publishing lifecycle with immutable version snapshots in `WorkflowVersion`.
- [x] Full observability integration reusing `ObservabilityService` and `ExecutionTraceEvent`.
- [x] Multi-tenant workspace and project boundary isolation strictly enforced across all workflow operations.
- [x] Pure JavaScript Next.js Workflow List page (`/app/workflows`) with filtering, template gallery, and run triggers.
- [x] Pure JavaScript Next.js Visual Workflow Builder (`/app/workflows/[workflowId]`) with step reordering, 9-type config drawer, live validation, and draft/publish controls.
- [x] Pure JavaScript Next.js Workflow Run Detail page (`/app/workflows/[workflowId]/runs/[runId]`) with step timeline, telemetry trace, variable inspector, and formatted output.
- [x] 247/247 passing backend unit & integration tests.
- [x] 100% successful Next.js production build with pure JavaScript (no TypeScript).





