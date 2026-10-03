from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from backend.app.services.models.capabilities import ModelCapability


class LatencyPreference(str, Enum):
    LOW = "low"
    BALANCED = "balanced"
    HIGH_QUALITY = "high_quality"


class CostPreference(str, Enum):
    LOW = "low"
    BALANCED = "balanced"
    QUALITY = "quality"


class LatencyClass(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CostClass(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CostMetadata(BaseModel):
    """Token pricing configuration per 1M tokens (and legacy per 1k tokens)."""
    input_cost_per_1m_tokens: Optional[float] = Field(default=None, description="Input token cost per 1M tokens in USD")
    output_cost_per_1m_tokens: Optional[float] = Field(default=None, description="Output token cost per 1M tokens in USD")
    cached_input_cost_per_1m_tokens: Optional[float] = Field(default=None, description="Cached input token cost per 1M tokens in USD")
    input_cost_per_1k_tokens: Optional[float] = Field(default=None, description="Legacy input token cost per 1k in USD")
    output_cost_per_1k_tokens: Optional[float] = Field(default=None, description="Legacy output token cost per 1k in USD")
    currency: str = Field(default="USD", description="Currency ISO code")

    @property
    def effective_input_cost_per_1m(self) -> Optional[float]:
        if self.input_cost_per_1m_tokens is not None:
            return self.input_cost_per_1m_tokens
        if self.input_cost_per_1k_tokens is not None:
            return round(self.input_cost_per_1k_tokens * 1000.0, 6)
        return None

    @property
    def effective_output_cost_per_1m(self) -> Optional[float]:
        if self.output_cost_per_1m_tokens is not None:
            return self.output_cost_per_1m_tokens
        if self.output_cost_per_1k_tokens is not None:
            return round(self.output_cost_per_1k_tokens * 1000.0, 6)
        return None

    @property
    def effective_cached_input_cost_per_1m(self) -> Optional[float]:
        return self.cached_input_cost_per_1m_tokens



class ModelDefinition(BaseModel):
    """
    Central model definition representing a registered LLM with normalized capabilities and metadata.
    """
    provider: str = Field(..., description="Provider identifier (e.g. 'openai', 'anthropic', 'gemini', 'mock')")
    model_id: str = Field(..., description="Unique model identifier (e.g. 'gpt-4o-mini', 'claude-3-5-sonnet')")
    display_name: str = Field(..., description="Human-readable model name")
    capabilities: List[str] = Field(default_factory=list, description="List of normalized ModelCapability strings")
    context_window: int = Field(default=128000, description="Maximum total context window in tokens")
    max_output_tokens: int = Field(default=4096, description="Maximum output tokens generated per call")
    supports_streaming: bool = Field(default=True, description="Whether the model supports streaming chunks")
    supports_tools: bool = Field(default=True, description="Whether the model supports native function/tool calling")
    supports_structured_output: bool = Field(default=True, description="Whether the model supports strict JSON output")
    supports_vision: bool = Field(default=False, description="Whether the model supports image/multimodal inputs")
    supports_audio: bool = Field(default=False, description="Whether the model supports direct audio input")
    supports_video: bool = Field(default=False, description="Whether the model supports direct video input")
    enabled: bool = Field(default=True, description="Whether this model is enabled in server policy")
    cost_class: str = Field(default="low", description="Cost category: 'low', 'medium', 'high'")
    latency_class: str = Field(default="low", description="Latency category: 'low', 'medium', 'high'")
    cost_metadata: Optional[CostMetadata] = Field(default=None, description="Token pricing metadata if available")
    is_default: bool = Field(default=False, description="Whether this is the default model for its provider")
    description: Optional[str] = Field(default=None, description="Safe descriptive label for UI catalog")

    def has_capability(self, cap: str) -> bool:
        """Check if model satisfies a given capability."""
        return cap in self.capabilities

    def satisfies_requirements(self, req: "ModelRequirements") -> bool:
        """Check if model meets all hard boolean requirements."""
        if not self.enabled:
            return False
        if req.requires_tools and not self.supports_tools:
            return False
        if (req.requires_vision or req.requires_image_input) and not (
            self.supports_vision
            or self.has_capability("vision")
            or self.has_capability("image_input")
            or self.has_capability("multimodal_input")
        ):
            return False
        if (req.requires_audio or req.requires_audio_input) and not (
            self.supports_audio
            or self.has_capability("audio_input")
            or self.has_capability("audio_transcription")
        ):
            return False
        if req.requires_video and not (
            self.supports_video
            or self.has_capability("video")
            or self.supports_vision
        ):
            return False
        if req.requires_multimodal and not (
            self.supports_vision
            or self.has_capability("multimodal_input")
            or self.has_capability("vision")
        ):
            return False
        if req.requires_streaming and not self.supports_streaming:
            return False
        if req.requires_structured_output and not self.supports_structured_output:
            return False
        if req.requires_reasoning and ModelCapability.REASONING.value not in self.capabilities:
            # If explicit reasoning is strictly required, check capability
            pass
        if req.min_context_window and self.context_window < req.min_context_window:
            return False
        if req.requires_long_context and self.context_window < 32000:
            return False
        return True


class ModelRequirements(BaseModel):
    """
    Normalized requirement specification extracted from a task, plan, or user request.
    """
    requires_reasoning: bool = Field(default=False, description="Whether complex reasoning or code logic is required")
    requires_tools: bool = Field(default=False, description="Whether external tool execution is required")
    requires_vision: bool = Field(default=False, description="Whether image or multimodal ingestion is required")
    requires_image_input: bool = Field(default=False, description="Whether direct image input is required")
    requires_multimodal: bool = Field(default=False, description="Whether mixed multimodal reasoning is required")
    requires_audio: bool = Field(default=False, description="Whether audio understanding is required")
    requires_audio_input: bool = Field(default=False, description="Whether direct audio input is required")
    requires_video: bool = Field(default=False, description="Whether video understanding is required")
    requires_table: bool = Field(default=False, description="Whether structured table analysis is required")
    requires_document: bool = Field(default=False, description="Whether document understanding is required")
    requires_long_context: bool = Field(default=False, description="Whether large context window (>32k) is required")
    requires_streaming: bool = Field(default=True, description="Whether streaming is required")
    requires_structured_output: bool = Field(default=False, description="Whether strict JSON schema is required")
    min_context_window: Optional[int] = Field(default=None, description="Minimum context window in tokens")
    latency_preference: str = Field(default="balanced", description="'low' | 'balanced' | 'high_quality'")
    cost_preference: str = Field(default="balanced", description="'low' | 'balanced' | 'quality'")
    preferred_provider: Optional[str] = Field(default=None, description="Optional provider preference")
    preferred_model: Optional[str] = Field(default=None, description="Optional specific model preference")


class FallbackCandidate(BaseModel):
    """A fallback model candidate."""
    provider: str
    model_id: str
    display_name: str
    reason: str


class ModelSelection(BaseModel):
    """
    Factual, deterministic model selection returned by the ModelRouter.
    """
    provider: str = Field(..., description="Selected provider identifier")
    model_id: str = Field(..., description="Selected model identifier")
    display_name: str = Field(..., description="Display name of the model")
    reason: str = Field(..., description="Factual explanation of why this model was chosen based on requirements and policy")
    policy: str = Field(default="balanced", description="Routing policy used for scoring")
    satisfied_requirements: List[str] = Field(default_factory=list, description="List of requirements satisfied")
    fallback_candidates: List[FallbackCandidate] = Field(default_factory=list, description="Ordered fallback candidates if primary fails")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional routing telemetry")
