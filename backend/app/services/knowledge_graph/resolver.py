"""
Entity Resolver for Knowledge Graph.
Performs deterministic canonical name normalization, alias matching, bounded similarity checks,
and ambiguity detection without silent merging.
"""
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.knowledge_graph.constants import ConflictType, EntityStatus
from backend.app.services.knowledge_graph.models import Entity
from backend.app.services.knowledge_graph.normalization import (
    compute_string_similarity,
    normalize_alias,
    normalize_entity_name,
    normalize_entity_type,
)
from backend.app.services.knowledge_graph.repository import KnowledgeGraphRepository
from backend.app.services.knowledge_graph.sanitizer import sanitize_properties, sanitize_source_metadata
from backend.app.services.knowledge_graph.schemas import EntityCreateRequest, EntityResponse


class EntityResolver:
    """
    Resolves raw entity names and types to canonical graph entities.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = KnowledgeGraphRepository(session)

    async def resolve_or_create_entity(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        raw_name: str,
        entity_type: str,
        description: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        aliases: Optional[List[str]] = None,
        source_type: str = "manual",
        source_id: Optional[str] = None,
        source_location: Optional[str] = None,
        content_hash: Optional[str] = None,
        source_metadata: Optional[Dict[str, Any]] = None,
        project_id: Optional[uuid.UUID] = None,
        confidence: Optional[float] = 1.0,
    ) -> Tuple[EntityResponse, bool]:
        """
        Resolves an entity through canonical name, aliases, or bounded similarity.
        Returns: (EntityResponse, was_created_bool)
        """
        norm_name = normalize_entity_name(raw_name)
        norm_type = normalize_entity_type(entity_type)

        # 1. Exact match on canonical name
        exact_match = await self.repo.get_entity_by_name(
            workspace_id=workspace_id,
            canonical_name=norm_name,
            entity_type=norm_type,
            project_id=project_id,
        )
        if exact_match:
            # Preserve source provenance
            if source_id:
                sanitized_meta = sanitize_source_metadata(source_metadata or {})
                await self.repo.add_source(
                    entity_id=exact_match.id,
                    source_type=source_type,
                    source_id=source_id,
                    source_location=source_location,
                    content_hash=content_hash,
                    metadata=sanitized_meta,
                )
            reloaded = await self.repo.get_entity_by_id(exact_match.id)
            return EntityResponse.model_validate(reloaded), False

        # 2. Match via alias
        alias_match = await self.repo.get_entity_by_alias(
            workspace_id=workspace_id,
            alias=raw_name,
            project_id=project_id,
        )
        if alias_match:
            if alias_match.entity_type == norm_type:
                if source_id:
                    sanitized_meta = sanitize_source_metadata(source_metadata or {})
                    await self.repo.add_source(
                        entity_id=alias_match.id,
                        source_type=source_type,
                        source_id=source_id,
                        source_location=source_location,
                        content_hash=content_hash,
                        metadata=sanitized_meta,
                    )
                reloaded = await self.repo.get_entity_by_id(alias_match.id)
                return EntityResponse.model_validate(reloaded), False

        # 3. Bounded similarity search for potential duplicates/ambiguities
        candidates = await self.repo.search_entities(
            workspace_id=workspace_id,
            query_str=raw_name,
            entity_type=norm_type,
            project_id=project_id,
            limit=10,
        )
        type_entities = await self.repo.list_entities(
            workspace_id=workspace_id,
            entity_type=norm_type,
            project_id=project_id,
            limit=50,
        )
        seen_cand_ids = {c.id for c in candidates}
        for te in type_entities:
            if te.id not in seen_cand_ids:
                candidates.append(te)

        ambiguous_candidates = []
        for cand in candidates:
            sim = compute_string_similarity(cand.canonical_name, raw_name)
            if sim >= 0.82:
                ambiguous_candidates.append((cand, sim))

        # If high ambiguity exists (similarity >= 0.82), record conflict rather than silently merging!
        if ambiguous_candidates:
            # Log an ambiguous_entity conflict for human operator review
            best_cand, best_sim = max(ambiguous_candidates, key=lambda x: x[1])
            await self.repo.create_conflict(
                organization_id=organization_id,
                workspace_id=workspace_id,
                conflict_type=ConflictType.AMBIGUOUS_ENTITY.value,
                details={
                    "incoming_name": raw_name,
                    "incoming_type": norm_type,
                    "candidate_entity_id": str(best_cand.id),
                    "candidate_canonical_name": best_cand.canonical_name,
                    "similarity": round(best_sim, 3),
                    "source_id": source_id,
                    "source_type": source_type,
                },
                entity_id=best_cand.id,
            )

        # 4. Create new canonical entity
        from backend.app.services.knowledge_graph.entity_service import EntityService
        entity_service = EntityService(self.session)

        created = await entity_service.create_entity(
            organization_id=organization_id,
            workspace_id=workspace_id,
            request=EntityCreateRequest(
                canonical_name=raw_name.strip(),
                entity_type=norm_type,
                description=description,
                properties=properties or {},
                confidence=confidence,
                aliases=list(aliases) if aliases else (
                    [raw_name.strip()] if raw_name.strip() != norm_name else []
                ),
                source_type=source_type,
                source_id=source_id,
                source_metadata=source_metadata or {},
                project_id=project_id,
            ),
        )
        return created, True
