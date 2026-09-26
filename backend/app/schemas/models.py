from typing import List, Optional
from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    id: str = Field(description="Unique model identifier, e.g. gpt-4o-mini")
    name: str = Field(description="Display name of the model")
    provider: str = Field(description="Provider identifier, e.g. openai, anthropic")
    description: Optional[str] = Field(default=None, description="Model description or capabilities")
    context_window: Optional[int] = Field(default=None, description="Max token context window")
    supports_streaming: bool = Field(default=True, description="Whether streaming generation is supported")
    is_default: bool = Field(default=False, description="Whether this is the default provider model")


class ProviderInfo(BaseModel):
    id: str = Field(description="Provider unique ID, e.g. openai")
    name: str = Field(description="Human-readable provider name")
    is_configured: bool = Field(description="Whether provider has active credentials/API keys configured")
    models: List[ModelInfo] = Field(default_factory=list, description="Supported models under this provider")


class ModelListResponse(BaseModel):
    models: List[ModelInfo] = Field(default_factory=list, description="List of all available models")
    providers: List[ProviderInfo] = Field(default_factory=list, description="Status of all registered providers")
