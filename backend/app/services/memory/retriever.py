"""
MemoryRetriever supporting semantic, keyword, and deterministic weighted hybrid retrieval.
Enforces multi-tenant workspace, user, and project scope boundaries.
"""
from datetime import datetime, timezone
import math
import re
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.db.models.memory import Memory, MemoryEmbedding
from backend.app.services.embeddings.base import BaseEmbeddingProvider
from backend.app.services.embeddings.factory import get_embedding_provider
from backend.app.services.memory.schemas import MemoryImportance, MemoryStatus

MAX_MEMORY_RESULTS = 10
MAX_MEMORY_CONTEXT_TOKENS = 3000

IMPORTANCE_WEIGHTS = {
    MemoryImportance.HIGH.value: 1.0,
    MemoryImportance.MEDIUM.value: 0.7,
    MemoryImportance.LOW.value: 0.4,
}


def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    sim = dot / (norm1 * norm2)
    return max(0.0, min(1.0, (sim + 1.0) / 2.0))


def _keyword_similarity(query: str, text: str) -> float:
    """Computes basic lexical overlap score between query terms and text."""
    if not query or not text:
        return 0.0
    q_words = set(re.findall(r"\w+", query.lower()))
    t_words = set(re.findall(r"\w+", text.lower()))
    if not q_words or not t_words:
        return 0.0
    intersection = q_words.intersection(t_words)
    return len(intersection) / len(q_words)


class MemoryRetriever:
    """
    Retrieves and ranks relevant memories using semantic, keyword, and factual metadata signals.
    """

    def __init__(self, embedding_provider: Optional[BaseEmbeddingProvider] = None):
        self.embedding_provider = embedding_provider or get_embedding_provider()

    async def retrieve(
        self,
        query: str,
        workspace_id: UUID,
        session: AsyncSession,
        user_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        top_k: int = MAX_MEMORY_RESULTS,
        max_tokens: int = MAX_MEMORY_CONTEXT_TOKENS,
        strategy: str = "hybrid",  # "semantic", "keyword", "hybrid"
    ) -> List[Tuple[Memory, float, Dict[str, Any]]]:
        """
        Retrieves active, authorized, unexpired memories matching query directives.
        """
        if not query or not query.strip():
            return []

        clean_query = query.strip()
        top_k = min(max(1, top_k), MAX_MEMORY_RESULTS)
        now = datetime.now(timezone.utc)

        # 1. Build Scope Boundaries
        # Rule: Never allow project memory to leak into another project.
        # Rule: Never allow private user memory to leak to another user.
        # Rule: Workspace memories are available across the workspace.
        scope_conditions = [Memory.scope == "workspace"]
        if user_id:
            scope_conditions.append(and_(Memory.scope == "user", Memory.user_id == user_id))
        if project_id:
            scope_conditions.append(and_(Memory.scope == "project", Memory.project_id == project_id))

        stmt = (
            select(Memory)
            .options(selectinload(Memory.embedding))
            .where(
                and_(
                    Memory.workspace_id == workspace_id,
                    Memory.status == MemoryStatus.ACTIVE.value,
                    or_(Memory.expires_at.is_(None), Memory.expires_at > now),
                    or_(*scope_conditions),
                )
            )
        )

        res = await session.execute(stmt)
        candidates = res.scalars().all()
        if not candidates:
            return []

        # 2. Embedding calculation for semantic retrieval if needed
        query_vector: Optional[List[float]] = None
        if strategy in ("semantic", "hybrid"):
            try:
                query_vector = await self.embedding_provider.embed_text(clean_query)
            except Exception:
                query_vector = None

        # 3. Deterministic scoring
        scored_memories: List[Tuple[Memory, float, Dict[str, Any]]] = []

        for mem in candidates:
            # Semantic score
            semantic_score = 0.0
            if query_vector and mem.embedding and mem.embedding.embedding:
                semantic_score = _cosine_similarity(query_vector, mem.embedding.embedding)

            # Keyword score
            combined_text = f"{mem.title} {mem.normalized_content}"
            keyword_score = _keyword_similarity(clean_query, combined_text)

            # Scope bonus: exact project or private user matches rank slightly higher than generic workspace
            scope_score = 0.5
            if mem.scope == "project" and project_id and mem.project_id == project_id:
                scope_score = 1.0
            elif mem.scope == "user" and user_id and mem.user_id == user_id:
                scope_score = 0.9

            # Importance weight
            importance_score = IMPORTANCE_WEIGHTS.get(mem.importance, 0.7)

            # Recency / usage frequency signal
            recency_score = 0.5
            if mem.last_used_at:
                days_since_used = (now - (mem.last_used_at.replace(tzinfo=timezone.utc) if mem.last_used_at.tzinfo is None else mem.last_used_at)).days
                recency_score = max(0.1, 1.0 - min(1.0, days_since_used / 90.0))

            # Strategy composition
            if strategy == "semantic":
                total_score = (0.75 * semantic_score) + (0.15 * scope_score) + (0.10 * importance_score)
            elif strategy == "keyword":
                total_score = (0.75 * keyword_score) + (0.15 * scope_score) + (0.10 * importance_score)
            else:  # hybrid
                total_score = (
                    (0.45 * semantic_score)
                    + (0.25 * keyword_score)
                    + (0.15 * scope_score)
                    + (0.10 * importance_score)
                    + (0.05 * recency_score)
                )

            # Minimum relevance gate
            if total_score > 0.15:
                explanation = {
                    "strategy": strategy,
                    "semantic_score": round(semantic_score, 4),
                    "keyword_score": round(keyword_score, 4),
                    "scope_score": round(scope_score, 2),
                    "importance_score": round(importance_score, 2),
                    "recency_score": round(recency_score, 2),
                    "final_score": round(total_score, 4),
                }
                scored_memories.append((mem, total_score, explanation))

        # 4. Sort and apply token / count limits
        scored_memories.sort(key=lambda x: x[1], reverse=True)

        final_items: List[Tuple[Memory, float, Dict[str, Any]]] = []
        token_count = 0

        for mem, score, exp in scored_memories[:top_k]:
            est_tokens = max(1, len(mem.content) // 4)
            if token_count + est_tokens > max_tokens and final_items:
                break
            final_items.append((mem, score, exp))
            token_count += est_tokens

        return final_items
