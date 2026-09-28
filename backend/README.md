# AI Work Layer — Backend Service

A high-performance Python FastAPI service providing an LLM-Assisted Planning System, Bounded Agentic Loop, provider-agnostic Tool System, Web Search Provider Integration, Context Engine, Intelligent Retrieval Router, Hybrid RAG with Vector + BM25 + Multi-Query strategies, LLM abstraction layer, PostgreSQL persistence with SQLAlchemy 2.x, multi-tenant isolation, Supabase Auth JWT verification, and Alembic database migrations.

---

## 🏛️ Architecture & Enforcement Pipeline

Every backend operation follows this mandatory architectural flow:
```
Request ──► Authentication ──► Authorization / Ownership ──► Validation ──► Service ──► Repository ──► Database
```

```
Next.js Frontend (Port 3000)
       │
       ▼ (HTTP Bearer JWT / SSE Stream)
FastAPI Backend Routes (/api/auth, /api/workspaces, /api/projects, /api/tasks, /api/tools, /api/documents, /api/context, /api/llm, /api/models, /api/health)
       │
       ├── Core Security & Auth Layer
       │     ├── get_current_user (JWT verification via Supabase secret or JWKS)
       │     ├── verify_workspace_access / verify_project_access / verify_task_access
       │     └── AuthService (Idempotent user & default workspace bootstrap)
       │
       ├── Orchestration Engine & LLM Planning (Step 10 & 11)
       │     ├── Orchestrator (Lifecycle coordinator, bounded agent loop, SSE streaming event dispatch)
       │     ├── ExecutionPlanner (Hybrid, Deterministic, LLM-Assisted planning dispatcher)
       │     ├── LLMPlanningProvider (Structured ExecutionPlan generation, prompt isolation, 1 controlled repair attempt)
       │     ├── HybridPlanner (Deterministic baseline + LLM proposal + safe automatic fallback)
       │     ├── PlanValidator (6-Layer Validation: schema, capabilities, permissions, security policies, limits, task config)
       │     ├── CompletionEvaluator (Structured evidence assessment, missing information diagnostics)
       │     ├── AntiLoopDetector (Tracks action signatures to prevent repeated queries / tool calls)
       │     ├── OrchestrationExecutor (Step execution, tool validation, context merging, failure handling)
       │     ├── ExecutionState (State tracking: iteration, planning_mode, proposed_plan, validated_plan, completion_evaluation)
       │     └── Plan Preview Endpoint (/api/tasks/{task_id}/plan)
       │
       ├── Tool System & Web Search Provider (Step 9)
       │     ├── BaseTool Interface (name, description, input_schema, requires_auth, execute, check_permission)
       │     ├── ToolRegistry (Centralized registration, lookup, Pydantic input validation)
       │     ├── ToolExecutor (Permission checks, timeout enforcement, latency measurement, normalized ToolResult)
       │     ├── WebSearchProvider Interface -> DuckDuckGoSearchProvider, TavilySearchProvider, SerperSearchProvider, MockWebSearchProvider
       │     └── Tool API Endpoints (GET /api/tools, POST /api/tools/{tool_name}/execute)
       │
       ├── Intelligent Retrieval Router (Step 8)
       │     ├── RetrievalDecisionProvider Interface
       │     ├── RuleBasedDecisionProvider (Deterministic Intent, Phrase, Scope & Grounding Analysis)
       │     ├── Modes: auto, always, never
       │     ├── Strategy Dispatcher: None, Keyword, Vector, Hybrid, Multi-Query
       │     └── Router Preview Endpoint (/api/tasks/{task_id}/retrieval/preview)
       │
       ├── Context Engine (Step 6 & 9)
       │     ├── ContextProvider Registry (task_context, manual_context, rag_context, web_context)
       │     ├── WebContextProvider (Transforms normalized search results to untrusted ContextItems with priority 60)
       │     ├── Local Deterministic Token Estimator
       │     ├── ContextBuilder (Deduplication, Priority Sorting, Budget Enforcement, Prompt Injection Boundaries)
       │     └── ContextPackage Assembly & LLM Message Formatting
       │
       ├── Retrieval Strategies & Ingestion (Step 7 & 8)
       │     ├── HybridRetriever (Reciprocal Rank Fusion - RRF)
       │     ├── VectorRetriever (pgvector cosine similarity)
       │     ├── KeywordRetriever (Lexical term coverage & sublinear TF scoring)
       │     ├── MultiQueryRetriever (Query generation, concurrent search, fusion & reranking)
       │     ├── LocalReranker (Deterministic term density & position alignment)
       │     └── Document Ingestion (PDF, Markdown, TXT, DOCX extractors & structure chunker)
       │
       ├── LLM Abstraction Layer (Dynamic Provider & Model Resolution)
       │     └── BaseLLMProvider -> OpenAIProvider, Anthropic, Gemini, Mock
       │
       └── Multi-Tenant Repository Layer (Decoupled Persistence Scoped to Owner)
             ├── UserRepository
             ├── WorkspaceRepository (scoped by owner_user_id)
             ├── ProjectRepository (scoped by workspace owner)
             ├── TaskRepository (scoped by project/workspace owner)
             ├── ContextRepository (scoped by task/workspace owner)
             ├── DocumentRepository (scoped by workspace owner)
             └── RunRepository (scoped by task/workspace owner - tracking planner_mode, planner_model, repair_count, iteration_count, completion_evaluation, execution_plan, execution_steps, orchestration_duration_ms, tools_used, retrieval_strategies, final_model, step_count, failed_step)
                   │
                   ▼
             PostgreSQL Database (AsyncPG + SQLAlchemy 2.x ORM)

```

---

## 🤖 LLM-Assisted Planning & Bounded Agentic Loop (Step 11)

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

### Untrusted External Content Boundary
Web search and document retrieval content is strictly treated as untrusted data:
```
System Instructions (Highest Trust)
      ↓
User Task (Trusted User Intent)
      ↓
Trusted Application Context
      ↓
[EXTERNAL UNTRUSTED WEB / DOCUMENT CONTENT - FACTUAL REFERENCE ONLY]
      ↓
LLM Execution
```

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.10+ (Tested on Python 3.12)
- PostgreSQL 14+ (or compatible SQLite for testing)

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp backend/.env.example backend/.env
```

Key Environment Variables:
```env
# Step 11: Planner Configuration
PLANNER_MODEL_PROVIDER=openai
PLANNER_MODEL=gpt-4o-mini
DEFAULT_PLANNER_MODE=hybrid # Options: hybrid, deterministic, llm

# Step 9: Web Search Configuration
WEB_SEARCH_PROVIDER=duckduckgo # Options: duckduckgo, tavily, serper, mock
WEB_SEARCH_API_KEY=
WEB_SEARCH_DEFAULT_LIMIT=5
WEB_SEARCH_MAX_LIMIT=20
WEB_SEARCH_TIMEOUT_SECONDS=10.0
MAX_TOOL_CALLS_PER_TASK=5
```

### 4. Run Database Migrations
```bash
python -m alembic -c backend/alembic.ini upgrade head
```

### 5. Run Development Server
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Running Tests

The test suite validates authentication, cross-tenant isolation, LLM planning, plan repair, hybrid fallback, bounded loop iterations, anti-loop detection, completion evaluation, tool registry, tool execution, web search providers, untrusted boundaries, retrieval routing policies, multi-query expansion, hybrid RAG, context assembly, budget enforcement, model completion, streaming, and error handling:
```bash
$env:PYTHONPATH="."
pytest backend/tests -v
```

---

## 📡 API Reference

### 1. Model Catalog & Model Router (Step 12)
- `GET  /api/models` — List registered LLM models with safe capability and cost metadata (no credentials).
- `POST /api/models/route` — Test and preview deterministic model selection based on normalized `ModelRequirements`.
- `POST /api/tasks/{task_id}/model-preview` — Analyze task requirements and preview proposed model without execution.

### 2. Orchestration & LLM-Assisted Planning (Step 10 & 11)
- `POST /api/tasks/{task_id}/plan` — Propose and validate structured `ExecutionPlan` using selected `planner_mode` (`hybrid`, `deterministic`, `llm`).
- `POST /api/tasks/{task_id}/run` — Execute task via Bounded Agentic Loop with dynamic model routing, fallback execution, and telemetry.
- `POST /api/tasks/{task_id}/run/stream` — Execute task with real-time SSE streaming for `model_selected`, `model_fallback`, `planning_start`, `plan_generated`, `step_start`, `step_completed`, `step_failed`, `evaluating`, `evaluation_completed`, `replan_generated`, `content_delta`, and `run_completed` events.
- `GET  /api/tasks/{task_id}/runs` — List historical runs with routed model, provider, failover attempts, and estimated cost.

### 3. Tools & Web Search (Step 9)
- `GET  /api/tools` — List registered tools available to the authenticated user
- `POST /api/tools/{tool_name}/execute` — Direct testing/execution endpoint returning normalized `ToolResult`

### 4. Retrieval Router & Preview (Step 8)
- `POST /api/tasks/{task_id}/retrieval/preview` — Debug preview of structured `RetrievalDecision`

### 5. Documents & Ingestion (Step 7)
- `POST   /api/workspaces/{workspace_id}/documents` — Multipart document upload with background ingestion
- `GET    /api/workspaces/{workspace_id}/documents` — List documents in workspace
- `GET    /api/documents/{document_id}` — Get document metadata & status
- `GET    /api/documents/{document_id}/chunks` — Inspect indexed vector chunks
- `DELETE /api/documents/{document_id}` — Delete document and chunks

### 6. Authentication, Tasks & Workspaces
- `GET    /api/auth/me` — Retrieve authenticated user profile
- `GET    /api/workspaces` — List workspaces owned by authenticated user
- `GET    /api/projects` — List projects in user's workspaces
- `GET    /api/tasks` — List tasks for authenticated user
- `POST   /api/tasks/{task_id}/context` — Create manual context item for task
- `GET    /api/tasks/{task_id}/context/inspect` — Debug inspection view of assembled context package
