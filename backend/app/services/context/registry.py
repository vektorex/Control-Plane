from typing import Dict, List, Optional
from backend.app.services.context.base import ContextProvider


class ContextProviderRegistry:
    """
    Registry for managing and discovering pluggable context providers.
    Enables future RAG, vector retrieval, web, git, file, and database providers
    to be registered seamlessly without rewriting execution or engine logic.
    """

    def __init__(self) -> None:
        self._providers: Dict[str, ContextProvider] = {}

    def register(self, provider: ContextProvider) -> None:
        """
        Registers a ContextProvider instance by its unique provider_id.
        """
        self._providers[provider.provider_id] = provider

    def unregister(self, provider_id: str) -> Optional[ContextProvider]:
        """
        Removes a provider from the registry.
        """
        return self._providers.pop(provider_id, None)

    def get_provider(self, provider_id: str) -> Optional[ContextProvider]:
        """
        Retrieves a registered provider by provider_id.
        """
        return self._providers.get(provider_id)

    def get_providers(self) -> List[ContextProvider]:
        """
        Returns all currently registered providers.
        """
        return list(self._providers.values())

    def clear(self) -> None:
        """
        Clears all registered providers.
        """
        self._providers.clear()
