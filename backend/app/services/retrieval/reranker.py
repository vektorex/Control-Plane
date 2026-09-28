from abc import ABC, abstractmethod
import re
from typing import List

from backend.app.services.retrieval.models import RetrievalCandidate


class BaseReranker(ABC):
    """
    Abstract interface for candidate rerankers.
    Prepares the architecture for future ML cross-encoders (e.g. Cohere, BGE, ColBERT)
    without coupling the rest of the application.
    """

    @abstractmethod
    async def rerank(
        self,
        query: str,
        candidates: List[RetrievalCandidate],
        top_k: int = 8,
    ) -> List[RetrievalCandidate]:
        pass


class LocalReranker(BaseReranker):
    """
    Deterministic rule-based local reranker that refines hybrid retrieval candidates.
    Combines fusion rank, exact match density, document title alignment, and chunk position.
    """

    async def rerank(
        self,
        query: str,
        candidates: List[RetrievalCandidate],
        top_k: int = 8,
    ) -> List[RetrievalCandidate]:
        if not candidates:
            return []

        clean_query = query.strip().lower()
        query_words = set(re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", clean_query))

        for cand in candidates:
            content_lower = cand.content.lower()
            lead_text = content_lower[:250]

            # 1. Base score from hybrid fusion (0.0 to 1.0)
            score = cand.fusion_score * 0.60

            # 2. Exact phrase bonus (0.15)
            if clean_query and clean_query in content_lower:
                score += 0.15

            # 3. Lead text keyword density bonus (0.15)
            lead_matches = sum(1 for w in query_words if w in lead_text)
            if query_words:
                lead_density = lead_matches / len(query_words)
                score += lead_density * 0.15

            # 4. Filename alignment bonus (0.10)
            if cand.filename:
                fn_matches = sum(1 for w in query_words if w in cand.filename.lower())
                if query_words and fn_matches > 0:
                    score += 0.10

            cand.rerank_score = round(max(0.0, min(1.0, score)), 4)

        # Sort descending by rerank_score
        sorted_candidates = sorted(candidates, key=lambda c: c.rerank_score, reverse=True)
        return sorted_candidates[:top_k]
