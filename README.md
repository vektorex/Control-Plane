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

## 🔐 Multi-Tenant Security & Isolation

Every document, chunk, context item, and task execution strictly enforces multi-tenant ownership:
$$\text{User} \longrightarrow \text{Workspace} \longrightarrow \text{Project} \longrightarrow \text{Document} \longrightarrow \text{DocumentChunk}$$

- **Cross-Tenant Isolation**: User A can NEVER search, retrieve, preview, execute tools, or access runs across User B's boundaries.
- **Tenant Scope Enforcement**: All SQL queries, tool calls, and vector searches filter on `workspace_id` and `project_id` at the database layer.
- **Safety Limits**: Configurable server-side limits (`WEB_SEARCH_MAX_LIMIT=20`, `MAX_TOOL_CALLS_PER_TASK=5`, `MAX_RETRIEVAL_RESULTS=50`).

---

## 📡 API Reference

### Tools & Web Search (Step 9)
- `GET  /api/tools` — List registered tools available to the authenticated user
- `POST /api/tools/{tool_name}/execute` — Direct testing/execution endpoint returning normalized `ToolResult`

### Retrieval Router & Preview (Step 8)
- `POST /api/tasks/{task_id}/retrieval/preview` — Inspect the structured `RetrievalDecision` for a task without executing the LLM or creating a run record.

### Document Management & Uploads (Step 7)
- `POST   /api/workspaces/{workspace_id}/documents` — Multipart upload for PDF, TXT, Markdown, DOCX with background ingestion
- `GET    /api/workspaces/{workspace_id}/documents` — List workspace documents with project and status filters
- `GET    /api/documents/{document_id}` — Get document status, metadata, and chunk count
- `GET    /api/documents/{document_id}/chunks` — Inspect indexed vector chunks for a document
- `DELETE /api/documents/{document_id}` — Delete document, vector chunks, and stored file

### Tasks, Context & Hybrid AI Execution
- `POST   /api/projects/{project_id}/tasks` — Create task
- `GET    /api/projects/{project_id}/tasks` — List tasks
- `GET    /api/tasks/{task_id}` — Get task
- `PATCH  /api/tasks/{task_id}` — Update task
- `DELETE /api/tasks/{task_id}` — Delete task
- `POST   /api/tasks/{task_id}/context` — Create manual context item
- `GET    /api/tasks/{task_id}/context` — List context items
- `GET    /api/tasks/{task_id}/context/inspect` — Debug view of assembled ContextPackage & prompt
- `POST   /api/tasks/{task_id}/run` — Execute task with Retrieval Router + Tools + ContextEngine + Telemetry
- `POST   /api/tasks/{task_id}/run/stream` — Execute task with SSE streaming + Tools + Retrieval Router Telemetry

---

## 🚀 Local Development Setup

### 1. Backend Setup & Database Migrations

```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Configure environment
cp backend/.env.example backend/.env

# 3. Apply Alembic database migrations (up to revision 007)
python -m alembic -c backend/alembic.ini upgrade head

# 4. Run full test suite (127 passing unit, integration, and security tests)
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

## ✅ Step 9 Verification Checklist

- [x] Provider-independent `BaseTool` interface (`name`, `description`, `input_schema`, `requires_auth`, `execute`, `check_permission`).
- [x] Centralized `ToolRegistry` with schema validation and metadata reflection.
- [x] Resilient `ToolExecutor` with permission validation, timeouts, latency tracking, and normalized `ToolResult`.
- [x] Pluggable `WebSearchProvider` interface with DuckDuckGo, Tavily, Serper, and Mock implementations.
- [x] Strict `WebSearchInput` validation (query length, min/max limits, recency filters).
- [x] Normalized `WebSearchResultItem` structure across all search providers.
- [x] `WebContextProvider` converting search results into untrusted `ContextItem`s (`source_type="web"`, priority 60).
- [x] Prompt injection trust boundary demarcations protecting system instructions from external web content.
- [x] Development API endpoints `GET /api/tools` and `POST /api/tools/{tool_name}/execute`.
- [x] Task tool configuration (`tool_mode`, `tools_enabled`, `enable_web_search`, `web_search_query`, `web_search_limit`, `web_search_recency_days`).
- [x] Alembic migration `007_tool_execution_metadata` persisting `tools_used`, `tool_call_count`, `tool_latency_ms`, `tool_errors`, `tool_executions` on Runs.
- [x] Frontend Task Workspace (`/app/tasks/[taskId]`) with Web Search toggle, query overrides, limit controls, grounded source cards with clickable URLs, and tool execution diagnostics.
- [x] 127/127 passing backend tests across all Steps 1–9.
- [x] Next.js production build passing with pure JavaScript.

