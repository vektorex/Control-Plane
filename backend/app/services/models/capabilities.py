from enum import Enum
from typing import List, Set


class ModelCapability(str, Enum):
    """
    Normalized model capabilities representing concrete, testable LLM feature flags.
    The platform relies on these normalized capabilities rather than vendor-specific model strings.
    """
    TEXT_GENERATION = "text_generation"
    REASONING = "reasoning"
    STRUCTURED_OUTPUT = "structured_output"
    TOOL_CALLING = "tool_calling"
    VISION = "vision"
    LONG_CONTEXT = "long_context"
    STREAMING = "streaming"
    EMBEDDINGS = "embeddings"


ALL_CAPABILITIES: Set[str] = {c.value for c in ModelCapability}


def normalize_capability(cap: str) -> str:
    """Normalize a capability string to lowercase standard format."""
    normalized = cap.strip().lower()
    if normalized in ALL_CAPABILITIES:
        return normalized
    # Handle common aliases
    alias_map = {
        "tools": ModelCapability.TOOL_CALLING.value,
        "tool_use": ModelCapability.TOOL_CALLING.value,
        "function_calling": ModelCapability.TOOL_CALLING.value,
        "json": ModelCapability.STRUCTURED_OUTPUT.value,
        "json_mode": ModelCapability.STRUCTURED_OUTPUT.value,
        "stream": ModelCapability.STREAMING.value,
        "image": ModelCapability.VISION.value,
        "multimodal": ModelCapability.VISION.value,
    }
    return alias_map.get(normalized, normalized)


def validate_capabilities(caps: List[str]) -> List[str]:
    """Validate and return normalized unique capability list."""
    return sorted(list(set(normalize_capability(c) for c in caps if c)))
