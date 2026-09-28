# AI Work Layer — Backend Service

A high-performance Python FastAPI service providing a provider-agnostic Context Engine & LLM abstraction layer, PostgreSQL persistence with SQLAlchemy 2.x, multi-tenant isolation, Supabase Auth JWT verification, and Alembic database migrations.

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
FastAPI Backend Routes (/api/auth, /api/workspaces, /api/projects, /api/tasks, /api/context, /api/llm, /api/models, /api/health)
       │
       ├── Core Security & Auth Layer
       │     ├── get_current_user (JWT verification via Supabase secret or JWKS)
       │     ├── verify_workspace_access / verify_project_access / verify_task_access
       │     └── AuthService (Idempotent user & default workspace bootstrap)
       │
       ├── Context Engine (Step 6)
       │     ├── ContextProvider Registry (task_context, manual_context, future vector/web/git)
       │     ├── Local Deterministic Token Estimator
       │     ├── ContextBuilder (Deduplication, Priority Sorting, Budget Enforcement)
       │     └── ContextPackage Assembly & LLM Message Formatting
       │
       ├── LLM Abstraction Layer (Dynamic Provider & Model Resolution)
       │     └── BaseLLMProvider -> OpenAIProvider, Anthropic, Gemini, Local
       │
       └── Multi-Tenant Repository Layer (Decoupled Persistence Scoped to Owner)
             ├── UserRepository
             ├── WorkspaceRepository (scoped by owner_user_id)
             ├── ProjectRepository (scoped by workspace owner)
             ├── TaskRepository (scoped by project/workspace owner)
             ├── ContextRepository (scoped by task/workspace owner)
             └── RunRepository (scoped by task/workspace owner)
                   │
                   ▼
             PostgreSQL Database (AsyncPG + SQLAlchemy 2.x ORM)
```

---

## 🧠 Context Engine Abstraction

The Context Engine enables multi-source context collection and packaging without tightly coupling execution to any single retrieval mechanism.

### Key Classes (`backend/app/services/context/`):
- `ContextProvider`: Abstract base class with `can_handle()`, `collect()`, `normalize()`, `provide()`.
- `TaskContextProvider`: Extracts baseline context from the `Task` entity (`context_text`, instructions).
- `ManualContextProvider`: Gathers user-attached `TaskContext` records.
- `ContextProviderRegistry`: Registry for dynamic registration of future RAG, vector, web, and tool providers.
- `ContextBuilder`: Deduplicates identical content via SHA-256 fingerprints, sorts by priority/relevance/recency, enforces `max_context_tokens` budget limits, and produces `ContextPackage`.
- `TaskExecutionService`: Orchestrates `ContextEngine.build_context()` -> message formatting -> LLM invocation -> Run telemetry persistence.

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
Set your database, Supabase Auth secret, and provider API keys:
```env
# PostgreSQL connection (AsyncPG driver)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_work_layer

# Supabase Auth
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
SUPABASE_ANON_KEY=your-supabase-anon-key

# OpenAI configuration
OPENAI_API_KEY=sk-...
OPENAI_DEFAULT_MODEL=gpt-4o-mini
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

The test suite validates authentication, cross-tenant isolation, Context Engine collection, budget enforcement, token estimation, model completion, streaming, and error handling:
```bash
python -m pytest backend/tests -v
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

### 4. Tasks & Context (Multi-Tenant Scoped)
- `GET    /api/tasks` — List tasks for authenticated user
- `GET    /api/tasks/{task_id}` — Get task by ID (404 if unowned)
- `PATCH  /api/tasks/{task_id}` — Update owned task
- `DELETE /api/tasks/{task_id}` — Cascade delete owned task
- `POST   /api/tasks/{task_id}/context` — Create manual context item for task
- `GET    /api/tasks/{task_id}/context` — List context items for task
- `GET    /api/tasks/{task_id}/context/inspect` — Debug inspection view of assembled context package
- `PATCH  /api/context/{context_id}` — Update individual context item
- `DELETE /api/context/{context_id}` — Delete individual context item

### 5. Task AI Execution & Runs (Multi-Tenant Scoped)
- `POST   /api/tasks/{task_id}/run` — Execute task via Context Engine & LLM
- `POST   /api/tasks/{task_id}/run/stream` — Execute task with real-time SSE streaming
- `GET    /api/tasks/{task_id}/runs` — List runs for owned task
- `POST   /api/tasks/{task_id}/runs` — Record run telemetry for owned task

### 6. LLM Generation (Authenticated)
- `POST /api/llm/generate` — Non-streaming direct completion
- `POST /api/llm/generate/stream` — Real-time Server-Sent Events (SSE) token stream
