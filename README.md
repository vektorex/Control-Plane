# AI Work Layer (LLM-Work-Orchestration-Layer)

> **"One workspace for getting real work done with LLMs."**

A universal, production-oriented LLM work orchestration platform that accepts complex user tasks and coordinates optimal LLMs, context sources, hybrid retrieval strategies (Vector + Keyword Search + Reranking), persistent project data, multi-tenant workspace isolation, and specialized execution tools.

---

## 🏛️ System Architecture

```
User
 │
 ▼
Task
 │
 ▼
ContextEngine
 ├── TaskContextProvider     (Task title, instructions, baseline context)
 ├── ManualContextProvider   (User-attached task notes, guidelines, constraints)
 └── RAGContextProvider      (User-owned domain knowledge retrieval)
          │
          ▼
     HybridRetriever
       ├── Vector Search     (pgvector cosine semantic similarity)
       └── Keyword Search    (Lexical term coverage + BM25-style scoring)
          │
          ▼
     Result Fusion           (Reciprocal Rank Fusion - RRF)
          │
          ▼
     Reranking               (Deterministic Local scoring & alignment)
          │
          ▼
     Context Items           (Prioritized & token-budget enforced)
          │
          ▼
     LLM Abstraction         (OpenAI, Anthropic, Mock providers)
```

---

## 📚 Document Ingestion & Hybrid RAG Pipeline (Step 7)

Step 7 implements document ingestion and an end-to-end production-oriented **Hybrid RAG Pipeline** that plugs directly into the existing `ContextEngine` via `RAGContextProvider`.

### Ingestion Pipeline Architecture:
```
Upload Document (PDF, Markdown, TXT, DOCX)
     │
     ▼
Create Document Record (status = "pending")
     │
     ▼
File Storage Abstraction (.storage/documents, R2/S3 ready)
     │
     ▼
Asynchronous Background Worker (Non-blocking)
     │
     ▼
Format-Specific Extractor (PDFExtractor, MarkdownExtractor, TextExtractor, DOCXExtractor)
     │
     ▼
Structure-Aware Chunking (Paragraph/Sentence split, Token Overlap, Page retention)
     │
     ▼
Batch Vector Embeddings (OpenAI text-embedding-3-small, 1536d / Mock 128d)
     │
     ▼
Persist DocumentChunks (pgvector / JSON vector type + Metadata)
     │
     ▼
Update Document Status (status = "ready", chunk_count = N)
```

### 1. Supported Document Formats & Extraction
- **PDF (`.pdf`)**: Extracted using `pypdf` with discrete per-page text tracking.
- **Markdown (`.md`, `.markdown`)**: Extracted with structural headings count and section demarcation.
- **Plain Text (`.txt`)**: Extracted with UTF-8 / latin-1 fallback encoding normalization.
- **Word Documents (`.docx`)**: Extracted using `python-docx` parsing body paragraphs and tables.
- **Security Validation**: File size limits (max 25MB), MIME type verification, dangerous executable rejection (`.exe`, `.sh`, `.bat`).

### 2. Storage Abstraction Layer
- Located at `backend/app/services/storage/`
- Implements `FileStorage` interface: `upload`, `download`, `delete`, `exists`.
- Local filesystem storage (`LocalFileStorage`) stores files securely outside the source tree at `DOCUMENT_STORAGE_PATH=.storage/documents` with path traversal defense.
- Ready for future zero-code swap to Cloudflare R2 or AWS S3. Storage filesystem paths are never exposed to the client.

### 3. Structure-Aware Chunking
- Located at `backend/app/services/chunking/`
- Splits continuous text along structural boundaries (paragraphs `\n\n`, sentences, linebreaks) rather than arbitrary character cuts.
- Retains `page_number`, `chunk_index`, document metadata, and token count estimates.
- Configurable `chunk_size` (default 500 tokens) and `chunk_overlap` (default 50 tokens).

### 4. Embedding Provider Abstraction
- Located at `backend/app/services/embeddings/`
- Implements `BaseEmbeddingProvider`: `embed_text()` and `embed_batch()`.
- Providers:
  - `OpenAIEmbeddingProvider`: Batched API requests with exponential backoff and rate-limit retries.
  - `MockEmbeddingProvider`: Deterministic unit-normalized float vectors for zero-cost testing.
- Configurable via `EMBEDDING_MODEL` and `EMBEDDING_DIMENSION`.

### 5. PostgreSQL + pgvector Schema
- `VectorType` in `backend/app/db/models/vector_type.py` dynamically uses native `pgvector.sqlalchemy.Vector` on PostgreSQL and JSON float arrays on SQLite.
- Fully managed via Alembic migration `005_documents_chunks_and_retrieval_telemetry.py`.

### 6. Hybrid Retrieval, Fusion & Reranking
- **Vector Search (`VectorRetriever`)**: Computes cosine similarity between query embeddings and workspace-scoped document chunks.
- **Keyword Search (`KeywordRetriever`)**: Computes term coverage, normalized term frequency (sublinear logarithmic scaling), exact phrase bonus, and filename bonus.
- **Reciprocal Rank Fusion (`HybridRetriever`)**:
  $$RRF(d) = \frac{w_{\text{vec}}}{k + \text{rank}_{\text{vec}}(d)} + \frac{w_{\text{kw}}}{k + \text{rank}_{\text{kw}}(d)}$$
  (Default weights: 0.6 vector, 0.4 keyword, $k=60$).
- **Deterministic Local Reranker (`LocalReranker`)**: Evaluates fusion rank, query term density in leading chunk text, and filename alignment to produce final ranked candidate order.

### 7. RAGContextProvider & Run Telemetry
- Implements the `ContextProvider` interface from Step 6.
- Injects retrieved sources as normalized `ContextItem`s with `source_type="document"` into the `ContextEngine`.
- Captures full telemetry in the `Run` entity:
  - `retrieval_enabled`: Boolean flag
  - `retrieved_chunk_count`: Total chunks retrieved
  - `retrieval_latency_ms`: Time taken for search + fusion + reranking
  - `retrieval_sources`: List of document names, pages, and relevance scores for UI transparency.

---

## 🔐 Multi-Tenant Security & Isolation

Every document, chunk, context item, and task execution strictly enforces multi-tenant ownership:
$$\text{User} \longrightarrow \text{Workspace} \longrightarrow \text{Project} \longrightarrow \text{Document} \longrightarrow \text{DocumentChunk}$$

- **Cross-Tenant Isolation**: User A can NEVER search, retrieve, view, or delete document chunks belonging to User B.
- **Tenant Scope Enforcement**: All SQL queries filter on `workspace_id` at the database layer.
- **Storage Safety**: Storage keys include non-guessable prefixes and filenames are sanitized.

---

## 📡 API Reference

### Document Management & Uploads (Step 7)
- `POST   /api/workspaces/{workspace_id}/documents` — Multipart upload for PDF, TXT, Markdown, DOCX with non-blocking background ingestion
- `GET    /api/workspaces/{workspace_id}/documents` — List workspace documents with project and status filters
- `GET    /api/documents/{document_id}` — Get document status, metadata, and chunk count
- `GET    /api/documents/{document_id}/chunks` — Inspect indexed vector chunks for a document
- `DELETE /api/documents/{document_id}` — Delete document, vector chunks, and stored file
- `POST   /api/documents/{document_id}/reprocess` — Trigger manual re-ingestion

### Workspaces & Projects
- `POST   /api/workspaces` — Create workspace owned by authenticated user
- `GET    /api/workspaces` — List workspaces owned by authenticated user
- `GET    /api/workspaces/{workspace_id}` — Get workspace details
- `PATCH  /api/workspaces/{workspace_id}` — Update workspace
- `DELETE /api/workspaces/{workspace_id}` — Delete workspace
- `POST   /api/workspaces/{workspace_id}/projects` — Create project
- `GET    /api/workspaces/{workspace_id}/projects` — List projects

### Tasks, Context & Hybrid AI Execution
- `POST   /api/projects/{project_id}/tasks` — Create task
- `GET    /api/projects/{project_id}/tasks` — List tasks
- `GET    /api/tasks/{task_id}` — Get task
- `PATCH  /api/tasks/{task_id}` — Update task
- `DELETE /api/tasks/{task_id}` — Delete task
- `POST   /api/tasks/{task_id}/context` — Create manual context item
- `GET    /api/tasks/{task_id}/context` — List context items
- `GET    /api/tasks/{task_id}/context/inspect` — Debug view of assembled ContextPackage & prompt
- `POST   /api/tasks/{task_id}/run` — Execute task with ContextEngine + Hybrid RAG + Telemetry
- `POST   /api/tasks/{task_id}/run/stream` — Execute task with SSE streaming + Hybrid RAG

---

## 🚀 Local Development Setup

### 1. Backend Setup & Database Migrations

```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Configure environment
cp backend/.env.example backend/.env

# 3. Apply Alembic database migrations (up to revision 005)
python -m alembic -c backend/alembic.ini upgrade head

# 4. Run full test suite (87 passing unit, integration, and security tests)
python -m pytest backend/tests -v

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

## ✅ Step 7 Verification Checklist

- [x] Database schema & Alembic migration `005` (Documents, DocumentChunks, VectorType, Run retrieval fields).
- [x] Storage abstraction (`FileStorage`, `LocalFileStorage`, `get_file_storage`).
- [x] Format extractors (PDF via `pypdf`, Markdown, Plain Text, DOCX via `python-docx`).
- [x] Structure-aware text chunker with token overlap and page preservation.
- [x] Embedding provider interface (`BaseEmbeddingProvider`, `OpenAIEmbeddingProvider`, `MockEmbeddingProvider`).
- [x] Vector retriever with cosine similarity & multi-tenant isolation.
- [x] Keyword retriever with sublinear TF scoring and full-text coverage.
- [x] Hybrid retriever with Reciprocal Rank Fusion (RRF).
- [x] Deterministic local reranker (`LocalReranker`).
- [x] `RAGContextProvider` integrated into `ContextEngine`.
- [x] Multipart Document upload API with background worker processing.
- [x] Document Management UI (`/app/documents`) with upload, status tracking, and chunk inspection.
- [x] Task Workspace UI (`/app/tasks/[taskId]`) with Knowledge/Retrieval toggle, scope selector, and Retrieved Sources inspection panel.
- [x] Run telemetry capturing `retrieval_enabled`, `retrieved_chunk_count`, `retrieval_latency_ms`, `retrieval_sources`.
- [x] Strict multi-tenant security preventing cross-user document access or retrieval.
- [x] 87/87 backend unit & integration tests passing.
- [x] Next.js frontend production build passing with 0 errors.
