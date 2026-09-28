from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from backend.app.services.models.base import CostClass, LatencyClass, ModelDefinition, ModelRequirements


class RoutingWeights(BaseModel):
    """Configuration-driven scoring weights for model routing."""
    capability_weight: float = Field(default=100.0, description="Weight for capability satisfaction")
    latency_match_weight: float = Field(default=25.0, description="Weight for matching latency preference")
    cost_match_weight: float = Field(default=25.0, description="Weight for matching cost preference")
    context_headroom_weight: float = Field(default=15.0, description="Weight for context window headroom")
    provider_preference_weight: float = Field(default=20.0, description="Weight for matching preferred provider")
    default_model_bonus: float = Field(default=5.0, description="Small tie-breaker bonus for default provider models")


DEFAULT_ROUTING_WEIGHTS = RoutingWeights()


class ModelRoutingPolicy:
    """
    Deterministic scoring and evaluation engine for candidate models.
    Scores models against ModelRequirements using objective, configuration-driven weights.
    """

    def __init__(self, weights: Optional[RoutingWeights] = None):
        self.weights = weights or DEFAULT_ROUTING_WEIGHTS

    def evaluate_model(
        self, model: ModelDefinition, requirements: ModelRequirements
    ) -> Tuple[float, List[str], List[str]]:
        """
        Evaluate a single model against requirements.
        Returns:
            (score, satisfied_reasons, disqualification_reasons)
        """
        disqualifications: List[str] = []
        satisfied: List[str] = []

        if not model.enabled:
            return -1.0, [], ["Model is disabled by server policy."]

        # 1. Hard capability checks
        if requirements.requires_tools and not model.supports_tools:
            disqualifications.append("Does not support required tool execution.")
        else:
            if requirements.requires_tools:
                satisfied.append("Supports tool calling")

        if requirements.requires_streaming and not model.supports_streaming:
            disqualifications.append("Does not support required streaming tokens.")
        else:
            if requirements.requires_streaming:
                satisfied.append("Supports real-time streaming")

        if requirements.requires_structured_output and not model.supports_structured_output:
            disqualifications.append("Does not support required structured JSON output.")
        else:
            if requirements.requires_structured_output:
                satisfied.append("Supports structured output")

        if requirements.requires_vision and not model.supports_vision:
            disqualifications.append("Does not support required vision/multimodal input.")
        else:
            if requirements.requires_vision:
                satisfied.append("Supports vision inputs")

        if requirements.requires_long_context and model.context_window < 32000:
            disqualifications.append(f"Context window ({model.context_window}) is below long-context requirement (32k+).")
        else:
            if requirements.requires_long_context:
                satisfied.append(f"Provides {model.context_window // 1000}k context window")

        if requirements.min_context_window and model.context_window < requirements.min_context_window:
            disqualifications.append(
                f"Context window ({model.context_window}) is smaller than required minimum ({requirements.min_context_window})."
            )

        if disqualifications:
            return -1.0, [], disqualifications

        # 2. Score computation for eligible models
        score = self.weights.capability_weight

        # Latency preference scoring
        lat_pref = requirements.latency_preference.lower()
        if lat_pref == "low":
            if model.latency_class == LatencyClass.LOW.value:
                score += self.weights.latency_match_weight
                satisfied.append("Low latency class")
            elif model.latency_class == LatencyClass.MEDIUM.value:
                score += self.weights.latency_match_weight * 0.5
        elif lat_pref == "high_quality":
            if model.latency_class in (LatencyClass.HIGH.value, LatencyClass.MEDIUM.value) or model.has_capability("reasoning"):
                score += self.weights.latency_match_weight
                satisfied.append("High quality reasoning class")
        else:  # balanced
            if model.latency_class in (LatencyClass.LOW.value, LatencyClass.MEDIUM.value):
                score += self.weights.latency_match_weight
                satisfied.append("Balanced latency class")

        # Cost preference scoring
        cost_pref = requirements.cost_preference.lower()
        if cost_pref == "low":
            if model.cost_class == CostClass.LOW.value:
                score += self.weights.cost_match_weight
                satisfied.append("Cost-efficient class")
            elif model.cost_class == CostClass.MEDIUM.value:
                score += self.weights.cost_match_weight * 0.5
        elif cost_pref == "quality":
            if model.cost_class in (CostClass.MEDIUM.value, CostClass.HIGH.value):
                score += self.weights.cost_match_weight
                satisfied.append("Deep capacity class")
        else:  # balanced
            if model.cost_class in (CostClass.LOW.value, CostClass.MEDIUM.value):
                score += self.weights.cost_match_weight
                satisfied.append("Balanced cost class")

        # Context headroom bonus
        if model.context_window >= 128000:
            score += self.weights.context_headroom_weight
        elif model.context_window >= 32000:
            score += self.weights.context_headroom_weight * 0.5

        # Provider preference bonus
        if requirements.preferred_provider and model.provider == requirements.preferred_provider:
            score += self.weights.provider_preference_weight
            satisfied.append(f"Preferred provider '{model.provider}'")

        # Specific model preference bonus
        if requirements.preferred_model and (
            model.model_id == requirements.preferred_model or f"{model.provider}/{model.model_id}" == requirements.preferred_model
        ):
            score += 50.0
            satisfied.append(f"Exact requested model match '{model.model_id}'")

        if model.is_default:
            score += self.weights.default_model_bonus

        return score, satisfied, []

    def rank_candidates(
        self, candidates: List[ModelDefinition], requirements: ModelRequirements
    ) -> List[Tuple[ModelDefinition, float, List[str]]]:
        """
        Evaluate and rank eligible candidates in descending order of score.
        Disqualified models (score < 0) are excluded.
        """
        scored = []
        for model in candidates:
            score, satisfied, _ = self.evaluate_model(model, requirements)
            if score >= 0:
                scored.append((model, score, satisfied))

        # Sort descending by score, then by context_window
        scored.sort(key=lambda item: (item[1], item[0].context_window), reverse=True)
        return scored

    def generate_selection_reason(
        self, model: ModelDefinition, requirements: ModelRequirements, satisfied: List[str]
    ) -> str:
        """
        Generate a factual, transparent explanation for model selection.
        """
        parts = []
        if satisfied:
            parts.append(f"Satisfies {', '.join(satisfied[:4])}")
        else:
            parts.append("Satisfies all baseline requirements")

        parts.append(f"matches {requirements.latency_preference} latency and {requirements.cost_preference} cost preferences")
        return f"Selected '{model.display_name}' ({model.provider}): " + "; ".join(parts) + "."
