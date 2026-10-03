"""
Knowledge Graph Service facade for Step 29.
Coordinates Entity and Relationship services, resolution, bounded retrieval,
extraction, proposals/HITL review, conflict management, and event publishing.
"""
import logging
import uuid
from typing import Any, Dict, List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.events.constants import ActorType, AggregateType, SystemEventType
from backend.app.services.events.publisher import EventPublisher
from backend.app.services.events.schemas import EventPublishRequest
from backend.app.services.knowledge_graph.constants import ProposalStatus
from backend.app.services.knowledge_graph.entity_service import EntityService
from backend.app.services.knowledge_graph.errors import ProposalNotFoundError
from backend.app.services.knowledge_graph.extraction import GraphExtractionService
from backend.app.services.knowledge_graph.models import GraphChangeProposal
from backend.app.services.knowledge_graph.policies import GraphPolicyEngine
from backend.app.services.knowledge_graph.relationship_service import RelationshipService
from backend.app.services.knowledge_graph.repository import KnowledgeGraphRepository
from backend.app.services.knowledge_graph.resolver import EntityResolver
from backend.app.services.knowledge_graph.retriever import GraphRetriever
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
    RelationshipCreateRequest,
    RelationshipResponse,
    RelationshipUpdateRequest,
)
from backend.app.services.notifications.service import NotificationService

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """
    Central service orchestrating all Knowledge Graph capabilities.
    """

    def __init__(
        self,
        session: AsyncSession,
        event_publisher: Optional[EventPublisher] = None,
        notification_service: Optional[NotificationService] = None,
    ):
        self.session = session
        self.repo = KnowledgeGraphRepository(session)
        self.entity_service = EntityService(session)
        self.relationship_service = RelationshipService(session)
        self.resolver = EntityResolver(session)
        self.retriever = GraphRetriever(session)
        self.extraction_service = GraphExtractionService(session)
        self.event_publisher = event_publisher or EventPublisher(session)
        self.notification_service = notification_service

    # =========================================================================
    # Entity Operations
    # =========================================================================

    async def create_entity(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        request: EntityCreateRequest,
        actor_id: Optional[uuid.UUID] = None,
    ) -> EntityResponse:
        entity = await self.entity_service.create_entity(
            organization_id=organization_id,
            workspace_id=workspace_id,
            request=request,
            actor_id=actor_id,
        )

        try:
            await self.event_publisher.publish(
                EventPublishRequest(
                    workspace_id=workspace_id,
                    project_id=entity.project_id,
                    event_type=SystemEventType.GRAPH_ENTITY_CREATED.value,
                    aggregate_type=AggregateType.GRAPH.value,
                    aggregate_id=str(entity.id),
                    actor_type=ActorType.USER.value if actor_id else ActorType.SYSTEM.value,
                    actor_id=str(actor_id) if actor_id else "system",
                    payload={"canonical_name": entity.canonical_name, "entity_type": entity.entity_type},
                )
            )
        except Exception as e:
            logger.warning(f"[KnowledgeGraphService] Failed to publish entity_created event: {e}")

        return entity

    async def get_entity(self, entity_id: uuid.UUID) -> EntityResponse:
        return await self.entity_service.get_entity(entity_id)

    async def update_entity(
        self,
        entity_id: uuid.UUID,
        request: EntityUpdateRequest,
        actor_id: Optional[uuid.UUID] = None,
    ) -> EntityResponse:
        entity = await self.entity_service.update_entity(entity_id, request, actor_id=actor_id)

        try:
            await self.event_publisher.publish(
                EventPublishRequest(
                    workspace_id=entity.workspace_id,
                    project_id=entity.project_id,
                    event_type=SystemEventType.GRAPH_ENTITY_UPDATED.value,
                    aggregate_type=AggregateType.GRAPH.value,
                    aggregate_id=str(entity.id),
                    actor_type=ActorType.USER.value if actor_id else ActorType.SYSTEM.value,
                    actor_id=str(actor_id) if actor_id else "system",
                    payload={"canonical_name": entity.canonical_name, "status": entity.status},
                )
            )
        except Exception as e:
            logger.warning(f"[KnowledgeGraphService] Failed to publish entity_updated event: {e}")

        return entity

    async def archive_entity(
        self,
        entity_id: uuid.UUID,
        actor_id: Optional[uuid.UUID] = None,
    ) -> EntityResponse:
        entity = await self.entity_service.archive_entity(entity_id, actor_id=actor_id)

        try:
            await self.event_publisher.publish(
                EventPublishRequest(
                    workspace_id=entity.workspace_id,
                    project_id=entity.project_id,
                    event_type=SystemEventType.GRAPH_ENTITY_ARCHIVED.value,
                    aggregate_type=AggregateType.GRAPH.value,
                    aggregate_id=str(entity.id),
                    actor_type=ActorType.USER.value if actor_id else ActorType.SYSTEM.value,
                    actor_id=str(actor_id) if actor_id else "system",
                    payload={"canonical_name": entity.canonical_name},
                )
            )
        except Exception as e:
            logger.warning(f"[KnowledgeGraphService] Failed to publish entity_archived event: {e}")

        return entity

    async def search_entities(
        self,
        workspace_id: uuid.UUID,
        query: str,
        entity_type: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        limit: int = 20,
    ) -> List[EntityResponse]:
        return await self.entity_service.search_entities(
            workspace_id=workspace_id,
            query=query,
            entity_type=entity_type,
            project_id=project_id,
            limit=limit,
        )

    async def list_entities(
        self,
        workspace_id: uuid.UUID,
        entity_type: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        status: str = "active",
        limit: int = 50,
        offset: int = 0,
    ) -> List[EntityResponse]:
        return await self.entity_service.list_entities(
            workspace_id=workspace_id,
            entity_type=entity_type,
            project_id=project_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def merge_entities(
        self,
        request: EntityMergeRequest,
        actor_id: Optional[uuid.UUID] = None,
    ) -> EntityMergeResponse:
        return await self.entity_service.merge_entities(
            source_entity_id=request.source_entity_id,
            target_canonical_entity_id=request.target_canonical_entity_id,
            actor_id=actor_id,
        )

    # =========================================================================
    # Relationship Operations
    # =========================================================================

    async def create_relationship(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        request: RelationshipCreateRequest,
        actor_id: Optional[uuid.UUID] = None,
    ) -> RelationshipResponse:
        rel = await self.relationship_service.create_relationship(
            organization_id=organization_id,
            workspace_id=workspace_id,
            request=request,
            actor_id=actor_id,
        )

        try:
            await self.event_publisher.publish(
                EventPublishRequest(
                    workspace_id=workspace_id,
                    project_id=rel.project_id,
                    event_type=SystemEventType.GRAPH_RELATIONSHIP_CREATED.value,
                    aggregate_type=AggregateType.GRAPH.value,
                    aggregate_id=str(rel.id),
                    actor_type=ActorType.USER.value if actor_id else ActorType.SYSTEM.value,
                    actor_id=str(actor_id) if actor_id else "system",
                    payload={"relationship_type": rel.relationship_type, "source_id": str(rel.source_entity_id), "target_id": str(rel.target_entity_id)},
                )
            )
        except Exception as e:
            logger.warning(f"[KnowledgeGraphService] Failed to publish relationship_created event: {e}")

        return rel

    async def get_relationship(self, relationship_id: uuid.UUID) -> RelationshipResponse:
        return await self.relationship_service.get_relationship(relationship_id)

    async def list_relationships(
        self,
        workspace_id: uuid.UUID,
        entity_id: Optional[uuid.UUID] = None,
        relationship_type: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        limit: int = 100,
    ) -> List[RelationshipResponse]:
        return await self.relationship_service.list_relationships(
            workspace_id=workspace_id,
            entity_id=entity_id,
            relationship_type=relationship_type,
            project_id=project_id,
            limit=limit,
        )

    async def update_relationship(
        self,
        relationship_id: uuid.UUID,
        request: RelationshipUpdateRequest,
        actor_id: Optional[uuid.UUID] = None,
    ) -> RelationshipResponse:
        return await self.relationship_service.update_relationship(
            relationship_id=relationship_id,
            request=request,
            actor_id=actor_id,
        )

    async def archive_relationship(
        self,
        relationship_id: uuid.UUID,
        actor_id: Optional[uuid.UUID] = None,
    ) -> RelationshipResponse:
        rel = await self.relationship_service.archive_relationship(relationship_id, actor_id=actor_id)

        try:
            await self.event_publisher.publish(
                EventPublishRequest(
                    workspace_id=rel.workspace_id,
                    project_id=rel.project_id,
                    event_type=SystemEventType.GRAPH_RELATIONSHIP_REMOVED.value,
                    aggregate_type=AggregateType.GRAPH.value,
                    aggregate_id=str(rel.id),
                    actor_type=ActorType.USER.value if actor_id else ActorType.SYSTEM.value,
                    actor_id=str(actor_id) if actor_id else "system",
                    payload={"relationship_type": rel.relationship_type},
                )
            )
        except Exception as e:
            logger.warning(f"[KnowledgeGraphService] Failed to publish relationship_removed event: {e}")

        return rel

    # =========================================================================
    # Query & Traversal
    # =========================================================================

    async def query_graph(
        self,
        workspace_id: uuid.UUID,
        request: GraphQueryRequest,
        authorized_project_ids: Optional[Set[uuid.UUID]] = None,
    ) -> GraphContextResult:
        return await self.retriever.retrieve(
            workspace_id=workspace_id,
            seed_entities=request.seed_entities,
            seed_names=request.seed_names,
            entity_types=request.entity_types,
            relationship_types=request.relationship_types,
            max_hops=request.max_hops,
            max_entities=request.max_entities,
            max_relationships=request.max_relationships,
            project_id=request.project_id,
            authorized_project_ids=authorized_project_ids,
            include_temporal_expired=request.include_temporal_expired,
        )

    async def get_entity_neighbors(
        self,
        entity_id: uuid.UUID,
        workspace_id: uuid.UUID,
        authorized_project_ids: Optional[Set[uuid.UUID]] = None,
    ) -> GraphNeighborResponse:
        entity = await self.get_entity(entity_id)
        result = await self.retriever.retrieve(
            workspace_id=workspace_id,
            seed_entities=[entity_id],
            max_hops=1,
            max_entities=30,
            max_relationships=50,
            authorized_project_ids=authorized_project_ids,
        )

        neighbors = [e for e in result.entities if e.id != entity_id]
        return GraphNeighborResponse(
            entity=entity,
            neighbors=neighbors,
            relationships=result.relationships,
        )

    # =========================================================================
    # Task Graph Preview
    # =========================================================================

    async def preview_task_graph(
        self,
        workspace_id: uuid.UUID,
        text: str,
        project_id: Optional[uuid.UUID] = None,
    ) -> GraphPreviewResponse:
        """
        Analyzes task text to determine if graph retrieval is recommended,
        and previews linked entities and candidate relationships.
        """
        linked_ids = await self.retriever.link_entities_from_text(
            workspace_id=workspace_id,
            text=text,
            project_id=project_id,
            max_seeds=6,
        )

        # Heuristic for recommendation: queries asking about dependencies, relationships, services, architecture
        dep_terms = {"depend", "call", "use", "connect", "service", "api", "architecture", "who", "owns", "member", "workflow"}
        has_rel_keyword = any(term in text.lower() for term in dep_terms)
        is_recommended = bool(linked_ids) and (has_rel_keyword or len(linked_ids) >= 2)

        detected_entities = []
        candidate_rels = []
        estimated_tokens = 0

        if linked_ids:
            res = await self.retriever.retrieve(
                workspace_id=workspace_id,
                seed_entities=linked_ids,
                max_hops=1,
                max_entities=20,
                max_relationships=30,
                project_id=project_id,
            )
            detected_entities = [e.canonical_name for e in res.entities]
            candidate_rels = [
                {"source": r.source_entity_name or str(r.source_entity_id), "type": r.relationship_type, "target": r.target_entity_name or str(r.target_entity_id)}
                for r in res.relationships
            ]
            estimated_tokens = res.token_estimate

        return GraphPreviewResponse(
            is_graph_recommended=is_recommended,
            detected_entities=detected_entities,
            candidate_relationships=candidate_rels,
            estimated_tokens=estimated_tokens,
            retrieval_scope="project" if project_id else "workspace",
        )

    # =========================================================================
    # Extraction
    # =========================================================================

    async def extract_knowledge(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        request: GraphExtractRequest,
        actor_id: Optional[uuid.UUID] = None,
    ) -> GraphExtractResponse:
        return await self.extraction_service.extract_from_text(
            organization_id=organization_id,
            workspace_id=workspace_id,
            text=request.content or "",
            source_id=request.source_id,
            source_type=request.source_type,
            project_id=request.project_id,
            actor_id=actor_id,
        )

    # =========================================================================
    # Proposals & HITL Review
    # =========================================================================

    async def list_proposals(
        self,
        workspace_id: uuid.UUID,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[GraphChangeProposalResponse]:
        proposals = await self.repo.list_proposals(workspace_id, status=status, limit=limit)
        return [GraphChangeProposalResponse.model_validate(p) for p in proposals]

    async def approve_proposal(
        self,
        proposal_id: uuid.UUID,
        reviewed_by: Optional[uuid.UUID] = None,
        organization_id: Optional[uuid.UUID] = None,
        workspace_id: Optional[uuid.UUID] = None,
        review_note: Optional[str] = None,
        **kwargs: Any,
    ) -> GraphChangeProposalResponse:
        """
        Approves a proposal and commits its proposed entities and relationships to the graph.
        """
        proposal = await self.repo.get_proposal_by_id(proposal_id)
        if not proposal:
            raise ProposalNotFoundError(f"Proposal {proposal_id} not found.")

        # Persist proposed entities
        resolved_name_to_id: Dict[str, uuid.UUID] = {}
        for ent_data in proposal.proposed_entities:
            created_resp, _ = await self.resolver.resolve_or_create_entity(
                organization_id=proposal.organization_id,
                workspace_id=proposal.workspace_id,
                raw_name=ent_data.get("canonical_name", ""),
                entity_type=ent_data.get("entity_type", "concept"),
                description=ent_data.get("description"),
                properties=ent_data.get("properties", {}),
                source_type=proposal.source_type,
                source_id=proposal.source_id,
                project_id=proposal.project_id,
                confidence=ent_data.get("confidence", 1.0),
            )
            resolved_name_to_id[ent_data.get("canonical_name", "").strip().lower()] = created_resp.id

        # Persist proposed relationships
        for rel_data in proposal.proposed_relationships:
            s_norm = rel_data.get("source_name", "").strip().lower()
            t_norm = rel_data.get("target_name", "").strip().lower()
            s_id = resolved_name_to_id.get(s_norm)
            t_id = resolved_name_to_id.get(t_norm)

            if s_id and t_id and s_id != t_id:
                try:
                    await self.relationship_service.create_relationship(
                        organization_id=proposal.organization_id,
                        workspace_id=proposal.workspace_id,
                        request=RelationshipCreateRequest(
                            source_entity_id=s_id,
                            relationship_type=rel_data.get("relationship_type", "related_to"),
                            target_entity_id=t_id,
                            properties=rel_data.get("properties", {}),
                            source_reference={"proposal_id": str(proposal.id)},
                            project_id=proposal.project_id,
                        ),
                        actor_id=reviewed_by,
                    )
                except Exception as e:
                    logger.warning(f"[KnowledgeGraphService] Could not persist approved relationship: {e}")

        # Update proposal status
        updated = await self.repo.update_proposal_status(
            proposal_id=proposal_id,
            status=ProposalStatus.APPROVED.value,
            reviewed_by=reviewed_by,
            reason=review_note,
        )

        try:
            effective_actor = str(reviewed_by or proposal.created_by or uuid.uuid4())
            await self.event_publisher.publish(
                EventPublishRequest(
                    workspace_id=proposal.workspace_id,
                    project_id=proposal.project_id,
                    event_type=SystemEventType.GRAPH_PROPOSAL_APPROVED.value,
                    aggregate_type=AggregateType.GRAPH.value,
                    aggregate_id=str(proposal.id),
                    actor_type=ActorType.USER.value,
                    actor_id=effective_actor,
                    payload={"proposal_id": str(proposal.id), "status": "approved"},
                )
            )
        except Exception as e:
            logger.warning(f"[KnowledgeGraphService] Failed to publish proposal_approved event: {e}")

        return GraphChangeProposalResponse.model_validate(updated)

    async def reject_proposal(
        self,
        proposal_id: uuid.UUID,
        reviewed_by: Optional[uuid.UUID] = None,
        reason: Optional[str] = None,
        organization_id: Optional[uuid.UUID] = None,
        workspace_id: Optional[uuid.UUID] = None,
        review_note: Optional[str] = None,
        **kwargs: Any,
    ) -> GraphChangeProposalResponse:
        effective_reason = reason or review_note
        updated = await self.repo.update_proposal_status(
            proposal_id=proposal_id,
            status=ProposalStatus.REJECTED.value,
            reviewed_by=reviewed_by,
            reason=effective_reason,
        )

        try:
            effective_actor = str(reviewed_by or updated.created_by or uuid.uuid4())
            await self.event_publisher.publish(
                EventPublishRequest(
                    workspace_id=updated.workspace_id,
                    project_id=updated.project_id,
                    event_type=SystemEventType.GRAPH_PROPOSAL_REJECTED.value,
                    aggregate_type=AggregateType.GRAPH.value,
                    aggregate_id=str(updated.id),
                    actor_type=ActorType.USER.value,
                    actor_id=effective_actor,
                    payload={"proposal_id": str(updated.id), "reason": effective_reason},
                )
            )
        except Exception as e:
            logger.warning(f"[KnowledgeGraphService] Failed to publish proposal_rejected event: {e}")

        return GraphChangeProposalResponse.model_validate(updated)

    # =========================================================================
    # Conflicts
    # =========================================================================

    async def list_conflicts(
        self,
        workspace_id: uuid.UUID,
        status: Optional[str] = "open",
        limit: int = 50,
    ) -> List[GraphConflictResponse]:
        conflicts = await self.repo.list_conflicts(workspace_id, status=status, limit=limit)
        return [GraphConflictResponse.model_validate(c) for c in conflicts]

    async def resolve_conflict(
        self,
        conflict_id: uuid.UUID,
        request: ConflictResolveRequest,
        resolved_by: uuid.UUID,
    ) -> GraphConflictResponse:
        resolved = await self.repo.resolve_conflict(
            conflict_id=conflict_id,
            resolved_by=resolved_by,
            resolution_action=request.resolution_action,
            notes=request.notes,
        )

        try:
            await self.event_publisher.publish(
                EventPublishRequest(
                    workspace_id=resolved.workspace_id,
                    event_type=SystemEventType.GRAPH_CONFLICT_RESOLVED.value,
                    aggregate_type=AggregateType.GRAPH.value,
                    aggregate_id=str(resolved.id),
                    actor_type=ActorType.USER.value,
                    actor_id=str(resolved_by),
                    payload={"conflict_id": str(resolved.id), "action": request.resolution_action},
                )
            )
        except Exception as e:
            logger.warning(f"[KnowledgeGraphService] Failed to publish conflict_resolved event: {e}")

        return GraphConflictResponse.model_validate(resolved)

    # =========================================================================
    # Summary
    # =========================================================================

    async def get_project_knowledge_summary(
        self,
        workspace_id: uuid.UUID,
        project_id: Optional[uuid.UUID] = None,
    ) -> ProjectKnowledgeSummary:
        raw_summary = await self.repo.get_project_knowledge_summary(workspace_id, project_id=project_id)
        return ProjectKnowledgeSummary(**raw_summary)
