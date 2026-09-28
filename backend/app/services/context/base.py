from abc import ABC, abstractmethod
from typing import Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.task import Task
from backend.app.services.context.models import ContextItem


class ContextProvider(ABC):
    """
    Abstract Base Class defining the provider-independent interface for all context sources.
    
    Responsibilities:
    - can_handle(): Determines if this provider applies to a given task or execution request.
    - collect(): Retrieves raw context items from its underlying storage or integration.
    - normalize(): Standardizes raw heterogeneous data into normalized ContextItem objects.
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique provider identifier (e.g., 'task_context', 'manual_context', 'vector_context')."""
        pass

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Primary ContextSourceType produced by this provider (e.g., 'task', 'manual', 'vector')."""
        pass

    @abstractmethod
    async def can_handle(self, task: Task, **kwargs: Any) -> bool:
        """
        Determines whether this provider can or should supply context for the given task.
        """
        pass

    @abstractmethod
    async def collect(
        self,
        task: Task,
        session: Optional[AsyncSession] = None,
        **kwargs: Any,
    ) -> List[Any]:
        """
        Gathers raw contextual data elements from the provider's backing data source.
        """
        pass

    @abstractmethod
    def normalize(self, raw_items: List[Any], **kwargs: Any) -> List[ContextItem]:
        """
        Transforms raw contextual data elements into normalized, typed ContextItem instances.
        """
        pass

    async def provide(
        self,
        task: Task,
        session: Optional[AsyncSession] = None,
        **kwargs: Any,
    ) -> List[ContextItem]:
        """
        Template method executing the complete lifecycle: can_handle -> collect -> normalize.
        """
        if not await self.can_handle(task, **kwargs):
            return []

        raw_items = await self.collect(task, session=session, **kwargs)
        return self.normalize(raw_items, **kwargs)
