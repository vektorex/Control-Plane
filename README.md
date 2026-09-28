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

### 4. Pluggable Decision Provider Architecture
The router is built on the `RetrievalDecisionProvider` abstract interface:
- **`RuleBasedDecisionProvider`**: Deterministic baseline router combining regex intent patterns, phrase detection, and grounding signals with zero LLM latency.
- **`LLMDecisionProvider` (Future)**: Drop-in replacement interface allowing zero-rewrite adoption of LLM-based query reasoning.

### 5. Multi-Query Retrieval Architecture
```
Original Query
     ↓
Query Generator (LLM Provider Factory)
     ↓
┌──────┬──────┬──────┐
↓      ↓      ↓
Q1     Q2     Q3
↓      ↓      ↓
Hybrid Retrieval for Each Query (Concurrent)
└──────┬──────┘
       ↓
Reciprocal Rank Merge & Deduplication
       ↓
Deterministic Local Reranker
       ↓
Final Ranked Context Chunks
```

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

- **Cross-Tenant Isolation**: User A can NEVER search, retrieve, preview, or execute tasks across User B's boundaries.
- **Tenant Scope Enforcement**: All SQL queries and vector searches filter on `workspace_id` and `project_id` at the database layer.
- **Safety Limits**: Configurable server-side limits (`MAX_RETRIEVAL_QUERIES=4`, `MAX_RETRIEVAL_TOP_K=25`, `MAX_RETRIEVAL_RESULTS=50`).

---

## 📡 API Reference

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
- `POST   /api/tasks/{task_id}/run` — Execute task with Retrieval Router + ContextEngine + Telemetry
- `POST   /api/tasks/{task_id}/run/stream` — Execute task with SSE streaming + Retrieval Router Telemetry

---

## 🚀 Local Development Setup

### 1. Backend Setup & Database Migrations

```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Configure environment
cp backend/.env.example backend/.env

# 3. Apply Alembic database migrations (up to revision 006)
python -m alembic -c backend/alembic.ini upgrade head

# 4. Run full test suite (105 passing unit, integration, and security tests)
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

## ✅ Step 8 Verification Checklist

- [x] Structured `RetrievalDecision` model (`retrieval_required`, `strategy`, `scope`, `top_k`, `query`, `reason`, `confidence`).
- [x] Pluggable `RetrievalDecisionProvider` interface and `RuleBasedDecisionProvider` implementation.
- [x] Deterministic routing rules (simple tasks $\rightarrow$ none, exact match $\rightarrow$ keyword, conceptual $\rightarrow$ vector, project inquiry $\rightarrow$ hybrid).
- [x] User override support (`retrieval_mode`: `auto`, `always`, `never`).
- [x] Safe task configuration (`retrieval_mode`, `retrieval_strategy`, `retrieval_scope`, `retrieval_top_k`).
- [x] Multi-query retrieval strategy (`MultiQueryRetriever`) with bounded queries, deduplication, reciprocal rank fusion, and reranking.
- [x] `ContextEngine` and `RAGContextProvider` consuming structured `RetrievalDecision`.
- [x] Run observability capturing `retrieval_mode`, `retrieval_required`, `retrieval_strategy`, `retrieval_scope`, `retrieval_reason`, `retrieval_confidence`.
- [x] Router debugging preview endpoint `POST /api/tasks/{task_id}/retrieval/preview`.
- [x] Frontend Task Workspace (`/app/tasks/[taskId]`) with Retrieval Mode radio cards, collapsible advanced options, preview inspector, and post-execution decision observability diagnostics.
- [x] Strict user, workspace, and project multi-tenant isolation across preview and execution.
- [x] 105/105 passing backend unit, integration, and security tests.
- [x] Next.js production build passing with zero errors.
