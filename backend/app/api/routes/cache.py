"""
REST API Routes for Step 31: Production-Grade Semantic Cache and Intelligent Reuse Layer.

Provides endpoints for factual cache metrics, entry inspection, surgical invalidation,
dry-run preview probes, and administrative cache policy configuration.
"""
import uuid
from typing import Any, Dict, List, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.access_control.permissions import (
    CACHE_CONFIGURE,
    CACHE_DELETE,
    CACHE_INVALIDATE,
    CACHE_READ,
)
from backend.app.services.access_control.service import AccessControlService
from backend.app.services.cache.models import CacheEntry
from backend.app.services.cache.schemas import (
    CacheEntryResponse,
    CacheInvalidationRequest,
    CacheInvalidationResult,
    CachePolicyConfig,
    CachePreviewRequest,
    CachePreviewResponse,
    CacheStatsResponse,
)
from backend.app.services.cache.service import CacheService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cache", tags=["Semantic Cache"])


async def verify_permission(
    session: AsyncSession,
    user: User,
    workspace_id: uuid.UUID,
    permission: str,
) -> None:
    """Helper to verify caller RBAC authorization within the workspace boundary."""
    ac_service = AccessControlService(session)
    has_perm = await ac_service.has_workspace_permission(user.id, workspace_id, permission)
    if not has_perm:
        # Fallback check for superadmin / org owner
        is_admin = await ac_service.is_workspace_admin(user.id, workspace_id)
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User lacks required '{permission}' permission for workspace {workspace_id}",
            )


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    workspace_id: uuid.UUID = Query(..., description="Target workspace ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CacheStatsResponse:
    """
    Fetch factual, non-subjective metrics reflecting cache health, hit ratios, and storage.
    """
    await verify_permission(session, current_user, workspace_id, CACHE_READ)
    cache_svc = CacheService()
    return await cache_svc.get_stats(session, workspace_id)


@router.get("/policy", response_model=CachePolicyConfig)
async def get_cache_policy(
    workspace_id: uuid.UUID = Query(..., description="Target workspace ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CachePolicyConfig:
    """
    Retrieve current workspace cache policy configuration.
    """
    await verify_permission(session, current_user, workspace_id, CACHE_READ)
    cache_svc = CacheService()
    return await cache_svc.policy_engine.get_workspace_policy(session, workspace_id)


@router.put("/policy", response_model=CachePolicyConfig)
async def update_cache_policy(
    policy: CachePolicyConfig,
    workspace_id: uuid.UUID = Query(..., description="Target workspace ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CachePolicyConfig:
    """
    Update workspace cache policy configuration (admin only).
    """
    await verify_permission(session, current_user, workspace_id, CACHE_CONFIGURE)
    cache_svc = CacheService()
    return await cache_svc.policy_engine.save_workspace_policy(session, workspace_id, policy)


@router.post("/invalidate", response_model=CacheInvalidationResult)
async def invalidate_cache(
    request: CacheInvalidationRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CacheInvalidationResult:
    """
    Surgically invalidate cache entries across entry, namespace, prompt, artifact, or workspace scopes.
    """
    await verify_permission(session, current_user, request.workspace_id, CACHE_INVALIDATE)
    cache_svc = CacheService()
    return await cache_svc.invalidate(session, request)


@router.post("/preview", response_model=CachePreviewResponse)
async def preview_cache(
    request: CachePreviewRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CachePreviewResponse:
    """
    Evaluate task cache eligibility and candidate match without executing any LLM calls.
    """
    workspace_id = request.workspace_id or current_user.workspace_id or uuid.uuid4()
    await verify_permission(session, current_user, workspace_id, CACHE_READ)
    cache_svc = CacheService()
    req_with_ws = request.model_copy(update={"workspace_id": workspace_id})
    return await cache_svc.preview(session, req_with_ws)


@router.get("/entries", response_model=Dict[str, Any])
async def list_cache_entries(
    workspace_id: uuid.UUID = Query(..., description="Target workspace ID"),
    namespace: Optional[str] = Query(None, description="Optional namespace filter"),
    status: Optional[str] = Query(None, description="Optional status filter"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    List sanitized cache entries within the authorized workspace.
    """
    await verify_permission(session, current_user, workspace_id, CACHE_READ)
    cache_svc = CacheService()
    entries, total = await cache_svc.list_entries(
        db=session,
        workspace_id=workspace_id,
        namespace=namespace,
        status=status,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [CacheEntryResponse.model_validate(e) for e in entries],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/entries/{entry_id}", response_model=CacheEntryResponse)
async def get_cache_entry(
    entry_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(..., description="Target workspace ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CacheEntryResponse:
    """
    Retrieve single sanitized cache entry by ID with authorization verification.
    """
    await verify_permission(session, current_user, workspace_id, CACHE_READ)
    cache_svc = CacheService()
    entry = await cache_svc.get_entry(session, entry_id)
    if not entry or entry.workspace_id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cache entry '{entry_id}' not found",
        )
    return CacheEntryResponse.model_validate(entry)


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cache_entry(
    entry_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(..., description="Target workspace ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete/invalidate a specific cache entry (admin/authorized user only).
    """
    await verify_permission(session, current_user, workspace_id, CACHE_DELETE)
    cache_svc = CacheService()
    entry = await cache_svc.get_entry(session, entry_id)
    if not entry or entry.workspace_id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cache entry '{entry_id}' not found",
        )
    await cache_svc.delete_entry(session, entry_id, reason="user_manual_deletion")
