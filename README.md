# AI Work Layer (LLM-Work-Orchestration-Layer)

> **"One workspace for getting real work done with LLMs."**

A universal, production-oriented LLM work orchestration platform that accepts complex user tasks and coordinates optimal LLMs, context sources, retrieval strategies, persistent project data, multi-tenant workspace isolation, and specialized execution tools.

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    Next.js Frontend                        │
│   • Modern App Router (JavaScript + Tailwind CSS)          │
│   • Supabase Auth Provider & Session Lifecycle             │
│   • Protected App Shell (/app, /tasks, /projects, /settings)│
│   • Developer Playground (/app/playground)                 │
└─────────────────────────────┬──────────────────────────────┘
                              │ HTTP (Bearer JWT) / SSE Stream
                              ▼
┌────────────────────────────────────────────────────────────┐
│                   Python FastAPI Backend                   │
│   • JWT Signature & Expiry Verification (Independent Auth) │
│   • Multi-Tenant Resource Ownership Authorization Layer    │
│   • Health & Model Metadata (/api/health, /api/models)     │
│   • Synchronous & SSE Streaming (/api/llm/generate)        │
│   • User Profile, Workspace, Project, Task & Run Endpoints │
│   • Request Validation & Structured Error Handling         │
└─────────────────────────────┬──────────────────────────────┘
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
┌─────────────────────────────┐┌─────────────────────────────┐
│    LLM Abstraction Layer    ││      Repository Layer       │
│  • Provider Factory         ││  • UserRepository           │
│  • AsyncOpenAI SDK Adapter  ││  • WorkspaceRepository      │
│  • Model Resolution         ││  • ProjectRepository        │
│  • Token Normalization      ││  • TaskRepository           │
│                             ││  • RunRepository            │
└──────────────┬──────────────┘└─────────────┬───────────────┘
               │                             │
               ▼                             ▼
┌─────────────────────────────┐┌─────────────────────────────┐
│       LLM Providers         ││    PostgreSQL Database      │
│   (OpenAI, Anthropic, etc.) ││ (SQLAlchemy 2.x + Alembic)  │
│                             ││ Multi-Tenant User Isolation │
└─────────────────────────────┘└─────────────────────────────┘
```

---

## 🔐 Authentication & Multi-Tenant Authorization Model

### Architectural Flow
Every backend operation strictly enforces the following pipeline:
```
Request ──► Authentication ──► Authorization / Ownership ──► Validation ──► Service ──► Repository ──► Database
```

1. **Authentication**:
   - The frontend authenticates via **Supabase Auth** (`email/password`).
   - Requests to `/api/*` automatically attach `Authorization: Bearer <access_token>`.
   - The FastAPI backend independently verifies token signature, claims (`sub`, `email`, `aud`), and expiration using `SUPABASE_JWT_SECRET` (or dev secret fallback). No client-provided user IDs or workspace IDs are trusted.
2. **First-Visit Workspace Bootstrap**:
   - Upon first valid authenticated call, the backend idempotently creates a `User` profile and provisions a default `Workspace` (`Default Workspace`, slug: `default`) with a starter `Project`.
   - Repeated logins never create duplicate workspaces.
3. **Multi-Tenant Ownership & Resource Isolation**:
   - Hierarchical data model:
     $$\text{Authenticated User} \longrightarrow \text{Workspace} \longrightarrow \text{Project} \longrightarrow \text{Task} \longrightarrow \text{Run}$$
   - When User A requests a resource belonging to User B, the backend returns a `404 Not Found` (never leaking whether another tenant's resource exists).
   - Compound unique constraint on `(owner_user_id, slug)` allows distinct users to independently own workspaces and projects with identical names or slugs without collisions.

---

## 📂 Project Structure

```
LLM Layer/
├── backend/                         # Python FastAPI Backend Service
│   ├── alembic/                     # Alembic Database Migrations
│   │   ├── env.py                   # Async Alembic environment runner
│   │   └── versions/
│   │       ├── 001_initial_schema.py# Initial schema (workspaces, projects, tasks, runs)
│   │       └── 002_user_and_workspace_ownership.py # User profile & multi-tenant ownership
│   ├── alembic.ini                  # Alembic CLI configuration
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point, CORS, and lifespan
│   │   ├── config.py                # Pydantic Settings & Supabase/JWT Config
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── auth.py          # GET /api/auth/me profile & workspace bootstrap
│   │   │       ├── health.py        # GET /api/health
│   │   │       ├── models.py        # GET /api/models
│   │   │       ├── llm.py           # Authenticated /api/llm/generate & stream
│   │   │       ├── workspaces.py    # Multi-tenant /api/workspaces CRUD
│   │   │       ├── projects.py      # Multi-tenant /api/projects CRUD
│   │   │       └── tasks.py         # Multi-tenant /api/tasks & /runs CRUD
│   │   ├── core/
│   │   │   ├── auth.py              # JWT verification & get_current_user dependency
│   │   │   ├── authorization.py     # Hierarchical ownership verification dependencies
│   │   │   ├── errors.py            # Structured errors (AuthenticationError, NotFoundError, etc.)
│   │   │   └── logging.py           # Structured logger setup
│   │   ├── db/
│   │   │   ├── base.py              # SQLAlchemy 2.0 DeclarativeBase
│   │   │   ├── database.py          # Async engine, session factory, get_db
│   │   │   └── models/
│   │   │       ├── user.py          # User/Profile entity
│   │   │       ├── workspace.py     # Workspace entity (with owner_user_id)
│   │   │       ├── project.py       # Project entity
│   │   │       ├── task.py          # Task entity
│   │   │       └── run.py           # Run telemetry entity
│   │   ├── repositories/            # Multi-tenant repository data access layer
│   │   │   ├── user.py              # User profile persistence
│   │   │   ├── workspace.py         # Workspace CRUD scoped to owner
│   │   │   ├── project.py           # Project CRUD scoped to owner workspace
│   │   │   ├── task.py              # Task CRUD scoped to owner project
│   │   │   └── run.py               # Run telemetry CRUD scoped to owner task
│   │   ├── schemas/                 # Pydantic validation schemas
│   │   └── services/                # Business logic & LLM abstraction
│   ├── tests/                       # Pytest test suite (44 passing tests)
│   ├── requirements.txt             # Backend Python dependencies
│   ├── .env.example                 # Backend environment variable template
│   └── README.md                    # Backend specific documentation
├── src/                             # Next.js Frontend Application
│   ├── app/                         # App Router pages and layouts
│   │   ├── page.jsx                 # SaaS landing page (/)
│   │   ├── login/page.jsx           # Sign in page (/login)
│   │   ├── signup/page.jsx          # Create account page (/signup)
│   │   └── app/
│   │       ├── layout.jsx           # Authenticated App Shell with route protection
│   │       ├── page.jsx             # Live Workspace Dashboard (/app)
│   │       ├── playground/page.jsx  # Protected LLM Abstraction Playground (/app/playground)
│   │       ├── tasks/page.jsx       # Real-time Tasks Management (/app/tasks)
│   │       ├── projects/page.jsx    # Projects & Context Scopes (/app/projects)
│   │       └── settings/page.jsx    # Platform & Auth Settings (/app/settings)
│   ├── components/                  # UI components, layout shell, and settings tabs
│   ├── lib/
│   │   ├── authContext.jsx          # AuthProvider & useAuth hook
│   │   ├── supabaseClient.js        # Supabase client with offline dev fallback
│   │   ├── workspaceContext.jsx     # User-scoped workspace context
│   │   └── api.js                   # Authenticated HTTP client
│   └── services/                    # Frontend service adapters
├── package.json
└── README.md
```

---

## ⚡ Environment Variables

### Frontend (`.env.local` / `.env`)
```bash
NEXT_PUBLIC_APP_NAME="AI Work Layer"
NEXT_PUBLIC_APP_URL="http://localhost:3000"
NEXT_PUBLIC_ORCHESTRATION_API_URL="http://localhost:8000/api"

# Supabase Auth
NEXT_PUBLIC_SUPABASE_URL="https://your-project.supabase.co"
NEXT_PUBLIC_SUPABASE_ANON_KEY="your-supabase-anon-key"
```

### Backend (`backend/.env`)
```bash
ENVIRONMENT="development"
DEBUG=true
HOST="0.0.0.0"
PORT=8000
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# PostgreSQL Database (SQLAlchemy AsyncPG)
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/ai_work_layer"

# Supabase Auth & JWT Verification
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_JWT_SECRET="your-supabase-jwt-secret"
SUPABASE_ANON_KEY="your-supabase-anon-key"

# OpenAI Provider
OPENAI_API_KEY="sk-..."
OPENAI_DEFAULT_MODEL="gpt-4o-mini"
```

---

## 🚀 Local Development Setup

### 1. Backend Setup & Database Migrations

```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Configure environment
cp backend/.env.example backend/.env

# 3. Apply Alembic database migrations
python -m alembic -c backend/alembic.ini upgrade head

# 4. Run full test suite (44 passing unit and integration tests)
python -m pytest backend/tests -v

# 5. Start FastAPI backend server
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend endpoints:
- **Swagger Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/api/health`
- **Auth Profile**: `http://localhost:8000/api/auth/me`

---

### 2. Frontend Setup & Startup

```bash
# 1. Install dependencies
npm install

# 2. Run lint and build validation
npm run lint
npm run build

# 3. Start development server
npm run dev
```

Frontend routes:
- **Landing Page**: `http://localhost:3000/`
- **Sign In**: `http://localhost:3000/login`
- **Sign Up**: `http://localhost:3000/signup`
- **Protected Dashboard**: `http://localhost:3000/app`
- **Protected Projects**: `http://localhost:3000/app/projects`
- **Protected Tasks**: `http://localhost:3000/app/tasks`
- **Protected Playground**: `http://localhost:3000/app/playground`
- **Account & Settings**: `http://localhost:3000/app/settings`

---

## 📡 API Reference

### Authentication & Profiles
- `GET    /api/auth/me` — Retrieve authenticated user profile and default workspace context

### Workspaces (Multi-Tenant Scoped)
- `POST   /api/workspaces` — Create workspace owned by authenticated user
- `GET    /api/workspaces` — List workspaces owned by authenticated user
- `GET    /api/workspaces/{workspace_id}` — Get workspace by ID (404 if unowned)
- `PATCH  /api/workspaces/{workspace_id}` — Update owned workspace
- `DELETE /api/workspaces/{workspace_id}` — Cascade delete owned workspace

### Projects (Multi-Tenant Scoped)
- `POST   /api/workspaces/{workspace_id}/projects` — Create project in owned workspace
- `GET    /api/workspaces/{workspace_id}/projects` — List projects in owned workspace
- `GET    /api/projects` — List all projects in user's workspaces
- `GET    /api/projects/{project_id}` — Get project by ID (404 if unowned)
- `PATCH  /api/projects/{project_id}` — Update owned project
- `DELETE /api/projects/{project_id}` — Cascade delete owned project

### Tasks & Runs (Multi-Tenant Scoped)
- `POST   /api/projects/{project_id}/tasks` — Create task in owned project
- `GET    /api/projects/{project_id}/tasks` — List tasks in owned project
- `GET    /api/tasks` — List tasks across user's projects
- `GET    /api/tasks/{task_id}` — Get task by ID (404 if unowned)
- `PATCH  /api/tasks/{task_id}` — Update owned task
- `DELETE /api/tasks/{task_id}` — Cascade delete owned task
- `GET    /api/tasks/{task_id}/runs` — List runs for owned task
- `POST   /api/tasks/{task_id}/runs` — Record execution run for owned task

### LLM Orchestration (Authenticated)
- `GET    /api/models` — List registered models across providers
- `POST   /api/llm/generate` — Synchronous completion
- `POST   /api/llm/generate/stream` — SSE token stream
