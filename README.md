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
│   • Task Context Management & Context Inspector Debug View │
│   • Developer Playground (/app/playground)                 │
└─────────────────────────────┬──────────────────────────────┘
                              │ HTTP (Bearer JWT) / SSE Stream
                              ▼
┌────────────────────────────────────────────────────────────┐
│                   Python FastAPI Backend                   │
│   • JWT Signature & Expiry Verification (Independent Auth) │
│   • Multi-Tenant Resource Ownership Authorization Layer    │
│   • Context Management (/api/tasks/{id}/context, /api/context)│
│   • Health & Model Metadata (/api/health, /api/models)     │
│   • Synchronous & SSE Streaming Task Execution             │
│   • Request Validation & Structured Error Handling         │
└─────────────────────────────┬──────────────────────────────┘
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
┌─────────────────────────────┐┌─────────────────────────────┐
│       Context Engine        ││      Repository Layer       │
│  • Provider Registry        ││  • UserRepository           │
│  • TaskContextProvider      ││  • WorkspaceRepository      │
│  • ManualContextProvider    ││  • ProjectRepository        │
│  • Future Vector/RAG/Web    ││  • TaskRepository           │
│  • Token Budget & Dedup     ││  • RunRepository            │
│  • ContextPackage Builder   ││  • ContextRepository        │
└──────────────┬──────────────┘└─────────────┬───────────────┘
               │                             │
               ▼                             ▼
┌─────────────────────────────┐┌─────────────────────────────┐
│    LLM Abstraction Layer    ││    PostgreSQL Database      │
│  • Provider Factory         ││ (SQLAlchemy 2.x + Alembic)  │
│  • AsyncOpenAI SDK Adapter  ││ Multi-Tenant User Isolation │
│  • Model Resolution         ││ TaskContext & Run Metadata  │
└──────────────┬──────────────┘└─────────────────────────────┘
               │
               ▼
┌─────────────────────────────┐
│       LLM Providers         │
│   (OpenAI, Anthropic, etc.) │
└─────────────────────────────┘
```

---

## 🧠 Context Engine Architecture (Step 6)

The **Context Engine** establishes the foundational abstraction for collecting, normalizing, prioritizing, deduplicating, and assembling context supplied to LLMs during task execution.

### Architectural Flow:
```
Task Execution
     │
     ▼
ContextEngine
     │
     ├── Provider Registry
     │         ├── TaskContextProvider (Task title, instructions, context_text)
     │         ├── ManualContextProvider (User-attached TaskContext records)
     │         └── Future Extensibility:
     │               ├── VectorRetrievalProvider (Embeddings / Vector DB)
     │               ├── WebSearchProvider (Live web retrieval)
     │               ├── GitHubProvider (Code repository snippets)
     │               └── DatabaseProvider (Structured SQL / Schema context)
     ▼
Raw Context Items
     │
     ▼
ContextBuilder
     ├── 1. Deduplication (SHA-256 fingerprinting with priority preservation)
     ├── 2. Priority Sorting (System 100 > Task 80-90 > Manual 50-85 > Recency)
     ├── 3. Deterministic Token Estimation
     └── 4. Budget Enforcement & Truncation Safety (max_context_tokens)
     │
     ▼
ContextPackage
  {
    "items": [...],
    "total_items": 4,
    "estimated_tokens": 1250,
    "truncated": false,
    "sources": ["task", "manual"]
  }
     │
     ▼
TaskExecutionService (Formats messages & dispatches to LLM Abstraction)
```

### ContextProvider Interface:
All context providers implement a uniform, provider-independent abstraction:
```python
class ContextProvider(ABC):
    @property
    def provider_id(self) -> str: ...
    @property
    def source_type(self) -> str: ...
    async def can_handle(self, task: Task, **kwargs) -> bool: ...
    async def collect(self, task: Task, session: AsyncSession, **kwargs) -> List[Any]: ...
    def normalize(self, raw_items: List[Any], **kwargs) -> List[ContextItem]: ...
    async def provide(self, task: Task, session: AsyncSession, **kwargs) -> List[ContextItem]: ...
```

### Extensibility Guarantee:
Adding future retrieval systems (e.g. `VectorProvider`, `WebProvider`, `GitHubProvider`, `FileProvider`) requires **zero modifications** to `TaskExecutionService`. New providers simply register with `ContextProviderRegistry` or `ContextEngine.register_provider(provider)`.

### Token Estimation Strategy:
To maintain deterministic speed and zero paid API dependencies, the engine implements a local character/word token estimator:
- Text averaging ~4 characters per token and ~1.33 tokens per word with 4-token structural wrapper overhead per item.
- Strict budget enforcement drops or truncates lower-priority items when total tokens exceed `max_context_tokens` (default 8,000, configurable per execution request).

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
2. **Multi-Tenant Ownership & Resource Isolation**:
   - Hierarchical data model:
     $$\text{Authenticated User} \longrightarrow \text{Workspace} \longrightarrow \text{Project} \longrightarrow \text{Task} \longrightarrow \text{TaskContext / Run}$$
   - When User A requests a resource belonging to User B, the backend returns `404 Not Found` (never leaking whether another tenant's resource exists).

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

### Tasks & Context (Multi-Tenant Scoped)
- `POST   /api/projects/{project_id}/tasks` — Create task in owned project
- `GET    /api/projects/{project_id}/tasks` — List tasks in owned project
- `GET    /api/tasks` — List tasks across user's projects
- `GET    /api/tasks/{task_id}` — Get task by ID (404 if unowned)
- `PATCH  /api/tasks/{task_id}` — Update owned task
- `DELETE /api/tasks/{task_id}` — Cascade delete owned task
- `POST   /api/tasks/{task_id}/context` — Create manual context item for task
- `GET    /api/tasks/{task_id}/context` — List context items for task
- `GET    /api/tasks/{task_id}/context/inspect` — Debug view of assembled ContextPackage & prompt
- `PATCH  /api/context/{context_id}` — Update individual context item
- `DELETE /api/context/{context_id}` — Delete individual context item

### Task AI Execution & Runs (Multi-Tenant Scoped)
- `POST   /api/tasks/{task_id}/run` — Execute task synchronously via Context Engine & LLM
- `POST   /api/tasks/{task_id}/run/stream` — Execute task with Server-Sent Events (SSE) streaming
- `GET    /api/tasks/{task_id}/runs` — List historical execution runs for task

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

# 4. Run full test suite (68 passing unit and integration tests)
python -m pytest backend/tests -v

# 5. Start FastAPI backend server
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup & Startup

```bash
# 1. Install dependencies
npm install

# 2. Run lint and build validation
npm run build

# 3. Start development server
npm run dev
```
