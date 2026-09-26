from fastapi import APIRouter, Depends
from backend.app.schemas.models import ModelListResponse
from backend.app.services.llm.factory import LLMProviderFactory, get_llm_factory

router = APIRouter(tags=["Models"])


@router.get("/models", response_model=ModelListResponse)
async def list_models(
    factory: LLMProviderFactory = Depends(get_llm_factory),
) -> ModelListResponse:
    """
    List all supported models and provider configuration states from the internal abstraction layer.
    """
    return factory.list_all_models()
