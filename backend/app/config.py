from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("backend/.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core App
    APP_NAME: str = "AI Work Layer Backend"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # OpenAI Provider Settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_DEFAULT_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: Optional[str] = None
    OPENAI_TIMEOUT_SECONDS: float = 60.0

    # Database Settings (PostgreSQL + AsyncPG)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_work_layer"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    @property
    def async_database_url(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    # Security & Authentication (Supabase Auth)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_AUDIENCE: str = "authenticated"
    ORCHESTRATION_API_SECRET: Optional[str] = None

    # Step 7: Document Storage & RAG Settings
    DOCUMENT_STORAGE_PATH: str = ".storage/documents"
    MAX_DOCUMENT_SIZE_MB: int = 25
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536
    RAG_DEFAULT_TOP_K: int = 8
    RAG_DEFAULT_MAX_CONTEXT_TOKENS: int = 6000

    # Step 8: Retrieval Router Limits & Settings
    MAX_RETRIEVAL_QUERIES: int = 4
    MAX_RETRIEVAL_TOP_K: int = 25
    MAX_RETRIEVAL_RESULTS: int = 50

    # Step 9: Tool System & Web Search Settings
    WEB_SEARCH_PROVIDER: str = "duckduckgo"
    WEB_SEARCH_API_KEY: Optional[str] = None
    WEB_SEARCH_DEFAULT_LIMIT: int = 5
    WEB_SEARCH_MAX_LIMIT: int = 10
    WEB_SEARCH_TIMEOUT_SECONDS: float = 10.0
    MAX_TOOL_CALLS_PER_TASK: int = 5

    # Step 10: Orchestration Engine Limits & Settings
    MAX_PLAN_STEPS: int = 10
    MAX_TOOL_CALLS_PER_PLAN: int = 5
    MAX_RETRIEVAL_CALLS_PER_PLAN: int = 3
    MAX_EXECUTION_TIME_SECONDS: float = 60.0

    # Step 11: LLM-Assisted Planning & Agentic Loop Settings
    PLANNER_MODEL_PROVIDER: str = "openai"
    PLANNER_MODEL: str = "gpt-4o-mini"
    PLANNER_DEFAULT_MODE: str = "hybrid"  # deterministic | llm | hybrid | auto
    PLANNER_TIMEOUT_SECONDS: float = 30.0
    MAX_PLAN_REPAIR_ATTEMPTS: int = 1
    MAX_AGENT_ITERATIONS: int = 3
    EVALUATOR_MODEL_PROVIDER: str = "openai"
    EVALUATOR_MODEL: str = "gpt-4o-mini"

    # Step 12: Model Intelligence & Model Router Settings
    DEFAULT_MODEL_MODE: str = "auto"  # auto | manual
    GENERATION_MODEL_PROVIDER: str = "openai"
    GENERATION_DEFAULT_MODEL: str = "gpt-4o-mini"
    PLANNER_MODEL_MODE: str = "auto"
    GENERATION_MODEL_MODE: str = "auto"
    MAX_MODEL_FALLBACK_ATTEMPTS: int = 2
    ALLOWED_MODEL_PROVIDERS: List[str] = ["openai", "mock", "anthropic", "gemini"]

    # Step 13: Evaluation & Verification Engine Settings
    EVALUATION_DEFAULT_MODE: str = "standard"  # off | basic | standard | strict
    MAX_REVISION_ATTEMPTS: int = 2
    EVALUATION_TIMEOUT_SECONDS: float = 30.0

    # Step 14: Observability, Usage & Cost Intelligence Settings
    OBSERVABILITY_RETENTION_DAYS: int = 30
    MAX_TRACE_METADATA_BYTES: int = 10240

    # Step 15: Workflow System Settings
    MAX_WORKFLOW_STEPS: int = 20
    MAX_WORKFLOW_DEPTH: int = 5
    MAX_WORKFLOW_TOOL_CALLS: int = 10
    MAX_WORKFLOW_RETRIEVAL_CALLS: int = 10
    MAX_WORKFLOW_EXECUTION_SECONDS: float = 300.0
    MAX_WORKFLOW_OUTPUT_BYTES: int = 1048576  # 1MB output limit


settings = Settings()




