"""
Bounded Traversal Engine for Knowledge Graph.
Performs breadth-first traversal up to 3 hops with cycle prevention, tenant bounding, and temporal filtering.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.services.knowledge_graph.constants import (
    GRAPH_DEFAULT_HOPS,
    GRAPH_MAX_ENTITIES,
    GRAPH_MAX_HOPS,
    GRAPH_MAX_RELATIONSHIPS,
    RelationshipStatus,
)
from backend.app.services.knowledge_graph.models import Entity, Relationship


@dataclass
class TraversalResult:
    """Result object returned by GraphTraversalEngine.traverse()."""
    entities: List[Entity] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    retrieval_metadata: Dict[str, Any] = field(default_factory=dict)


class GraphTraversalEngine:
    """
    Executes bounded multi-hop traversals over the relational property graph.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def traverse(
        self,
        workspace_id: uuid.UUID,
        seed_entity_ids: List[uuid.UUID],
        max_hops: int = GRAPH_DEFAULT_HOPS,
        max_entities: int = 50,
        max_relationships: int = 100,
        entity_types: Optional[List[str]] = None,
        relationship_types: Optional[List[str]] = None,
        project_id: Optional[uuid.UUID] = None,
        authorized_project_ids: Optional[Set[uuid.UUID]] = None,
        include_temporal_expired: bool = False,
        direction: str = "outgoing",
    ) -> TraversalResult:
        """
        Performs bounded BFS traversal starting from seed entities.
        Returns a TraversalResult with .entities, .relationships, and .retrieval_metadata.
        """
        effective_hops = min(max(1, max_hops), GRAPH_MAX_HOPS)
        entity_cap = min(max_entities, GRAPH_MAX_ENTITIES)
        relationship_cap = min(max_relationships, GRAPH_MAX_RELATIONSHIPS)

        if not seed_entity_ids:
            return TraversalResult(
                retrieval_metadata={
                    "hops": effective_hops,
                    "entity_cap": entity_cap,
                    "relationship_cap": relationship_cap,
                }
            )

        visited_entity_ids: Set[uuid.UUID] = set(seed_entity_ids)
        visited_relationship_ids: Set[uuid.UUID] = set()

        collected_entities: Dict[uuid.UUID, Entity] = {}
        collected_relationships: List[Relationship] = []

        # Load seed entities
        seeds_query = select(Entity).where(
            Entity.id.in_(seed_entity_ids),
            Entity.workspace_id == workspace_id,
            Entity.status == "active",
        ).options(
            selectinload(Entity.aliases),
            selectinload(Entity.sources),
        )
        seeds_res = await self.session.execute(seeds_query)
        for e in seeds_res.scalars().all():
            if authorized_project_ids is not None and e.project_id and e.project_id not in authorized_project_ids:
                continue
            collected_entities[e.id] = e

        current_frontier = set(collected_entities.keys())
        now = datetime.now(timezone.utc)

        for hop in range(effective_hops):
            if not current_frontier or len(collected_entities) >= entity_cap or len(collected_relationships) >= relationship_cap:
                break

            if direction == "incoming":
                cond = Relationship.target_entity_id.in_(current_frontier)
            elif direction in ("both", "undirected"):
                cond = or_(
                    Relationship.source_entity_id.in_(current_frontier),
                    Relationship.target_entity_id.in_(current_frontier),
                )
            else:  # "outgoing" default
                cond = Relationship.source_entity_id.in_(current_frontier)

            # Find relationships adjacent to current frontier
            rel_query = select(Relationship).where(
                Relationship.workspace_id == workspace_id,
                Relationship.status == RelationshipStatus.ACTIVE.value,
                cond,
            ).options(
                selectinload(Relationship.source_entity),
                selectinload(Relationship.target_entity),
            )

            if relationship_types:
                rel_query = rel_query.where(Relationship.relationship_type.in_(relationship_types))

            if project_id:
                rel_query = rel_query.where(or_(Relationship.project_id == project_id, Relationship.project_id.is_(None)))

            if not include_temporal_expired:
                rel_query = rel_query.where(
                    or_(Relationship.valid_to.is_(None), Relationship.valid_to >= now)
                )

            rels_res = await self.session.execute(rel_query)
            active_rels = list(rels_res.scalars().all())

            next_frontier: Set[uuid.UUID] = set()

            for rel in active_rels:
                if rel.id in visited_relationship_ids:
                    continue

                # Project restriction check on relationship
                if authorized_project_ids is not None and rel.project_id and rel.project_id not in authorized_project_ids:
                    continue

                visited_relationship_ids.add(rel.id)
                collected_relationships.append(rel)

                if len(collected_relationships) >= relationship_cap:
                    break

                # Expand to neighbors according to direction
                if direction == "incoming":
                    neighbors = [rel.source_entity_id]
                elif direction in ("both", "undirected"):
                    neighbors = [rel.source_entity_id, rel.target_entity_id]
                else:  # "outgoing"
                    neighbors = [rel.target_entity_id]

                for neighbor_id in neighbors:
                    if neighbor_id not in visited_entity_ids:
                        next_frontier.add(neighbor_id)
                        visited_entity_ids.add(neighbor_id)

            if not next_frontier:
                break

            # Fetch next level entities
            next_query = select(Entity).where(
                Entity.id.in_(next_frontier),
                Entity.workspace_id == workspace_id,
                Entity.status == "active",
            ).options(
                selectinload(Entity.aliases),
                selectinload(Entity.sources),
            )
            if entity_types:
                next_query = next_query.where(Entity.entity_type.in_(entity_types))

            next_res = await self.session.execute(next_query)
            valid_next = next_res.scalars().all()

            current_frontier = set()
            for entity in valid_next:
                if authorized_project_ids is not None and entity.project_id and entity.project_id not in authorized_project_ids:
                    continue

                collected_entities[entity.id] = entity
                current_frontier.add(entity.id)
                if len(collected_entities) >= entity_cap:
                    break

        return TraversalResult(
            entities=list(collected_entities.values()),
            relationships=collected_relationships,
            retrieval_metadata={
                "hops": effective_hops,
                "entities_collected": len(collected_entities),
                "relationships_collected": len(collected_relationships),
                "entity_cap": entity_cap,
                "relationship_cap": relationship_cap,
            },
        )
