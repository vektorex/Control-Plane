# AI Work Layer — Backend Service

A high-performance Python FastAPI service providing a provider-agnostic LLM abstraction layer, PostgreSQL persistence with SQLAlchemy 2.x, multi-tenant isolation, Supabase Auth JWT verification, and Alembic database migrations.

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
FastAPI Backend Routes (/api/auth, /api/workspaces, /api/projects, /api/tasks, /api/llm, /api/models, /api/health)
       │
       ├── Core Security & Auth Layer
       │     ├── get_current_user (JWT verification via Supabase secret or JWKS)
       │     ├── verify_workspace_access / verify_project_access / verify_task_access
       │     └── AuthService (Idempotent user & default workspace bootstrap)
       │
       ├── LLM Abstraction Layer (Dynamic Provider & Model Resolution)
       │     └── BaseLLMProvider -> OpenAIProvider, Anthropic, Gemini, Local
       │
       └── Multi-Tenant Repository Layer (Decoupled Persistence Scoped to Owner)
             ├── UserRepository
             ├── WorkspaceRepository (scoped by owner_user_id)
             ├── ProjectRepository (scoped by workspace owner)
             ├── TaskRepository (scoped by project/workspace owner)
             └── RunRepository (scoped by task/workspace owner)
                   │
                   ▼
             PostgreSQL Database (AsyncPG + SQLAlchemy 2.x ORM)
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
# Run migrations to head
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

The test suite validates authentication, cross-tenant isolation, request schemas, health checks, provider factory resolution, model completion, streaming, and error handling with isolated async SQLite database sessions:
```bash
python -m pytest backend/tests -v
```

---

## 🗄️ Database Management & Migrations

| Action | Command |
| :--- | :--- |
| **Apply All Migrations** | `python -m alembic -c backend/alembic.ini upgrade head` |
| **Rollback Previous Migration** | `python -m alembic -c backend/alembic.ini downgrade -1` |
| **Rollback to Empty Schema** | `python -m alembic -c backend/alembic.ini downgrade base` |
| **Inspect Static SQL** | `python -m alembic -c backend/alembic.ini upgrade head --sql` |
| **Create New Migration** | `python -m alembic -c backend/alembic.ini revision -m "description"` |

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

### 4. Tasks & Runs (Multi-Tenant Scoped)
- `GET    /api/tasks` — List tasks for authenticated user
- `GET    /api/tasks/{task_id}` — Get task by ID (404 if unowned)
- `PATCH  /api/tasks/{task_id}` — Update owned task
- `DELETE /api/tasks/{task_id}` — Cascade delete owned task
- `GET    /api/tasks/{task_id}/runs` — List runs for owned task
- `POST   /api/tasks/{task_id}/runs` — Record run telemetry for owned task

### 5. LLM Generation (Authenticated)
- `POST /api/llm/generate` — Non-streaming completion
- `POST /api/llm/generate/stream` — Real-time Server-Sent Events (SSE) token stream
