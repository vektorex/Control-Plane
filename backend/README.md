# AI Work Layer — Backend Service

A high-performance Python FastAPI service providing a provider-agnostic LLM abstraction layer for universal work orchestration.

---

## 🏛️ Architecture Overview

```
Next.js Frontend (Port 3000)
       │
       ▼ (HTTP / SSE)
FastAPI Backend Routes (/api/llm, /api/models, /api/health)
       │
       ▼
LLM Provider Factory (Dynamic Provider & Model Resolution)
       │
       ▼
Base LLM Provider Interface (`BaseLLMProvider`)
       │
       ├── OpenAI Provider Adapter (`OpenAIProvider` -> official AsyncOpenAI)
       ├── Anthropic Provider Adapter (Ready to plug in)
       ├── Google Gemini Provider Adapter (Ready to plug in)
       └── Local Ollama / vLLM Provider Adapter (Ready to plug in)
```

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.10+ (Tested on Python 3.12)
- Virtual environment or system Python

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp backend/.env.example backend/.env
```
Set your provider API keys:
```env
OPENAI_API_KEY=sk-...
OPENAI_DEFAULT_MODEL=gpt-4o-mini
```

### 4. Run Development Server
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Running Tests

The test suite validates request schemas, health checks, provider factory resolution, mock streaming, and error handling without needing live API keys:
```bash
python -m pytest backend/tests -v
```

---

## 📡 API Reference & Examples

### 1. Health Status
`GET /api/health`
```bash
curl http://localhost:8000/api/health
```
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2026-09-26T06:45:02Z",
  "environment": "development",
  "providers_configured": ["openai"]
}
```

### 2. List Models & Providers
`GET /api/models`
```bash
curl http://localhost:8000/api/models
```
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
      {"role": "user", "content": "Explain work orchestration in one sentence."}
    ],
    "temperature": 0.2
  }'
```
```json
{
  "content": "Work orchestration autonomously coordinates LLM models, retrieval strategies, and tools to complete complex tasks.",
  "model": "gpt-4o-mini",
  "provider": "openai",
  "usage": {
    "input_tokens": 16,
    "output_tokens": 20,
    "total_tokens": 36
  },
  "finish_reason": "stop"
}
```

### 4. Server-Sent Events (SSE) Streaming
`POST /api/llm/generate/stream`
```bash
curl -N -X POST http://localhost:8000/api/llm/generate/stream \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Count from 1 to 5."}
    ],
    "stream": true
  }'
```
```
data: {"content": "1", "model": "gpt-4o-mini", "provider": "openai", "is_finished": false, "usage": null, "finish_reason": null}

data: {"content": ", 2", "model": "gpt-4o-mini", "provider": "openai", "is_finished": false, "usage": null, "finish_reason": null}

data: {"content": ", 3, 4, 5", "model": "gpt-4o-mini", "provider": "openai", "is_finished": false, "usage": null, "finish_reason": null}

data: {"content": "", "model": "gpt-4o-mini", "provider": "openai", "is_finished": true, "usage": {"input_tokens": 12, "output_tokens": 8, "total_tokens": 20}, "finish_reason": "stop"}

data: [DONE]
```

---

## 🔌 How to Add Another LLM Provider

Adding a new provider (such as Anthropic, Google Gemini, or Ollama) requires **zero modifications** to core API routes or orchestration code:

1. **Subclass `BaseLLMProvider`**:
   Create a new adapter in `backend/app/services/llm/providers/<provider_name>.py`:
   ```python
   from backend.app.services.llm.base import BaseLLMProvider
   from backend.app.schemas.llm import LLMGenerateRequest, LLMGenerateResponse, LLMStreamChunk
   from backend.app.schemas.models import ModelInfo

   class AnthropicProvider(BaseLLMProvider):
       @property
       def provider_id(self) -> str:
           return "anthropic"

       @property
       def provider_name(self) -> str:
           return "Anthropic"

       @property
       def is_configured(self) -> bool:
           return bool(self._api_key)

       def get_models(self) -> list[ModelInfo]:
           return [
               ModelInfo(
                   id="claude-3-5-sonnet-latest",
                   name="Claude 3.5 Sonnet",
                   provider=self.provider_id,
                   context_window=200000,
                   supports_streaming=True
               )
           ]

       def supports_model(self, model_id: str) -> bool:
           return model_id.startswith("claude-")

       async def generate(self, request: LLMGenerateRequest) -> LLMGenerateResponse:
           # Call Anthropic Async SDK and return normalized LLMGenerateResponse
           pass

       async def generate_stream(self, request: LLMGenerateRequest):
           # Yield normalized LLMStreamChunk instances
           pass
   ```

2. **Register with the Provider Factory**:
   In `backend/app/services/llm/factory.py`:
   ```python
   from backend.app.services.llm.providers.anthropic import AnthropicProvider

   def _initialize_default_providers(self):
       self.register_provider(OpenAIProvider())
       self.register_provider(AnthropicProvider())
   ```

3. **Add Environment Variables**:
   Add `ANTHROPIC_API_KEY` to `backend/app/config.py` and `.env.example`.
