import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.task import Task
from backend.app.services.context.base import ContextProvider
from backend.app.services.context.models import ContextItem, ContextSourceType
from backend.app.services.context.token_estimator import estimate_context_item_tokens


class TaskContextProvider(ContextProvider):
    """
    Context Provider that extracts and normalizes context inherently defined within the Task entity.
    Includes:
    - Task background context text (context_text)
    - Task instructions/directive
    """

    @property
    def provider_id(self) -> str:
        return "task_context"

    @property
    def source_type(self) -> str:
        return ContextSourceType.TASK.value

    async def can_handle(self, task: Task, **kwargs: Any) -> bool:
        """
        Applies whenever a Task entity is present.
        """
        return task is not None

    async def collect(
        self,
        task: Task,
        session: Optional[AsyncSession] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """
        Extracts raw context elements from the Task model.
        """
        raw_items: List[Dict[str, Any]] = []

        # 1. Task background context
        if task.context_text and task.context_text.strip():
            raw_items.append({
                "id": f"task-ctx-{task.id}",
                "title": f"Task Context: {task.title}",
                "content": task.context_text.strip(),
                "priority": 80,
                "metadata": {
                    "task_id": str(task.id),
                    "project_id": str(task.project_id) if task.project_id else None,
                    "kind": "task_context_text",
                },
            })

        # 2. If task has explicit description distinct from instructions
        if (
            task.description
            and task.description.strip()
            and (not task.instructions or task.description.strip() != task.instructions.strip())
        ):
            raw_items.append({
                "id": f"task-desc-{task.id}",
                "title": f"Task Description: {task.title}",
                "content": task.description.strip(),
                "priority": 75,
                "metadata": {
                    "task_id": str(task.id),
                    "kind": "task_description",
                },
            })

        return raw_items

    def normalize(self, raw_items: List[Dict[str, Any]], **kwargs: Any) -> List[ContextItem]:
        """
        Normalizes raw task elements into ContextItem objects with token estimation.
        """
        items: List[ContextItem] = []
        for raw in raw_items:
            item = ContextItem(
                id=raw.get("id", str(uuid.uuid4())),
                source_type=self.source_type,
                title=raw.get("title", "Task Context"),
                content=raw.get("content", ""),
                metadata=raw.get("metadata", {}),
                priority=raw.get("priority", 80),
                relevance_score=raw.get("relevance_score", 1.0),
            )
            item.token_estimate = estimate_context_item_tokens(item)
            items.append(item)
        return items
