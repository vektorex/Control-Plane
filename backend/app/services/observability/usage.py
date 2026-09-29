from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from backend.app.services.observability.cost import default_cost_calculator


class NormalizedUsage(BaseModel):
    """
    Normalized token usage across all LLM providers and estimation methods.
    """
    input_tokens: int = Field(default=0, description="Prompt/input tokens consumed")
    output_tokens: int = Field(default=0, description="Completion/output tokens generated")
    total_tokens: int = Field(default=0, description="Total tokens consumed")
    cached_input_tokens: Optional[int] = Field(default=0, description="Cached prompt tokens if supported")
    estimated_cost: Optional[float] = Field(default=None, description="Estimated cost in USD based on configured catalog")
    usage_source: str = Field(default="provider", description="Source of metrics: 'provider', 'estimated', or 'unavailable'")


def normalize_provider_usage(
    provider: str,
    model: str,
    raw_usage: Optional[Dict[str, Any]] = None,
    estimated_tokens: Optional[Dict[str, int]] = None,
) -> NormalizedUsage:
    """
    Normalizes usage reported by OpenAI, Anthropic, Gemini, or local estimators.
    """
    in_tok = 0
    out_tok = 0
    cached_tok = 0
    source = "unavailable"

    if raw_usage and isinstance(raw_usage, dict):
        # OpenAI style
        if "prompt_tokens" in raw_usage or "completion_tokens" in raw_usage:
            in_tok = raw_usage.get("prompt_tokens") or 0
            out_tok = raw_usage.get("completion_tokens") or 0
            cached_meta = raw_usage.get("prompt_tokens_details", {})
            if isinstance(cached_meta, dict):
                cached_tok = cached_meta.get("cached_tokens", 0)
            source = "provider"

        # Anthropic style
        elif "input_tokens" in raw_usage or "output_tokens" in raw_usage:
            in_tok = raw_usage.get("input_tokens") or 0
            out_tok = raw_usage.get("output_tokens") or 0
            cached_tok = raw_usage.get("cache_read_input_tokens") or 0
            source = "provider"

        # Generic total
        elif "total_tokens" in raw_usage:
            in_tok = raw_usage.get("input_tokens") or 0
            out_tok = raw_usage.get("output_tokens") or 0
            source = "provider"

    elif estimated_tokens and isinstance(estimated_tokens, dict):
        in_tok = estimated_tokens.get("input_tokens") or estimated_tokens.get("estimated_prompt_tokens") or 0
        out_tok = estimated_tokens.get("output_tokens") or estimated_tokens.get("estimated_completion_tokens") or 0
        source = "estimated"

    total_tok = in_tok + out_tok

    cost = default_cost_calculator.calculate_generation_cost(
        model_id=model,
        provider=provider,
        input_tokens=in_tok,
        output_tokens=out_tok,
        cached_input_tokens=cached_tok,
    )

    return NormalizedUsage(
        input_tokens=in_tok,
        output_tokens=out_tok,
        total_tokens=total_tok,
        cached_input_tokens=cached_tok,
        estimated_cost=cost,
        usage_source=source,
    )
