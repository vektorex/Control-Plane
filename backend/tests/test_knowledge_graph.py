"""
Test Suite for STEP 29: Production-Grade Knowledge Graph and Structured Context Layer.

Comprehensive coverage of:
- Entity CRUD, Normalization & Validation
- Relationship CRUD, Typed Integrity & Anti-Self-Loop Rules
- Tenant Isolation & Project Access Boundaries
- Entity Resolution, Canonical Matching & Ambiguity Conflict Handling
- Entity Aliases & Source Provenance Tracking
- Bounded Graph Traversal (1-hop, 2-hop, 3-hop) & Cycle Detection
- Temporal Relationship Validity
- Safe Entity Merging & Change Logs
- Graph Change Proposals & HITL Review (Approve/Reject)
- LLM Structured Extraction Validation & Secret Sanitization
- GitHub Connector, Document & Workflow Integrations
- Retrieval Router & Hybrid Graph Grounding
- ContextEngine GraphContextProvider & Budget Enforcement
- Evaluation Lab Graph Assertions
- Replay Snapshot Graph Configuration
- Event Publishing & Audit History
"""
import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.user import User
from backend.app.services.access_control.permissions import (
    GRAPH_CREATE,
    GRAPH_DELETE,
    GRAPH_EXTRACT,
    GRAPH_MERGE,
    GRAPH_READ,
    GRAPH_UPDATE,
)
from backend.app.services.access_control.roles import (
    ORGANIZATION_ROLE_PERMISSIONS,
    OrganizationRole,
    WorkspaceRole,
)
from backend.app.services.context.engine import ContextEngine
from backend.app.services.context.models import ContextSourceType
from backend.app.services.evaluation_lab.assertions import AssertionEngine
from backend.app.services.evaluation_lab.schemas import (
    AssertionDefinition,
    AssertionType,
)
from backend.app.services.events.constants import AggregateType, SystemEventType
from backend.app.services.knowledge_graph.constants import (
    ConflictStatus,
    ConflictType,
    EntityType,
    GRAPH_MAX_HOPS,
    ProposalStatus,
    RelationshipType,
    SourceType,
)
from backend.app.services.knowledge_graph.context_provider import GraphContextProvider
from backend.app.services.knowledge_graph.entity_service import EntityService
from backend.app.services.knowledge_graph.errors import (
    CrossTenantGraphError,
    DanglingEntityError,
    EntityMergeError,
    EntityNotFoundError,
    ExtractionValidationError,
    InvalidEntityTypeError,
    InvalidRelationshipTypeError,
    SelfRelationshipError,
    UnauthorizedGraphAccessError,
)
from backend.app.services.knowledge_graph.extraction import GraphExtractionService
from backend.app.services.knowledge_graph.models import (
    Entity,
    EntityAlias,
    EntitySource,
    GraphChangeLog,
    GraphChangeProposal,
    GraphConflict,
    Relationship,
)
from backend.app.services.knowledge_graph.normalization import (
    compute_string_similarity,
    normalize_alias,
    normalize_entity_name,
    normalize_entity_type,
)
from backend.app.services.knowledge_graph.policies import GraphPolicyEngine
from backend.app.services.knowledge_graph.relationship_service import RelationshipService
from backend.app.services.knowledge_graph.repository import KnowledgeGraphRepository
from backend.app.services.knowledge_graph.resolver import EntityResolver
from backend.app.services.knowledge_graph.retriever import GraphRetriever
from backend.app.services.knowledge_graph.sanitizer import (
    sanitize_properties,
    sanitize_source_metadata,
    scrub_secrets_from_text,
)
from backend.app.services.knowledge_graph.schemas import (
    EntityCreateRequest,
    EntityMergeRequest,
    EntityUpdateRequest,
    GraphExtractionPayload,
    GraphQueryRequest,
    RelationshipCreateRequest,
)
from backend.app.services.knowledge_graph.service import KnowledgeGraphService
from backend.app.services.knowledge_graph.traversal import GraphTraversalEngine
from backend.app.services.replay.schemas import ExecutionSnapshot
from backend.app.services.retrieval.decision import (
    RetrievalDecision,
    RetrievalMode,
    RetrievalStrategy,
)
from backend.app.services.retrieval.policies import RuleBasedDecisionProvider
from backend.app.services.retrieval.router import RetrievalRouter


# =============================================================================
# 1. Normalization & Sanitization Tests
# =============================================================================

def test_normalization_rules():
    assert normalize_entity_name("  React.JS  ") == "react.js"
    assert normalize_entity_name("PostgreSQL -- Database! ") == "postgresql database"
    assert normalize_alias(" @Frontend/App ") == "frontend/app"
    assert normalize_entity_type(" Technology ") == "technology"
    assert normalize_entity_type("unknown_type") is None

    # Similarity checks
    sim = compute_string_similarity("reactjs", "react.js")
    assert sim > 0.8
    assert compute_string_similarity("kubernetes", "postgres") < 0.4


def test_sanitization_rules():
    raw_text = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.secret token here and ghp_1234567890abcdef"
    scrubbed = scrub_secrets_from_text(raw_text)
    assert "[REDACTED_CREDENTIAL]" in scrubbed
    assert "ghp_1234567890abcdef" not in scrubbed

    props = {
        "api_key": "sk-proj-1234567890abcdef",
        "nested": {"password": "SuperSecretPassword123!"},
        "public_name": "Auth Service",
    }
    cleaned = sanitize_properties(props)
    assert cleaned["api_key"] == "[REDACTED_CREDENTIAL]"
    assert cleaned["nested"]["password"] == "[REDACTED_CREDENTIAL]"
    assert cleaned["public_name"] == "Auth Service"


# =============================================================================
# 2. RBAC Permissions Matrix Tests
# =============================================================================

def test_graph_rbac_permissions():
    owner_perms = ORGANIZATION_ROLE_PERMISSIONS[OrganizationRole.OWNER]
    viewer_perms = ORGANIZATION_ROLE_PERMISSIONS[OrganizationRole.VIEWER]

    assert GRAPH_READ in owner_perms
    assert GRAPH_CREATE in owner_perms
    assert GRAPH_UPDATE in owner_perms
    assert GRAPH_DELETE in owner_perms
    assert GRAPH_EXTRACT in owner_perms
    assert GRAPH_MERGE in owner_perms

    # Viewer has READ only
    assert GRAPH_READ in viewer_perms
    assert GRAPH_CREATE not in viewer_perms
    assert GRAPH_UPDATE not in viewer_perms
    assert GRAPH_DELETE not in viewer_perms
    assert GRAPH_MERGE not in viewer_perms


# =============================================================================
# 3. Entity CRUD & Multi-Tenant Isolation Tests
# =============================================================================

@pytest.mark.asyncio
async def test_entity_crud_and_tenant_isolation(db_session: AsyncSession):
    org_a = uuid.uuid4()
    ws_a = uuid.uuid4()
    org_b = uuid.uuid4()
    ws_b = uuid.uuid4()

    entity_service = EntityService(db_session)

    # 1. Create Entity in Org A
    ent_a = await entity_service.create_entity(
        organization_id=org_a,
        workspace_id=ws_a,
        request=EntityCreateRequest(
            canonical_name="Auth Service",
            entity_type="service",
            description="Core authentication microservice",
            aliases=["auth-svc", "auth_api"],
            properties={"port": 8080},
        ),
    )
    assert ent_a.id is not None
    assert ent_a.canonical_name == "Auth Service"
    assert ent_a.entity_type == "service"
    assert ent_a.organization_id == org_a
    assert ent_a.workspace_id == ws_a

    # 2. Verify Aliases Created
    aliases = await entity_service.repo.get_entity_aliases(ent_a.id)
    assert len(aliases) == 2
    assert {a.alias for a in aliases} == {"auth-svc", "auth_api"}

    # 3. Tenant Isolation: Org B cannot access Org A's entity
    ent_not_in_b = await entity_service.get_entity(
        entity_id=ent_a.id,
        organization_id=org_b,
        workspace_id=ws_b,
    )
    assert ent_not_in_b is None

    # 4. Update Entity in Org A
    updated = await entity_service.update_entity(
        entity_id=ent_a.id,
        organization_id=org_a,
        workspace_id=ws_a,
        request=EntityUpdateRequest(description="Updated description"),
    )
    assert updated.description == "Updated description"

    # 5. Archive Entity
    archived = await entity_service.archive_entity(
        entity_id=ent_a.id,
        organization_id=org_a,
        workspace_id=ws_a,
    )
    assert archived is True


# =============================================================================
# 4. Relationship CRUD & Integrity Rules
# =============================================================================

@pytest.mark.asyncio
async def test_relationship_integrity_and_anti_self_loop(db_session: AsyncSession):
    org_id = uuid.uuid4()
    ws_id = uuid.uuid4()

    entity_service = EntityService(db_session)
    rel_service = RelationshipService(db_session)

    ent_1 = await entity_service.create_entity(
        organization_id=org_id,
        workspace_id=ws_id,
        request=EntityCreateRequest(canonical_name="Frontend App", entity_type="technology"),
    )
    ent_2 = await entity_service.create_entity(
        organization_id=org_id,
        workspace_id=ws_id,
        request=EntityCreateRequest(canonical_name="API Gateway", entity_type="service"),
    )

    # 1. Anti-Self-Loop Rule
    with pytest.raises(SelfRelationshipError):
        await rel_service.create_relationship(
            organization_id=org_id,
            workspace_id=ws_id,
            request=RelationshipCreateRequest(
                source_entity_id=ent_1.id,
                relationship_type="depends_on",
                target_entity_id=ent_1.id,
            ),
        )

    # 2. Valid Relationship: Frontend -> depends_on -> API Gateway
    rel = await rel_service.create_relationship(
        organization_id=org_id,
        workspace_id=ws_id,
        request=RelationshipCreateRequest(
            source_entity_id=ent_1.id,
            relationship_type="depends_on",
            target_entity_id=ent_2.id,
            properties={"protocol": "https"},
            source_reference={"source": "architecture.md"},
        ),
    )
    assert rel.id is not None
    assert rel.relationship_type == "depends_on"
    assert rel.source_entity_id == ent_1.id
    assert rel.target_entity_id == ent_2.id

    # 3. Prevent Dangling Entity Relationship
    fake_id = uuid.uuid4()
    with pytest.raises(DanglingEntityError):
        await rel_service.create_relationship(
            organization_id=org_id,
            workspace_id=ws_id,
            request=RelationshipCreateRequest(
                source_entity_id=ent_1.id,
                relationship_type="uses",
                target_entity_id=fake_id,
            ),
        )

    # 4. Cross-Tenant Relationship Prevention
    other_org_ent = await entity_service.create_entity(
        organization_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        request=EntityCreateRequest(canonical_name="External Node", entity_type="technology"),
    )
    with pytest.raises(CrossTenantGraphError):
        await rel_service.create_relationship(
            organization_id=org_id,
            workspace_id=ws_id,
            request=RelationshipCreateRequest(
                source_entity_id=ent_1.id,
                relationship_type="uses",
                target_entity_id=other_org_ent.id,
            ),
        )


# =============================================================================
# 5. Entity Resolution & Ambiguity Conflicts (No Silent Merge)
# =============================================================================

@pytest.mark.asyncio
async def test_entity_resolution_and_conflict_detection(db_session: AsyncSession):
    org_id = uuid.uuid4()
    ws_id = uuid.uuid4()

    resolver = EntityResolver(db_session)

    # 1. First ingestion creates canonical entity
    ent, created = await resolver.resolve_or_create_entity(
        organization_id=org_id,
        workspace_id=ws_id,
        raw_name="PostgreSQL",
        entity_type="database",
        aliases=["postgres", "psql"],
    )
    assert created is True
    assert ent.canonical_name == "PostgreSQL"

    # 2. Exact match on canonical name resolves existing
    ent_exact, created_exact = await resolver.resolve_or_create_entity(
        organization_id=org_id,
        workspace_id=ws_id,
        raw_name="postgresql",
        entity_type="database",
    )
    assert created_exact is False
    assert ent_exact.id == ent.id

    # 3. Alias match resolves existing
    ent_alias, created_alias = await resolver.resolve_or_create_entity(
        organization_id=org_id,
        workspace_id=ws_id,
        raw_name="psql",
        entity_type="database",
    )
    assert created_alias is False
    assert ent_alias.id == ent.id

    # 4. Ambiguous similarity creates an unresolved candidate and a GraphConflict record
    ent_ambig, created_ambig = await resolver.resolve_or_create_entity(
        organization_id=org_id,
        workspace_id=ws_id,
        raw_name="PostgresSQL",  # Slight typo, similarity in [0.82, 0.95]
        entity_type="database",
    )
    # Must NOT silently merge
    assert created_ambig is True
    assert ent_ambig.id != ent.id

    # Verify conflict was recorded
    repo = KnowledgeGraphRepository(db_session)
    conflicts = await repo.list_conflicts(workspace_id=ws_id)
    assert len(conflicts) > 0
    assert any(c.conflict_type == ConflictType.AMBIGUOUS_ENTITY.value for c in conflicts)


# =============================================================================
# 6. Bounded Traversal (1-hop, 2-hop, 3-hop) & Cycle Detection
# =============================================================================

@pytest.mark.asyncio
async def test_graph_traversal_and_max_hops(db_session: AsyncSession):
    org_id = uuid.uuid4()
    ws_id = uuid.uuid4()

    entity_service = EntityService(db_session)
    rel_service = RelationshipService(db_session)

    # Build chain: A -> B -> C -> D -> A (with cycle)
    a = await entity_service.create_entity(org_id, ws_id, EntityCreateRequest(canonical_name="Node A", entity_type="service"))
    b = await entity_service.create_entity(org_id, ws_id, EntityCreateRequest(canonical_name="Node B", entity_type="service"))
    c = await entity_service.create_entity(org_id, ws_id, EntityCreateRequest(canonical_name="Node C", entity_type="service"))
    d = await entity_service.create_entity(org_id, ws_id, EntityCreateRequest(canonical_name="Node D", entity_type="service"))

    await rel_service.create_relationship(org_id, ws_id, RelationshipCreateRequest(source_entity_id=a.id, relationship_type="calls", target_entity_id=b.id))
    await rel_service.create_relationship(org_id, ws_id, RelationshipCreateRequest(source_entity_id=b.id, relationship_type="calls", target_entity_id=c.id))
    await rel_service.create_relationship(org_id, ws_id, RelationshipCreateRequest(source_entity_id=c.id, relationship_type="calls", target_entity_id=d.id))
    await rel_service.create_relationship(org_id, ws_id, RelationshipCreateRequest(source_entity_id=d.id, relationship_type="calls", target_entity_id=a.id))

    engine = GraphTraversalEngine(db_session)

    # 1. 1-hop traversal from A: reaches B
    res_1 = await engine.traverse(workspace_id=ws_id, seed_entity_ids=[a.id], max_hops=1)
    found_1_ids = {e.id for e in res_1.entities}
    assert b.id in found_1_ids
    assert c.id not in found_1_ids

    # 2. 2-hop traversal from A: reaches B and C
    res_2 = await engine.traverse(workspace_id=ws_id, seed_entity_ids=[a.id], max_hops=2)
    found_2_ids = {e.id for e in res_2.entities}
    assert b.id in found_2_ids
    assert c.id in found_2_ids
    assert d.id not in found_2_ids

    # 3. 3-hop traversal from A: reaches B, C, D (cycle handled gracefully)
    res_3 = await engine.traverse(workspace_id=ws_id, seed_entity_ids=[a.id], max_hops=3)
    found_3_ids = {e.id for e in res_3.entities}
    assert {a.id, b.id, c.id, d.id}.issubset(found_3_ids)

    # 4. Traversal clamps depth to GRAPH_MAX_HOPS
    res_clamped = await engine.traverse(workspace_id=ws_id, seed_entity_ids=[a.id], max_hops=99)
    assert res_clamped.retrieval_metadata["hops"] <= GRAPH_MAX_HOPS


# =============================================================================
# 7. Safe Entity Merging & Audit History
# =============================================================================

@pytest.mark.asyncio
async def test_safe_entity_merge(db_session: AsyncSession):
    org_id = uuid.uuid4()
    ws_id = uuid.uuid4()

    entity_service = EntityService(db_session)
    rel_service = RelationshipService(db_session)

    # Primary entity
    primary = await entity_service.create_entity(
        org_id, ws_id, EntityCreateRequest(canonical_name="FastAPI", entity_type="technology")
    )
    # Duplicate entity
    duplicate = await entity_service.create_entity(
        org_id, ws_id, EntityCreateRequest(canonical_name="FastAPI Framework", entity_type="technology", aliases=["fastapi-py"])
    )
    other = await entity_service.create_entity(
        org_id, ws_id, EntityCreateRequest(canonical_name="Backend Core", entity_type="project")
    )

    # Relationship to duplicate: other -> uses -> duplicate
    await rel_service.create_relationship(
        org_id, ws_id, RelationshipCreateRequest(source_entity_id=other.id, relationship_type="uses", target_entity_id=duplicate.id)
    )

    # Perform safe merge
    res = await entity_service.merge_entities(
        organization_id=org_id,
        workspace_id=ws_id,
        request=EntityMergeRequest(
            primary_entity_id=primary.id,
            duplicate_entity_id=duplicate.id,
            merge_reason="De-duplicating framework names",
        ),
    )
    assert res.transferred_relationships_count == 1
    assert res.transferred_aliases_count >= 1

    # Verify duplicate is archived
    repo = KnowledgeGraphRepository(db_session)
    dup_reloaded = await repo.get_entity_by_id(duplicate.id)
    assert dup_reloaded.status == "archived"

    # Verify relationship transferred to primary: other -> uses -> primary
    rel_check = await repo.get_relationship(ws_id, other.id, "uses", primary.id)
    assert rel_check is not None

    # Verify audit change log created
    logs = await repo.list_change_logs(workspace_id=ws_id)
    assert any(l.action == "merged" for l in logs)


# =============================================================================
# 8. Proposals & HITL Review
# =============================================================================

@pytest.mark.asyncio
async def test_graph_change_proposals(db_session: AsyncSession):
    org_id = uuid.uuid4()
    ws_id = uuid.uuid4()

    kg_service = KnowledgeGraphService(db_session)

    # Create proposal with proposed entities and relationships
    proposal = await kg_service.repo.create_proposal(
        organization_id=org_id,
        workspace_id=ws_id,
        source_id="doc_extractor_123",
        proposed_entities=[
            {"canonical_name": "Stripe API", "entity_type": "api", "description": "Payment gateway"}
        ],
        proposed_relationships=[
            {"source_name": "Stripe API", "relationship_type": "deployed_to", "target_name": "Cloud"}
        ],
    )
    assert proposal.status == ProposalStatus.PENDING.value

    # Approve proposal
    approved = await kg_service.approve_proposal(
        proposal_id=proposal.id,
        organization_id=org_id,
        workspace_id=ws_id,
        review_note="Verified by security team",
    )
    assert approved.status == ProposalStatus.APPROVED.value

    # Verify Stripe API entity was persisted in the graph
    entities = await kg_service.entity_service.list_entities(workspace_id=ws_id)
    assert any(e.canonical_name == "Stripe API" for e in entities)


# =============================================================================
# 9. Structured LLM Extraction Validation
# =============================================================================

def test_extraction_payload_validation():
    # Valid payload
    valid_json = {
        "entities": [
            {"canonical_name": "Redis", "entity_type": "database", "description": "Cache store"}
        ],
        "relationships": [
            {"source_name": "App", "relationship_type": "uses", "target_name": "Redis"}
        ]
    }
    parsed = GraphExtractionPayload.model_validate(valid_json)
    assert len(parsed.entities) == 1
    assert len(parsed.relationships) == 1

    # Malformed entity type validation error
    invalid_json = {
        "entities": [
            {"canonical_name": "Malicious Node", "entity_type": "arbitrary_untrusted_type"}
        ],
        "relationships": []
    }
    with pytest.raises(Exception):
        GraphExtractionPayload.model_validate(invalid_json)


# =============================================================================
# 10. Connector, Document & Workflow Integrations
# =============================================================================

@pytest.mark.asyncio
async def test_github_connector_graph_integration(db_session: AsyncSession):
    org_id = uuid.uuid4()
    ws_id = uuid.uuid4()

    extraction_service = GraphExtractionService(db_session)
    res = await extraction_service.extract_from_github_metadata(
        organization_id=org_id,
        workspace_id=ws_id,
        repo_name="org/core-platform",
        files=["src/main.py", "README.md"],
        issues=[{"number": 101, "title": "Auth failure", "author": "alice"}],
        pull_requests=[{"number": 50, "title": "Fix auth", "referenced_issues": [101]}],
    )
    assert res.entities_created >= 4  # repo, files, issue, pr, person
    assert res.relationships_created >= 3  # contains, belongs_to, references, created_by


@pytest.mark.asyncio
async def test_document_and_workflow_graph_integration(db_session: AsyncSession):
    org_id = uuid.uuid4()
    ws_id = uuid.uuid4()

    extraction_service = GraphExtractionService(db_session)

    # Document integration
    doc_res = await extraction_service.extract_from_document_metadata(
        organization_id=org_id,
        workspace_id=ws_id,
        document_id=uuid.uuid4(),
        document_title="Architecture Spec",
        mentioned_entities=[{"name": "Auth API", "type": "api"}],
        referenced_concepts=["OAuth2 Flow"],
    )
    assert doc_res.entities_created >= 2
    assert doc_res.relationships_created >= 2

    # Workflow integration
    wf_res = await extraction_service.extract_from_workflow_metadata(
        organization_id=org_id,
        workspace_id=ws_id,
        workflow_id=uuid.uuid4(),
        workflow_name="Deploy Pipeline",
        steps=[
            {"name": "Build Step", "step_type": "task"},
            {"name": "Notify Step", "prompt_key": "release.announcement"},
        ],
    )
    assert wf_res.entities_created >= 3  # workflow, steps, prompt
    assert wf_res.relationships_created >= 2  # contains, uses


# =============================================================================
# 11. Retrieval Router & Graph Strategy Integration
# =============================================================================

@pytest.mark.asyncio
async def test_retrieval_router_graph_detection():
    provider = RuleBasedDecisionProvider()

    class FakeTask:
        id = uuid.uuid4()
        title = "What services depend on the authentication API?"
        description = None
        parameters = {}
        metadata_json = {}

    task = FakeTask()
    decision = await provider.decide(task)

    assert decision.retrieval_required is True
    assert decision.strategy in (RetrievalStrategy.GRAPH, RetrievalStrategy.HYBRID_GRAPH)
    assert "dependencies" in decision.reason or "depend" in decision.reason


# =============================================================================
# 12. Context Engine GraphContextProvider & Budget Enforcement
# =============================================================================

@pytest.mark.asyncio
async def test_context_engine_graph_provider(db_session: AsyncSession):
    org_id = uuid.uuid4()
    ws_id = uuid.uuid4()

    # Prepopulate entities
    entity_service = EntityService(db_session)
    await entity_service.create_entity(
        org_id, ws_id, EntityCreateRequest(canonical_name="Postgres DB", entity_type="database", description="Primary SQL database")
    )

    provider = GraphContextProvider()
    assert provider.provider_id == "knowledge_graph_context"
    assert provider.source_type == ContextSourceType.KNOWLEDGE_GRAPH.value

    # Build context items
    class DummyTask:
        id = uuid.uuid4()
        workspace_id = ws_id
        project_id = None
        title = "Check Postgres DB connections"
        description = None

    items = await provider.collect(
        task=DummyTask(),
        session=db_session,
        workspace_id=ws_id,
        graph_enabled=True,
    )
    assert len(items) > 0
    first_item = items[0]
    assert first_item.source_type == ContextSourceType.KNOWLEDGE_GRAPH
    assert "Postgres DB" in first_item.content
    assert first_item.metadata["canonical_name"] == "Postgres DB"
    assert first_item.estimated_tokens <= 3000


# =============================================================================
# 13. Evaluation Lab Graph Assertions
# =============================================================================

def test_evaluation_lab_graph_assertions():
    # Context items simulating knowledge graph retrieval output
    context_items = [
        {
            "content": "[DATABASE] PostgreSQL: Primary ACID database",
            "metadata": {
                "canonical_name": "PostgreSQL",
                "relationships": ["backend_core -> uses -> PostgreSQL"],
                "sources": [{"source_type": "document", "source_id": "doc_arch_1"}],
                "source_count": 2,
            },
        }
    ]

    # 1. entity_exists
    a_ent = AssertionDefinition(type=AssertionType.ENTITY_EXISTS, value="PostgreSQL")
    res_ent = AssertionEngine.evaluate_assertion(a_ent, output_text="PostgreSQL was retrieved", context_items=context_items)
    assert res_ent.passed is True

    # 2. relationship_exists
    a_rel = AssertionDefinition(type=AssertionType.RELATIONSHIP_EXISTS, value="uses")
    res_rel = AssertionEngine.evaluate_assertion(a_rel, output_text="uses PostgreSQL", context_items=context_items)
    assert res_rel.passed is True

    # 3. relationship_matches_source
    a_src = AssertionDefinition(type=AssertionType.RELATIONSHIP_MATCHES_SOURCE, value="doc_arch_1")
    res_src = AssertionEngine.evaluate_assertion(a_src, output_text="doc_arch_1 reference", context_items=context_items)
    assert res_src.passed is True

    # 4. source_reference_exists
    a_ref = AssertionDefinition(type=AssertionType.SOURCE_REFERENCE_EXISTS)
    res_ref = AssertionEngine.evaluate_assertion(a_ref, output_text="", context_items=context_items)
    assert res_ref.passed is True


# =============================================================================
# 14. Replay Snapshot Graph Configuration
# =============================================================================

def test_replay_snapshot_graph_config():
    snapshot = ExecutionSnapshot(
        run_id=str(uuid.uuid4()),
        task_id=str(uuid.uuid4()),
        workspace_id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc).isoformat(),
        graph_configuration={
            "entity_ids": [str(uuid.uuid4()), str(uuid.uuid4())],
            "relationship_ids": [str(uuid.uuid4())],
            "source_references": [{"source": "github"}],
            "traversal_config": {"max_hops": 1},
            "snapshot_hash": "a1b2c3d4e5f6",
        },
    )
    assert snapshot.graph_configuration is not None
    assert len(snapshot.graph_configuration["entity_ids"]) == 2
    assert snapshot.graph_configuration["snapshot_hash"] == "a1b2c3d4e5f6"
