from typing import Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.db.models.task import Task
from backend.app.services.context.base import ContextProvider
from backend.app.services.context.builders.context_builder import ContextBuilder
from backend.app.services.context.models import ContextBudget, ContextItem, ContextPackage
from backend.app.services.context.providers.manual_context import ManualContextProvider
from backend.app.services.context.providers.rag_context import RAGContextProvider
from backend.app.services.context.providers.task_context import TaskContextProvider
from backend.app.services.context.providers.web_context import WebContextProvider
from backend.app.services.context.registry import ContextProviderRegistry


class ContextEngine:
    """
    Core Context Engine orchestrator.
    
    Coordinates registered providers, gathers context items, normalizes them,
    enforces token budget limits, removes duplicate contents, and packages the result
    into an LLM-ready ContextPackage.
    """

    def __init__(
        self,
        registry: Optional[ContextProviderRegistry] = None,
        builder: Optional[ContextBuilder] = None,
    ) -> None:
        self.registry = registry or ContextProviderRegistry()
        self.builder = builder or ContextBuilder()

        # Register default built-in providers if not already registered
        if not self.registry.get_provider("task_context"):
            self.registry.register(TaskContextProvider())
        if not self.registry.get_provider("manual_context"):
            self.registry.register(ManualContextProvider())
        if not self.registry.get_provider("rag_context"):
            self.registry.register(RAGContextProvider())
        if not self.registry.get_provider("web_context"):
            self.registry.register(WebContextProvider())


    def register_provider(self, provider: ContextProvider) -> None:
        """Dynamically registers an additional context provider (e.g. VectorProvider, WebProvider)."""
        self.registry.register(provider)

    def unregister_provider(self, provider_id: str) -> Optional[ContextProvider]:
        """Removes a registered context provider."""
        return self.registry.unregister(provider_id)

    async def build_context(
        self,
        task: Task,
        session: Optional[AsyncSession] = None,
        max_context_tokens: int = 8000,
        **kwargs: Any,
    ) -> ContextPackage:
        """
        Gathers context across all registered providers for the given task and returns
        a packaged, budget-constrained ContextPackage.
        """
        all_raw_items: List[ContextItem] = []
        providers = self.registry.get_providers()

        for provider in providers:
            try:
                if await provider.can_handle(task, **kwargs):
                    items = await provider.provide(task, session=session, **kwargs)
                    all_raw_items.extend(items)
            except Exception as e:
                logger.error(
                    f"[ContextEngine] Provider '{provider.provider_id}' failed collecting context: {str(e)}",
                    exc_info=True,
                )

        # Build budget configuration
        budget = ContextBudget(max_context_tokens=max_context_tokens)

        # Assemble package
        package = self.builder.build(all_raw_items, budget=budget)
        logger.info(
            f"[ContextEngine] Assembled context for task '{task.id}': "
            f"{package.total_items} items, {package.estimated_tokens} tokens, "
            f"sources={package.sources}, truncated={package.truncated}"
        )
        return package


# Default global engine instance (lazily initialized)
_default_context_engine: Optional[ContextEngine] = None


def get_context_engine() -> ContextEngine:
    """Dependency injector / factory function for ContextEngine."""
    global _default_context_engine
    if _default_context_engine is None:
        _default_context_engine = ContextEngine()
    return _default_context_engine
