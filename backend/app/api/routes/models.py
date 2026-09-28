from typing import List, Optional
from fastapi import APIRouter, Depends
from backend.app.core.auth import get_current_user, get_optional_current_user
from backend.app.db.models.user import User
from backend.app.schemas.models import (
    ModelInfo,
    ModelListResponse,
    ModelRouteRequest,
    ModelRouteResponse,
    ModelSelectionSchema,
    ProviderInfo,
)
from backend.app.services.llm.factory import LLMProviderFactory, get_llm_factory
from backend.app.services.models.base import ModelRequirements
from backend.app.services.models.registry import default_model_registry
from backend.app.services.models.router import default_model_router

router = APIRouter(tags=["Models"])


@router.get("/models", response_model=ModelListResponse)
async def list_models(
    current_user: Optional[User] = Depends(get_optional_current_user),
    factory: LLMProviderFactory = Depends(get_llm_factory),
) -> ModelListResponse:
    """
    List safe model catalog metadata for the authenticated user.
    Never exposes provider API keys, credentials, or secret configuration.
    """
    catalog_models = default_model_registry.list_models_for_user(current_user, enabled_only=True)
    model_infos = [ModelInfo(**m) for m in catalog_models]

    # Collect active provider status from factory
    providers_info: List[ProviderInfo] = []
    for p_id, provider in factory._providers.items():
        p_models = [m for m in model_infos if m.provider == p_id]
        providers_info.append(
            ProviderInfo(
                id=provider.provider_id,
                name=provider.provider_name,
                is_configured=provider.is_configured,
                models=p_models,
            )
        )

    return ModelListResponse(models=model_infos, providers=providers_info)


@router.post("/models/route", response_model=ModelRouteResponse)
async def route_model(
    request: ModelRouteRequest,
    current_user: User = Depends(get_current_user),
) -> ModelRouteResponse:
    """
    Deterministic Model Routing endpoint.
    Accepts ModelRequirements and returns the approved ModelSelection with reasoning and fallback candidates.
    """
    reqs = ModelRequirements(**request.requirements.model_dump())
    selection = default_model_router.route(reqs, policy_name=request.policy or "balanced")

    return ModelRouteResponse(
        selection=ModelSelectionSchema(
            provider=selection.provider,
            model_id=selection.model_id,
            display_name=selection.display_name,
            reason=selection.reason,
            policy=selection.policy,
            satisfied_requirements=selection.satisfied_requirements,
            fallback_candidates=[
                {
                    "provider": fb.provider,
                    "model_id": fb.model_id,
                    "display_name": fb.display_name,
                    "reason": fb.reason,
                }
                for fb in selection.fallback_candidates
            ],
            metadata=selection.metadata,
        )
    )
