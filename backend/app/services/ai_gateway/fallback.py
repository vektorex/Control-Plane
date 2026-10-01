from typing import Any, Dict, List, Optional
from backend.app.core.logging import logger
from backend.app.services.ai_gateway.errors import (
    AllFallbacksFailedError,
    CapabilityUnsupportedError,
    InvalidRequestError,
    ModelNotAllowedError,
    PolicyDeniedError,
    RateLimitedError,
    ProviderTimeoutError,
    ModelTimeoutError,
    ProviderUnavailableError,
)
from backend.app.services.ai_gateway.requests import GatewayRequest
from backend.app.services.models.base import FallbackCandidate, ModelDefinition, ModelRequirements
from backend.app.services.models.registry import default_model_registry

MAX_MODEL_FALLBACKS = 2


class FallbackEngine:
    """
    Manages fallback model candidate evaluation, capability verification,
    and resilience routing when a primary model experiences transient operational failure.
    """

    ELIGIBLE_FALLBACK_ERRORS = (
        RateLimitedError,
        ProviderTimeoutError,
        ModelTimeoutError,
        ProviderUnavailableError,
    )

    INELIGIBLE_FALLBACK_ERRORS = (
        PolicyDeniedError,
        ModelNotAllowedError,
        InvalidRequestError,
        CapabilityUnsupportedError,
    )

    @classmethod
    def is_eligible_for_fallback(cls, exc: Exception) -> bool:
        """
        Check whether an exception warrants triggering a fallback candidate.
        Strictly forbids fallbacks on policy denials, validation errors, or auth failures.
        """
        from backend.app.core.errors import ProviderAuthError
        if isinstance(exc, (cls.INELIGIBLE_FALLBACK_ERRORS, ProviderAuthError)):
            return False
        if isinstance(exc, cls.ELIGIBLE_FALLBACK_ERRORS):
            return True
        err_msg = str(exc).lower()
        if any(w in err_msg for w in ["invalid", "schema", "validation", "not allowed", "forbidden", "unauthorized", "auth", "permission"]):
            return False
        return any(w in err_msg for w in ["timeout", "rate limit", "429", "unavailable", "network", "503", "502"])

    @classmethod
    def verify_candidate_safety(
        cls,
        candidate_model_id: str,
        candidate_provider: str,
        original_request: GatewayRequest,
        workspace_policy: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Validate that fallback candidate strictly satisfies all hard requirements
        and does not violate workspace policy or downgrade required capabilities.
        """
        model_def = default_model_registry.get_model(candidate_model_id, provider=candidate_provider)
        if not model_def:
            if candidate_provider == "mock":
                return True
            return False
        if not model_def.enabled:
            return False

        # 1. Capability checks
        if original_request.tools and not model_def.supports_tools:
            return False
        if original_request.stream and not model_def.supports_streaming:
            return False
        if original_request.response_format and not model_def.supports_structured_output:
            return False

        # 2. Workspace policy checks
        if workspace_policy:
            allowed_providers = [p.lower() for p in workspace_policy.get("allowed_providers", [])]
            if allowed_providers and candidate_provider.lower() not in allowed_providers:
                return False

            allowed_models = workspace_policy.get("allowed_models", [])
            if allowed_models and candidate_model_id not in allowed_models:
                return False

        return True

    @classmethod
    def resolve_fallback_candidates(
        cls,
        candidates: List[FallbackCandidate],
        original_request: GatewayRequest,
        workspace_policy: Optional[Dict[str, Any]] = None,
        max_fallbacks: int = MAX_MODEL_FALLBACKS,
    ) -> List[FallbackCandidate]:
        """Filter and order safe, eligible fallback candidates."""
        safe_candidates: List[FallbackCandidate] = []
        for cand in candidates:
            if cls.verify_candidate_safety(
                candidate_model_id=cand.model_id,
                candidate_provider=cand.provider,
                original_request=original_request,
                workspace_policy=workspace_policy,
            ):
                safe_candidates.append(cand)
                if len(safe_candidates) >= max_fallbacks:
                    break
        return safe_candidates
