import math
import re
from typing import Dict, List, Optional, Set
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.document import Document
from backend.app.db.models.document_chunk import DocumentChunk
from backend.app.services.retrieval.models import RetrievalCandidate

STOP_WORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
    "which", "this", "that", "these", "those", "then", "just", "so", "than",
    "such", "both", "through", "about", "for", "is", "of", "while", "during",
    "to", "from", "in", "out", "on", "off", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "any", "both", "each",
    "few", "more", "most", "other", "some", "no", "nor", "not", "only", "own",
    "same", "too", "very", "can", "will", "should", "now", "be", "have", "do"
}


def _tokenize(text: str) -> List[str]:
    """Tokenize and normalize text into lowercase alphanumeric tokens."""
    return re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", text.lower())


def _compute_keyword_score(query_tokens: List[str], raw_query: str, content: str, filename: str) -> float:
    """
    Computes a deterministic keyword relevance score based on:
    - Term coverage (how many query terms appear in content)
    - Term frequency with logarithmic dampening
    - Exact phrase match bonus
    - Document filename match bonus
    """
    if not query_tokens or not content:
        return 0.0

    content_lower = content.lower()
    content_tokens = _tokenize(content)
    total_content_tokens = max(len(content_tokens), 1)

    # Token frequency map
    tf_map: Dict[str, int] = {}
    for token in content_tokens:
        tf_map[token] = tf_map.get(token, 0) + 1

    matched_query_terms = 0
    tf_score = 0.0

    for q_tok in query_tokens:
        count = tf_map.get(q_tok, 0)
        if count > 0:
            matched_query_terms += 1
            # Sublinear TF term scaling
            tf_score += 1.0 + math.log(count)

    # Term coverage: fraction of unique query terms present
    unique_q_terms = len(set(query_tokens))
    coverage = matched_query_terms / unique_q_terms if unique_q_terms > 0 else 0.0

    # Normalized TF score relative to document length
    norm_tf = min(1.0, tf_score / (1.0 + math.log(total_content_tokens)))

    # Exact phrase match bonus
    phrase_bonus = 0.0
    cleaned_raw = raw_query.strip().lower()
    if len(query_tokens) > 1 and cleaned_raw in content_lower:
        phrase_bonus = 0.25

    # Filename match bonus
    filename_bonus = 0.0
    filename_lower = filename.lower()
    for q_tok in query_tokens:
        if q_tok in filename_lower:
            filename_bonus += 0.05
    filename_bonus = min(0.15, filename_bonus)

    # Combined composite keyword score
    raw_score = (0.5 * coverage) + (0.35 * norm_tf) + phrase_bonus + filename_bonus
    return max(0.0, min(1.0, raw_score))


class KeywordRetriever:
    """
    Retrieves relevant document chunks using lexical keyword matching and full-text scoring.
    Enforces multi-tenant workspace and optional project boundaries.
    """

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

        clean_query = query.strip()
        tokens = [t for t in _tokenize(clean_query) if t not in STOP_WORDS]
        if not tokens:
            tokens = _tokenize(clean_query)

        if not tokens:
            return []

        # Multi-tenant workspace scoped query
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

        scored_candidates: List[RetrievalCandidate] = []
        for chunk, filename in rows:
            kw_score = _compute_keyword_score(
                query_tokens=tokens,
                raw_query=clean_query,
                content=chunk.content,
                filename=filename,
            )

            # Only retain candidates with non-zero keyword match
            if kw_score > 0.01:
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
                        keyword_score=kw_score,
                    )
                )

        scored_candidates.sort(key=lambda x: x.keyword_score or 0.0, reverse=True)
        return scored_candidates[:top_k]
