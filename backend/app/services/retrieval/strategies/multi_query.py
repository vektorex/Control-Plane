import asyncio
import re
import time
from typing import Dict, List, Optional, TYPE_CHECKING
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.schemas.llm import ChatMessage, LLMGenerateRequest
from backend.app.services.retrieval.hybrid import HybridRetriever
from backend.app.services.retrieval.models import RetrievalCandidate, RetrievalResult
from backend.app.services.retrieval.reranker import BaseReranker, LocalReranker

if TYPE_CHECKING:
    from backend.app.services.llm.factory import LLMProviderFactory


class MultiQueryRetriever:
    """
    MultiQueryRetriever expands a single search query into multiple distinct query variations
    using the LLM abstraction, executes hybrid retrieval across all queries concurrently,
    deduplicates candidate chunks, and applies a reranker to produce the final context.
    """

    def __init__(
        self,
        hybrid_retriever: HybridRetriever,
        llm_factory: Optional["LLMProviderFactory"] = None,
        reranker: Optional[BaseReranker] = None,
        max_queries: int = settings.MAX_RETRIEVAL_QUERIES,
    ) -> None:
        self.hybrid_retriever = hybrid_retriever
        if llm_factory is not None:
            self.llm_factory = llm_factory
        else:
            from backend.app.services.llm.factory import get_llm_factory
            self.llm_factory = get_llm_factory()
        self.reranker = reranker or LocalReranker()
        self.max_queries = max(1, min(max_queries, settings.MAX_RETRIEVAL_QUERIES))

    async def generate_queries(self, original_query: str) -> List[str]:
        """
        Generates alternative search queries from different perspectives (keyword, semantic, subtopics).
        Always includes original query as first item and bounds total query count.
        Falls back to [original_query] on any LLM or parsing failure.
        """
        clean_query = original_query.strip()
        if not clean_query:
            return []

        queries = [clean_query]
        max_variations = max(0, self.max_queries - 1)
        if max_variations == 0:
            return queries

        prompt = (
            f"You are an AI assistant helping with document retrieval. "
            f"Given the user's search query, generate {max_variations} distinct alternative search queries "
            f"from different perspectives (e.g. key terms, conceptual phrasing, specific subtopics). "
            f"Do not answer the query. Output ONLY the alternative queries, one per line, with no numbering, bullets, or intro/outro.\n\n"
            f"User Query: {clean_query}"
        )

        try:
            from backend.app.services.ai_gateway import GatewayRequest, default_ai_gateway

            gw_req = GatewayRequest(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a specialized search query expansion engine. Output only queries, one per line."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                metadata={"purpose": "multi_query_expansion"},
            )

            res = await default_ai_gateway.execute(gw_req)
            raw_output = res.content.strip() if res and res.content else ""

            # Parse lines and clean up formatting
            seen = {clean_query.lower()}
            for line in raw_output.splitlines():
                cleaned_line = re.sub(r"^\s*([0-9]+[\.\-\)]|\*|\-|\•)\s*", "", line).strip()
                # Remove quotes if wrapped
                cleaned_line = re.sub(r"^[\"']|[\"']$", "", cleaned_line).strip()

                if cleaned_line and cleaned_line.lower() not in seen and len(cleaned_line) > 3:
                    seen.add(cleaned_line.lower())
                    queries.append(cleaned_line)
                    if len(queries) >= self.max_queries:
                        break

            logger.info(f"[MultiQueryRetriever] Expanded '{clean_query}' into {len(queries)} queries: {queries}")
            return queries

        except Exception as e:
            logger.warning(f"[MultiQueryRetriever] Query expansion failed ({str(e)}). Falling back to original query.")
            return queries

    async def retrieve(
        self,
        query: str,
        workspace_id: UUID,
        session: AsyncSession,
        project_id: Optional[UUID] = None,
        top_k: int = 8,
        fetch_k: int = 20,
    ) -> RetrievalResult:
        """
        Executes multi-query retrieval by generating queries, running concurrent hybrid searches,
        deduplicating candidate chunks across runs, and reranking candidates.
        """
        start_time = time.perf_counter()

        if not query or not query.strip():
            return RetrievalResult(query=query, retrieval_latency_ms=0)

        # 1. Expand query into variations
        queries = await self.generate_queries(query)

        # 2. Run hybrid retrieval for each query concurrently
        tasks = [
            self.hybrid_retriever.retrieve(
                query=q,
                workspace_id=workspace_id,
                session=session,
                project_id=project_id,
                top_k=fetch_k,
                fetch_k=fetch_k,
            )
            for q in queries
        ]

        results: List[RetrievalResult] = await asyncio.gather(*tasks, return_exceptions=False)

        # 3. Deduplicate and merge candidate chunks across queries
        merged_candidates: Dict[UUID, RetrievalCandidate] = {}
        total_vector = 0
        total_keyword = 0

        for r in results:
            total_vector += r.vector_count
            total_keyword += r.keyword_count

            for rank, cand in enumerate(r.candidates, start=1):
                chunk_id = cand.chunk_id
                # Reciprocal rank contribution from this query pass
                rank_contrib = 1.0 / (60 + rank)

                if chunk_id not in merged_candidates:
                    cand.fusion_score = rank_contrib
                    merged_candidates[chunk_id] = cand
                else:
                    existing = merged_candidates[chunk_id]
                    existing.fusion_score += rank_contrib
                    # Preserve highest vector/keyword scores
                    if cand.vector_score is not None:
                        existing.vector_score = max(existing.vector_score or 0.0, cand.vector_score)
                    if cand.keyword_score is not None:
                        existing.keyword_score = max(existing.keyword_score or 0.0, cand.keyword_score)

        all_candidates = list(merged_candidates.values())

        # Normalize fusion scores
        if all_candidates:
            max_fusion = max(c.fusion_score for c in all_candidates)
            if max_fusion > 0:
                for c in all_candidates:
                    c.fusion_score = round(c.fusion_score / max_fusion, 4)

        # 4. Rerank candidates with local reranker against the original query
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
            vector_count=total_vector,
            keyword_count=total_keyword,
            retrieval_latency_ms=latency_ms,
        )
