"""
Graph Retriever for Knowledge Graph.
Performs deterministic entity linking from task/query text, executes bounded traversal,
and produces a normalized GraphContextResult.
"""
import re
import uuid
from typing import Any, Dict, List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.knowledge_graph.models import Entity, Relationship
from backend.app.services.knowledge_graph.normalization import normalize_entity_name
from backend.app.services.knowledge_graph.repository import KnowledgeGraphRepository
from backend.app.services.knowledge_graph.schemas import (
    EntityResponse,
    GraphContextResult,
    RelationshipResponse,
)
from backend.app.services.knowledge_graph.traversal import GraphTraversalEngine


class GraphRetriever:
    """
    Retrieves structured graph subgraphs relevant to a query or explicit entity seeds.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = KnowledgeGraphRepository(session)
        self.traversal = GraphTraversalEngine(session)

    async def link_entities_from_text(
        self,
        workspace_id: uuid.UUID,
        text: str,
        project_id: Optional[uuid.UUID] = None,
        max_seeds: int = 5,
    ) -> List[uuid.UUID]:
        """
        Deterministic entity linking: extracts potential candidate terms from query text
        and checks for exact or alias matches in the workspace.
        """
        if not text or not text.strip():
            return []

        linked_ids: List[uuid.UUID] = []
        seen_ids: Set[uuid.UUID] = set()

        # 1. Clean tokens & phrases (1-word, 2-word, 3-word n-grams)
        words = re.findall(r"\b[A-Za-z0-9_\-\.]{2,}\b", text)
        phrases: List[str] = []

        # Unigrams
        for w in words:
            if len(w) >= 3 and w.lower() not in {"what", "which", "where", "how", "the", "and", "for", "with", "this", "that", "from"}:
                phrases.append(w)

        # Bigrams
        for i in range(len(words) - 1):
            phrases.append(f"{words[i]} {words[i+1]}")

        # Search graph for matching entities
        for phrase in phrases:
            matched = await self.repo.get_entity_by_name(workspace_id, phrase, project_id=project_id)
            if not matched:
                matched = await self.repo.get_entity_by_alias(workspace_id, phrase, project_id=project_id)

            if matched and matched.id not in seen_ids:
                seen_ids.add(matched.id)
                linked_ids.append(matched.id)
                if len(linked_ids) >= max_seeds:
                    break

        return linked_ids

    async def retrieve(
        self,
        workspace_id: uuid.UUID,
        query: Optional[str] = None,
        seed_entities: Optional[List[uuid.UUID]] = None,
        seed_names: Optional[List[str]] = None,
        entity_types: Optional[List[str]] = None,
        relationship_types: Optional[List[str]] = None,
        max_hops: int = 1,
        max_entities: int = 50,
        max_relationships: int = 100,
        project_id: Optional[uuid.UUID] = None,
        authorized_project_ids: Optional[Set[uuid.UUID]] = None,
        include_temporal_expired: bool = False,
    ) -> GraphContextResult:
        """
        Main retrieval method: links entities, executes bounded BFS traversal,
        and packs the resulting subgraph into GraphContextResult.
        """
        all_seed_ids: List[uuid.UUID] = list(seed_entities or [])
        seen_seeds: Set[uuid.UUID] = set(all_seed_ids)

        # 1. Resolve seed names if provided
        if seed_names:
            for s_name in seed_names:
                e = await self.repo.get_entity_by_name(workspace_id, s_name, project_id=project_id)
                if not e:
                    e = await self.repo.get_entity_by_alias(workspace_id, s_name, project_id=project_id)
                if e and e.id not in seen_seeds:
                    seen_seeds.add(e.id)
                    all_seed_ids.append(e.id)

        # 2. Extract entities from query text if seeds are empty
        if not all_seed_ids and query:
            linked = await self.link_entities_from_text(workspace_id, query, project_id=project_id)
            for l_id in linked:
                if l_id not in seen_seeds:
                    seen_seeds.add(l_id)
                    all_seed_ids.append(l_id)

        if not all_seed_ids:
            return GraphContextResult(
                entities=[],
                relationships=[],
                source_references=[],
                retrieval_metadata={"status": "no_seeds_found", "query": query},
                token_estimate=0,
            )

        # 3. Execute bounded traversal
        traversal_result = await self.traversal.traverse(
            workspace_id=workspace_id,
            seed_entity_ids=all_seed_ids,
            max_hops=max_hops,
            max_entities=max_entities,
            max_relationships=max_relationships,
            entity_types=entity_types,
            relationship_types=relationship_types,
            project_id=project_id,
            authorized_project_ids=authorized_project_ids,
            include_temporal_expired=include_temporal_expired,
        )
        entities = traversal_result.entities
        relationships = traversal_result.relationships

        # 4. Format responses
        entity_responses: List[EntityResponse] = [EntityResponse.model_validate(e) for e in entities]
        entity_name_map = {e.id: e.canonical_name for e in entities}

        rel_responses: List[RelationshipResponse] = []
        for r in relationships:
            r_resp = RelationshipResponse.model_validate(r)
            r_resp.source_entity_name = entity_name_map.get(r.source_entity_id, "Unknown")
            r_resp.target_entity_name = entity_name_map.get(r.target_entity_id, "Unknown")
            rel_responses.append(r_resp)

        # Collect source references
        all_sources: List[Dict[str, Any]] = []
        for e in entities:
            for s in getattr(e, "sources", []):
                all_sources.append({
                    "entity_id": str(e.id),
                    "entity_name": e.canonical_name,
                    "source_type": s.source_type,
                    "source_id": s.source_id,
                    "location": s.source_location,
                })

        # Token estimate (approx 4 characters per token)
        total_chars = sum(len(e.canonical_name) + len(e.description or "") for e in entities)
        total_chars += sum(len(r.relationship_type) + len(r.source_entity_name or "") + len(r.target_entity_name or "") for r in rel_responses)
        token_estimate = max(1, total_chars // 4)

        return GraphContextResult(
            entities=entity_responses,
            relationships=rel_responses,
            source_references=all_sources,
            retrieval_metadata={
                "seed_count": len(all_seed_ids),
                "hops": max_hops,
                "entity_count": len(entity_responses),
                "relationship_count": len(rel_responses),
            },
            token_estimate=token_estimate,
        )
