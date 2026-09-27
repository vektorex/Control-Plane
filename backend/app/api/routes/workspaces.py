from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.repositories.workspace import WorkspaceRepository
from backend.app.repositories.project import ProjectRepository
from backend.app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceListResponse,
)
from backend.app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectListResponse,
)

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    data: WorkspaceCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> WorkspaceResponse:
    """
    Create a new organizational workspace owned by the authenticated user.
    """
    repo = WorkspaceRepository(session)
    workspace = await repo.create(user.id, data)
    return WorkspaceResponse.model_validate(workspace)


@router.get("", response_model=WorkspaceListResponse)
async def list_workspaces(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> WorkspaceListResponse:
    """
    List all workspaces owned by the authenticated user.
    """
    repo = WorkspaceRepository(session)
    workspaces, total = await repo.list_by_owner(user.id, skip=skip, limit=limit)
    response_items = []
    for w in workspaces:
        item = WorkspaceResponse.model_validate(w)
        item.project_count = len(w.projects) if hasattr(w, "projects") and w.projects is not None else 0
        response_items.append(item)
    return WorkspaceListResponse(workspaces=response_items, total=total)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> WorkspaceResponse:
    """
    Retrieve an authenticated user's workspace by identifier.
    Returns 404 if not found or owned by another user.
    """
    repo = WorkspaceRepository(session)
    workspace = await repo.get_by_id_and_owner_or_raise(workspace_id, user.id)
    response = WorkspaceResponse.model_validate(workspace)
    response.project_count = len(workspace.projects) if hasattr(workspace, "projects") and workspace.projects is not None else 0
    return response


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: UUID,
    data: WorkspaceUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> WorkspaceResponse:
    """
    Update workspace name or slug for an owned workspace.
    """
    repo = WorkspaceRepository(session)
    workspace = await repo.update(workspace_id, user.id, data)
    response = WorkspaceResponse.model_validate(workspace)
    response.project_count = len(workspace.projects) if hasattr(workspace, "projects") and workspace.projects is not None else 0
    return response


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Delete an owned workspace and cascade-delete all associated projects, tasks, and runs.
    """
    repo = WorkspaceRepository(session)
    await repo.delete(workspace_id, user.id)
    return None


# --- Nested Workspace Projects Routes ---

@router.post("/{workspace_id}/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace_project(
    workspace_id: UUID,
    data: ProjectCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """
    Create a project within a specific owned workspace.
    """
    repo = ProjectRepository(session)
    project = await repo.create(workspace_id, user.id, data)
    return ProjectResponse.model_validate(project)


@router.get("/{workspace_id}/projects", response_model=ProjectListResponse)
async def list_workspace_projects(
    workspace_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProjectListResponse:
    """
    List all projects belonging to an owned workspace.
    """
    repo = ProjectRepository(session)
    projects, total = await repo.list_by_workspace(workspace_id, user.id, skip=skip, limit=limit)
    response_items = []
    for p in projects:
        item = ProjectResponse.model_validate(p)
        item.task_count = len(p.tasks) if hasattr(p, "tasks") and p.tasks is not None else 0
        response_items.append(item)
    return ProjectListResponse(projects=response_items, total=total)
