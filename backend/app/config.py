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


settings = Settings()

