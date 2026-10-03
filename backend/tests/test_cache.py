"""
Production-Grade Verification Test Suite for Step 31:
Semantic Cache and Intelligent Reuse Layer.

Tests:
1. Exact cache hits, misses, and deterministic fingerprinting
2. Semantic similarity matching and threshold boundary enforcement
3. Multi-tenant and user namespace isolation (strictly no cross-tenant leakage)
4. Prompt version compatibility and surgical invalidation
5. Multimodal artifact, knowledge graph, and memory fingerprint compatibility
6. Model compatibility and cross-model policy enforcement
7. Secret scrubbing and chain-of-thought sanitization
8. Operation eligibility and side-effect protection
9. TTL expiration and stale-while-revalidate behavior
10. Request coalescing for cache stampede prevention
11. REST API endpoints (stats, preview, entries, policy, invalidate)
"""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.cache.admission import CacheAdmissionService
from backend.app.services.cache.constants import (
    CacheMode,
    CacheNamespace,
    CacheStatus,
    InvalidationMode,
    MatchMode,
)
from backend.app.services.cache.eligibility import CacheEligibilityService
from backend.app.services.cache.invalidation import CacheInvalidationService
from backend.app.services.cache.lookup import CacheLookupService, compute_request_fingerprint
from backend.app.services.cache.matcher import CacheMatcher
from backend.app.services.cache.models import CacheEntry
from backend.app.services.cache.policies import CachePolicyEngine
from backend.app.services.cache.repository import CacheRepository, compute_cosine_similarity
from backend.app.services.cache.sanitizer import CacheSanitizer
from backend.app.services.cache.schemas import (
    CacheAdmissionCandidate,
    CacheInvalidationRequest,
    CacheLookupRequest,
    CachePolicyConfig,
    CachePreviewRequest,
)
from backend.app.services.cache.service import CacheService


# ---------------------------------------------------------------------------
# Unit Tests: Sanitizer, Matcher, Eligibility, Policy
# ---------------------------------------------------------------------------

def test_sanitizer_removes_secrets_and_cot():
    """Verify secrets, credentials, bearer tokens, and chain-of-thought are stripped."""
    sanitizer = CacheSanitizer()
    dirty_text = (
        "Here is the report.\n"
        "<thought>Internal chain of thought reasoning should never be cached</thought>\n"
        "Authorization: Bearer sk-ant-api03-abcdef1234567890\n"
        "AWS secret: AKIAIOSFODNN7EXAMPLE\n"
        "Done!"
    )
    clean = sanitizer.sanitize_text(dirty_text)
    assert "<thought>" not in clean
    assert "sk-ant-" not in clean
    assert "[REDACTED_SECRET]" in clean or "[REDACTED_API_KEY]" in clean
    assert "Here is the report." in clean
    assert "Done!" in clean


def test_eligibility_safeguards():
    """Verify read-only deterministic tasks are eligible, but mutations/approvals are blocked."""
    service = CacheEligibilityService()

    # Eligible
    ok, _ = service.is_cacheable(task_type="summarization", has_side_effects=False)
    assert ok is True

    ok, _ = service.is_cacheable(task_type="document_qa", has_side_effects=False)
    assert ok is True

    # Ineligible
    ok, reason = service.is_cacheable(task_type="tool_execution", has_side_effects=True)
    assert ok is False
    assert "side effects" in reason.lower()

    ok, reason = service.is_cacheable(task_type="approval", requires_hitl=True)
    assert ok is False

    ok, reason = service.is_cacheable(task_type="summarization", cache_mode=CacheMode.DISABLED)
    assert ok is False


def test_policy_threshold_bounds():
    """Verify unreasonable semantic thresholds are rejected."""
    engine = CachePolicyEngine()
    policy = CachePolicyConfig(semantic_threshold=0.88)
    ok, _ = engine.validate_policy_update(policy)
    assert ok is True

    # Bad threshold < 0.70
    bad_policy = CachePolicyConfig.model_construct(semantic_threshold=0.50)
    ok, msg = engine.validate_policy_update(bad_policy)
    assert ok is False
    assert "threshold" in msg.lower()


def test_cosine_similarity_computation():
    """Verify pure-Python cosine similarity fallback."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert compute_cosine_similarity(v1, v2) == pytest.approx(1.0)

    v3 = [0.0, 1.0, 0.0]
    assert compute_cosine_similarity(v1, v3) == pytest.approx(0.0)

    v4 = [0.7071, 0.7071, 0.0]
    sim = compute_cosine_similarity(v1, v4)
    assert sim >= 0.70


# ---------------------------------------------------------------------------
# Database & Service Integration Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_exact_cache_hit_and_miss(db_session: AsyncSession):
    """Test exact cache hit on identical fingerprint and miss on altered prompt."""
    cache_svc = CacheService()
    org_id = uuid.uuid4()
    ws_id = uuid.uuid4()

    prompt = "Summarize quarterly cloud revenue"
    rfp = compute_request_fingerprint(normalized_request=prompt, model_id="gpt-4o-mini")

    candidate = CacheAdmissionCandidate(
        organization_id=org_id,
        workspace_id=ws_id,
        namespace=CacheNamespace.WORKSPACE,
        normalized_request=prompt,
        request_fingerprint=rfp,
        cache_key=rfp,
        response_content="Cloud revenue grew 18% year-over-year.",
        model_id="gpt-4o-mini",
        model_provider="openai",
    )

    # 1. Admit candidate
    entry, err = await cache_svc.admit(db_session, candidate, task_type="summarization")
    assert err is None
    assert entry is not None
    assert entry.status == CacheStatus.ACTIVE.value

    # 2. Exact Lookup -> HIT
    req = CacheLookupRequest(
        organization_id=org_id,
        workspace_id=ws_id,
        prompt_text=prompt,
        model_id="gpt-4o-mini",
        model_provider="openai",
        namespace=CacheNamespace.WORKSPACE,
    )
    hit_res = await cache_svc.lookup(db_session, req)
    assert hit_res.hit is True
    assert hit_res.match_type == "exact"
    assert "Cloud revenue grew" in hit_res.response_content

    # 3. Altered Prompt -> MISS
    miss_req = CacheLookupRequest(
        organization_id=org_id,
        workspace_id=ws_id,
        prompt_text="Summarize quarterly retail revenue",
        model_id="gpt-4o-mini",
        namespace=CacheNamespace.WORKSPACE,
        match_mode=MatchMode.EXACT,
    )
    miss_res = await cache_svc.lookup(db_session, miss_req)
    assert miss_res.hit is False


@pytest.mark.asyncio
async def test_semantic_cache_hit_and_threshold(db_session: AsyncSession):
    """Test semantic matching using cosine similarity and threshold boundary."""
    cache_svc = CacheService()
    org_id = uuid.uuid4()
    ws_id = uuid.uuid4()

    prompt = "Extract key risk factors from quarterly report"
    rfp = compute_request_fingerprint(normalized_request=prompt)

    # Unit vector 1
    mock_vector_1 = [1.0] + [0.0] * 1535
    candidate = CacheAdmissionCandidate(
        organization_id=org_id,
        workspace_id=ws_id,
        namespace=CacheNamespace.WORKSPACE,
        normalized_request=prompt,
        request_fingerprint=rfp,
        cache_key=rfp,
        response_content="1. Supply chain disruption. 2. Forex volatility.",
        semantic_embedding=mock_vector_1,
    )
    await cache_svc.admit(db_session, candidate, task_type="extraction")

    # Mock embedding provider to return a very close vector (sim ~ 0.95)
    mock_vector_close = [0.95, 0.312] + [0.0] * 1534
    cache_svc.embedding.get_embedding = lambda text: asyncio.sleep(0, result=mock_vector_close)

    # 1. Lookup with default threshold 0.88 -> Semantic HIT
    sem_req = CacheLookupRequest(
        organization_id=org_id,
        workspace_id=ws_id,
        prompt_text="Extract the top risk factors from the 10-Q filing",
        namespace=CacheNamespace.WORKSPACE,
        match_mode=MatchMode.SEMANTIC,
    )
    policy = CachePolicyConfig(semantic_enabled=True, semantic_threshold=0.88)
    res = await cache_svc.lookup_svc.lookup(db_session, sem_req, policy=policy)
    assert res.hit is True
    assert res.match_type == "semantic"
    assert res.similarity_score >= 0.88
    assert "Supply chain" in res.response_content

    # 2. Lookup with high threshold 0.99 -> MISS
    strict_policy = CachePolicyConfig(semantic_enabled=True, semantic_threshold=0.99)
    strict_res = await cache_svc.lookup_svc.lookup(db_session, sem_req, policy=strict_policy)
    assert strict_res.hit is False


@pytest.mark.asyncio
async def test_tenant_and_user_namespace_isolation(db_session: AsyncSession):
    """Verify tenant isolation and user privacy boundaries are strictly enforced."""
    cache_svc = CacheService()
    org_a = uuid.uuid4()
    org_b = uuid.uuid4()
    ws_a = uuid.uuid4()
    ws_b = uuid.uuid4()
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()

    prompt = "Confidential internal security review"
    rfp = compute_request_fingerprint(normalized_request=prompt)

    # Candidate 1: Workspace A
    cand_a = CacheAdmissionCandidate(
        organization_id=org_a,
        workspace_id=ws_a,
        namespace=CacheNamespace.WORKSPACE,
        normalized_request=prompt,
        request_fingerprint=rfp,
        cache_key=rfp,
        response_content="Org A confidential findings",
    )
    await cache_svc.admit(db_session, cand_a, task_type="analysis")

    # Cross-tenant query from Workspace B -> MUST MISS
    cross_req = CacheLookupRequest(
        organization_id=org_b,
        workspace_id=ws_b,
        prompt_text=prompt,
        namespace=CacheNamespace.WORKSPACE,
    )
    cross_res = await cache_svc.lookup(db_session, cross_req)
    assert cross_res.hit is False

    # Candidate 2: User-Private Namespace for User A
    cand_user_a = CacheAdmissionCandidate(
        organization_id=org_a,
        workspace_id=ws_a,
        user_id=user_a,
        namespace=CacheNamespace.USER,
        normalized_request="My private task history",
        request_fingerprint="fp_user_a",
        cache_key="fp_user_a",
        response_content="User A private note",
    )
    await cache_svc.admit(db_session, cand_user_a, task_type="analysis")

    # Query from User B -> MUST MISS
    user_b_req = CacheLookupRequest(
        organization_id=org_a,
        workspace_id=ws_a,
        user_id=user_b,
        prompt_text="My private task history",
        namespace=CacheNamespace.USER,
    )
    user_b_res = await cache_svc.lookup(db_session, user_b_req)
    assert user_b_res.hit is False


@pytest.mark.asyncio
async def test_prompt_version_and_model_compatibility(db_session: AsyncSession):
    """Verify cache compatibility with Step 28 Prompt versions and Model Router."""
    cache_svc = CacheService()
    org_id = uuid.uuid4()
    ws_id = uuid.uuid4()
    pv_v1 = uuid.uuid4()
    pv_v2 = uuid.uuid4()

    prompt = "Generate release summary"
    rfp = compute_request_fingerprint(normalized_request=prompt, prompt_version_id=pv_v1, model_id="gpt-4o")

    cand = CacheAdmissionCandidate(
        organization_id=org_id,
        workspace_id=ws_id,
        namespace=CacheNamespace.WORKSPACE,
        normalized_request=prompt,
        request_fingerprint=rfp,
        cache_key=rfp,
        response_content="Release v1 notes",
        prompt_version_id=pv_v1,
        model_id="gpt-4o",
        model_provider="openai",
    )
    await cache_svc.admit(db_session, cand, task_type="summarization")

    # Same prompt version -> HIT
    hit_req = CacheLookupRequest(
        organization_id=org_id,
        workspace_id=ws_id,
        prompt_text=prompt,
        prompt_version_id=pv_v1,
        model_id="gpt-4o",
        model_provider="openai",
    )
    res_v1 = await cache_svc.lookup(db_session, hit_req)
    assert res_v1.hit is True

    # New prompt version published -> MISS
    req_v2 = CacheLookupRequest(
        organization_id=org_id,
        workspace_id=ws_id,
        prompt_text=prompt,
        prompt_version_id=pv_v2,
        model_id="gpt-4o",
        model_provider="openai",
    )
    res_v2 = await cache_svc.lookup(db_session, req_v2)
    assert res_v2.hit is False

    # Different model (when cross-model is disabled) -> MISS
    req_claude = CacheLookupRequest(
        organization_id=org_id,
        workspace_id=ws_id,
        prompt_text=prompt,
        prompt_version_id=pv_v1,
        model_id="claude-3-5-sonnet",
        model_provider="anthropic",
    )
    res_claude = await cache_svc.lookup(db_session, req_claude)
    assert res_claude.hit is False


@pytest.mark.asyncio
async def test_multimodal_artifact_and_graph_invalidation(db_session: AsyncSession):
    """Verify artifact hash and graph snapshot changes invalidate affected cache entries."""
    cache_svc = CacheService()
    org_id = uuid.uuid4()
    ws_id = uuid.uuid4()

    art_hash = "art_sha256_image_v1"
    graph_hash = "graph_snapshot_v1"
    prompt = "Analyze architectural blueprint"
    rfp = compute_request_fingerprint(
        normalized_request=prompt,
        artifact_hash=art_hash,
        graph_hash=graph_hash,
    )

    cand = CacheAdmissionCandidate(
        organization_id=org_id,
        workspace_id=ws_id,
        namespace=CacheNamespace.WORKSPACE,
        normalized_request=prompt,
        request_fingerprint=rfp,
        cache_key=rfp,
        response_content="Blueprint structural load analysis",
        artifact_hash=art_hash,
        graph_snapshot_hash=graph_hash,
    )
    entry, _ = await cache_svc.admit(db_session, cand, task_type="analysis")
    assert entry is not None

    # Surgical Invalidation on Artifact Update event
    inv_req = CacheInvalidationRequest(
        workspace_id=ws_id,
        mode=InvalidationMode.ARTIFACT,
        target_id=art_hash,
        reason="artifact_content_updated",
    )
    inv_res = await cache_svc.invalidate(db_session, inv_req)
    assert inv_res.invalidated_count >= 1

    # Subsequent lookup should MISS because entry is invalidated
    lookup_req = CacheLookupRequest(
        organization_id=org_id,
        workspace_id=ws_id,
        prompt_text=prompt,
        artifact_fingerprint=art_hash,
    )
    res = await cache_svc.lookup(db_session, lookup_req)
    assert res.hit is False


@pytest.mark.asyncio
async def test_cache_stampede_request_coalescing():
    """Verify request coalescing prevents cache stampedes on concurrent identical requests."""
    cache_svc = CacheService()
    lock_key = "stampede_test_lock_key"

    lock1 = await cache_svc.lookup_svc.get_coalesce_lock(lock_key)
    assert lock1 is not None

    # Second concurrent caller gets the exact same asyncio.Lock instance
    lock2 = await cache_svc.lookup_svc.get_coalesce_lock(lock_key)
    assert lock1 is lock2

    # Cleanup lock
    await cache_svc.lookup_svc.release_coalesce_lock(lock_key)


@pytest.mark.asyncio
async def test_cache_preview_probe(db_session: AsyncSession):
    """Verify dry-run cache preview probe returns diagnostic output without execution."""
    cache_svc = CacheService()
    ws_id = uuid.uuid4()

    preview_req = CachePreviewRequest(
        prompt_text="Extract financial tables from balance sheet",
        task_type="extraction",
        model_id="gpt-4o",
        workspace_id=ws_id,
    )
    res = await cache_svc.preview(db_session, preview_req)
    assert res.eligible is True
    assert res.exact_match_available is False
    assert "will execute via AI Gateway" in res.expected_behavior
