# AI Work Layer (LLM-Work-Orchestration-Layer)

> **"One workspace for getting real work done with LLMs."**

A universal, production-oriented LLM work orchestration platform that accepts complex user tasks and coordinates optimal LLMs, context sources, retrieval strategies, and specialized execution tools.

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
│   • Request Validation & Structured Error Handling         │
└─────────────────────────────┬──────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│             LLM Abstraction Layer (`factory.py`)           │
│   • Dynamic Model-to-Provider Resolution                   │
│   • Unified `BaseLLMProvider` Base Class                   │
│   • Token Usage & Telemetry Normalization                  │
└───────┬─────────────────────┬──────────────────────┬───────┘
        │                     │                      │
        ▼                     ▼                      ▼
┌──────────────┐      ┌──────────────┐       ┌──────────────┐
│    OpenAI    │      │  Anthropic   │       │ Google/Local │
│ Provider SDK │      │ (Plug-ready) │       │ (Plug-ready) │
└───────┬──────┘      └──────────────┘       └──────────────┘
        │
        ▼
   LLM APIs (GPT-4o, Claude 3.5, etc.)
```

---

## 📂 Project Structure

```
LLM Layer/
├── backend/                         # Python FastAPI Backend Service
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point & CORS configuration
│   │   ├── config.py                # Pydantic Settings & Environment Variables
│   │   ├── api/
│   │   │   ├── deps.py              # Dependency Injection
│   │   │   └── routes/
│   │   │       ├── health.py        # GET /api/health
│   │   │       ├── models.py        # GET /api/models
│   │   │       └── llm.py           # POST /api/llm/generate & /generate/stream
│   │   ├── core/
│   │   │   ├── errors.py            # Error hierarchy & Exception handlers
│   │   │   └── logging.py           # Structured logger setup
│   │   ├── schemas/                 # Pydantic schemas (health, models, llm)
│   │   └── services/
│   │       └── llm/
│   │           ├── base.py          # BaseLLMProvider abstract interface
│   │           ├── factory.py       # LLMProviderFactory registry & router
│   │           └── providers/
│   │               └── openai.py    # OpenAI AsyncOpenAI provider adapter
│   ├── tests/                       # Pytest test suite (14 passing unit tests)
│   ├── requirements.txt             # Backend Python dependencies
│   ├── .env.example                 # Backend environment variable template
│   └── README.md                    # Backend specific documentation
├── src/                             # Next.js Frontend Application
│   ├── app/                         # App Router pages and layouts
│   │   ├── page.jsx                 # Professional SaaS landing page (/)
│   │   ├── layout.jsx               # Root layout & design tokens
│   │   ├── error.jsx                # Error boundary
│   │   ├── loading.jsx              # Loading spinner
│   │   ├── not-found.jsx            # 404 page handler
│   │   └── app/
│   │       ├── layout.jsx           # Authenticated App Shell (Sidebar & Header)
│   │       ├── page.jsx             # Workspace Dashboard (/app)
│   │       ├── playground/page.jsx  # LLM Abstraction Playground (/app/playground)
│   │       ├── tasks/page.jsx       # Tasks Management (/app/tasks)
│   │       ├── projects/page.jsx    # Projects & Context Scopes (/app/projects)
│   │       └── settings/page.jsx    # Platform & Engine Settings (/app/settings)
│   ├── components/
│   │   ├── landing/                 # Hero, Architecture, Capabilities, Navbar, Footer
│   │   ├── shell/                   # AppSidebar, AppHeader, WorkspaceSelector, UserDropdown
│   │   ├── ui/                      # Reusable Button, Card, Badge, Input, Select, Modal, Tabs, etc.
│   │   └── features/                # Domain-specific components
│   ├── config/                      # Site, env, and constants configs
│   ├── lib/                         # API client and utility helpers
│   ├── services/                    # Frontend orchestrator service contracts
│   └── styles/                      # Tailwind CSS v4 & custom dark theme tokens
├── package.json
└── README.md
```

---

## ⚡ Getting Started

### 1. Prerequisites
- **Node.js**: `v20+` (Tested on `v24`)
- **Python**: `3.10+` (Tested on `3.12`)

---

### 2. Backend Setup & Startup

```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Configure environment
cp backend/.env.example backend/.env

# Optional: Add your OpenAI API Key in backend/.env:
# OPENAI_API_KEY=sk-...

# 3. Run backend tests
python -m pytest backend/tests -v

# 4. Start backend server
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be running at `http://localhost:8000`.
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/health`
- Model Directory: `http://localhost:8000/api/models`

---

### 3. Frontend Setup & Startup

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
- Landing Page: `http://localhost:3000/`
- Workspace Dashboard: `http://localhost:3000/app`
- **Developer Test Playground**: `http://localhost:3000/app/playground`
- Tasks: `http://localhost:3000/app/tasks`
- Projects: `http://localhost:3000/app/projects`
- Settings: `http://localhost:3000/app/settings`

---

## 📡 API Reference & Examples

### 1. Health Status
`GET /api/health`
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2026-09-26T06:45:02Z",
  "environment": "development",
  "providers_configured": ["openai"]
}
```

### 2. Available Models & Providers
`GET /api/models`
```json
{
  "models": [
    {
      "id": "gpt-4o-mini",
      "name": "GPT-4o Mini",
      "provider": "openai",
      "description": "Fast, highly cost-effective flagship model.",
      "context_window": 128000,
      "supports_streaming": true,
      "is_default": true
    }
  ],
  "providers": [
    {
      "id": "openai",
      "name": "OpenAI",
      "is_configured": true
    }
  ]
}
```

### 3. Synchronous LLM Generation
`POST /api/llm/generate`
```bash
curl -X POST http://localhost:8000/api/llm/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Explain work orchestration in 1 sentence."}
    ],
    "temperature": 0.2
  }'
```

### 4. Real-time Streaming Generation (Server-Sent Events)
`POST /api/llm/generate/stream`
```bash
curl -N -X POST http://localhost:8000/api/llm/generate/stream \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Write a 3-step deployment checklist."}
    ],
    "stream": true
  }'
```

---

## 🔌 How to Add Another LLM Provider

The LLM abstraction layer allows adding new model providers (Anthropic, Gemini, DeepSeek, Local Ollama) without modifying core route logic:

1. **Create Provider Adapter**: Subclass `BaseLLMProvider` in `backend/app/services/llm/providers/<provider_name>.py`.
2. **Implement Required Methods**: `get_models()`, `supports_model()`, `generate()`, and `generate_stream()`.
3. **Register in Factory**: In `backend/app/services/llm/factory.py`, call `self.register_provider(MyNewProvider())`.
4. **Configure Environment Keys**: Add credentials in `backend/app/config.py` and `backend/.env`.
