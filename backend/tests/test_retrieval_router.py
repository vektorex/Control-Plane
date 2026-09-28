import io
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.app.config import settings
from backend.app.db.models.task import Task
from backend.app.schemas.llm import LLMGenerateResponse
from backend.app.services.llm.factory import LLMProviderFactory
from backend.app.services.retrieval.decision import (
    RetrievalDecision,
    RetrievalMode,
    RetrievalScope,
    RetrievalStrategy,
)
from backend.app.services.retrieval.hybrid import HybridRetriever
from backend.app.services.retrieval.models import RetrievalCandidate, RetrievalResult
from backend.app.services.retrieval.policies import RuleBasedDecisionProvider
from backend.app.services.retrieval.reranker import LocalReranker
from backend.app.services.retrieval.strategies.multi_query import MultiQueryRetriever


# =====================================================================
# 1. ROUTING POLICY UNIT TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_routing_simple_task_no_retrieval():
    """1. simple task -> no retrieval"""
    provider = RuleBasedDecisionProvider()
    task = Task(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Summarization",
        instructions="Summarize this paragraph.",
    )
    decision = await provider.decide(task)
    assert decision.retrieval_required is False
    assert decision.strategy == RetrievalStrategy.NONE
    assert decision.confidence >= 0.80
    assert "closed-form" in decision.reason.lower() or "not requiring" in decision.reason.lower()


@pytest.mark.asyncio
async def test_routing_factual_project_task_hybrid():
    """2. factual project task -> hybrid"""
    provider = RuleBasedDecisionProvider()
    task = Task(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Auth implementation",
        instructions="What does our authentication implementation do?",
    )
    decision = await provider.decide(task)
    assert decision.retrieval_required is True
    assert decision.strategy == RetrievalStrategy.HYBRID
    assert decision.scope == RetrievalScope.PROJECT
    assert decision.confidence >= 0.85


@pytest.mark.asyncio
async def test_routing_exact_phrase_search_keyword():
    """3. exact phrase search -> keyword"""
    provider = RuleBasedDecisionProvider()
    task = Task(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Search token",
        instructions="Find the exact phrase 'refresh token' in the documentation.",
    )
    decision = await provider.decide(task)
    assert decision.retrieval_required is True
    assert decision.strategy == RetrievalStrategy.KEYWORD
    assert "refresh token" in decision.query


@pytest.mark.asyncio
async def test_routing_semantic_task_vector():
    """4. semantic task -> vector"""
    provider = RuleBasedDecisionProvider()
    task = Task(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Explain concepts",
        instructions="Explain the concepts related to authentication from our project documentation.",
    )
    decision = await provider.decide(task)
    assert decision.retrieval_required is True
    assert decision.strategy == RetrievalStrategy.VECTOR
    assert decision.confidence >= 0.85


@pytest.mark.asyncio
async def test_routing_comparison_task_hybrid():
    """5. comparison task -> hybrid"""
    provider = RuleBasedDecisionProvider()
    task = Task(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Compare security",
        instructions="Compare our JWT implementation with the security requirements in the uploaded documentation.",
    )
    decision = await provider.decide(task)
    assert decision.retrieval_required is True
    assert decision.strategy == RetrievalStrategy.HYBRID
    assert decision.scope == RetrievalScope.PROJECT


@pytest.mark.asyncio
async def test_routing_explicit_never_override():
    """6. explicit never -> no retrieval"""
    provider = RuleBasedDecisionProvider()
    task = Task(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Factual question",
        instructions="What does our authentication implementation do?",
    )
    decision = await provider.decide(task, retrieval_mode="never")
    assert decision.retrieval_required is False
    assert decision.strategy == RetrievalStrategy.NONE
    assert decision.confidence == 1.0


@pytest.mark.asyncio
async def test_routing_explicit_always_override():
    """7. explicit always -> retrieval"""
    provider = RuleBasedDecisionProvider()
    task = Task(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Simple greeting",
        instructions="Hello, how are you today?",
    )
    decision = await provider.decide(task, retrieval_mode="always", retrieval_strategy="vector")
    assert decision.retrieval_required is True
    assert decision.strategy == RetrievalStrategy.VECTOR
    assert decision.confidence == 1.0


@pytest.mark.asyncio
async def test_routing_invalid_strategy_and_scope():
    """8. invalid strategy fallback & 9. invalid scope fallback & 10. confidence generation"""
    provider = RuleBasedDecisionProvider()
    task = Task(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Custom task",
        instructions="Analyze our database schemas across all projects.",
    )
    decision = await provider.decide(
        task,
        retrieval_mode="always",
        retrieval_strategy="non_existent_strategy",
        retrieval_scope="non_existent_scope",
        retrieval_top_k=999,  # Test top_k clamping
    )
    # Should fall back to default HYBRID and workspace scope from text
    assert decision.retrieval_required is True
    assert decision.strategy == RetrievalStrategy.HYBRID
    assert decision.scope == RetrievalScope.WORKSPACE
    assert decision.top_k == settings.MAX_RETRIEVAL_TOP_K
    assert 0.0 <= decision.confidence <= 1.0
    assert len(decision.reason) > 0


# =====================================================================
# 2. MULTI-QUERY RETRIEVER TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_multi_query_generation_and_deduplication():
    """11. query generation, 12. duplicate query removal, 13. bounded query count"""
    mock_factory = MagicMock(spec=LLMProviderFactory)
    mock_provider = AsyncMock()
    mock_provider.is_configured = True
    # LLM returns variations including duplicate and excess
    mock_provider.generate.return_value = LLMGenerateResponse(
        content="1. JWT token lifecycle\n2. jwt token lifecycle\n3. auth refresh mechanism\n4. extra query 4\n5. extra query 5\n6. extra query 6",
        model="gpt-4o-mini",
    )
    mock_factory.get_provider_for_model.return_value = mock_provider

    mock_hybrid = AsyncMock(spec=HybridRetriever)
    mock_reranker = LocalReranker()

    multi_retriever = MultiQueryRetriever(
        hybrid_retriever=mock_hybrid,
        llm_factory=mock_factory,
        reranker=mock_reranker,
        max_queries=3,
    )

    queries = await multi_retriever.generate_queries("JWT token lifecycle")

    # Bounded to max_queries (3)
    assert len(queries) <= 3
    # Original query is first
    assert queries[0] == "JWT token lifecycle"
    # Duplicate 'jwt token lifecycle' is removed
    assert len(set(q.lower() for q in queries)) == len(queries)


@pytest.mark.asyncio
async def test_multi_query_fallback_on_llm_failure():
    """14. retrieval failure fallback"""
    mock_factory = MagicMock(spec=LLMProviderFactory)
    mock_provider = AsyncMock()
    mock_provider.is_configured = True
    mock_provider.generate.side_effect = RuntimeError("OpenAI API rate limited")
    mock_factory.get_provider_for_model.return_value = mock_provider

    mock_hybrid = AsyncMock(spec=HybridRetriever)
    multi_retriever = MultiQueryRetriever(
        hybrid_retriever=mock_hybrid,
        llm_factory=mock_factory,
    )

    queries = await multi_retriever.generate_queries("original search query")
    assert queries == ["original search query"]


@pytest.mark.asyncio
async def test_multi_query_result_merging_and_reranking():
    """15. result merging and 16. reranking"""
    ws_id = uuid.uuid4()
    chunk1_id = uuid.uuid4()
    chunk2_id = uuid.uuid4()

    c1 = RetrievalCandidate(
        chunk_id=chunk1_id,
        document_id=uuid.uuid4(),
        workspace_id=ws_id,
        filename="auth.md",
        content="Authentication using JWT tokens and refresh mechanisms.",
        page_number=1,
        vector_score=0.9,
        keyword_score=0.8,
        fusion_score=0.85,
    )
    c2 = RetrievalCandidate(
        chunk_id=chunk2_id,
        document_id=uuid.uuid4(),
        workspace_id=ws_id,
        filename="billing.md",
        content="Billing and invoice subscription handling.",
        page_number=2,
        vector_score=0.4,
        keyword_score=0.3,
        fusion_score=0.35,
    )

    mock_hybrid = AsyncMock(spec=HybridRetriever)
    mock_hybrid.retrieve.side_effect = [
        RetrievalResult(candidates=[c1, c2], query="JWT authentication", total_found=2),
        RetrievalResult(candidates=[c1], query="token mechanisms", total_found=1),
    ]

    mock_factory = MagicMock(spec=LLMProviderFactory)
    mock_provider = AsyncMock()
    mock_provider.is_configured = True
    mock_provider.generate.return_value = LLMGenerateResponse(
        content="token mechanisms",
        model="gpt-4o-mini",
    )
    mock_factory.get_provider_for_model.return_value = mock_provider

    multi_retriever = MultiQueryRetriever(
        hybrid_retriever=mock_hybrid,
        llm_factory=mock_factory,
        reranker=LocalReranker(),
    )

    result = await multi_retriever.retrieve(
        query="JWT authentication",
        workspace_id=ws_id,
        session=MagicMock(),
        top_k=5,
    )

    assert result.total_found == 2
    assert result.candidates[0].chunk_id == chunk1_id
    assert result.candidates[0].rerank_score > 0


# =====================================================================
# 3. ROUTER DEBUG / PREVIEW API & SECURITY ISOLATION TESTS
# =====================================================================

def test_retrieval_preview_endpoint(auth_client):
    """Router debugging preview endpoint and structured decision verification"""
    # Create workspace, project, and task
    ws_resp = auth_client.post("/api/workspaces", json={"name": "Preview Test WS"})
    assert ws_resp.status_code == 201
    ws_id = ws_resp.json()["id"]

    proj_resp = auth_client.post(
        f"/api/workspaces/{ws_id}/projects",
        json={"name": "Router Test Proj", "description": "Test"},
    )
    assert proj_resp.status_code == 201
    proj_id = proj_resp.json()["id"]

    task_resp = auth_client.post(
        f"/api/projects/{proj_id}/tasks",
        json={
            "title": "Auth Exploration",
            "instructions": "What does our authentication implementation do?",
        },
    )
    assert task_resp.status_code == 201
    task_id = task_resp.json()["id"]

    # Call preview endpoint
    preview_resp = auth_client.post(
        f"/api/tasks/{task_id}/retrieval/preview",
        json={"retrieval_mode": "auto"},
    )
    assert preview_resp.status_code == 200
    data = preview_resp.json()
    assert data["task_id"] == task_id
    decision = data["decision"]
    assert decision["retrieval_required"] is True
    assert decision["strategy"] == "hybrid"
    assert decision["scope"] == "project"
    assert decision["top_k"] == 8
    assert decision["confidence"] >= 0.85


def test_retrieval_preview_cross_user_isolation(client, user1_auth, user2_auth):
    """17. user isolation on preview endpoint"""
    h1 = user1_auth["headers"]
    h2 = user2_auth["headers"]

    ws_resp = client.post("/api/workspaces", json={"name": "User 1 WS"}, headers=h1)
    ws_id = ws_resp.json()["id"]

    proj_resp = client.post(
        f"/api/workspaces/{ws_id}/projects",
        json={"name": "User1 Proj"},
        headers=h1,
    )
    proj_id = proj_resp.json()["id"]

    task_resp = client.post(
        f"/api/projects/{proj_id}/tasks",
        json={"title": "User1 Task", "instructions": "Explain our auth."},
        headers=h1,
    )
    task_id = task_resp.json()["id"]

    # User 2 attempts to preview User 1's task retrieval -> 404
    unauth_resp = client.post(
        f"/api/tasks/{task_id}/retrieval/preview",
        json={"retrieval_mode": "auto"},
        headers=h2,
    )
    assert unauth_resp.status_code == 404


def test_workspace_and_project_retrieval_isolation(client, user1_auth, user2_auth):
    """18. workspace isolation and 19. project isolation"""
    h1 = user1_auth["headers"]
    h2 = user2_auth["headers"]

    # User 2 uploads document in User 2 workspace
    ws2_res = client.post("/api/workspaces", json={"name": "WS2 Isolated"}, headers=h2)
    assert ws2_res.status_code == 201
    ws2_id = ws2_res.json()["id"]

    doc2_res = client.post(
        f"/api/workspaces/{ws2_id}/documents",
        headers=h2,
        files={"file": ("ws2_secret.txt", io.BytesIO(b"Confidential workspace 2 data only."), "text/plain")},
    )
    assert doc2_res.status_code == 201

    # User 1 creates workspace, 2 projects
    ws1_res = client.post("/api/workspaces", json={"name": "WS1 Isolated"}, headers=h1)
    ws1_id = ws1_res.json()["id"]

    p1_res = client.post(f"/api/workspaces/{ws1_id}/projects", json={"name": "P1"}, headers=h1)
    p1_id = p1_res.json()["id"]

    p2_res = client.post(f"/api/workspaces/{ws1_id}/projects", json={"name": "P2"}, headers=h1)
    p2_id = p2_res.json()["id"]

    # Upload document to P1 only
    doc1_res = client.post(
        f"/api/workspaces/{ws1_id}/documents",
        data={"project_id": p1_id},
        headers=h1,
        files={"file": ("p1_auth.txt", io.BytesIO(b"Project 1 authentication protocol details."), "text/plain")},
    )
    assert doc1_res.status_code == 201

    # User 1 task in P2 should not retrieve P1 doc when project-scoped
    task_p2_res = client.post(
        f"/api/projects/{p2_id}/tasks",
        json={
            "title": "Search Protocol",
            "instructions": "What does our authentication protocol do?",
        },
        headers=h1,
    )
    task_p2_id = task_p2_res.json()["id"]

    run_res = client.post(
        f"/api/tasks/{task_p2_id}/run",
        json={
            "model": "mock-model-v1",
            "retrieval_mode": "always",
            "retrieval_project_scope": True,
        },
        headers=h1,
    )
    assert run_res.status_code == 201
    run_data = run_res.json()
    assert run_data["retrieved_chunk_count"] == 0


# =====================================================================
# 4. INTEGRATION & TELEMETRY PERSISTENCE TESTS
# =====================================================================

def test_task_execution_records_retrieval_decision(auth_client):
    """20. Task -> Router -> ContextEngine, 21. Decision stored in Run"""
    ws_resp = auth_client.post("/api/workspaces", json={"name": "WS Telemetry"})
    ws_id = ws_resp.json()["id"]

    proj_resp = auth_client.post(
        f"/api/workspaces/{ws_id}/projects",
        json={"name": "Telemetry Proj"},
    )
    proj_id = proj_resp.json()["id"]

    # Create task that triggers hybrid retrieval
    task_resp = auth_client.post(
        f"/api/projects/{proj_id}/tasks",
        json={
            "title": "Auth Architecture",
            "instructions": "What does our authentication implementation do?",
        },
    )
    task_id = task_resp.json()["id"]

    run_resp = auth_client.post(
        f"/api/tasks/{task_id}/run",
        json={"retrieval_mode": "auto", "model": "mock-model-v1"},
    )
    assert run_resp.status_code == 201
    run_data = run_resp.json()

    assert run_data["retrieval_mode"] == "auto"
    assert run_data["retrieval_required"] is True
    assert run_data["retrieval_strategy"] == "hybrid"
    assert run_data["retrieval_scope"] == "project"
    assert run_data["retrieval_confidence"] is not None
    assert run_data["retrieval_reason"] is not None


def test_task_streaming_records_retrieval_decision(auth_client):
    """22. Streaming still works and emits retrieval router decision telemetry"""
    ws_resp = auth_client.post("/api/workspaces", json={"name": "WS Stream Telemetry"})
    ws_id = ws_resp.json()["id"]

    proj_resp = auth_client.post(
        f"/api/workspaces/{ws_id}/projects",
        json={"name": "Stream Proj"},
    )
    proj_id = proj_resp.json()["id"]

    task_resp = auth_client.post(
        f"/api/projects/{proj_id}/tasks",
        json={
            "title": "Stream Task",
            "instructions": "What does our authentication implementation do?",
        },
    )
    task_id = task_resp.json()["id"]

    stream_resp = auth_client.post(
        f"/api/tasks/{task_id}/run/stream",
        json={"retrieval_mode": "auto", "model": "mock-model-v1"},
    )
    assert stream_resp.status_code == 200
    assert "text/event-stream" in stream_resp.headers["content-type"]

    body = stream_resp.text
    assert "run_start" in body
    assert "retrieval_strategy" in body
    assert "hybrid" in body


def test_existing_rag_retrieval_works(auth_client):
    """23. Existing RAG still works when documents are indexed"""
    ws_resp = auth_client.post("/api/workspaces", json={"name": "WS RAG Grounded"})
    ws_id = ws_resp.json()["id"]

    proj_resp = auth_client.post(
        f"/api/workspaces/{ws_id}/projects",
        json={"name": "RAG Proj"},
    )
    proj_id = proj_resp.json()["id"]

    # Upload document to project
    doc_res = auth_client.post(
        f"/api/workspaces/{ws_id}/documents",
        data={"project_id": proj_id},
        files={"file": ("auth_guide.txt", io.BytesIO(b"Our system uses JWT access tokens with 15-minute expiry and refresh tokens."), "text/plain")},
    )
    assert doc_res.status_code == 201

    task_resp = auth_client.post(
        f"/api/projects/{proj_id}/tasks",
        json={
            "title": "Token Expiry Inquiry",
            "instructions": "What is the expiry time of our JWT access tokens in the documentation?",
        },
    )
    task_id = task_resp.json()["id"]

    run_resp = auth_client.post(
        f"/api/tasks/{task_id}/run",
        json={"retrieval_mode": "auto", "model": "mock-model-v1"},
    )
    assert run_resp.status_code == 201
    run_data = run_resp.json()
    assert run_data["retrieval_required"] is True
    assert run_data["retrieval_strategy"] == "hybrid"
    assert run_data["retrieved_chunk_count"] > 0
    assert len(run_data["retrieval_sources"]) > 0
    assert "auth_guide.txt" in run_data["retrieval_sources"][0]["filename"]


def test_non_rag_task_records_no_retrieval_decision(auth_client):
    """24. Existing non-RAG tasks still work and record no-retrieval decision"""
    ws_resp = auth_client.post("/api/workspaces", json={"name": "WS Non-RAG"})
    ws_id = ws_resp.json()["id"]

    proj_resp = auth_client.post(
        f"/api/workspaces/{ws_id}/projects",
        json={"name": "Non-RAG Proj"},
    )
    proj_id = proj_resp.json()["id"]

    task_resp = auth_client.post(
        f"/api/projects/{proj_id}/tasks",
        json={
            "title": "Translate",
            "instructions": "Translate the following to French: Hello world.",
        },
    )
    task_id = task_resp.json()["id"]

    run_resp = auth_client.post(
        f"/api/tasks/{task_id}/run",
        json={"retrieval_mode": "auto", "model": "mock-model-v1"},
    )
    assert run_resp.status_code == 201
    run_data = run_resp.json()

    assert run_data["retrieval_mode"] == "auto"
    assert run_data["retrieval_required"] is False
    assert run_data["retrieval_strategy"] == "none"
    assert run_data["retrieval_enabled"] is False

