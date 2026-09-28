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


