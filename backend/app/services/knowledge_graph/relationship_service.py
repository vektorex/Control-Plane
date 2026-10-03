"""
Relationship Service for Knowledge Graph.
Enforces edge integrity, controlled relationship types, anti-self-loop rules, and temporal constraints.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.knowledge_graph.constants import (
    ALLOWED_RELATIONSHIP_TYPES,
    ChangeLogAction,
    RelationshipStatus,
)
from backend.app.services.knowledge_graph.errors import (
    CrossTenantGraphError,
    DanglingEntityError,
    InvalidRelationshipTypeError,
    RelationshipNotFoundError,
    SelfRelationshipError,
)
from backend.app.services.knowledge_graph.models import Relationship
from backend.app.services.knowledge_graph.repository import KnowledgeGraphRepository
from backend.app.services.knowledge_graph.sanitizer import sanitize_properties, sanitize_source_metadata
from backend.app.services.knowledge_graph.schemas import (
    RelationshipCreateRequest,
    RelationshipResponse,
    RelationshipUpdateRequest,
)


class RelationshipService:
    """
    Business logic and constraints for graph edges.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = KnowledgeGraphRepository(session)

    async def create_relationship(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        request: RelationshipCreateRequest,
        actor_id: Optional[uuid.UUID] = None,
    ) -> RelationshipResponse:
        # 1. Reject self-relationships
        if request.source_entity_id == request.target_entity_id:
            raise SelfRelationshipError("Self-relationships are not permitted in this graph configuration.")

        # 2. Validate relationship type
        rel_type = request.relationship_type.strip().lower()
        if rel_type not in ALLOWED_RELATIONSHIP_TYPES:
            raise InvalidRelationshipTypeError(
                f"Relationship type '{request.relationship_type}' is not recognized in controlled registry."
            )

        # 3. Validate source & target entities exist and belong to the same tenant scope
        source_entity = await self.repo.get_entity_by_id(request.source_entity_id, include_relations=False)
        if not source_entity or source_entity.status != "active":
            raise DanglingEntityError(f"Source entity {request.source_entity_id} does not exist or is archived.")

        target_entity = await self.repo.get_entity_by_id(request.target_entity_id, include_relations=False)
        if not target_entity or target_entity.status != "active":
            raise DanglingEntityError(f"Target entity {request.target_entity_id} does not exist or is archived.")

        if source_entity.organization_id != organization_id or target_entity.organization_id != organization_id:
            raise CrossTenantGraphError("Cannot create relationships across organization boundaries.")

        if source_entity.workspace_id != workspace_id or target_entity.workspace_id != workspace_id:
            raise CrossTenantGraphError("Cannot create relationships across workspace boundaries.")

        # 4. Validate temporal bounds
        if request.valid_from and request.valid_to and request.valid_from > request.valid_to:
            raise InvalidRelationshipTypeError("valid_from timestamp cannot be later than valid_to timestamp.")

        sanitized_props = sanitize_properties(request.properties)
        sanitized_ref = sanitize_source_metadata(request.source_reference)

        rel = await self.repo.create_relationship(
            organization_id=organization_id,
            workspace_id=workspace_id,
            source_entity_id=request.source_entity_id,
            relationship_type=rel_type,
            target_entity_id=request.target_entity_id,
            properties=sanitized_props,
            source_reference=sanitized_ref,
            confidence=request.confidence,
            valid_from=request.valid_from,
            valid_to=request.valid_to,
            project_id=request.project_id or source_entity.project_id,
        )

        await self.repo.log_change(
            organization_id=organization_id,
            workspace_id=workspace_id,
            action=ChangeLogAction.RELATIONSHIP_CREATED.value,
            actor_id=actor_id,
            relationship_id=rel.id,
            after_state={
                "source": str(rel.source_entity_id),
                "type": rel.relationship_type,
                "target": str(rel.target_entity_id),
            },
        )

        resp = RelationshipResponse.model_validate(rel)
        resp.source_entity_name = source_entity.canonical_name
        resp.target_entity_name = target_entity.canonical_name
        return resp

    async def get_relationship(self, relationship_id: uuid.UUID) -> RelationshipResponse:
        rel = await self.repo.get_relationship_by_id(relationship_id)
        if not rel:
            raise RelationshipNotFoundError(f"Relationship {relationship_id} not found.")

        resp = RelationshipResponse.model_validate(rel)
        if rel.source_entity:
            resp.source_entity_name = rel.source_entity.canonical_name
        if rel.target_entity:
            resp.target_entity_name = rel.target_entity.canonical_name
        return resp

    async def list_relationships(
        self,
        workspace_id: uuid.UUID,
        entity_id: Optional[uuid.UUID] = None,
        relationship_type: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        status: str = RelationshipStatus.ACTIVE.value,
        limit: int = 100,
    ) -> List[RelationshipResponse]:
        rels = await self.repo.list_relationships(
            workspace_id=workspace_id,
            entity_id=entity_id,
            relationship_type=relationship_type,
            project_id=project_id,
            status=status,
            limit=limit,
        )
        results = []
        for r in rels:
            resp = RelationshipResponse.model_validate(r)
            if r.source_entity:
                resp.source_entity_name = r.source_entity.canonical_name
            if r.target_entity:
                resp.target_entity_name = r.target_entity.canonical_name
            results.append(resp)
        return results

    async def update_relationship(
        self,
        relationship_id: uuid.UUID,
        request: RelationshipUpdateRequest,
        actor_id: Optional[uuid.UUID] = None,
    ) -> RelationshipResponse:
        existing = await self.repo.get_relationship_by_id(relationship_id)
        if not existing:
            raise RelationshipNotFoundError(f"Relationship {relationship_id} not found.")

        before_state = {
            "properties": existing.properties,
            "source_reference": existing.source_reference,
            "confidence": existing.confidence,
            "valid_from": existing.valid_from.isoformat() if existing.valid_from else None,
            "valid_to": existing.valid_to.isoformat() if existing.valid_to else None,
            "status": existing.status,
        }

        # Check temporal bounds
        vf = request.valid_from if request.valid_from is not None else existing.valid_from
        vt = request.valid_to if request.valid_to is not None else existing.valid_to
        if vf and vt and vf > vt:
            raise InvalidRelationshipTypeError("valid_from timestamp cannot be later than valid_to timestamp.")

        sanitized_props = sanitize_properties(request.properties) if request.properties is not None else None
        sanitized_ref = sanitize_source_metadata(request.source_reference) if request.source_reference is not None else None

        updated = await self.repo.update_relationship(
            relationship_id=relationship_id,
            properties=sanitized_props,
            source_reference=sanitized_ref,
            confidence=request.confidence,
            valid_from=request.valid_from,
            valid_to=request.valid_to,
            status=request.status,
        )

        await self.repo.log_change(
            organization_id=updated.organization_id,
            workspace_id=updated.workspace_id,
            action=ChangeLogAction.UPDATED.value,
            actor_id=actor_id,
            relationship_id=updated.id,
            before_state=before_state,
            after_state={
                "properties": updated.properties,
                "confidence": updated.confidence,
                "status": updated.status,
            },
        )

        reloaded = await self.repo.get_relationship_by_id(updated.id)
        resp = RelationshipResponse.model_validate(reloaded)
        if reloaded.source_entity:
            resp.source_entity_name = reloaded.source_entity.canonical_name
        if reloaded.target_entity:
            resp.target_entity_name = reloaded.target_entity.canonical_name
        return resp

    async def archive_relationship(
        self,
        relationship_id: uuid.UUID,
        actor_id: Optional[uuid.UUID] = None,
    ) -> RelationshipResponse:
        rel = await self.repo.get_relationship_by_id(relationship_id)
        if not rel:
            raise RelationshipNotFoundError(f"Relationship {relationship_id} not found.")

        archived = await self.repo.archive_relationship(relationship_id)

        await self.repo.log_change(
            organization_id=archived.organization_id,
            workspace_id=archived.workspace_id,
            action=ChangeLogAction.RELATIONSHIP_REMOVED.value,
            actor_id=actor_id,
            relationship_id=archived.id,
        )

        reloaded = await self.repo.get_relationship_by_id(archived.id)
        resp = RelationshipResponse.model_validate(reloaded)
        return resp
