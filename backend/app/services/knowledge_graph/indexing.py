"""
Query optimization and indexing helpers for the Knowledge Graph relational property model.
Optimizes neighbor lookups, type filtering, and canonical name search.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from backend.app.services.knowledge_graph.models import Entity, Relationship


def build_neighbor_query(
    entity_id: UUID,
    workspace_id: UUID,
    relationship_types: Optional[List[str]] = None,
    include_expired: bool = False,
):
    """
    Builds an optimized query to fetch outgoing and incoming edges for an entity.
    Leverages composite indexes on (source_entity_id, relationship_type) and (target_entity_id, relationship_type).
    """
    query = select(Relationship).where(
        Relationship.workspace_id == workspace_id,
        Relationship.status == "active",
        or_(
            Relationship.source_entity_id == entity_id,
            Relationship.target_entity_id == entity_id,
        )
    ).options(
        selectinload(Relationship.source_entity),
        selectinload(Relationship.target_entity),
    )

    if relationship_types:
        query = query.where(Relationship.relationship_type.in_(relationship_types))

    return query
