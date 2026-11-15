"""
REST API endpoints for the Memory & Persistent Context Intelligence System.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.logging import logger
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.memory import (
    CandidateMemory,
    ConflictResolveRequest,
    MemoryCreateRequest,
    MemoryError,
    MemoryListResponse,
    MemoryNotFoundError,
    MemoryPermissionError,
    MemoryResponse,
    MemorySecretDetectedError,
    MemoryService,
    MemorySuggestionResponse,
    MemoryConflictResponse,
    MemoryUpdateRequest,
    MemoryValidationError,
    UserMemorySettingsResponse,
    UserMemorySettingsUpdateRequest,
)

router = APIRouter(prefix="/memories", tags=["Memories"])


def _resolve_workspace_id(
    user: User,
    header_ws_id: Optional[str] = None,
    query_ws_id: Optional[UUID] = None,
) -> UUID:
    """Extracts and verifies active workspace ID for the request."""
    if query_ws_id:
        return query_ws_id
    if header_ws_id:
        try:
            return UUID(header_ws_id)
        except ValueError:
            pass
    if getattr(user, "default_workspace_id", None):
        return user.default_workspace_id
    if getattr(user, "workspaces", None) and len(user.workspaces) > 0:
        return user.workspaces[0].id
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Workspace context could not be resolved. Please specify 'X-Workspace-Id' header.",
    )


# =============================================================================
# Explicit Memory Endpoints
# =============================================================================

@router.post("", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    request: MemoryCreateRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
):
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    svc = MemoryService(session)
    try:
        mem = await svc.create_memory(workspace_id=ws_id, user=user, request=request)
        return mem
    except MemorySecretDetectedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except MemoryValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=e.message)
    except MemoryError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/from-source", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory_from_source(
    request: MemoryCreateRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
):
    """
    Explicit user action: 'Save this as memory' from a document snippet or connector item.
    Enforces sanitization, secret detection, and keeps source attribution.
    """
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    if request.source_type.value not in ("document", "connector"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from-source endpoint is intended for 'document' or 'connector' sources with explicit user action.",
        )
    svc = MemoryService(session)
    try:
        mem = await svc.create_memory(workspace_id=ws_id, user=user, request=request)
        return mem
    except MemorySecretDetectedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except MemoryValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=e.message)
    except MemoryError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("", response_model=MemoryListResponse)
async def list_memories(
    scope: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    project_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
):
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    svc = MemoryService(session)
    items, total = await svc.list_memories(
        workspace_id=ws_id,
        user=user,
        scope=scope,
        type_=type,
        status=status,
        project_id=project_id,
        search=search,
        limit=limit,
        offset=offset,
    )
    return MemoryListResponse(items=items, total=total, limit=limit, offset=offset)


# =============================================================================
# Suggestions Endpoints (Must be registered before /{memory_id} path)
# =============================================================================

@router.get("/suggestions", response_model=List[MemorySuggestionResponse])
async def list_suggestions(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
):
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    svc = MemoryService(session)
    return await svc.list_suggestions(workspace_id=ws_id, user=user)


@router.post("/suggestions/{suggestion_id}/accept", response_model=MemoryResponse)
async def accept_suggestion(
    suggestion_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
):
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    svc = MemoryService(session)
    try:
        return await svc.accept_suggestion(suggestion_id=suggestion_id, workspace_id=ws_id, user=user)
    except MemoryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except MemoryValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post("/suggestions/{suggestion_id}/reject", status_code=status.HTTP_200_OK)
async def reject_suggestion(
    suggestion_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
):
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    svc = MemoryService(session)
    try:
        await svc.reject_suggestion(suggestion_id=suggestion_id, workspace_id=ws_id, user=user)
        return {"status": "rejected", "suggestion_id": str(suggestion_id)}
    except MemoryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


# =============================================================================
# Conflicts Endpoints
# =============================================================================

@router.get("/conflicts", response_model=List[MemoryConflictResponse])
async def list_conflicts(
    status: Optional[str] = Query("unresolved"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
):
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    svc = MemoryService(session)
    return await svc.list_conflicts(workspace_id=ws_id, status=status)


@router.post("/conflicts/{conflict_id}/resolve", response_model=MemoryConflictResponse)
async def resolve_conflict(
    conflict_id: UUID,
    request: ConflictResolveRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
):
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    svc = MemoryService(session)
    try:
        return await svc.resolve_conflict(conflict_id=conflict_id, workspace_id=ws_id, user=user, request=request)
    except MemoryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except MemoryValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=e.message)


@router.post("/conflicts/{conflict_id}/dismiss", response_model=MemoryConflictResponse)
async def dismiss_conflict(
    conflict_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
):
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    svc = MemoryService(session)
    try:
        req = ConflictResolveRequest(action="dismiss", resolution_note="Dismissed by user.")
        return await svc.resolve_conflict(conflict_id=conflict_id, workspace_id=ws_id, user=user, request=req)
    except MemoryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


# =============================================================================
# Settings Endpoints
# =============================================================================

@router.get("/settings", response_model=UserMemorySettingsResponse)
async def get_settings(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
):
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    svc = MemoryService(session)
    st = await svc.get_or_create_settings(workspace_id=ws_id, user_id=user.id)
    return UserMemorySettingsResponse(
        memory_enabled=st.memory_enabled,
        suggestions_enabled=st.suggestions_enabled,
        default_retrieval_mode=st.default_retrieval_mode,
        default_scope=st.default_scope,
        retention_preference=st.retention_preference,
    )


@router.put("/settings", response_model=UserMemorySettingsResponse)
async def update_settings(
    request: UserMemorySettingsUpdateRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
):
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    svc = MemoryService(session)
    st = await svc.update_settings(workspace_id=ws_id, user_id=user.id, request=request)
    return UserMemorySettingsResponse(
        memory_enabled=st.memory_enabled,
        suggestions_enabled=st.suggestions_enabled,
        default_retrieval_mode=st.default_retrieval_mode,
        default_scope=st.default_scope,
        retention_preference=st.retention_preference,
    )


# =============================================================================
# Privacy Controls (Bulk Deletion)
# =============================================================================

@router.delete("/scope/project/{project_id}", status_code=status.HTTP_200_OK)
async def delete_project_memories(
    project_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
):
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    svc = MemoryService(session)
    count = await svc.delete_all_project_memories(workspace_id=ws_id, project_id=project_id, user=user)
    return {"status": "deleted", "deleted_count": count, "project_id": str(project_id)}


@router.delete("/scope/workspace", status_code=status.HTTP_200_OK)
async def delete_workspace_memories(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
):
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    svc = MemoryService(session)
    count = await svc.delete_all_workspace_memories(workspace_id=ws_id, user=user)
    return {"status": "deleted", "deleted_count": count, "workspace_id": str(ws_id)}


# =============================================================================
# Single Memory Detail, Actions, and Lifecycle
# =============================================================================

@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory_detail(
    memory_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
):
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    svc = MemoryService(session)
    try:
        return await svc.get_memory(memory_id=memory_id, workspace_id=ws_id, user=user)
    except MemoryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except MemoryPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)


@router.patch("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: UUID,
    request: MemoryUpdateRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
):
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    svc = MemoryService(session)
    try:
        return await svc.update_memory(memory_id=memory_id, workspace_id=ws_id, user=user, request=request)
    except MemoryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except MemoryPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except MemorySecretDetectedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.delete("/{memory_id}", status_code=status.HTTP_200_OK)
async def delete_memory(
    memory_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
):
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    svc = MemoryService(session)
    try:
        await svc.delete_memory(memory_id=memory_id, workspace_id=ws_id, user=user)
        return {"status": "deleted", "memory_id": str(memory_id)}
    except MemoryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except MemoryPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)


@router.post("/{memory_id}/archive", response_model=MemoryResponse)
async def archive_memory(
    memory_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
):
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    svc = MemoryService(session)
    try:
        return await svc.archive_memory(memory_id=memory_id, workspace_id=ws_id, user=user)
    except MemoryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except MemoryPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)


@router.post("/{memory_id}/restore", response_model=MemoryResponse)
async def restore_memory(
    memory_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
):
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    svc = MemoryService(session)
    try:
        return await svc.restore_memory(memory_id=memory_id, workspace_id=ws_id, user=user)
    except MemoryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except MemoryPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)


@router.post("/{memory_id}/use", status_code=status.HTTP_200_OK)
async def use_memory(
    memory_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
):
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    svc = MemoryService(session)
    await svc.touch_memory_used(memory_id=memory_id, workspace_id=ws_id)
    return {"status": "touched", "memory_id": str(memory_id)}
