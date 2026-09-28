import asyncio
import time
from typing import Dict, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.retrieval.keyword import KeywordRetriever
from backend.app.services.retrieval.models import RetrievalCandidate, RetrievalResult
from backend.app.services.retrieval.reranker import BaseReranker, LocalReranker
from backend.app.services.retrieval.vector import VectorRetriever


class HybridRetriever:
    """
    Coordinates Hybrid Search by executing Vector Search and Keyword Search concurrently,
    fusing the candidate results using Reciprocal Rank Fusion (RRF), and applying Reranking.
    """

    def __init__(
        self,
        vector_retriever: VectorRetriever,
        keyword_retriever: KeywordRetriever,
        reranker: Optional[BaseReranker] = None,
        rrf_k: int = 60,
        vector_weight: float = 0.6,
        keyword_weight: float = 0.4,
    ) -> None:
        self.vector_retriever = vector_retriever
        self.keyword_retriever = keyword_retriever
        self.reranker = reranker or LocalReranker()
        self.rrf_k = rrf_k
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight

    async def retrieve(
        self,
        query: str,
        workspace_id: UUID,
        session: AsyncSession,
        project_id: Optional[UUID] = None,
        top_k: int = 8,
        fetch_k: int = 20,
    ) -> RetrievalResult:
        start_time = time.perf_counter()

        if not query or not query.strip():
            return RetrievalResult(query=query, retrieval_latency_ms=0)

        # 1. Run Vector and Keyword search concurrently
        vector_task = self.vector_retriever.retrieve(
            query=query,
            workspace_id=workspace_id,
            session=session,
            project_id=project_id,
            top_k=fetch_k,
        )
        keyword_task = self.keyword_retriever.retrieve(
            query=query,
            workspace_id=workspace_id,
            session=session,
            project_id=project_id,
            top_k=fetch_k,
        )

        vector_candidates, keyword_candidates = await asyncio.gather(
            vector_task, keyword_task, return_exceptions=False
        )

        vector_count = len(vector_candidates)
        keyword_count = len(keyword_candidates)

        # 2. Reciprocal Rank Fusion (RRF)
        merged_map: Dict[UUID, RetrievalCandidate] = {}

        # Process vector ranks
        for rank, cand in enumerate(vector_candidates, start=1):
            rrf_contrib = self.vector_weight / (self.rrf_k + rank)
            if cand.chunk_id not in merged_map:
                cand.fusion_score = rrf_contrib
                merged_map[cand.chunk_id] = cand
            else:
                existing = merged_map[cand.chunk_id]
                existing.vector_score = cand.vector_score
                existing.fusion_score += rrf_contrib

        # Process keyword ranks
        for rank, cand in enumerate(keyword_candidates, start=1):
            rrf_contrib = self.keyword_weight / (self.rrf_k + rank)
            if cand.chunk_id not in merged_map:
                cand.fusion_score = rrf_contrib
                merged_map[cand.chunk_id] = cand
            else:
                existing = merged_map[cand.chunk_id]
                existing.keyword_score = cand.keyword_score
                existing.fusion_score += rrf_contrib

        all_candidates = list(merged_map.values())

        # Normalize fusion scores to [0.0, 1.0]
        if all_candidates:
            max_fusion = max(c.fusion_score for c in all_candidates)
            if max_fusion > 0:
                for c in all_candidates:
                    c.fusion_score = round(c.fusion_score / max_fusion, 4)

        # 3. Reranking
        reranked_candidates = await self.reranker.rerank(
            query=query,
            candidates=all_candidates,
            top_k=top_k,
        )

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        return RetrievalResult(
            candidates=reranked_candidates,
            query=query,
            total_found=len(all_candidates),
            vector_count=vector_count,
            keyword_count=keyword_count,
            retrieval_latency_ms=latency_ms,
        )
