"""
Context Provider that retrieves and normalizes persistent memories into ContextItems.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.memory import Memory
from backend.app.db.models.task import Task
from backend.app.services.context.base import ContextProvider
from backend.app.services.context.models import ContextItem, ContextSourceType
from backend.app.services.context.token_estimator import estimate_context_item_tokens
from backend.app.services.memory.retriever import MemoryRetriever, MAX_MEMORY_RESULTS, MAX_MEMORY_CONTEXT_TOKENS


class MemoryContextProvider(ContextProvider):
    """
    Retrieves and injects relevant, authorized persistent memories into the ContextEngine.
    """

    def __init__(self, retriever: Optional[MemoryRetriever] = None):
        self.retriever = retriever or MemoryRetriever()

    @property
    def provider_id(self) -> str:
        return "memory_context"

    @property
    def source_type(self) -> str:
        return ContextSourceType.MEMORY.value

    async def can_handle(self, task: Task, **kwargs: Any) -> bool:
        # Activated when memories are explicitly provided in kwargs, or when a task has instructions to match against
        if kwargs.get("memories"):
            return True
        if kwargs.get("memory_enabled", True) is False:
            return False
        return task is not None

    async def collect(
        self,
        task: Task,
        session: Optional[AsyncSession] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        raw_items: List[Dict[str, Any]] = []

        # 1. Direct memory objects provided in kwargs
        direct_memories = kwargs.get("memories")
        if direct_memories:
            for mem in direct_memories:
                raw_items.append(self._memory_to_raw(mem, score=1.0, explanation={"strategy": "explicit"}))
            return raw_items

        # 2. Dynamic memory retrieval if session and task available
        if session and task:
            workspace_id = kwargs.get("workspace_id")
            if not workspace_id and "project" in getattr(task, "__dict__", {}) and task.__dict__["project"]:
                workspace_id = getattr(task.__dict__["project"], "workspace_id", None)
            elif not workspace_id and getattr(task, "project_id", None) and session:
                from backend.app.db.models.project import Project
                from sqlalchemy import select
                proj_stmt = select(Project.workspace_id).where(Project.id == task.project_id)
                proj_res = await session.execute(proj_stmt)
                workspace_id = proj_res.scalar_one_or_none()

            if not workspace_id:
                return []

            query = (
                kwargs.get("query")
                or (task.instructions or "").strip()
                or (task.description or "").strip()
                or task.title
            )
            user_id = kwargs.get("user_id") or getattr(task, "user_id", None)
            project_id = kwargs.get("project_id") or getattr(task, "project_id", None)
            top_k = kwargs.get("top_k", MAX_MEMORY_RESULTS)
            max_tokens = kwargs.get("max_tokens", MAX_MEMORY_CONTEXT_TOKENS)

            try:
                scored_results = await self.retriever.retrieve(
                    query=query,
                    workspace_id=workspace_id,
                    session=session,
                    user_id=user_id,
                    project_id=project_id,
                    top_k=top_k,
                    max_tokens=max_tokens,
                )
                for mem, score, exp in scored_results:
                    raw_items.append(self._memory_to_raw(mem, score=score, explanation=exp))
            except Exception:
                return []

        return raw_items

    def _memory_to_raw(self, mem: Memory, score: float = 1.0, explanation: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        priority = 70 if getattr(mem, "importance", "medium") == "high" else (60 if getattr(mem, "importance", "medium") == "medium" else 50)
        return {
            "id": f"mem-{mem.id}",
            "title": mem.title,
            "content": mem.content,
            "priority": priority,
            "relevance_score": score,
            "metadata": {
                "memory_id": str(mem.id),
                "scope": mem.scope,
                "memory_type": mem.type,
                "importance": mem.importance,
                "source_type": mem.source_type,
                "retrieval_explanation": explanation or {},
            },
            "trust_level": "trusted_user_context",
        }

    def normalize(self, raw_items: List[Dict[str, Any]], **kwargs: Any) -> List[ContextItem]:
        items: List[ContextItem] = []
        for raw in raw_items:
            item = ContextItem(
                id=raw.get("id"),
                source_type=self.source_type,
                title=raw.get("title", "Persistent Memory"),
                content=raw.get("content", ""),
                metadata=raw.get("metadata", {}),
                priority=raw.get("priority", 60),
                relevance_score=raw.get("relevance_score", 1.0),
                trust_level=raw.get("trust_level", "trusted_user_context"),
            )
            item.token_estimate = estimate_context_item_tokens(item)
            items.append(item)
        return items
