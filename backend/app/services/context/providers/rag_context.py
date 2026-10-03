import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.db.models.task import Task
from backend.app.services.context.base import ContextProvider
from backend.app.services.context.models import ContextItem, ContextSourceType
from backend.app.services.context.token_estimator import estimate_context_item_tokens
from backend.app.services.retrieval.decision import (
    RetrievalDecision,
    RetrievalMode,
    RetrievalScope,
    RetrievalStrategy,
)
from backend.app.services.retrieval.models import RetrievalCandidate, RetrievalResult
from backend.app.services.retrieval.router import RetrievalRouter, get_retrieval_router


class RAGContextProvider(ContextProvider):
    """
    Context Provider that consumes RetrievalDecision from RetrievalRouter and executes
    the selected retrieval strategy (None, Keyword, Vector, Hybrid, Multi-Query)
    over user-owned documents within the task's workspace/project boundary.
    """

    def __init__(self, router: Optional[RetrievalRouter] = None) -> None:
        self.router = router or get_retrieval_router()

    @property
    def provider_id(self) -> str:
        return "rag_context"

    @property
    def source_type(self) -> str:
        return ContextSourceType.DOCUMENT.value

    async def can_handle(self, task: Task, **kwargs: Any) -> bool:
        """
        Determines whether RAG context processing should participate.
        Returns False only if explicitly disabled via mode='never'.
        """
        if not task:
            return False

        mode = kwargs.get("retrieval_mode")
        if mode is None and hasattr(task, "metadata_json") and task.metadata_json:
            mode = task.metadata_json.get("retrieval_mode")

        if mode == RetrievalMode.NEVER.value:
            return False

        return True

    async def collect(
        self,
        task: Task,
        session: Optional[AsyncSession] = None,
        **kwargs: Any,
    ) -> List[RetrievalCandidate]:
        """
        Evaluates retrieval decision via the RetrievalRouter and dispatches to the selected retriever.
        """
        if session is None:
            logger.warning("[RAGContextProvider] Database session is missing. Skipping retrieval.")
            return []

        # 1. Obtain or compute RetrievalDecision
        decision: Optional[RetrievalDecision] = kwargs.get("retrieval_decision")
        if decision is None:
            decision = await self.router.decide(task, **kwargs)

        telemetry_callback = kwargs.get("retrieval_telemetry_callback")

        # 2. Check if retrieval is deemed unnecessary
        if not decision.retrieval_required or decision.strategy == RetrievalStrategy.NONE:
            logger.info(f"[RAGContextProvider] Retrieval not required for task '{task.id}' ({decision.reason})")
            if callable(telemetry_callback):
                empty_res = RetrievalResult(query=decision.query, retrieval_latency_ms=0)
                telemetry_callback({"decision": decision, "result": empty_res})
            return []

        # 3. Determine workspace and project scoping
        workspace_id = None
        if "project" in getattr(task, "__dict__", {}) and task.__dict__["project"]:
            workspace_id = getattr(task.__dict__["project"], "workspace_id", None)
        elif getattr(task, "workspace_id", None):
            workspace_id = task.workspace_id
        elif getattr(task, "project_id", None) and session:
            from backend.app.db.models.project import Project
            from sqlalchemy import select
            proj_stmt = select(Project.workspace_id).where(Project.id == task.project_id)
            proj_res = await session.execute(proj_stmt)
            workspace_id = proj_res.scalar_one_or_none()

        if not workspace_id:
            logger.warning(f"[RAGContextProvider] Could not resolve workspace for task '{task.id}'. Skipping retrieval.")
            if callable(telemetry_callback):
                empty_res = RetrievalResult(query=decision.query, retrieval_latency_ms=0)
                telemetry_callback({"decision": decision, "result": empty_res})
            return []

        logger.info(
            f"[RAGContextProvider] Executing '{decision.strategy.value}' retrieval for task '{task.id}' "
            f"in workspace '{workspace_id}' (scope='{decision.scope.value}', top_k={decision.top_k})"
        )

        # 4. Execute retrieval strategy via Router
        result: RetrievalResult = await self.router.execute(
            decision=decision,
            workspace_id=workspace_id,
            session=session,
            project_id=task.project_id,
        )

        # 5. Record telemetry
        if callable(telemetry_callback):
            telemetry_callback({"decision": decision, "result": result})

        return result.candidates

    def normalize(self, raw_items: List[RetrievalCandidate], **kwargs: Any) -> List[ContextItem]:
        """
        Transforms raw RetrievalCandidate objects into normalized ContextItems.
        """
        items: List[ContextItem] = []
        for cand in raw_items:
            page_suffix = f" (Page {cand.page_number})" if cand.page_number else ""
            title = f"Document: {cand.filename}{page_suffix}"

            score = cand.rerank_score if cand.rerank_score > 0 else cand.fusion_score

            metadata = {
                "document_id": str(cand.document_id),
                "chunk_id": str(cand.chunk_id),
                "filename": cand.filename,
                "page_number": cand.page_number,
                "vector_score": cand.vector_score,
                "keyword_score": cand.keyword_score,
                "fusion_score": cand.fusion_score,
                "rerank_score": cand.rerank_score,
                **cand.metadata,
            }

            item = ContextItem(
                id=f"chunk-{cand.chunk_id}",
                source_type=self.source_type,
                title=title,
                content=cand.content,
                metadata=metadata,
                priority=70,
                relevance_score=score,
            )
            item.token_estimate = estimate_context_item_tokens(item)
            items.append(item)

        return items
