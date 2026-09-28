import uuid
import pytest

from backend.app.services.retrieval.hybrid import HybridRetriever
from backend.app.services.retrieval.keyword import _compute_keyword_score, _tokenize, KeywordRetriever
from backend.app.services.retrieval.models import RetrievalCandidate
from backend.app.services.retrieval.reranker import LocalReranker
from backend.app.services.retrieval.vector import _cosine_similarity


def test_cosine_similarity_computation():
    # Identical vectors -> 1.0
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert _cosine_similarity(v1, v2) == 1.0

    # Orthogonal vectors -> 0.5 (normalized (0+1)/2)
    v3 = [0.0, 1.0, 0.0]
    assert _cosine_similarity(v1, v3) == 0.5

    # Empty or mismatched vectors -> 0.0
    assert _cosine_similarity([], []) == 0.0
    assert _cosine_similarity([1.0], [1.0, 2.0]) == 0.0


def test_keyword_scoring_heuristics():
    tokens = _tokenize("PostgreSQL pgvector query optimization")
    assert "postgresql" in tokens
    assert "pgvector" in tokens

    content = "PostgreSQL pgvector query optimization allows indexing high-dimensional embeddings."
    filename = "database_pgvector.md"

    score = _compute_keyword_score(tokens, "PostgreSQL pgvector query optimization", content, filename)
    assert score > 0.6  # High coverage + phrase match + filename bonus

    # Unrelated content
    unrelated = "Cooking recipe for chocolate chip cookies."
    zero_score = _compute_keyword_score(tokens, "PostgreSQL pgvector query optimization", unrelated, "recipe.txt")
    assert zero_score == 0.0


@pytest.mark.asyncio
async def test_local_reranker():
    reranker = LocalReranker()
    c1 = RetrievalCandidate(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        filename="security_auth.md",
        content="JWT tokens and OAuth2 authentication flow overview.",
        fusion_score=0.9,
    )
    c2 = RetrievalCandidate(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        filename="unrelated.txt",
        content="General styling guidelines and CSS architecture.",
        fusion_score=0.3,
    )

    ranked = await reranker.rerank("JWT tokens OAuth2", [c2, c1], top_k=2)
    assert len(ranked) == 2
    assert ranked[0].chunk_id == c1.chunk_id
    assert ranked[0].rerank_score > ranked[1].rerank_score
