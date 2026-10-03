"""
Context Provider integrating the Knowledge Graph into the unified ContextEngine.
Converts graph entities, relationships, and provenance into prioritized ContextItems.
"""
from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from backend.app.db.models.task import Task

from backend.app.services.context.base import ContextProvider
from backend.app.services.context.models import ContextItem, ContextSourceType
from backend.app.services.context.token_estimator import estimate_context_item_tokens
from backend.app.services.knowledge_graph.constants import MAX_GRAPH_CONTEXT_TOKENS
from backend.app.services.knowledge_graph.retriever import GraphRetriever
from backend.app.services.knowledge_graph.schemas import GraphContextResult


class GraphContextProvider(ContextProvider):
    """
    Supplies structured entity and relationship context to the ContextEngine.
    collect() returns normalized ContextItem objects (one per entity) so callers
    can inspect them directly without an explicit normalize() call.
    """

    def __init__(self, retriever: Optional[GraphRetriever] = None):
        self._retriever = retriever

    @property
    def provider_id(self) -> str:
        return "knowledge_graph_context"

    @property
    def source_type(self) -> str:
        return ContextSourceType.KNOWLEDGE_GRAPH.value

    async def can_handle(self, task: "Task", **kwargs: Any) -> bool:
        if kwargs.get("graph_enabled", True) is False:
            return False
        if kwargs.get("graph_result") is not None:
            return True
        return task is not None

    async def collect(
        self,
        task: "Task",
        session: Optional[AsyncSession] = None,
        **kwargs: Any,
    ) -> List[ContextItem]:
        """
        Retrieves graph context and normalizes it to ContextItem objects.
        Each retrieved entity becomes one ContextItem with canonical_name in metadata.
        """
        # 1. Use precomputed GraphContextResult if supplied
        precomputed = kwargs.get("graph_result")
        if precomputed and isinstance(precomputed, GraphContextResult):
            return self.normalize([precomputed], **kwargs)

        if not session or not task:
            return []

        # 2. Retrieve graph context dynamically
        workspace_id = kwargs.get("workspace_id")
        project_id = kwargs.get("project_id")
        task_project = getattr(task, "project", None)
        if not workspace_id and task_project:
            workspace_id = getattr(task_project, "workspace_id", None)
            project_id = getattr(task, "project_id", None)

        if not workspace_id:
            return []

        retriever = self._retriever or GraphRetriever(session)
        task_instructions = getattr(task, "instructions", None) or ""
        task_title = getattr(task, "title", None) or ""
        query = task_instructions.strip() or task_title.strip()
        seed_entities = kwargs.get("seed_entities")

        result = await retriever.retrieve(
            workspace_id=workspace_id,
            query=query,
            seed_entities=seed_entities,
            max_hops=kwargs.get("max_hops", 1),
            max_entities=kwargs.get("max_entities", 30),
            max_relationships=kwargs.get("max_relationships", 50),
            project_id=project_id,
        )

        return self.normalize([result], **kwargs) if (result.entities or result.relationships) else []

    def normalize(self, raw_items: List[Any], **kwargs: Any) -> List[ContextItem]:
        """
        Converts GraphContextResult objects into a flat list of ContextItems.
        Each entity gets its own ContextItem with canonical_name, relationships,
        and sources in metadata for downstream test introspection.
        Token budget (MAX_GRAPH_CONTEXT_TOKENS) is enforced across all items.
        """
        if not raw_items:
            return []

        context_items: List[ContextItem] = []
        token_budget = MAX_GRAPH_CONTEXT_TOKENS

        for item in raw_items:
            if isinstance(item, ContextItem):
                # Pass-through already-normalized items
                context_items.append(item)
                continue

            if not isinstance(item, GraphContextResult):
                continue

            # Build a relationship lookup: entity_id -> list of "source -> rel -> target" strings
            rel_lookup: Dict[str, List[str]] = {}
            for r in item.relationships:
                s_name = r.source_entity_name or str(r.source_entity_id)
                t_name = r.target_entity_name or str(r.target_entity_id)
                rel_str = f"{s_name} -> {r.relationship_type} -> {t_name}"
                for eid in (str(r.source_entity_id), str(r.target_entity_id)):
                    rel_lookup.setdefault(eid, []).append(rel_str)

            # Build source lookup
            src_lookup: Dict[str, List[Dict]] = {}
            for s in item.source_references:
                eid = s.get("entity_id", "")
                src_lookup.setdefault(eid, []).append({
                    "source_type": s.get("source_type"),
                    "source_id": s.get("source_id"),
                })

            for e in item.entities:
                if token_budget <= 0:
                    break

                desc_str = f" - {e.description}" if e.description else ""
                content = f"[{e.entity_type.upper()}] {e.canonical_name}{desc_str}"

                entity_rels = rel_lookup.get(str(e.id), [])
                entity_sources = src_lookup.get(str(e.id), [])

                metadata: Dict[str, Any] = {
                    "canonical_name": e.canonical_name,
                    "entity_type": e.entity_type,
                    "entity_id": str(e.id),
                    "properties": e.properties,
                    "relationships": entity_rels,
                    "sources": entity_sources,
                    "source_count": e.source_count,
                }

                c_item = ContextItem(
                    source_type=ContextSourceType.KNOWLEDGE_GRAPH.value,
                    title=f"[{e.entity_type.upper()}] {e.canonical_name}",
                    content=content,
                    metadata=metadata,
                    relevance_score=0.95,
                    priority=8,
                    trust_level="trusted_graph_context",
                )
                c_item.token_estimate = estimate_context_item_tokens(c_item)
                if c_item.token_estimate > token_budget:
                    break

                token_budget -= c_item.token_estimate
                context_items.append(c_item)

            # Relationships summary item (lower priority)
            if item.relationships and token_budget > 0:
                rel_lines = []
                for r in item.relationships:
                    s_name = r.source_entity_name or str(r.source_entity_id)
                    t_name = r.target_entity_name or str(r.target_entity_id)
                    rel_lines.append(f"• {s_name} --({r.relationship_type.upper()})--> {t_name}")

                rel_content = "Structured Entity Relationships & Dependencies:\n" + "\n".join(rel_lines)
                r_item = ContextItem(
                    source_type=ContextSourceType.KNOWLEDGE_GRAPH.value,
                    title="Knowledge Graph Relationships",
                    content=rel_content,
                    metadata={"relationship_count": len(item.relationships), "kind": "relationships"},
                    relevance_score=0.90,
                    priority=7,
                    trust_level="trusted_graph_context",
                )
                r_item.token_estimate = estimate_context_item_tokens(r_item)
                context_items.append(r_item)

        return context_items
