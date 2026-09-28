from typing import Dict, List, Optional
from backend.app.core.errors import ModelNotFoundError, ProviderNotConfiguredError
from backend.app.core.logging import logger
from backend.app.schemas.models import ModelInfo, ModelListResponse, ProviderInfo
from backend.app.services.llm.base import BaseLLMProvider
from backend.app.services.llm.providers.openai import OpenAIProvider


class LLMProviderFactory:
    """
    Registry and factory for LLM Providers.
    Decouples API routes from specific vendor implementations and provides
    dynamic resolution of models to their appropriate provider adapters.
    """

    def __init__(self):
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._initialize_default_providers()

    def _initialize_default_providers(self):
        """Register the built-in provider adapters."""
        openai_provider = OpenAIProvider()
        self.register_provider(openai_provider)
        logger.info("[LLMFactory] Initialized default provider registry.")

    def register_provider(self, provider: BaseLLMProvider):
        """Register or override an LLM provider adapter."""
        self._providers[provider.provider_id] = provider
        logger.info(
            f"[LLMFactory] Registered provider: '{provider.provider_id}' "
            f"(Configured: {provider.is_configured})"
        )

    def get_provider(self, provider_id: str) -> BaseLLMProvider:
        """Retrieve a specific provider by its ID."""
        if provider_id not in self._providers:
            raise ProviderNotConfiguredError(f"Provider '{provider_id}' is not registered in this system.")
        return self._providers[provider_id]

    def get_provider_for_model(self, model_id: str) -> BaseLLMProvider:
        """
        Find the registered provider adapter that supports the given model identifier.
        Supports both bare model IDs ('gpt-4o') and namespaced identifiers ('openai/gpt-4o').
        """
        # Check namespaced prefix (e.g. "openai/gpt-4o")
        if "/" in model_id:
            prefix, bare_model = model_id.split("/", 1)
            if prefix in self._providers:
                return self._providers[prefix]
            model_id = bare_model

        # 1. Exact match among registered models
        for provider in self._providers.values():
            for m in provider.get_models():
                if m.id == model_id:
                    return provider

        # 2. Pattern / heuristic match supported by provider
        for provider in self._providers.values():
            if provider.supports_model(model_id):
                return provider

        # 3. Model not supported by any registered provider
        raise ModelNotFoundError(
            f"Model '{model_id}' is not supported by any registered LLM provider."
        )

    def has_provider_for_model(self, model_id: str) -> bool:
        """Check if any registered provider supports the given model identifier."""
        try:
            self.get_provider_for_model(model_id)
            return True
        except ModelNotFoundError:
            return False

    def list_all_models(self) -> ModelListResponse:
        """Aggregate models and provider readiness from all registered providers."""
        all_models: List[ModelInfo] = []
        providers_info: List[ProviderInfo] = []

        for p_id, provider in self._providers.items():
            models = provider.get_models()
            all_models.extend(models)
            providers_info.append(
                ProviderInfo(
                    id=provider.provider_id,
                    name=provider.provider_name,
                    is_configured=provider.is_configured,
                    models=models,
                )
            )

        return ModelListResponse(models=all_models, providers=providers_info)

    def get_configured_provider_ids(self) -> List[str]:
        """Return list of provider IDs that have active API keys configured."""
        return [
            provider.provider_id
            for provider in self._providers.values()
            if provider.is_configured
        ]


# Global singleton factory instance
llm_factory = LLMProviderFactory()


def get_llm_factory() -> LLMProviderFactory:
    """Dependency injector for LLMProviderFactory."""
    return llm_factory
