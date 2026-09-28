# AI Work Layer — Backend Service

A high-performance Python FastAPI service providing a provider-agnostic Context Engine, Intelligent Retrieval Router, Hybrid RAG with Vector + BM25 + Multi-Query strategies, LLM abstraction layer, PostgreSQL persistence with SQLAlchemy 2.x, multi-tenant isolation, Supabase Auth JWT verification, and Alembic database migrations.

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
FastAPI Backend Routes (/api/auth, /api/workspaces, /api/projects, /api/tasks, /api/documents, /api/context, /api/llm, /api/models, /api/health)
       │
       ├── Core Security & Auth Layer
       │     ├── get_current_user (JWT verification via Supabase secret or JWKS)
       │     ├── verify_workspace_access / verify_project_access / verify_task_access
       │     └── AuthService (Idempotent user & default workspace bootstrap)
       │
       ├── Intelligent Retrieval Router (Step 8)
       │     ├── RetrievalDecisionProvider Interface
       │     ├── RuleBasedDecisionProvider (Deterministic Intent, Phrase, Scope & Grounding Analysis)
       │     ├── Modes: auto, always, never
       │     ├── Strategy Dispatcher: None, Keyword, Vector, Hybrid, Multi-Query
       │     └── Router Preview Endpoint (/api/tasks/{task_id}/retrieval/preview)
       │
       ├── Context Engine (Step 6)
       │     ├── ContextProvider Registry (task_context, manual_context, rag_context)
       │     ├── Local Deterministic Token Estimator
       │     ├── ContextBuilder (Deduplication, Priority Sorting, Budget Enforcement)
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
             └── RunRepository (scoped by task/workspace owner)
                   │
                   ▼
             PostgreSQL Database (AsyncPG + SQLAlchemy 2.x ORM)
```

---

## 🧭 Intelligent Retrieval Router (Step 8)

The Retrieval Router analyzes task instructions, user mode preferences, and grounding signals to decide whether external knowledge retrieval is necessary and dispatches the optimal strategy.

```
Task
 ↓
Retrieval Router (RuleBasedDecisionProvider)
 ↓
Decision (RetrievalDecision)
 ↓
Retriever (None / Keyword / Vector / Hybrid / Multi-Query)
 ↓
ContextEngine
 ↓
LLM
```

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.10+ (Tested on Python 3.12)
- PostgreSQL 14+ (or compatible)

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp backend/.env.example backend/.env
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

The test suite validates authentication, cross-tenant isolation, retrieval routing policies, multi-query expansion, hybrid RAG, context assembly, budget enforcement, model completion, streaming, and error handling:
```bash
python -m pytest -v
```

---

## 📡 API Reference

### 1. Authentication & Profiles
- `GET /api/auth/me` — Retrieve authenticated user profile and default workspace context

### 2. Workspaces (Multi-Tenant Scoped)
- `POST   /api/workspaces` — Create workspace owned by authenticated user
- `GET    /api/workspaces` — List workspaces owned by authenticated user
- `GET    /api/workspaces/{workspace_id}` — Get workspace by ID (404 if unowned)
- `PATCH  /api/workspaces/{workspace_id}` — Update owned workspace
- `DELETE /api/workspaces/{workspace_id}` — Cascade delete owned workspace
- `POST   /api/workspaces/{workspace_id}/projects` — Create project under owned workspace
- `GET    /api/workspaces/{workspace_id}/projects` — List projects in owned workspace

### 3. Projects (Multi-Tenant Scoped)
- `GET    /api/projects` — List all projects belonging to user's workspaces
- `GET    /api/projects/{project_id}` — Get project by ID (404 if unowned)
- `PATCH  /api/projects/{project_id}` — Update owned project
- `DELETE /api/projects/{project_id}` — Cascade delete owned project
- `POST   /api/projects/{project_id}/tasks` — Create task under owned project
- `GET    /api/projects/{project_id}/tasks` — List tasks under owned project

### 4. Documents & Ingestion (Step 7)
- `POST   /api/workspaces/{workspace_id}/documents` — Multipart document upload with background ingestion
- `GET    /api/workspaces/{workspace_id}/documents` — List documents in workspace
- `GET    /api/documents/{document_id}` — Get document metadata & status
- `GET    /api/documents/{document_id}/chunks` — Inspect indexed vector chunks
- `DELETE /api/documents/{document_id}` — Delete document and chunks

### 5. Tasks, Retrieval Router & Context
- `GET    /api/tasks` — List tasks for authenticated user
- `GET    /api/tasks/{task_id}` — Get task by ID (404 if unowned)
- `PATCH  /api/tasks/{task_id}` — Update owned task
- `DELETE /api/tasks/{task_id}` — Cascade delete owned task
- `POST   /api/tasks/{task_id}/retrieval/preview` — Debug preview of structured `RetrievalDecision`
- `POST   /api/tasks/{task_id}/context` — Create manual context item for task
- `GET    /api/tasks/{task_id}/context` — List context items for task
- `GET    /api/tasks/{task_id}/context/inspect` — Debug inspection view of assembled context package
- `PATCH  /api/context/{context_id}` — Update individual context item
- `DELETE /api/context/{context_id}` — Delete individual context item

### 6. Task AI Execution & Runs (Multi-Tenant Scoped)
- `POST   /api/tasks/{task_id}/run` — Execute task via Retrieval Router + Context Engine + LLM
- `POST   /api/tasks/{task_id}/run/stream` — Execute task with real-time SSE streaming + retrieval decision telemetry
- `GET    /api/tasks/{task_id}/runs` — List runs for owned task
- `POST   /api/tasks/{task_id}/runs` — Record run telemetry for owned task
