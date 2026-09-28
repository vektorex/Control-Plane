from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    id: str = Field(description="Unique model identifier, e.g. gpt-4o-mini")
    name: str = Field(description="Display name of the model")
    provider: str = Field(description="Provider identifier, e.g. openai, anthropic")
    description: Optional[str] = Field(default=None, description="Model description or capabilities")
    capabilities: List[str] = Field(default_factory=list, description="Supported normalized capabilities")
    context_window: Optional[int] = Field(default=None, description="Max token context window")
    supports_streaming: bool = Field(default=True, description="Whether streaming generation is supported")
    supports_tools: bool = Field(default=True, description="Whether tool/function calling is supported")
    supports_vision: bool = Field(default=False, description="Whether vision/multimodal input is supported")
    supports_structured_output: bool = Field(default=True, description="Whether structured JSON output is supported")
    cost_class: Optional[str] = Field(default="low", description="Cost category: low, medium, high")
    latency_class: Optional[str] = Field(default="low", description="Latency category: low, medium, high")
    is_default: bool = Field(default=False, description="Whether this is the default provider model")
    enabled: bool = Field(default=True, description="Whether model is enabled")


class ProviderInfo(BaseModel):
    id: str = Field(description="Provider unique ID, e.g. openai")
    name: str = Field(description="Human-readable provider name")
    is_configured: bool = Field(description="Whether provider has active credentials/API keys configured")
    models: List[ModelInfo] = Field(default_factory=list, description="Supported models under this provider")


class ModelListResponse(BaseModel):
    models: List[ModelInfo] = Field(default_factory=list, description="List of all available models")
    providers: List[ProviderInfo] = Field(default_factory=list, description="Status of all registered providers")


class ModelRequirementsSchema(BaseModel):
    requires_reasoning: bool = Field(default=False)
    requires_tools: bool = Field(default=False)
    requires_vision: bool = Field(default=False)
    requires_long_context: bool = Field(default=False)
    requires_streaming: bool = Field(default=True)
    requires_structured_output: bool = Field(default=False)
    min_context_window: Optional[int] = Field(default=None)
    latency_preference: str = Field(default="balanced")
    cost_preference: str = Field(default="balanced")
    preferred_provider: Optional[str] = Field(default=None)
    preferred_model: Optional[str] = Field(default=None)


class ModelRouteRequest(BaseModel):
    requirements: ModelRequirementsSchema = Field(default_factory=ModelRequirementsSchema)
    policy: Optional[str] = Field(default="balanced")


class FallbackCandidateSchema(BaseModel):
    provider: str
    model_id: str
    display_name: str
    reason: str


class ModelSelectionSchema(BaseModel):
    provider: str
    model_id: str
    display_name: str
    reason: str
    policy: str = "balanced"
    satisfied_requirements: List[str] = Field(default_factory=list)
    fallback_candidates: List[FallbackCandidateSchema] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModelRouteResponse(BaseModel):
    selection: ModelSelectionSchema


class TaskModelPreviewResponse(BaseModel):
    task_id: str
    model_mode: str
    requirements: ModelRequirementsSchema
    selection: ModelSelectionSchema
