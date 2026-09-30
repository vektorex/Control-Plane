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

        # 4. Strategy: Memory
        elif decision.strategy == RetrievalStrategy.MEMORY:
            start_time = time.perf_counter()
            from backend.app.services.memory.retriever import MemoryRetriever, MAX_MEMORY_RESULTS, MAX_MEMORY_CONTEXT_TOKENS
            from backend.app.services.retrieval.models import RetrievalCandidate

            user_id = kwargs.get("user_id")
            mem_retriever = MemoryRetriever(embedding_provider=self.vector_retriever.embedding_provider)
            bounded_k = min(decision.top_k, MAX_MEMORY_RESULTS)
            scored = await mem_retriever.retrieve(
                query=decision.query,
                workspace_id=workspace_id,
                session=session,
                user_id=user_id,
                project_id=effective_project_id,
                top_k=bounded_k,
                max_tokens=MAX_MEMORY_CONTEXT_TOKENS,
                strategy="hybrid",
            )
            candidates = []
            for mem, score, exp in scored:
                candidates.append(
                    RetrievalCandidate(
                        chunk_id=mem.id,
                        document_id=mem.id,
                        workspace_id=workspace_id,
                        project_id=mem.project_id,
                        filename=f"memory:{mem.scope}",
                        content=f"[{mem.type.upper()}] {mem.title}\n{mem.content}",
                        metadata={
                            "memory_id": str(mem.id),
                            "scope": mem.scope,
                            "type": mem.type,
                            "importance": mem.importance,
                            "trust_level": "trusted_user_context",
                            "explanation": exp,
                        },
                        fusion_score=score,
                        rerank_score=score,
                    )
                )
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return RetrievalResult(
                candidates=candidates,
                query=decision.query,
                total_found=len(candidates),
                vector_count=len(candidates),
                keyword_count=len(candidates),
                retrieval_latency_ms=latency_ms,
            )

        # 5. Strategy: Connector / GitHub
        elif decision.strategy in (RetrievalStrategy.CONNECTOR, RetrievalStrategy.GITHUB):
            start_time = time.perf_counter()
            import uuid as uuid_pkg
            from backend.app.services.connectors.executor import get_connector_executor
            from backend.app.services.retrieval.models import RetrievalCandidate

            conn_executor = get_connector_executor()
            conn_name = decision.metadata.get("connector", "github")
            conn_op = decision.metadata.get("operation", "search_issues")

            conn_res = await conn_executor.execute(
                connector_name=conn_name,
                operation=conn_op,
                arguments={"query": decision.query, "limit": decision.top_k},
                workspace_id=workspace_id,
                session=session,
            )

            candidates: List[RetrievalCandidate] = []
            if conn_res.success and conn_res.items:
                for idx, item in enumerate(conn_res.items):
                    c_title = item.get("title") or item.get("name") or f"Item {idx+1}"
                    c_body = item.get("body") or item.get("description") or str(item)
                    content_str = f"[{conn_name.upper()} {conn_op}] {c_title}\n\n{c_body}"

                    candidate = RetrievalCandidate(
                        chunk_id=uuid_pkg.uuid4(),
                        document_id=uuid_pkg.uuid4(),
                        workspace_id=workspace_id,
                        project_id=effective_project_id,
                        filename=f"{conn_name}_{conn_op}",
                        content=content_str,
                        metadata={
                            "connector": conn_name,
                            "operation": conn_op,
                            "trust_level": "external_untrusted",
                            "source_url": item.get("html_url") or "",
                        },
                        fusion_score=0.9 - (idx * 0.05),
                        rerank_score=0.9 - (idx * 0.05),
                    )
                    candidates.append(candidate)

            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return RetrievalResult(
                candidates=candidates,
                query=decision.query,
                total_found=len(candidates),
                vector_count=0,
                keyword_count=len(candidates),
                retrieval_latency_ms=latency_ms,
            )

        # 6. Strategy: Document / Hybrid (default)
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
