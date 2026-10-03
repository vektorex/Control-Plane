"""
Knowledge Graph API routes for Step 29.
Provides endpoints for Entities, Relationships, Traversal, Search, Extraction, Proposals, and Conflicts.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.access_control.permissions import (
    GRAPH_CREATE,
    GRAPH_DELETE,
    GRAPH_EXTRACT,
    GRAPH_MERGE,
    GRAPH_READ,
    GRAPH_UPDATE,
)
from backend.app.services.knowledge_graph.errors import (
    EntityNotFoundError,
    ProposalNotFoundError,
    RelationshipNotFoundError,
    UnauthorizedGraphAccessError,
)
from backend.app.services.knowledge_graph.policies import GraphPolicyEngine
from backend.app.services.knowledge_graph.schemas import (
    ConflictResolveRequest,
    EntityCreateRequest,
    EntityMergeRequest,
    EntityMergeResponse,
    EntityResponse,
    EntityUpdateRequest,
    GraphChangeProposalResponse,
    GraphConflictResponse,
    GraphContextResult,
    GraphExtractRequest,
    GraphExtractResponse,
    GraphNeighborResponse,
    GraphPreviewResponse,
    GraphQueryRequest,
    ProjectKnowledgeSummary,
    ProposalActionRequest,
    RelationshipCreateRequest,
    RelationshipResponse,
    RelationshipUpdateRequest,
)
from backend.app.services.knowledge_graph.service import KnowledgeGraphService

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])


# =============================================================================
# Summary & Search (Static Routes)
# =============================================================================

@router.get("/summary", response_model=ProjectKnowledgeSummary)
async def get_graph_summary(
    workspace_id: UUID = Query(...),
    project_id: Optional[UUID] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectKnowledgeSummary:
    """
    Returns aggregate knowledge graph statistics (entities, relationships, proposals, conflicts).
    """
    await GraphPolicyEngine.authorize_graph_operation(
        session=db,
        user=user,
        permission=GRAPH_READ,
        workspace_id=workspace_id,
        project_id=project_id,
    )
    service = KnowledgeGraphService(db)
    return await service.get_project_knowledge_summary(workspace_id=workspace_id, project_id=project_id)


@router.get("/entities/search", response_model=List[EntityResponse])
async def search_entities(
    workspace_id: UUID = Query(...),
    q: str = Query(..., min_length=1, description="Search query string"),
    entity_type: Optional[str] = Query(None),
    project_id: Optional[UUID] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[EntityResponse]:
    """
    Searches entities by canonical name, alias, or description within authorized scope.
    """
    await GraphPolicyEngine.authorize_graph_operation(
        session=db,
        user=user,
        permission=GRAPH_READ,
        workspace_id=workspace_id,
        project_id=project_id,
    )
    service = KnowledgeGraphService(db)
    return await service.search_entities(
        workspace_id=workspace_id,
        query=q,
        entity_type=entity_type,
        project_id=project_id,
        limit=limit,
    )


# =============================================================================
# Entities CRUD
# =============================================================================

@router.get("/entities", response_model=List[EntityResponse])
async def list_entities(
    workspace_id: UUID = Query(...),
    entity_type: Optional[str] = Query(None),
    project_id: Optional[UUID] = Query(None),
    status: str = Query("active"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[EntityResponse]:
    """
    Lists entities matching optional filters.
    """
    await GraphPolicyEngine.authorize_graph_operation(
        session=db,
        user=user,
        permission=GRAPH_READ,
        workspace_id=workspace_id,
        project_id=project_id,
    )
    service = KnowledgeGraphService(db)
    return await service.list_entities(
        workspace_id=workspace_id,
        entity_type=entity_type,
        project_id=project_id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.post("/entities", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)
async def create_entity(
    request: EntityCreateRequest,
    workspace_id: UUID = Query(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EntityResponse:
    """
    Creates a new canonical entity in the Knowledge Graph.
    """
    await GraphPolicyEngine.authorize_graph_operation(
        session=db,
        user=user,
        permission=GRAPH_CREATE,
        workspace_id=workspace_id,
        project_id=request.project_id,
    )
    service = KnowledgeGraphService(db)
    return await service.create_entity(
        organization_id=user.organization_id,
        workspace_id=workspace_id,
        request=request,
        actor_id=user.id,
    )


@router.get("/entities/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EntityResponse:
    """
    Retrieves an entity by ID including aliases and provenance sources.
    """
    service = KnowledgeGraphService(db)
    entity = await service.get_entity(entity_id)

    await GraphPolicyEngine.authorize_graph_operation(
        session=db,
        user=user,
        permission=GRAPH_READ,
        workspace_id=entity.workspace_id,
        project_id=entity.project_id,
    )
    GraphPolicyEngine.verify_tenant_boundary(user, entity.organization_id)
    return entity


@router.patch("/entities/{entity_id}", response_model=EntityResponse)
async def update_entity(
    entity_id: UUID,
    request: EntityUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EntityResponse:
    """
    Updates entity metadata or status.
    """
    service = KnowledgeGraphService(db)
    existing = await service.get_entity(entity_id)

    await GraphPolicyEngine.authorize_graph_operation(
        session=db,
        user=user,
        permission=GRAPH_UPDATE,
        workspace_id=existing.workspace_id,
        project_id=existing.project_id,
    )
    GraphPolicyEngine.verify_tenant_boundary(user, existing.organization_id)
    return await service.update_entity(entity_id, request, actor_id=user.id)


@router.delete("/entities/{entity_id}", response_model=EntityResponse)
async def archive_entity(
    entity_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EntityResponse:
    """
    Archives an entity and its associated relationships.
    """
    service = KnowledgeGraphService(db)
    existing = await service.get_entity(entity_id)

    await GraphPolicyEngine.authorize_graph_operation(
        session=db,
        user=user,
        permission=GRAPH_DELETE,
        workspace_id=existing.workspace_id,
        project_id=existing.project_id,
    )
    GraphPolicyEngine.verify_tenant_boundary(user, existing.organization_id)
    return await service.archive_entity(entity_id, actor_id=user.id)


@router.get("/entities/{entity_id}/neighbors", response_model=GraphNeighborResponse)
async def get_entity_neighbors(
    entity_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GraphNeighborResponse:
    """
    Retrieves 1-hop connected neighbors and relationships for a specific entity.
    """
    service = KnowledgeGraphService(db)
    entity = await service.get_entity(entity_id)

    await GraphPolicyEngine.authorize_graph_operation(
        session=db,
        user=user,
        permission=GRAPH_READ,
        workspace_id=entity.workspace_id,
        project_id=entity.project_id,
    )
    GraphPolicyEngine.verify_tenant_boundary(user, entity.organization_id)

    authorized_proj_ids = await GraphPolicyEngine.get_authorized_project_ids(
        session=db,
        user=user,
        workspace_id=entity.workspace_id,
    )
    return await service.get_entity_neighbors(
        entity_id=entity_id,
        workspace_id=entity.workspace_id,
        authorized_project_ids=authorized_proj_ids,
    )


@router.post("/entities/merge", response_model=EntityMergeResponse)
async def merge_entities(
    request: EntityMergeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EntityMergeResponse:
    """
    Merges duplicate source entity into target canonical entity.
    """
    service = KnowledgeGraphService(db)
    source = await service.get_entity(request.source_entity_id)
    target = await service.get_entity(request.target_canonical_entity_id)

    await GraphPolicyEngine.authorize_graph_operation(
        session=db,
        user=user,
        permission=GRAPH_MERGE,
        workspace_id=target.workspace_id,
        project_id=target.project_id,
    )
    GraphPolicyEngine.verify_tenant_boundary(user, source.organization_id)
    GraphPolicyEngine.verify_tenant_boundary(user, target.organization_id)

    return await service.merge_entities(request, actor_id=user.id)


# =============================================================================
# Relationships CRUD
# =============================================================================

@router.get("/relationships", response_model=List[RelationshipResponse])
async def list_relationships(
    workspace_id: UUID = Query(...),
    entity_id: Optional[UUID] = Query(None),
    relationship_type: Optional[str] = Query(None),
    project_id: Optional[UUID] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[RelationshipResponse]:
    """
    Lists relationships matching optional filters.
    """
    await GraphPolicyEngine.authorize_graph_operation(
        session=db,
        user=user,
        permission=GRAPH_READ,
        workspace_id=workspace_id,
        project_id=project_id,
    )
    service = KnowledgeGraphService(db)
    return await service.list_relationships(
        workspace_id=workspace_id,
        entity_id=entity_id,
        relationship_type=relationship_type,
        project_id=project_id,
        limit=limit,
    )


@router.post("/relationships", response_model=RelationshipResponse, status_code=status.HTTP_201_CREATED)
async def create_relationship(
    request: RelationshipCreateRequest,
    workspace_id: UUID = Query(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RelationshipResponse:
    """
    Creates a directed edge between two entities.
    """
    await GraphPolicyEngine.authorize_graph_operation(
        session=db,
        user=user,
        permission=GRAPH_CREATE,
        workspace_id=workspace_id,
        project_id=request.project_id,
    )
    service = KnowledgeGraphService(db)
    return await service.create_relationship(
        organization_id=user.organization_id,
        workspace_id=workspace_id,
        request=request,
        actor_id=user.id,
    )


@router.patch("/relationships/{relationship_id}", response_model=RelationshipResponse)
async def update_relationship(
    relationship_id: UUID,
    request: RelationshipUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RelationshipResponse:
    """
    Updates relationship properties or validity dates.
    """
    service = KnowledgeGraphService(db)
    existing = await service.get_relationship(relationship_id)

    await GraphPolicyEngine.authorize_graph_operation(
        session=db,
        user=user,
        permission=GRAPH_UPDATE,
        workspace_id=existing.workspace_id,
        project_id=existing.project_id,
    )
    GraphPolicyEngine.verify_tenant_boundary(user, existing.organization_id)
    return await service.update_relationship(relationship_id, request, actor_id=user.id)


@router.delete("/relationships/{relationship_id}", response_model=RelationshipResponse)
async def archive_relationship(
    relationship_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RelationshipResponse:
    """
    Archives a relationship edge.
    """
    service = KnowledgeGraphService(db)
    existing = await service.get_relationship(relationship_id)

    await GraphPolicyEngine.authorize_graph_operation(
        session=db,
        user=user,
        permission=GRAPH_DELETE,
        workspace_id=existing.workspace_id,
        project_id=existing.project_id,
    )
    GraphPolicyEngine.verify_tenant_boundary(user, existing.organization_id)
    return await service.archive_relationship(relationship_id, actor_id=user.id)


# =============================================================================
# Graph Query & Traversal
# =============================================================================

@router.post("/query", response_model=GraphContextResult)
async def query_graph(
    request: GraphQueryRequest,
    workspace_id: UUID = Query(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GraphContextResult:
    """
    Executes bounded BFS graph traversal starting from seed entities.
    """
    await GraphPolicyEngine.authorize_graph_operation(
        session=db,
        user=user,
        permission=GRAPH_READ,
        workspace_id=workspace_id,
        project_id=request.project_id,
    )
    service = KnowledgeGraphService(db)
    authorized_proj_ids = await GraphPolicyEngine.get_authorized_project_ids(
        session=db,
        user=user,
        workspace_id=workspace_id,
    )
    return await service.query_graph(
        workspace_id=workspace_id,
        request=request,
        authorized_project_ids=authorized_proj_ids,
    )


# =============================================================================
# Extraction & Preview
# =============================================================================

@router.post("/extract", response_model=GraphExtractResponse)
async def extract_graph(
    request: GraphExtractRequest,
    workspace_id: UUID = Query(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GraphExtractResponse:
    """
    Extracts entities and relationships from text or document source.
    """
    await GraphPolicyEngine.authorize_graph_operation(
        session=db,
        user=user,
        permission=GRAPH_EXTRACT,
        workspace_id=workspace_id,
        project_id=request.project_id,
    )
    service = KnowledgeGraphService(db)
    return await service.extract_knowledge(
        organization_id=user.organization_id,
        workspace_id=workspace_id,
        request=request,
        actor_id=user.id,
    )


@router.post("/preview", response_model=GraphPreviewResponse)
async def preview_graph(
    text: str = Query(..., description="Text to analyze for graph relevance"),
    workspace_id: UUID = Query(...),
    project_id: Optional[UUID] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GraphPreviewResponse:
    """
    Previews whether graph retrieval is recommended for a task or query.
    """
    await GraphPolicyEngine.authorize_graph_operation(
        session=db,
        user=user,
        permission=GRAPH_READ,
        workspace_id=workspace_id,
        project_id=project_id,
    )
    service = KnowledgeGraphService(db)
    return await service.preview_task_graph(
        workspace_id=workspace_id,
        text=text,
        project_id=project_id,
    )


# =============================================================================
# Proposals & Review
# =============================================================================

@router.get("/proposals", response_model=List[GraphChangeProposalResponse])
async def list_proposals(
    workspace_id: UUID = Query(...),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[GraphChangeProposalResponse]:
    """
    Lists extracted graph change proposals awaiting review.
    """
    await GraphPolicyEngine.authorize_graph_operation(
        session=db,
        user=user,
        permission=GRAPH_READ,
        workspace_id=workspace_id,
    )
    service = KnowledgeGraphService(db)
    return await service.list_proposals(workspace_id=workspace_id, status=status, limit=limit)


@router.post("/proposals/{proposal_id}/approve", response_model=GraphChangeProposalResponse)
async def approve_proposal(
    proposal_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GraphChangeProposalResponse:
    """
    Approves a proposal, committing its proposed entities and relationships to the graph.
    """
    service = KnowledgeGraphService(db)
    proposal = await service.repo.get_proposal_by_id(proposal_id)
    if not proposal:
        raise ProposalNotFoundError(f"Proposal {proposal_id} not found.")

    await GraphPolicyEngine.authorize_graph_operation(
        session=db,
        user=user,
        permission=GRAPH_CREATE,
        workspace_id=proposal.workspace_id,
        project_id=proposal.project_id,
    )
    GraphPolicyEngine.verify_tenant_boundary(user, proposal.organization_id)
    return await service.approve_proposal(proposal_id=proposal_id, reviewed_by=user.id)


@router.post("/proposals/{proposal_id}/reject", response_model=GraphChangeProposalResponse)
async def reject_proposal(
    proposal_id: UUID,
    request: ProposalActionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GraphChangeProposalResponse:
    """
    Rejects a proposal with optional reason.
    """
    service = KnowledgeGraphService(db)
    proposal = await service.repo.get_proposal_by_id(proposal_id)
    if not proposal:
        raise ProposalNotFoundError(f"Proposal {proposal_id} not found.")

    await GraphPolicyEngine.authorize_graph_operation(
        session=db,
        user=user,
        permission=GRAPH_UPDATE,
        workspace_id=proposal.workspace_id,
        project_id=proposal.project_id,
    )
    GraphPolicyEngine.verify_tenant_boundary(user, proposal.organization_id)
    return await service.reject_proposal(
        proposal_id=proposal_id,
        reviewed_by=user.id,
        reason=request.rejection_reason,
    )


# =============================================================================
# Conflicts
# =============================================================================

@router.get("/conflicts", response_model=List[GraphConflictResponse])
async def list_conflicts(
    workspace_id: UUID = Query(...),
    status: Optional[str] = Query("open"),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[GraphConflictResponse]:
    """
    Lists detected graph conflicts requiring operator review.
    """
    await GraphPolicyEngine.authorize_graph_operation(
        session=db,
        user=user,
        permission=GRAPH_READ,
        workspace_id=workspace_id,
    )
    service = KnowledgeGraphService(db)
    return await service.list_conflicts(workspace_id=workspace_id, status=status, limit=limit)


@router.post("/conflicts/{conflict_id}/resolve", response_model=GraphConflictResponse)
async def resolve_conflict(
    conflict_id: UUID,
    request: ConflictResolveRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GraphConflictResponse:
    """
    Resolves or dismisses a graph conflict.
    """
    service = KnowledgeGraphService(db)
    conflict = await service.repo.get_conflict_by_id(conflict_id)
    if not conflict:
        from backend.app.services.knowledge_graph.errors import ConflictNotFoundError
        raise ConflictNotFoundError(f"Conflict {conflict_id} not found.")

    await GraphPolicyEngine.authorize_graph_operation(
        session=db,
        user=user,
        permission=GRAPH_UPDATE,
        workspace_id=conflict.workspace_id,
    )
    GraphPolicyEngine.verify_tenant_boundary(user, conflict.organization_id)
    return await service.resolve_conflict(conflict_id=conflict_id, request=request, resolved_by=user.id)
