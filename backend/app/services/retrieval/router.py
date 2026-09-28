from __future__ import annotations
import time
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.db.models.task import Task
from backend.app.services.embeddings.factory import get_embedding_provider
from backend.app.services.retrieval.decision import (
    RetrievalDecision,
    RetrievalScope,
    RetrievalStrategy,
)

if TYPE_CHECKING:
    from backend.app.services.context.models import ContextItem
from backend.app.services.retrieval.hybrid import HybridRetriever
from backend.app.services.retrieval.keyword import KeywordRetriever
from backend.app.services.retrieval.models import RetrievalResult
from backend.app.services.retrieval.policies import (
    RetrievalDecisionProvider,
    RuleBasedDecisionProvider,
)
from backend.app.services.retrieval.reranker import BaseReranker, LocalReranker
from backend.app.services.retrieval.strategies.multi_query import MultiQueryRetriever
from backend.app.services.retrieval.vector import VectorRetriever


class RetrievalRouter:
    """
    Intelligent Retrieval Router that analyzes task directives, determines whether
    external knowledge is needed, chooses the optimal retrieval strategy and scope,
    and dispatches execution to the corresponding retriever component.
    """

    def __init__(
        self,
        decision_provider: Optional[RetrievalDecisionProvider] = None,
        hybrid_retriever: Optional[HybridRetriever] = None,
        vector_retriever: Optional[VectorRetriever] = None,
        keyword_retriever: Optional[KeywordRetriever] = None,
        multi_query_retriever: Optional[MultiQueryRetriever] = None,
        reranker: Optional[BaseReranker] = None,
    ) -> None:
        self.decision_provider = decision_provider or RuleBasedDecisionProvider()
        self.reranker = reranker or LocalReranker()

        # Initialize underlying retrievers if not provided
        embedding_provider = get_embedding_provider()
        self.vector_retriever = vector_retriever or VectorRetriever(embedding_provider=embedding_provider)
        self.keyword_retriever = keyword_retriever or KeywordRetriever()
        self.hybrid_retriever = hybrid_retriever or HybridRetriever(
            vector_retriever=self.vector_retriever,
            keyword_retriever=self.keyword_retriever,
            reranker=self.reranker,
        )
        if multi_query_retriever is not None:
            self.multi_query_retriever = multi_query_retriever
        else:
            from backend.app.services.llm.factory import get_llm_factory
            self.multi_query_retriever = MultiQueryRetriever(
                hybrid_retriever=self.hybrid_retriever,
                llm_factory=get_llm_factory(),
                reranker=self.reranker,
            )

    async def decide(
        self,
        task: Task,
        context_items: Optional[List[ContextItem]] = None,
        **kwargs,
    ) -> RetrievalDecision:
        """
        Evaluates task directives and parameters to produce a structured RetrievalDecision.
        """
        decision = await self.decision_provider.decide(task, context_items=context_items, **kwargs)
        logger.info(
            f"[RetrievalRouter] Task '{task.id}' Decision: required={decision.retrieval_required}, "
            f"strategy='{decision.strategy.value}', scope='{decision.scope.value}', "
            f"confidence={decision.confidence}, top_k={decision.top_k}"
        )
        return decision

    async def execute(
        self,
        decision: RetrievalDecision,
        workspace_id: UUID,
        session: AsyncSession,
        project_id: Optional[UUID] = None,
    ) -> RetrievalResult:
        """
        Dispatches retrieval execution based on the strategy specified in the RetrievalDecision.
        """
        if not decision.retrieval_required or decision.strategy == RetrievalStrategy.NONE:
            return RetrievalResult(query=decision.query, retrieval_latency_ms=0)

        # Enforce scope: project vs workspace
        effective_project_id = project_id if decision.scope == RetrievalScope.PROJECT else None

        # 1. Strategy: Keyword
        if decision.strategy == RetrievalStrategy.KEYWORD:
            start_time = time.perf_counter()
            candidates = await self.keyword_retriever.retrieve(
                query=decision.query,
                workspace_id=workspace_id,
                session=session,
                project_id=effective_project_id,
                top_k=decision.top_k,
            )
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return RetrievalResult(
                candidates=candidates,
                query=decision.query,
                total_found=len(candidates),
                vector_count=0,
                keyword_count=len(candidates),
                retrieval_latency_ms=latency_ms,
            )

        # 2. Strategy: Vector
        elif decision.strategy == RetrievalStrategy.VECTOR:
            start_time = time.perf_counter()
            candidates = await self.vector_retriever.retrieve(
                query=decision.query,
                workspace_id=workspace_id,
                session=session,
                project_id=effective_project_id,
                top_k=decision.top_k,
            )
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return RetrievalResult(
                candidates=candidates,
                query=decision.query,
                total_found=len(candidates),
                vector_count=len(candidates),
                keyword_count=0,
                retrieval_latency_ms=latency_ms,
            )

        # 3. Strategy: Multi-Query
        elif decision.strategy == RetrievalStrategy.MULTI_QUERY:
            return await self.multi_query_retriever.retrieve(
                query=decision.query,
                workspace_id=workspace_id,
                session=session,
                project_id=effective_project_id,
                top_k=decision.top_k,
            )

        # 4. Strategy: Hybrid (default)
        else:
            return await self.hybrid_retriever.retrieve(
                query=decision.query,
                workspace_id=workspace_id,
                session=session,
                project_id=effective_project_id,
                top_k=decision.top_k,
            )


# Default global router instance (lazily initialized)
_default_retrieval_router: Optional[RetrievalRouter] = None


def get_retrieval_router() -> RetrievalRouter:
    """Dependency injector for RetrievalRouter."""
    global _default_retrieval_router
    if _default_retrieval_router is None:
        _default_retrieval_router = RetrievalRouter()
    return _default_retrieval_router
