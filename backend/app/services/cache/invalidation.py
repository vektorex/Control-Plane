"""
Cache Invalidation Service for Step 31: Production-Grade Semantic Cache and Intelligent Reuse Layer.

Supports surgical invalidation across entries, namespaces, prompt versions, multimodal artifacts,
document updates, knowledge graph mutations, memory state changes, and models.
"""
import uuid
from typing import List, Optional
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.cache.constants import InvalidationMode
from backend.app.services.cache.repository import CacheRepository
from backend.app.services.cache.schemas import (
    CacheInvalidationRequest,
    CacheInvalidationResult,
)
from backend.app.services.cache.statistics import CacheStatisticsService

logger = logging.getLogger(__name__)


class CacheInvalidationService:
    """Coordinates administrative and event-driven surgical invalidation sweeps."""

    def __init__(
        self,
        repository: Optional[CacheRepository] = None,
        stats_service: Optional[CacheStatisticsService] = None,
    ):
        self.repository = repository or CacheRepository()
        self.stats_service = stats_service or CacheStatisticsService()

    async def invalidate(
        self,
        db: AsyncSession,
        request: CacheInvalidationRequest,
    ) -> CacheInvalidationResult:
        """
        Invalidate cache entries matching request criteria.
        """
        count = 0
        reason = request.reason or f"invalidated_{request.mode.value}"

        if request.mode == InvalidationMode.ENTRY:
            if request.target_id:
                try:
                    entry_uuid = uuid.UUID(request.target_id)
                    count = await self.repository.invalidate_by_ids(db, [entry_uuid], reason)
                except ValueError:
                    logger.warning("Invalid UUID for entry invalidation: %s", request.target_id)
        elif request.mode == InvalidationMode.NAMESPACE:
            count = await self.repository.invalidate_by_filter(
                db=db,
                workspace_id=request.workspace_id,
                namespace=request.target_id,
                reason=reason,
            )
        elif request.mode == InvalidationMode.PROMPT:
            prompt_version_uuid = None
            if request.target_id:
                try:
                    prompt_version_uuid = uuid.UUID(request.target_id)
                except ValueError:
                    pass
            count = await self.repository.invalidate_by_filter(
                db=db,
                workspace_id=request.workspace_id,
                prompt_version_id=prompt_version_uuid,
                reason=reason,
            )
        elif request.mode == InvalidationMode.ARTIFACT:
            count = await self.repository.invalidate_by_filter(
                db=db,
                workspace_id=request.workspace_id,
                artifact_hash=request.target_id,
                reason=reason,
            )
        elif request.mode == InvalidationMode.DOCUMENT:
            count = await self.repository.invalidate_by_filter(
                db=db,
                workspace_id=request.workspace_id,
                reason=reason,
            )
        elif request.mode == InvalidationMode.GRAPH:
            count = await self.repository.invalidate_by_filter(
                db=db,
                workspace_id=request.workspace_id,
                graph_snapshot_hash=request.target_id,
                reason=reason,
            )
        elif request.mode == InvalidationMode.MEMORY:
            count = await self.repository.invalidate_by_filter(
                db=db,
                workspace_id=request.workspace_id,
                memory_snapshot_hash=request.target_id,
                reason=reason,
            )
        elif request.mode == InvalidationMode.MODEL:
            count = await self.repository.invalidate_by_filter(
                db=db,
                workspace_id=request.workspace_id,
                model_id=request.target_id,
                reason=reason,
            )
        elif request.mode == InvalidationMode.PROJECT:
            project_uuid = None
            if request.target_id:
                try:
                    project_uuid = uuid.UUID(request.target_id)
                except ValueError:
                    pass
            count = await self.repository.invalidate_by_filter(
                db=db,
                workspace_id=request.workspace_id,
                project_id=project_uuid,
                reason=reason,
            )
        elif request.mode == InvalidationMode.WORKSPACE:
            count = await self.repository.invalidate_by_filter(
                db=db,
                workspace_id=request.workspace_id,
                reason=reason,
            )

        if count > 0:
            self.stats_service.record_invalidation(request.workspace_id, count)
            logger.info(
                "Invalidated %d entries in workspace %s for mode %s (reason: %s)",
                count,
                request.workspace_id,
                request.mode.value,
                reason,
            )

        return CacheInvalidationResult(
            invalidated_count=count,
            mode=request.mode.value,
            reason=reason,
        )

    async def handle_domain_event(
        self,
        db: AsyncSession,
        event_name: str,
        payload: dict,
    ) -> int:
        """
        Surgically invalidates cache entries upon domain events.
        Does NOT flush the entire cache for every event.
        """
        workspace_id_raw = payload.get("workspace_id")
        if not workspace_id_raw:
            return 0
        try:
            workspace_id = uuid.UUID(str(workspace_id_raw))
        except ValueError:
            return 0

        if event_name in ("prompt.release_changed", "prompt.rolled_back"):
            pv_id = payload.get("prompt_version_id")
            if pv_id:
                req = CacheInvalidationRequest(
                    workspace_id=workspace_id,
                    mode=InvalidationMode.PROMPT,
                    target_id=str(pv_id),
                    reason=f"event:{event_name}",
                )
                res = await self.invalidate(db, req)
                return res.invalidated_count

        elif event_name == "artifact.processing_completed":
            artifact_hash = payload.get("content_hash") or payload.get("artifact_id")
            if artifact_hash:
                req = CacheInvalidationRequest(
                    workspace_id=workspace_id,
                    mode=InvalidationMode.ARTIFACT,
                    target_id=str(artifact_hash),
                    reason=f"event:{event_name}",
                )
                res = await self.invalidate(db, req)
                return res.invalidated_count

        elif event_name in ("graph.entity_updated", "graph.relationship_created", "graph.relationship_removed"):
            graph_hash = payload.get("graph_snapshot_hash")
            if graph_hash:
                req = CacheInvalidationRequest(
                    workspace_id=workspace_id,
                    mode=InvalidationMode.GRAPH,
                    target_id=str(graph_hash),
                    reason=f"event:{event_name}",
                )
                res = await self.invalidate(db, req)
                return res.invalidated_count

        elif event_name == "memory.updated":
            mem_hash = payload.get("memory_snapshot_hash")
            if mem_hash:
                req = CacheInvalidationRequest(
                    workspace_id=workspace_id,
                    mode=InvalidationMode.MEMORY,
                    target_id=str(mem_hash),
                    reason=f"event:{event_name}",
                )
                res = await self.invalidate(db, req)
                return res.invalidated_count

        elif event_name == "model.configuration_changed":
            model_id = payload.get("model_id")
            if model_id:
                req = CacheInvalidationRequest(
                    workspace_id=workspace_id,
                    mode=InvalidationMode.MODEL,
                    target_id=str(model_id),
                    reason=f"event:{event_name}",
                )
                res = await self.invalidate(db, req)
                return res.invalidated_count

        return 0
