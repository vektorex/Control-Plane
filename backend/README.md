# AI Work Layer — Backend Service

A high-performance Python FastAPI service providing a provider-agnostic LLM abstraction layer, PostgreSQL persistence with SQLAlchemy 2.x, and Alembic database migrations.

---

## 🏛️ Architecture Overview

```
Next.js Frontend (Port 3000)
       │
       ▼ (HTTP / SSE)
FastAPI Backend Routes (/api/workspaces, /api/projects, /api/tasks, /api/llm, /api/models, /api/health)
       │
       ├── LLM Abstraction Layer (Dynamic Provider & Model Resolution)
       │     └── BaseLLMProvider -> OpenAIProvider, Anthropic, Gemini, Local
       │
       └── Repository Layer (Decoupled Persistence & Query Handlers)
             ├── WorkspaceRepository
             ├── ProjectRepository
             ├── TaskRepository
             └── RunRepository
                   │
                   ▼
             PostgreSQL Database (AsyncPG + SQLAlchemy 2.x ORM)
```

> **Note on Authentication:** Authentication and multi-user tenant isolation will be implemented in a subsequent step. Currently, the system operates in a development-only workspace context to establish the core data model.

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
Set your database and provider API keys:
```env
# PostgreSQL connection (AsyncPG driver)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_work_layer

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

The test suite validates request schemas, health checks, provider factory resolution, model completion, streaming, workspace/project/task CRUD, and error handling with isolated async SQLite database sessions:
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

### 1. Health Status
`GET /api/health`
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2026-09-27T12:00:00Z",
  "environment": "development",
  "providers_configured": ["openai"]
}
```

### 2. Workspaces
- `POST   /api/workspaces` — Create workspace
- `GET    /api/workspaces` — List workspaces
- `GET    /api/workspaces/{workspace_id}` — Get workspace by ID
- `PATCH  /api/workspaces/{workspace_id}` — Update workspace
- `DELETE /api/workspaces/{workspace_id}` — Cascade delete workspace
- `POST   /api/workspaces/{workspace_id}/projects` — Create project under workspace
- `GET    /api/workspaces/{workspace_id}/projects` — List projects in workspace

### 3. Projects
- `GET    /api/projects` — List all projects across platform
- `GET    /api/projects/{project_id}` — Get project by ID
- `PATCH  /api/projects/{project_id}` — Update project
- `DELETE /api/projects/{project_id}` — Cascade delete project
- `POST   /api/projects/{project_id}/tasks` — Create task under project
- `GET    /api/projects/{project_id}/tasks` — List tasks under project

### 4. Tasks & Runs
- `GET    /api/tasks` — List all tasks (supports `?status=draft|active|completed|archived`)
- `GET    /api/tasks/{task_id}` — Get task by ID
- `PATCH  /api/tasks/{task_id}` — Update task
- `DELETE /api/tasks/{task_id}` — Cascade delete task
- `GET    /api/tasks/{task_id}/runs` — List runs associated with task
- `POST   /api/tasks/{task_id}/runs` — Record run telemetry

### 5. LLM Generation
- `POST /api/llm/generate` — Non-streaming completion
- `POST /api/llm/generate/stream` — Real-time Server-Sent Events (SSE) token stream
