from typing import Any, Dict, List, Optional
from backend.app.core.errors import ModelNotFoundError, ValidationError
from backend.app.core.logging import logger
from backend.app.db.models.task import Task
from backend.app.services.models.base import (
    FallbackCandidate,
    ModelDefinition,
    ModelRequirements,
    ModelSelection,
)
from backend.app.services.models.policies import ModelRoutingPolicy
from backend.app.services.models.registry import ModelRegistry, default_model_registry
from backend.app.services.orchestration.plan import ExecutionPlan, StepType


class ModelRequirementAnalyzer:
    """
    Deterministic rule-based analyzer that extracts ModelRequirements
    from task instructions, context items, tools, and execution plans.
    Does NOT invoke an LLM for routing.
    """

    @staticmethod
    def analyze(
        task: Task,
        context_token_estimate: int = 0,
        enable_tools: bool = False,
        streaming: bool = True,
        execution_plan: Optional[ExecutionPlan] = None,
        latency_preference: str = "balanced",
        cost_preference: str = "balanced",
        manual_model_pref: Optional[str] = None,
    ) -> ModelRequirements:
        """
        Analyze task state and execution plan to generate normalized requirements.
        """
        requires_tools = enable_tools
        requires_structured_output = False
        requires_vision = False

        # Inspect execution plan if available
        if execution_plan and execution_plan.steps:
            for step in execution_plan.steps:
                if step.type == StepType.TOOL:
                    requires_tools = True
                elif step.type == StepType.RETRIEVE:
                    # Retrieval steps often require structured grounding synthesis
                    pass

        # Text analysis for reasoning indicators
        combined_text = f"{task.title} {task.instructions or ''} {task.description or ''}".lower()
        requires_reasoning = any(
            kw in combined_text
            for kw in [
                "compare",
                "contrast",
                "analyze",
                "evaluate",
                "code",
                "algorithm",
                "step by step",
                "architecture",
                "design",
                "debug",
                "why",
                "tradeoff",
            ]
        )

        # Context window sizing
        requires_long_context = context_token_estimate > 8000 or len(combined_text) > 16000
        min_context = max(context_token_estimate + 4000, 16000)

        # Explicit model preference on Task
        pref_model = manual_model_pref or getattr(task, "preferred_model", None)

        return ModelRequirements(
            requires_reasoning=requires_reasoning,
            requires_tools=requires_tools,
            requires_vision=requires_vision,
            requires_long_context=requires_long_context,
            requires_streaming=streaming,
            requires_structured_output=requires_structured_output,
            min_context_window=min_context,
            latency_preference=latency_preference,
            cost_preference=cost_preference,
            preferred_model=pref_model,
        )


class ModelRouter:
    """
    Deterministic Model Router that matches ModelRequirements against ModelRegistry
    using ModelRoutingPolicy to produce an approved ModelSelection.
    """

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        policy: Optional[ModelRoutingPolicy] = None,
    ):
        self.registry = registry or default_model_registry
        self.policy = policy or ModelRoutingPolicy()

    def route(
        self, requirements: ModelRequirements, policy_name: str = "balanced"
    ) -> ModelSelection:
        """
        Select the optimal model for the given requirements.
        """
        candidates = self.registry.list_models(enabled_only=True)
        if not candidates:
            raise ValidationError("No enabled models found in Model Registry.")

        ranked = self.policy.rank_candidates(candidates, requirements)
        if not ranked:
            # Fallback: find any enabled model matching minimal streaming
            fallback_candidates = [
                m for m in candidates if (not requirements.requires_tools or m.supports_tools)
            ]
            if not fallback_candidates:
                fallback_candidates = candidates
            selected = fallback_candidates[0]
            reason = f"Selected '{selected.display_name}' as safe default fallback; standard requirements could not be strictly satisfied."
            return ModelSelection(
                provider=selected.provider,
                model_id=selected.model_id,
                display_name=selected.display_name,
                reason=reason,
                policy=policy_name,
                satisfied_requirements=["Fallback Model"],
                fallback_candidates=[],
            )

        top_model, top_score, satisfied = ranked[0]
        reason = self.policy.generate_selection_reason(top_model, requirements, satisfied)

        # Build fallback list (up to 3 distinct candidates, prioritizing cross-provider resilience)
        fallbacks: List[FallbackCandidate] = []
        seen_providers = {top_model.provider}
        seen_models = {top_model.model_id}

        # 1. First prioritize alternative provider
        for alt_model, _, alt_sat in ranked[1:]:
            if alt_model.provider not in seen_providers and alt_model.model_id not in seen_models:
                fallbacks.append(
                    FallbackCandidate(
                        provider=alt_model.provider,
                        model_id=alt_model.model_id,
                        display_name=alt_model.display_name,
                        reason=f"Cross-provider fallback matching required capabilities.",
                    )
                )
                seen_providers.add(alt_model.provider)
                seen_models.add(alt_model.model_id)
                if len(fallbacks) >= 2:
                    break

        # 2. Add same-provider backup if needed
        for alt_model, _, _ in ranked[1:]:
            if alt_model.model_id not in seen_models and len(fallbacks) < 3:
                fallbacks.append(
                    FallbackCandidate(
                        provider=alt_model.provider,
                        model_id=alt_model.model_id,
                        display_name=alt_model.display_name,
                        reason=f"Same-provider backup candidate.",
                    )
                )
                seen_models.add(alt_model.model_id)

        return ModelSelection(
            provider=top_model.provider,
            model_id=top_model.model_id,
            display_name=top_model.display_name,
            reason=reason,
            policy=policy_name,
            satisfied_requirements=satisfied,
            fallback_candidates=fallbacks,
            metadata={"score": top_score, "candidate_count": len(ranked)},
        )

    def validate_manual_selection(
        self,
        model_id: str,
        provider: Optional[str] = None,
        requirements: Optional[ModelRequirements] = None,
    ) -> ModelSelection:
        """
        Validate a user-requested manual model against registry and requirements.
        """
        model = self.registry.validate_model_access(model_id, provider=provider)

        satisfied = []
        if requirements:
            if requirements.requires_tools and not model.supports_tools:
                raise ValidationError(
                    f"Model '{model.display_name}' does not support required tool execution."
                )
            if requirements.requires_vision and not model.supports_vision:
                raise ValidationError(
                    f"Model '{model.display_name}' does not support required vision capabilities."
                )
            if requirements.min_context_window and model.context_window < requirements.min_context_window:
                raise ValidationError(
                    f"Model '{model.display_name}' context window ({model.context_window}) cannot accommodate required context ({requirements.min_context_window})."
                )
            _, satisfied, _ = self.policy.evaluate_model(model, requirements)

        reason = f"Manual selection approved: '{model.display_name}' ({model.provider}) is enabled and policy-compliant."

        # Compute fallback candidates in case manual model fails at runtime
        fallback_req = requirements or ModelRequirements(
            requires_tools=model.supports_tools, requires_streaming=model.supports_streaming
        )
        ranked = self.policy.rank_candidates(
            [m for m in self.registry.list_models(enabled_only=True) if m.model_id != model.model_id],
            fallback_req,
        )
        fallbacks = [
            FallbackCandidate(
                provider=m.provider,
                model_id=m.model_id,
                display_name=m.display_name,
                reason="Automatic fallback for manual selection failure.",
            )
            for m, _, _ in ranked[:2]
        ]

        return ModelSelection(
            provider=model.provider,
            model_id=model.model_id,
            display_name=model.display_name,
            reason=reason,
            policy="manual",
            satisfied_requirements=satisfied,
            fallback_candidates=fallbacks,
        )


# Global singleton instance
default_model_router = ModelRouter()
