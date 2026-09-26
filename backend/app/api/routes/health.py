from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from backend.app.config import settings
from backend.app.schemas.health import HealthResponse
from backend.app.services.llm.factory import LLMProviderFactory, get_llm_factory

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def get_health(factory: LLMProviderFactory = Depends(get_llm_factory)) -> HealthResponse:
    """
    Get backend operational health, runtime metadata, and configured LLM providers.
    """
    configured_providers = factory.get_configured_provider_ids()
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc),
        environment=settings.ENVIRONMENT,
        providers_configured=configured_providers,
    )
