import math
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.document import Document
from backend.app.db.models.document_chunk import DocumentChunk
from backend.app.services.embeddings.base import BaseEmbeddingProvider
from backend.app.services.retrieval.models import RetrievalCandidate


def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    # Bound between 0.0 and 1.0 (normalized cosine score)
    sim = dot / (norm1 * norm2)
    return max(0.0, min(1.0, (sim + 1.0) / 2.0))


class VectorRetriever:
    """
    Retrieves relevant document chunks using vector semantic similarity.
    Enforces multi-tenant workspace and optional project boundaries.
    """

    def __init__(self, embedding_provider: BaseEmbeddingProvider) -> None:
        self.embedding_provider = embedding_provider

    async def retrieve(
        self,
        query: str,
        workspace_id: UUID,
        session: AsyncSession,
        project_id: Optional[UUID] = None,
        top_k: int = 10,
    ) -> List[RetrievalCandidate]:
        if not query or not query.strip():
            return []

        # 1. Embed query
        query_vector = await self.embedding_provider.embed_text(query.strip())

        # 2. Query candidate chunks within multi-tenant workspace boundary
        stmt = (
            select(DocumentChunk, Document.filename)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(
                DocumentChunk.workspace_id == workspace_id,
                Document.status == "ready",
            )
        )

        if project_id:
            stmt = stmt.where(DocumentChunk.project_id == project_id)

        res = await session.execute(stmt)
        rows = res.all()

        if not rows:
            return []

        # 3. Score and rank candidates
        scored_candidates: List[RetrievalCandidate] = []
        for chunk, filename in rows:
            if not chunk.embedding:
                continue

            sim_score = _cosine_similarity(query_vector, chunk.embedding)

            scored_candidates.append(
                RetrievalCandidate(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    workspace_id=chunk.workspace_id,
                    project_id=chunk.project_id,
                    filename=filename,
                    content=chunk.content,
                    page_number=chunk.page_number,
                    metadata=chunk.metadata_json or {},
                    vector_score=sim_score,
                )
            )

        # Sort descending by vector similarity
        scored_candidates.sort(key=lambda x: x.vector_score or 0.0, reverse=True)
        return scored_candidates[:top_k]
