"""
Entity Service for Knowledge Graph.
Manages Entity creation, updates, aliases, sources, searches, and safe entity merging.
"""
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.knowledge_graph.constants import (
    ALLOWED_ENTITY_TYPES,
    ChangeLogAction,
    EntityStatus,
    RelationshipStatus,
)
from backend.app.services.knowledge_graph.errors import (
    EntityMergeError,
    EntityNotFoundError,
    InvalidEntityTypeError,
)
from backend.app.services.knowledge_graph.models import Entity, EntityAlias, EntitySource, Relationship
from backend.app.services.knowledge_graph.normalization import (
    normalize_alias,
    normalize_entity_name,
    normalize_entity_type,
)
from backend.app.services.knowledge_graph.repository import KnowledgeGraphRepository
from backend.app.services.knowledge_graph.sanitizer import sanitize_properties, sanitize_source_metadata
from backend.app.services.knowledge_graph.schemas import (
    EntityCreateRequest,
    EntityMergeRequest,
    EntityMergeResponse,
    EntityResponse,
    EntityUpdateRequest,
)


class EntityService:
    """
    Business logic for Entity assets, aliases, provenance, and merging.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = KnowledgeGraphRepository(session)

    async def create_entity(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        request: EntityCreateRequest,
        actor_id: Optional[uuid.UUID] = None,
    ) -> EntityResponse:
        norm_type = normalize_entity_type(request.entity_type)
        if norm_type not in ALLOWED_ENTITY_TYPES:
            raise InvalidEntityTypeError(
                f"Entity type '{request.entity_type}' is not recognized in controlled registry."
            )

        sanitized_props = sanitize_properties(request.properties)

        entity = await self.repo.create_entity(
            organization_id=organization_id,
            workspace_id=workspace_id,
            entity_type=norm_type,
            canonical_name=request.canonical_name.strip(),
            description=request.description,
            properties=sanitized_props,
            confidence=request.confidence,
            project_id=request.project_id,
        )

        # Add aliases if provided
        for alias in request.aliases:
            if alias.strip():
                await self.repo.add_alias(entity.id, alias.strip(), source_type=request.source_type)

        # Add source reference if provided
        if request.source_id:
            sanitized_meta = sanitize_source_metadata(request.source_metadata)
            await self.repo.add_source(
                entity_id=entity.id,
                source_type=request.source_type,
                source_id=request.source_id,
                metadata=sanitized_meta,
            )

        # Log change
        await self.repo.log_change(
            organization_id=organization_id,
            workspace_id=workspace_id,
            action=ChangeLogAction.CREATED.value,
            actor_id=actor_id,
            source_type=request.source_type,
            entity_id=entity.id,
            after_state={"canonical_name": entity.canonical_name, "type": entity.entity_type},
        )

        # Reload full entity with relations
        reloaded = await self.repo.get_entity_by_id(entity.id)
        return EntityResponse.model_validate(reloaded)

    async def get_entity(
        self,
        entity_id: uuid.UUID,
        organization_id: Optional[uuid.UUID] = None,
        workspace_id: Optional[uuid.UUID] = None,
    ) -> Optional[EntityResponse]:
        entity = await self.repo.get_entity_by_id(entity_id)
        if not entity:
            return None
        # Tenant isolation: if caller supplies org/workspace context, enforce boundary
        if organization_id is not None and entity.organization_id != organization_id:
            return None
        if workspace_id is not None and entity.workspace_id != workspace_id:
            return None
        return EntityResponse.model_validate(entity)

    async def update_entity(
        self,
        entity_id: uuid.UUID,
        request: EntityUpdateRequest,
        organization_id: Optional[uuid.UUID] = None,
        workspace_id: Optional[uuid.UUID] = None,
        actor_id: Optional[uuid.UUID] = None,
    ) -> EntityResponse:
        existing = await self.repo.get_entity_by_id(entity_id)
        if not existing:
            raise EntityNotFoundError(f"Entity {entity_id} not found.")
        if organization_id is not None and existing.organization_id != organization_id:
            raise EntityNotFoundError(f"Entity {entity_id} not found for the given organization.")
        if workspace_id is not None and existing.workspace_id != workspace_id:
            raise EntityNotFoundError(f"Entity {entity_id} not found for the given workspace.")

        before_state = {
            "canonical_name": existing.canonical_name,
            "description": existing.description,
            "properties": existing.properties,
            "confidence": existing.confidence,
            "status": existing.status,
        }

        sanitized_props = sanitize_properties(request.properties) if request.properties is not None else None

        updated = await self.repo.update_entity(
            entity_id=entity_id,
            canonical_name=request.canonical_name.strip() if request.canonical_name else None,
            description=request.description,
            properties=sanitized_props,
            confidence=request.confidence,
            status=request.status,
        )

        await self.repo.log_change(
            organization_id=updated.organization_id,
            workspace_id=updated.workspace_id,
            action=ChangeLogAction.UPDATED.value,
            actor_id=actor_id,
            entity_id=updated.id,
            before_state=before_state,
            after_state={
                "canonical_name": updated.canonical_name,
                "description": updated.description,
                "properties": updated.properties,
                "confidence": updated.confidence,
                "status": updated.status,
            },
        )

        reloaded = await self.repo.get_entity_by_id(updated.id)
        return EntityResponse.model_validate(reloaded)

    async def archive_entity(
        self,
        entity_id: uuid.UUID,
        organization_id: Optional[uuid.UUID] = None,
        workspace_id: Optional[uuid.UUID] = None,
        actor_id: Optional[uuid.UUID] = None,
    ) -> bool:
        entity = await self.repo.get_entity_by_id(entity_id)
        if not entity:
            raise EntityNotFoundError(f"Entity {entity_id} not found.")
        if organization_id is not None and entity.organization_id != organization_id:
            raise EntityNotFoundError(f"Entity {entity_id} not found for the given organization.")
        if workspace_id is not None and entity.workspace_id != workspace_id:
            raise EntityNotFoundError(f"Entity {entity_id} not found for the given workspace.")

        archived = await self.repo.archive_entity(entity_id)

        await self.repo.log_change(
            organization_id=archived.organization_id,
            workspace_id=archived.workspace_id,
            action=ChangeLogAction.ARCHIVED.value,
            actor_id=actor_id,
            entity_id=archived.id,
        )
        return True

    async def search_entities(
        self,
        workspace_id: uuid.UUID,
        query: str,
        entity_type: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        limit: int = 20,
    ) -> List[EntityResponse]:
        entities = await self.repo.search_entities(
            workspace_id=workspace_id,
            query_str=query,
            entity_type=entity_type,
            project_id=project_id,
            limit=limit,
        )
        return [EntityResponse.model_validate(e) for e in entities]

    async def list_entities(
        self,
        workspace_id: uuid.UUID,
        entity_type: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        status: str = EntityStatus.ACTIVE.value,
        limit: int = 50,
        offset: int = 0,
    ) -> List[EntityResponse]:
        entities = await self.repo.list_entities(
            workspace_id=workspace_id,
            entity_type=entity_type,
            project_id=project_id,
            status=status,
            limit=limit,
            offset=offset,
        )
        return [EntityResponse.model_validate(e) for e in entities]

    async def merge_entities(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        request: EntityMergeRequest,
        actor_id: Optional[uuid.UUID] = None,
    ) -> EntityMergeResponse:
        """
        Safely merges a duplicate entity into a primary (canonical) entity.
        """
        primary_id = request.primary_entity_id
        duplicate_id = request.duplicate_entity_id

        if primary_id == duplicate_id:
            raise EntityMergeError("Cannot merge an entity into itself.")

        source = await self.repo.get_entity_by_id(duplicate_id)
        if not source:
            raise EntityNotFoundError(f"Duplicate entity {duplicate_id} not found.")

        target = await self.repo.get_entity_by_id(primary_id)
        if not target:
            raise EntityNotFoundError(f"Primary entity {primary_id} not found.")

        if source.organization_id != target.organization_id:
            raise EntityMergeError("Cannot merge entities across different organizations.")

        if source.entity_type != target.entity_type:
            raise EntityMergeError(
                f"Cannot merge incompatible entity types ('{source.entity_type}' vs '{target.entity_type}')."
            )

        # 1. Transfer outgoing relationships
        rel_out = await self.session.execute(
            select(Relationship).where(
                Relationship.source_entity_id == source.id,
                Relationship.status == RelationshipStatus.ACTIVE.value,
            )
        )
        outgoing_rels = list(rel_out.scalars().all())
        transferred_rels = 0
        for r in outgoing_rels:
            # Check if target already has this outgoing relationship to avoiding duplicates
            existing = await self.repo.get_relationship(
                workspace_id=target.workspace_id,
                source_id=target.id,
                relationship_type=r.relationship_type,
                target_id=r.target_entity_id,
            )
            if not existing and r.target_entity_id != target.id:
                r.source_entity_id = target.id
                transferred_rels += 1
            else:
                r.status = RelationshipStatus.ARCHIVED.value

        # 2. Transfer incoming relationships
        rel_in = await self.session.execute(
            select(Relationship).where(
                Relationship.target_entity_id == source.id,
                Relationship.status == RelationshipStatus.ACTIVE.value,
            )
        )
        incoming_rels = list(rel_in.scalars().all())
        for r in incoming_rels:
            existing = await self.repo.get_relationship(
                workspace_id=target.workspace_id,
                source_id=r.source_entity_id,
                relationship_type=r.relationship_type,
                target_id=target.id,
            )
            if not existing and r.source_entity_id != target.id:
                r.target_entity_id = target.id
                transferred_rels += 1
            else:
                r.status = RelationshipStatus.ARCHIVED.value

        # 3. Transfer aliases & add source canonical name as an alias
        await self.repo.add_alias(target.id, source.canonical_name, source_type="merge")
        transferred_aliases = 1

        aliases_query = select(EntityAlias).where(EntityAlias.entity_id == source.id)
        source_aliases = (await self.session.execute(aliases_query)).scalars().all()
        for a in source_aliases:
            await self.repo.add_alias(target.id, a.alias, source_type=a.source_type)
            transferred_aliases += 1

        # 4. Transfer sources
        sources_query = select(EntitySource).where(EntitySource.entity_id == source.id)
        source_records = (await self.session.execute(sources_query)).scalars().all()
        for s in source_records:
            s.entity_id = target.id

        target.source_count += len(source_records)

        # 5. Archive source entity
        source.status = EntityStatus.ARCHIVED.value

        # 6. Audit log
        await self.repo.log_change(
            organization_id=target.organization_id,
            workspace_id=target.workspace_id,
            action=ChangeLogAction.MERGED.value,
            actor_id=actor_id,
            entity_id=target.id,
            before_state={"merged_from_id": str(source.id), "merged_from_name": source.canonical_name},
            after_state={"target_id": str(target.id), "target_name": target.canonical_name},
        )

        await self.session.flush()

        reloaded_target = await self.repo.get_entity_by_id(target.id)
        return EntityMergeResponse(
            canonical_entity=EntityResponse.model_validate(reloaded_target),
            archived_entity_id=source.id,
            transferred_relationships_count=transferred_rels,
            transferred_aliases_count=transferred_aliases,
        )
