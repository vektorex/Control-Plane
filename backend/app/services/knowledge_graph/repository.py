"""
Database repository for Knowledge Graph entities, relationships, aliases, sources, proposals, and conflicts.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy import desc, func, select, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.services.knowledge_graph.constants import (
    ConflictStatus,
    EntityStatus,
    ProposalStatus,
    RelationshipStatus,
)
from backend.app.services.knowledge_graph.errors import (
    ConflictNotFoundError,
    EntityNotFoundError,
    ProposalNotFoundError,
    RelationshipNotFoundError,
)
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
    normalize_alias,
    normalize_entity_name,
)


class KnowledgeGraphRepository:
    """
    Data access layer for the relational property graph.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # =========================================================================
    # Entities
    # =========================================================================

    async def create_entity(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        entity_type: str,
        canonical_name: str,
        description: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = 1.0,
        project_id: Optional[uuid.UUID] = None,
    ) -> Entity:
        entity = Entity(
            id=uuid.uuid4(),
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            entity_type=entity_type,
            canonical_name=canonical_name,
            description=description,
            properties=properties or {},
            source_count=1,
            confidence=confidence,
            status=EntityStatus.ACTIVE.value,
        )
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def get_entity_by_id(
        self,
        entity_id: uuid.UUID,
        include_relations: bool = True,
    ) -> Optional[Entity]:
        query = select(Entity).where(Entity.id == entity_id)
        if include_relations:
            query = query.options(
                selectinload(Entity.aliases),
                selectinload(Entity.sources),
            )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def get_entity_by_name(
        self,
        workspace_id: uuid.UUID,
        canonical_name: str,
        entity_type: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
    ) -> Optional[Entity]:
        norm_name = normalize_entity_name(canonical_name)
        query = select(Entity).where(
            Entity.workspace_id == workspace_id,
            func.lower(Entity.canonical_name) == norm_name,
            Entity.status == EntityStatus.ACTIVE.value,
        )
        if entity_type:
            query = query.where(Entity.entity_type == entity_type)
        if project_id:
            query = query.where(or_(Entity.project_id == project_id, Entity.project_id.is_(None)))

        query = query.options(
            selectinload(Entity.aliases),
            selectinload(Entity.sources),
        )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def search_entities(
        self,
        workspace_id: uuid.UUID,
        query_str: str,
        entity_type: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        limit: int = 20,
    ) -> List[Entity]:
        norm_query = normalize_entity_name(query_str)
        query = select(Entity).where(
            Entity.workspace_id == workspace_id,
            Entity.status == EntityStatus.ACTIVE.value,
            or_(
                Entity.canonical_name.ilike(f"%{norm_query}%"),
                Entity.description.ilike(f"%{norm_query}%"),
                Entity.id.in_(
                    select(EntityAlias.entity_id).where(
                        EntityAlias.normalized_alias.ilike(f"%{norm_query}%")
                    )
                ),
            ),
        )
        if entity_type:
            query = query.where(Entity.entity_type == entity_type)
        if project_id:
            query = query.where(or_(Entity.project_id == project_id, Entity.project_id.is_(None)))

        query = query.options(
            selectinload(Entity.aliases),
            selectinload(Entity.sources),
        ).limit(limit)

        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def list_entities(
        self,
        workspace_id: uuid.UUID,
        entity_type: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        status: str = EntityStatus.ACTIVE.value,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Entity]:
        query = select(Entity).where(
            Entity.workspace_id == workspace_id,
            Entity.status == status,
        )
        if entity_type:
            query = query.where(Entity.entity_type == entity_type)
        if project_id:
            query = query.where(or_(Entity.project_id == project_id, Entity.project_id.is_(None)))

        query = query.options(
            selectinload(Entity.aliases),
            selectinload(Entity.sources),
        ).order_by(desc(Entity.updated_at)).offset(offset).limit(limit)

        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def update_entity(
        self,
        entity_id: uuid.UUID,
        canonical_name: Optional[str] = None,
        description: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        status: Optional[str] = None,
    ) -> Entity:
        entity = await self.get_entity_by_id(entity_id, include_relations=False)
        if not entity:
            raise EntityNotFoundError(f"Entity {entity_id} not found.")

        if canonical_name is not None:
            entity.canonical_name = canonical_name
        if description is not None:
            entity.description = description
        if properties is not None:
            entity.properties = properties
        if confidence is not None:
            entity.confidence = confidence
        if status is not None:
            entity.status = status

        entity.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return entity

    async def archive_entity(self, entity_id: uuid.UUID) -> Entity:
        entity = await self.get_entity_by_id(entity_id, include_relations=False)
        if not entity:
            raise EntityNotFoundError(f"Entity {entity_id} not found.")

        entity.status = EntityStatus.ARCHIVED.value
        entity.updated_at = datetime.now(timezone.utc)

        # Also archive outgoing and incoming relationships
        await self.session.execute(
            update(Relationship)
            .where(
                or_(
                    Relationship.source_entity_id == entity_id,
                    Relationship.target_entity_id == entity_id,
                )
            )
            .values(
                status=RelationshipStatus.ARCHIVED.value,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.session.flush()
        return entity

    # =========================================================================
    # Aliases
    # =========================================================================

    async def add_alias(
        self,
        entity_id: uuid.UUID,
        alias: str,
        source_type: str = "manual",
    ) -> EntityAlias:
        norm = normalize_alias(alias)
        existing = await self.session.execute(
            select(EntityAlias).where(
                EntityAlias.entity_id == entity_id,
                EntityAlias.normalized_alias == norm,
            )
        )
        found = existing.scalar_one_or_none()
        if found:
            return found

        alias_obj = EntityAlias(
            id=uuid.uuid4(),
            entity_id=entity_id,
            alias=alias,
            normalized_alias=norm,
            source_type=source_type,
        )
        self.session.add(alias_obj)
        await self.session.flush()
        return alias_obj

    async def get_entity_by_alias(
        self,
        workspace_id: uuid.UUID,
        alias: str,
        project_id: Optional[uuid.UUID] = None,
    ) -> Optional[Entity]:
        norm = normalize_alias(alias)
        query = (
            select(Entity)
            .join(EntityAlias, Entity.id == EntityAlias.entity_id)
            .where(
                Entity.workspace_id == workspace_id,
                Entity.status == EntityStatus.ACTIVE.value,
                EntityAlias.normalized_alias == norm,
            )
        )
        if project_id:
            query = query.where(or_(Entity.project_id == project_id, Entity.project_id.is_(None)))

        query = query.options(
            selectinload(Entity.aliases),
            selectinload(Entity.sources),
        )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def get_entity_aliases(self, entity_id: uuid.UUID) -> List[EntityAlias]:
        """Returns all alias records for a given entity."""
        query = select(EntityAlias).where(EntityAlias.entity_id == entity_id)
        res = await self.session.execute(query)
        return list(res.scalars().all())

    # =========================================================================
    # Sources
    # =========================================================================

    async def add_source(
        self,
        entity_id: uuid.UUID,
        source_type: str,
        source_id: str,
        source_location: Optional[str] = None,
        content_hash: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EntitySource:
        source = EntitySource(
            id=uuid.uuid4(),
            entity_id=entity_id,
            source_type=source_type,
            source_id=source_id,
            source_location=source_location,
            content_hash=content_hash,
            meta=metadata or {},
        )
        self.session.add(source)

        # Increment source count on entity
        await self.session.execute(
            update(Entity)
            .where(Entity.id == entity_id)
            .values(
                source_count=Entity.source_count + 1,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.session.flush()
        return source

    # =========================================================================
    # Relationships
    # =========================================================================

    async def create_relationship(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        source_entity_id: uuid.UUID,
        relationship_type: str,
        target_entity_id: uuid.UUID,
        properties: Optional[Dict[str, Any]] = None,
        source_reference: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = 1.0,
        valid_from: Optional[datetime] = None,
        valid_to: Optional[datetime] = None,
        project_id: Optional[uuid.UUID] = None,
    ) -> Relationship:
        rel = Relationship(
            id=uuid.uuid4(),
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            source_entity_id=source_entity_id,
            relationship_type=relationship_type,
            target_entity_id=target_entity_id,
            properties=properties or {},
            source_reference=source_reference or {},
            confidence=confidence,
            valid_from=valid_from,
            valid_to=valid_to,
            status=RelationshipStatus.ACTIVE.value,
        )
        self.session.add(rel)
        await self.session.flush()
        return rel

    async def get_relationship_by_id(
        self,
        relationship_id: uuid.UUID,
    ) -> Optional[Relationship]:
        query = select(Relationship).where(Relationship.id == relationship_id).options(
            selectinload(Relationship.source_entity),
            selectinload(Relationship.target_entity),
        )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def get_relationship(
        self,
        workspace_id: uuid.UUID,
        source_id: uuid.UUID,
        relationship_type: str,
        target_id: uuid.UUID,
    ) -> Optional[Relationship]:
        query = select(Relationship).where(
            Relationship.workspace_id == workspace_id,
            Relationship.source_entity_id == source_id,
            Relationship.relationship_type == relationship_type,
            Relationship.target_entity_id == target_id,
            Relationship.status == RelationshipStatus.ACTIVE.value,
        )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def list_relationships(
        self,
        workspace_id: uuid.UUID,
        entity_id: Optional[uuid.UUID] = None,
        relationship_type: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        status: str = RelationshipStatus.ACTIVE.value,
        limit: int = 100,
    ) -> List[Relationship]:
        query = select(Relationship).where(
            Relationship.workspace_id == workspace_id,
            Relationship.status == status,
        )
        if entity_id:
            query = query.where(
                or_(
                    Relationship.source_entity_id == entity_id,
                    Relationship.target_entity_id == entity_id,
                )
            )
        if relationship_type:
            query = query.where(Relationship.relationship_type == relationship_type)
        if project_id:
            query = query.where(or_(Relationship.project_id == project_id, Relationship.project_id.is_(None)))

        query = query.options(
            selectinload(Relationship.source_entity),
            selectinload(Relationship.target_entity),
        ).order_by(desc(Relationship.updated_at)).limit(limit)

        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def update_relationship(
        self,
        relationship_id: uuid.UUID,
        properties: Optional[Dict[str, Any]] = None,
        source_reference: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        valid_from: Optional[datetime] = None,
        valid_to: Optional[datetime] = None,
        status: Optional[str] = None,
    ) -> Relationship:
        rel = await self.get_relationship_by_id(relationship_id)
        if not rel:
            raise RelationshipNotFoundError(f"Relationship {relationship_id} not found.")

        if properties is not None:
            rel.properties = properties
        if source_reference is not None:
            rel.source_reference = source_reference
        if confidence is not None:
            rel.confidence = confidence
        if valid_from is not None:
            rel.valid_from = valid_from
        if valid_to is not None:
            rel.valid_to = valid_to
        if status is not None:
            rel.status = status

        rel.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return rel

    async def archive_relationship(self, relationship_id: uuid.UUID) -> Relationship:
        return await self.update_relationship(relationship_id, status=RelationshipStatus.ARCHIVED.value)

    # =========================================================================
    # Proposals
    # =========================================================================

    async def create_proposal(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        source_id: str,
        proposed_entities: List[Dict[str, Any]],
        proposed_relationships: List[Dict[str, Any]],
        source_type: str = "extraction",
        created_by: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None,
    ) -> GraphChangeProposal:
        proposal = GraphChangeProposal(
            id=uuid.uuid4(),
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            source_id=source_id,
            source_type=source_type,
            proposed_entities=proposed_entities,
            proposed_relationships=proposed_relationships,
            status=ProposalStatus.PENDING.value,
            created_by=created_by,
        )
        self.session.add(proposal)
        await self.session.flush()
        return proposal

    async def get_proposal_by_id(self, proposal_id: uuid.UUID) -> Optional[GraphChangeProposal]:
        query = select(GraphChangeProposal).where(GraphChangeProposal.id == proposal_id)
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def list_proposals(
        self,
        workspace_id: uuid.UUID,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[GraphChangeProposal]:
        query = select(GraphChangeProposal).where(GraphChangeProposal.workspace_id == workspace_id)
        if status:
            query = query.where(GraphChangeProposal.status == status)
        query = query.order_by(desc(GraphChangeProposal.created_at)).limit(limit)
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def update_proposal_status(
        self,
        proposal_id: uuid.UUID,
        status: str,
        reviewed_by: Optional[uuid.UUID] = None,
        reason: Optional[str] = None,
    ) -> GraphChangeProposal:
        proposal = await self.get_proposal_by_id(proposal_id)
        if not proposal:
            raise ProposalNotFoundError(f"Proposal {proposal_id} not found.")

        proposal.status = status
        proposal.reviewed_by = reviewed_by
        proposal.reviewed_at = datetime.now(timezone.utc)
        if reason:
            proposal.rejection_reason = reason
        await self.session.flush()
        return proposal

    # =========================================================================
    # Change Logs
    # =========================================================================

    async def log_change(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        action: str,
        actor_id: Optional[uuid.UUID] = None,
        source_type: str = "manual",
        entity_id: Optional[uuid.UUID] = None,
        relationship_id: Optional[uuid.UUID] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
    ) -> GraphChangeLog:
        log = GraphChangeLog(
            id=uuid.uuid4(),
            organization_id=organization_id,
            workspace_id=workspace_id,
            action=action,
            actor_id=actor_id,
            source_type=source_type,
            entity_id=entity_id,
            relationship_id=relationship_id,
            before_state=before_state,
            after_state=after_state,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def list_change_logs(
        self,
        workspace_id: uuid.UUID,
        entity_id: Optional[uuid.UUID] = None,
        limit: int = 50,
    ) -> List[GraphChangeLog]:
        """Returns audit change logs for a workspace, optionally filtered by entity."""
        query = select(GraphChangeLog).where(GraphChangeLog.workspace_id == workspace_id)
        if entity_id:
            query = query.where(GraphChangeLog.entity_id == entity_id)
        query = query.order_by(desc(GraphChangeLog.created_at)).limit(limit)
        res = await self.session.execute(query)
        return list(res.scalars().all())

    # =========================================================================
    # Conflicts
    # =========================================================================

    async def create_conflict(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        conflict_type: str,
        details: Dict[str, Any],
        entity_id: Optional[uuid.UUID] = None,
        relationship_id: Optional[uuid.UUID] = None,
    ) -> GraphConflict:
        conflict = GraphConflict(
            id=uuid.uuid4(),
            organization_id=organization_id,
            workspace_id=workspace_id,
            entity_id=entity_id,
            relationship_id=relationship_id,
            conflict_type=conflict_type,
            details=details,
            status=ConflictStatus.OPEN.value,
        )
        self.session.add(conflict)
        await self.session.flush()
        return conflict

    async def get_conflict_by_id(self, conflict_id: uuid.UUID) -> Optional[GraphConflict]:
        query = select(GraphConflict).where(GraphConflict.id == conflict_id)
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def list_conflicts(
        self,
        workspace_id: uuid.UUID,
        status: Optional[str] = ConflictStatus.OPEN.value,
        limit: int = 50,
    ) -> List[GraphConflict]:
        query = select(GraphConflict).where(GraphConflict.workspace_id == workspace_id)
        if status:
            query = query.where(GraphConflict.status == status)
        query = query.order_by(desc(GraphConflict.created_at)).limit(limit)
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def resolve_conflict(
        self,
        conflict_id: uuid.UUID,
        resolved_by: Optional[uuid.UUID] = None,
        resolution_action: str = "resolve",
        notes: Optional[str] = None,
    ) -> GraphConflict:
        conflict = await self.get_conflict_by_id(conflict_id)
        if not conflict:
            raise ConflictNotFoundError(f"Conflict {conflict_id} not found.")

        conflict.status = ConflictStatus.RESOLVED.value if resolution_action != "dismiss" else ConflictStatus.DISMISSED.value
        conflict.resolved_at = datetime.now(timezone.utc)
        conflict.resolved_by = resolved_by
        if notes:
            details = dict(conflict.details or {})
            details["resolution_notes"] = notes
            conflict.details = details
        await self.session.flush()
        return conflict

    # =========================================================================
    # Knowledge Map Summary
    # =========================================================================

    async def get_project_knowledge_summary(
        self,
        workspace_id: uuid.UUID,
        project_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, Any]:
        e_filter = [Entity.workspace_id == workspace_id, Entity.status == EntityStatus.ACTIVE.value]
        r_filter = [Relationship.workspace_id == workspace_id, Relationship.status == RelationshipStatus.ACTIVE.value]
        if project_id:
            e_filter.append(or_(Entity.project_id == project_id, Entity.project_id.is_(None)))
            r_filter.append(or_(Relationship.project_id == project_id, Relationship.project_id.is_(None)))

        # Total entities
        e_count_query = select(func.count(Entity.id)).where(*e_filter)
        entity_count = (await self.session.execute(e_count_query)).scalar_one()

        # Total relationships
        r_count_query = select(func.count(Relationship.id)).where(*r_filter)
        relationship_count = (await self.session.execute(r_count_query)).scalar_one()

        # Pending proposals
        prop_query = select(func.count(GraphChangeProposal.id)).where(
            GraphChangeProposal.workspace_id == workspace_id,
            GraphChangeProposal.status == ProposalStatus.PENDING.value,
        )
        proposals_count = (await self.session.execute(prop_query)).scalar_one()

        # Open conflicts
        conf_query = select(func.count(GraphConflict.id)).where(
            GraphConflict.workspace_id == workspace_id,
            GraphConflict.status == ConflictStatus.OPEN.value,
        )
        conflicts_count = (await self.session.execute(conf_query)).scalar_one()

        # Counts by entity_type
        type_query = select(Entity.entity_type, func.count(Entity.id)).where(*e_filter).group_by(Entity.entity_type)
        type_res = await self.session.execute(type_query)
        entity_type_counts = {row[0]: row[1] for row in type_res.all()}

        # Counts by relationship_type
        rel_type_query = select(Relationship.relationship_type, func.count(Relationship.id)).where(*r_filter).group_by(Relationship.relationship_type)
        rel_res = await self.session.execute(rel_type_query)
        relationship_type_counts = {row[0]: row[1] for row in rel_res.all()}

        return {
            "entity_count": entity_count,
            "relationship_count": relationship_count,
            "pending_proposals_count": proposals_count,
            "open_conflicts_count": conflicts_count,
            "entity_type_counts": entity_type_counts,
            "relationship_type_counts": relationship_type_counts,
        }
