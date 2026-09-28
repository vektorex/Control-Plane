import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.db.models.task import Task
from backend.app.services.context.base import ContextProvider
from backend.app.services.context.models import ContextItem, ContextSourceType
from backend.app.services.context.token_estimator import estimate_context_item_tokens
from backend.app.services.embeddings.factory import get_embedding_provider
from backend.app.services.retrieval.hybrid import HybridRetriever
from backend.app.services.retrieval.keyword import KeywordRetriever
from backend.app.services.retrieval.models import RetrievalCandidate, RetrievalResult
from backend.app.services.retrieval.reranker import LocalReranker
from backend.app.services.retrieval.vector import VectorRetriever


class RAGContextProvider(ContextProvider):
    """
    Context Provider that performs Hybrid RAG Retrieval (Vector + Keyword Search + Reranking)
    over user-owned documents within the task's workspace and optional project scope.
    """

    def __init__(self, hybrid_retriever: Optional[HybridRetriever] = None) -> None:
        if hybrid_retriever is not None:
            self.hybrid_retriever = hybrid_retriever
        else:
            embedding_provider = get_embedding_provider()
            vector_retriever = VectorRetriever(embedding_provider=embedding_provider)
            keyword_retriever = KeywordRetriever()
            reranker = LocalReranker()
            self.hybrid_retriever = HybridRetriever(
                vector_retriever=vector_retriever,
                keyword_retriever=keyword_retriever,
                reranker=reranker,
            )

    @property
    def provider_id(self) -> str:
        return "rag_context"

    @property
    def source_type(self) -> str:
        return ContextSourceType.DOCUMENT.value

    async def can_handle(self, task: Task, **kwargs: Any) -> bool:
        """
        Applies when retrieval is explicitly enabled via kwargs or task configuration,
        and a valid database session and task workspace are present.
        """
        if not task:
            return False

        # Check kwargs flag first, fallback to task metadata
        retrieval_enabled = kwargs.get("retrieval_enabled")
        if retrieval_enabled is None and hasattr(task, "metadata_json") and task.metadata_json:
            retrieval_enabled = task.metadata_json.get("retrieval_enabled", False)

        return bool(retrieval_enabled)

    async def collect(
        self,
        task: Task,
        session: Optional[AsyncSession] = None,
        **kwargs: Any,
    ) -> List[RetrievalCandidate]:
        """
        Executes Hybrid Retrieval (Vector + Keyword + Reranking) against document chunks.
        """
        if session is None:
            logger.warning("[RAGContextProvider] Database session is missing. Skipping retrieval.")
            return []

        # 1. Determine retrieval query
        query = kwargs.get("query")
        if not query or not str(query).strip():
            # Build query from task directive and title
            parts = [task.title]
            if task.instructions:
                parts.append(task.instructions)
            elif task.description:
                parts.append(task.description)
            query = " ".join(parts).strip()

        if not query:
            return []

        # 2. Determine workspace and project scoping
        workspace_id = None
        if hasattr(task, "project") and task.project and hasattr(task.project, "workspace_id"):
            workspace_id = task.project.workspace_id
        elif task.project_id:
            from backend.app.db.models.project import Project
            from sqlalchemy import select
            proj_stmt = select(Project.workspace_id).where(Project.id == task.project_id)
            proj_res = await session.execute(proj_stmt)
            workspace_id = proj_res.scalar_one_or_none()

        if not workspace_id:
            logger.warning(f"[RAGContextProvider] Could not resolve workspace for task '{task.id}'. Skipping retrieval.")
            return []

        project_scope = kwargs.get("retrieval_project_scope", kwargs.get("project_scope", True))
        project_id = task.project_id if project_scope else None

        # 3. Determine top_k limit
        top_k = kwargs.get("retrieval_top_k", kwargs.get("top_k", 8))

        logger.info(
            f"[RAGContextProvider] Running hybrid retrieval for task '{task.id}' "
            f"in workspace '{workspace_id}' (project='{project_id}', top_k={top_k})"
        )

        # 4. Run hybrid retriever
        result: RetrievalResult = await self.hybrid_retriever.retrieve(
            query=query,
            workspace_id=workspace_id,
            session=session,
            project_id=project_id,
            top_k=top_k,
        )

        # 5. Record telemetry if collector is provided in kwargs
        telemetry_callback = kwargs.get("retrieval_telemetry_callback")
        if callable(telemetry_callback):
            telemetry_callback(result)

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
