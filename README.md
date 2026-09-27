# AI Work Layer (LLM-Work-Orchestration-Layer)

> **"One workspace for getting real work done with LLMs."**

A universal, production-oriented LLM work orchestration platform that accepts complex user tasks and coordinates optimal LLMs, context sources, retrieval strategies, persistent project data, and specialized execution tools.

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    Next.js Frontend                        │
│   • Modern App Router (JavaScript + Tailwind CSS)          │
│   • Landing Page (/) & App Shell (/app, /tasks, /projects) │
│   • Developer Playground (/app/playground)                 │
└─────────────────────────────┬──────────────────────────────┘
                              │ HTTP / SSE
                              ▼
┌────────────────────────────────────────────────────────────┐
│                   Python FastAPI Backend                   │
│   • Health & Model Metadata (/api/health, /api/models)     │
│   • Synchronous & SSE Streaming (/api/llm/generate)        │
│   • Workspace, Project, Task & Run CRUD API Endpoints      │
│   • Request Validation & Structured Error Handling         │
└─────────────────────────────┬──────────────────────────────┘
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
┌─────────────────────────────┐┌─────────────────────────────┐
│    LLM Abstraction Layer    ││      Repository Layer       │
│  • Provider Factory         ││  • WorkspaceRepository      │
│  • AsyncOpenAI SDK Adapter  ││  • ProjectRepository        │
│  • Model Resolution         ││  • TaskRepository           │
│  • Token Normalization      ││  • RunRepository            │
└──────────────┬──────────────┘└─────────────┬───────────────┘
               │                             │
               ▼                             ▼
┌─────────────────────────────┐┌─────────────────────────────┐
│       LLM Providers         ││    PostgreSQL Database      │
│   (OpenAI, Anthropic, etc.) ││ (SQLAlchemy 2.x + Alembic)  │
└─────────────────────────────┘└─────────────────────────────┘
```

> **Note on Authentication:** Authentication and multi-user tenant isolation will be implemented in a subsequent step. Currently, the system uses a development-only workspace context to establish the core data model.

---

## 📂 Project Structure

```
LLM Layer/
├── backend/                         # Python FastAPI Backend Service
│   ├── alembic/                     # Alembic Database Migrations
│   │   ├── env.py                   # Async Alembic environment runner
│   │   ├── script.py.mako           # Migration template
│   │   └── versions/
│   │       └── 001_initial_schema.py# Initial migration (workspaces, projects, tasks, runs)
│   ├── alembic.ini                  # Alembic CLI configuration
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point, CORS, and lifespan
│   │   ├── config.py                # Pydantic Settings & Environment Variables
│   │   ├── api/
│   │   │   ├── deps.py              # Dependency Injection
│   │   │   └── routes/
│   │   │       ├── health.py        # GET /api/health
│   │   │       ├── models.py        # GET /api/models
│   │   │       ├── llm.py           # POST /api/llm/generate & /generate/stream
│   │   │       ├── workspaces.py    # CRUD /api/workspaces & nested projects
│   │   │       ├── projects.py      # CRUD /api/projects & nested tasks
│   │   │       └── tasks.py         # CRUD /api/tasks & /runs
│   │   ├── core/
│   │   │   ├── errors.py            # Error hierarchy & Exception handlers
│   │   │   └── logging.py           # Structured logger setup
│   │   ├── db/
│   │   │   ├── base.py              # SQLAlchemy 2.0 DeclarativeBase
│   │   │   ├── database.py          # Async engine, session factory, get_db
│   │   │   └── models/
│   │   │       ├── enums.py         # TaskStatus and RunStatus Enums
│   │   │       ├── guid.py          # Cross-dialect GUID/UUID type
│   │   │       ├── workspace.py     # Workspace entity
│   │   │       ├── project.py       # Project entity
│   │   │       ├── task.py          # Task entity
│   │   │       └── run.py           # Run telemetry entity
│   │   ├── repositories/            # Repository data access layer
│   │   │   ├── workspace.py         # Workspace CRUD
│   │   │   ├── project.py           # Project CRUD
│   │   │   ├── task.py              # Task CRUD
│   │   │   └── run.py               # Run telemetry CRUD
│   │   ├── schemas/                 # Pydantic validation schemas
│   │   │   ├── health.py
│   │   │   ├── models.py
│   │   │   ├── llm.py
│   │   │   ├── workspace.py
│   │   │   ├── project.py
│   │   │   ├── task.py
│   │   │   └── run.py
│   │   └── services/
│   │       └── llm/
│   │           ├── base.py          # BaseLLMProvider abstract interface
│   │           ├── factory.py       # LLMProviderFactory registry & router
│   │           └── providers/
│   │               └── openai.py    # OpenAI AsyncOpenAI provider adapter
│   ├── tests/                       # Pytest test suite (33 passing unit tests)
│   ├── requirements.txt             # Backend Python dependencies
│   ├── .env.example                 # Backend environment variable template
│   └── README.md                    # Backend specific documentation
├── src/                             # Next.js Frontend Application
│   ├── app/                         # App Router pages and layouts
│   │   ├── page.jsx                 # SaaS landing page (/)
│   │   ├── layout.jsx               # Root layout & design tokens
│   │   └── app/
│   │       ├── layout.jsx           # Authenticated App Shell with WorkspaceProvider
│   │       ├── page.jsx             # Live Workspace Dashboard (/app)
│   │       ├── playground/page.jsx  # LLM Abstraction Playground (/app/playground)
│   │       ├── tasks/page.jsx       # Real-time Tasks Management (/app/tasks)
│   │       ├── projects/page.jsx    # Projects & Context Scopes (/app/projects)
│   │       └── settings/page.jsx    # Platform & Engine Settings (/app/settings)
│   ├── components/
│   │   ├── landing/                 # Hero, Architecture, Capabilities, Navbar, Footer
│   │   ├── shell/                   # AppSidebar, AppHeader, WorkspaceSelector
│   │   ├── ui/                      # Reusable Button, Card, Badge, Input, Select, Modal, Table
│   │   └── features/                # Domain-specific components (Projects, Tasks, Dashboard)
│   ├── config/                      # Site, env, and constants configs
│   ├── lib/                         # API client and WorkspaceContext
│   ├── services/                    # Frontend services (workspaces, projects, tasks, orchestrator)
│   └── styles/                      # Tailwind CSS v4 & custom dark theme tokens
├── package.json
└── README.md
```

---

## ⚡ Getting Started

### 1. Prerequisites
- **Node.js**: `v20+` (Tested on `v24`)
- **Python**: `3.10+` (Tested on `3.12`)
- **PostgreSQL**: `14+`

---

### 2. Backend Setup & Database Migrations

```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Configure environment
cp backend/.env.example backend/.env

# Configure your DATABASE_URL in backend/.env:
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_work_layer

# Optional: Add your OpenAI API Key:
# OPENAI_API_KEY=sk-...

# 3. Create the PostgreSQL database (if not already created)
# createdb ai_work_layer

# 4. Run Alembic database migrations
python -m alembic -c backend/alembic.ini upgrade head

# 5. Run backend tests (33 unit tests with async database isolation)
python -m pytest backend/tests -v

# 6. Start FastAPI backend server
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be running at `http://localhost:8000`.
- **API Docs (Swagger UI)**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/api/health`
- **Model Directory**: `http://localhost:8000/api/models`
- **Workspaces API**: `http://localhost:8000/api/workspaces`

---

### 3. Database Migration Commands

| Action | Command |
| :--- | :--- |
| **Apply All Migrations** | `python -m alembic -c backend/alembic.ini upgrade head` |
| **Rollback 1 Migration** | `python -m alembic -c backend/alembic.ini downgrade -1` |
| **Rollback to Base** | `python -m alembic -c backend/alembic.ini downgrade base` |
| **View Migration History** | `python -m alembic -c backend/alembic.ini history` |
| **Inspect Pending SQL** | `python -m alembic -c backend/alembic.ini upgrade head --sql` |

---

### 4. Frontend Setup & Startup

```bash
# 1. Install dependencies
npm install

# 2. Run lint & build validation
npm run lint
npm run build

# 3. Start development server
npm run dev
```

Frontend will be running at `http://localhost:3000`.
- **Landing Page**: `http://localhost:3000/`
- **Workspace Dashboard**: `http://localhost:3000/app`
- **Projects Management**: `http://localhost:3000/app/projects`
- **Tasks & Runs Management**: `http://localhost:3000/app/tasks`
- **LLM Abstraction Playground**: `http://localhost:3000/app/playground`

---

## 📡 Core API Reference

### Workspaces
- `POST   /api/workspaces` — Create workspace
- `GET    /api/workspaces` — List workspaces
- `GET    /api/workspaces/{workspace_id}` — Get workspace by ID
- `PATCH  /api/workspaces/{workspace_id}` — Update workspace
- `DELETE /api/workspaces/{workspace_id}` — Cascade delete workspace

### Projects
- `POST   /api/workspaces/{workspace_id}/projects` — Create project in workspace
- `GET    /api/workspaces/{workspace_id}/projects` — List projects in workspace
- `GET    /api/projects` — List all projects
- `GET    /api/projects/{project_id}` — Get project by ID
- `PATCH  /api/projects/{project_id}` — Update project
- `DELETE /api/projects/{project_id}` — Cascade delete project

### Tasks & Runs
- `POST   /api/projects/{project_id}/tasks` — Create task in project
- `GET    /api/projects/{project_id}/tasks` — List tasks in project
- `GET    /api/tasks` — List all tasks (with status filtering)
- `GET    /api/tasks/{task_id}` — Get task by ID
- `PATCH  /api/tasks/{task_id}` — Update task status/title/description
- `DELETE /api/tasks/{task_id}` — Cascade delete task
- `GET    /api/tasks/{task_id}/runs` — List execution runs for task
- `POST   /api/tasks/{task_id}/runs` — Record an execution run

### LLM Orchestration
- `GET    /api/models` — List registered models across providers
- `POST   /api/llm/generate` — Synchronous completion
- `POST   /api/llm/generate/stream` — SSE token stream
