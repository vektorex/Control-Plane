from typing import Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.context import TaskContext
from backend.app.db.models.task import Task
from backend.app.services.context.base import ContextProvider
from backend.app.services.context.models import ContextItem, ContextSourceType
from backend.app.services.context.token_estimator import estimate_context_item_tokens


class ManualContextProvider(ContextProvider):
    """
    Context Provider responsible for retrieving explicit user-provided context records (TaskContext)
    stored in the database for a specific task.
    """

    @property
    def provider_id(self) -> str:
        return "manual_context"

    @property
    def source_type(self) -> str:
        return ContextSourceType.MANUAL.value

    async def can_handle(self, task: Task, **kwargs: Any) -> bool:
        return task is not None

    async def collect(
        self,
        task: Task,
        session: Optional[AsyncSession] = None,
        **kwargs: Any,
    ) -> List[TaskContext]:
        """
        Retrieves TaskContext records from the database or relationship.
        """
        if hasattr(task, "contexts") and task.contexts is not None and len(task.contexts) > 0:
            return list(task.contexts)

        if session:
            stmt = (
                select(TaskContext)
                .where(TaskContext.task_id == task.id)
                .order_by(TaskContext.priority.desc(), TaskContext.created_at.desc())
            )
            res = await session.execute(stmt)
            return list(res.scalars().all())

        return []

    def normalize(self, raw_items: List[TaskContext], **kwargs: Any) -> List[ContextItem]:
        """
        Normalizes database TaskContext entities into provider-independent ContextItem instances.
        """
        items: List[ContextItem] = []
        for ctx in raw_items:
            item = ContextItem(
                id=str(ctx.id),
                source_type=ctx.source_type or self.source_type,
                title=ctx.title,
                content=ctx.content,
                metadata=ctx.metadata_json or {},
                priority=ctx.priority,
                created_at=ctx.created_at,
                relevance_score=1.0,
            )
            item.token_estimate = estimate_context_item_tokens(item)
            items.append(item)
        return items
