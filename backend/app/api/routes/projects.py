from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.repositories.project import ProjectRepository
from backend.app.repositories.task import TaskRepository
from backend.app.schemas.project import (
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
)
from backend.app.schemas.task import (
    TaskCreate,
    TaskResponse,
    TaskListResponse,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=ProjectListResponse)
async def list_all_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProjectListResponse:
    """
    List all projects belonging to the authenticated user's workspaces.
    """
    repo = ProjectRepository(session)
    projects, total = await repo.list_by_owner(user.id, skip=skip, limit=limit)
    response_items = []
    for p in projects:
        item = ProjectResponse.model_validate(p)
        item.task_count = len(p.tasks) if hasattr(p, "tasks") and p.tasks is not None else 0
        response_items.append(item)
    return ProjectListResponse(projects=response_items, total=total)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """
    Retrieve project details by project identifier for an owned workspace.
    Returns 404 if not found or unowned.
    """
    repo = ProjectRepository(session)
    project = await repo.get_by_id_and_owner_or_raise(project_id, user.id)
    response = ProjectResponse.model_validate(project)
    response.task_count = len(project.tasks) if hasattr(project, "tasks") and project.tasks is not None else 0
    return response


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """
    Update project details (name, slug, description) for an owned project.
    """
    repo = ProjectRepository(session)
    project = await repo.update(project_id, user.id, data)
    response = ProjectResponse.model_validate(project)
    response.task_count = len(project.tasks) if hasattr(project, "tasks") and project.tasks is not None else 0
    return response


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Delete an owned project and cascade-delete all associated tasks and runs.
    """
    repo = ProjectRepository(session)
    await repo.delete(project_id, user.id)
    return None


# --- Nested Project Tasks Routes ---

@router.post("/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_project_task(
    project_id: UUID,
    data: TaskCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """
    Create a new task under a specific owned project.
    """
    repo = TaskRepository(session)
    task = await repo.create(project_id, user.id, data)
    return TaskResponse.model_validate(task)


@router.get("/{project_id}/tasks", response_model=TaskListResponse)
async def list_project_tasks(
    project_id: UUID,
    status: Optional[str] = Query(None, description="Filter by task status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TaskListResponse:
    """
    List all tasks belonging to an owned project.
    """
    repo = TaskRepository(session)
    tasks, total = await repo.list_by_project(project_id, user.id, status=status, skip=skip, limit=limit)
    response_items = []
    for t in tasks:
        item = TaskResponse.model_validate(t)
        item.run_count = len(t.runs) if hasattr(t, "runs") and t.runs is not None else 0
        response_items.append(item)
    return TaskListResponse(tasks=response_items, total=total)


# --- Project Members Routes (Step 27) ---

from backend.app.services.access_control.schemas import (
    ProjectMemberCreate,
    ProjectMemberUpdate,
    ProjectMemberResponse,
    ProjectMemberListResponse,
)
from backend.app.services.access_control.service import AccessControlService


@router.get("/{project_id}/members", response_model=ProjectMemberListResponse)
async def list_project_members(
    project_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProjectMemberListResponse:
    """
    List explicit members for a restricted project.
    """
    service = AccessControlService(session)
    members = await service.membership.list_project_members(project_id=project_id, current_user=user)
    items = []
    for m in members:
        email = m.user.email if hasattr(m, "user") and m.user else None
        items.append(
            ProjectMemberResponse(
                id=m.id,
                project_id=m.project_id,
                user_id=m.user_id,
                email=email,
                role=m.role,
                created_at=m.created_at,
            )
        )
    return ProjectMemberListResponse(members=items, total=len(items))


@router.post("/{project_id}/members", response_model=ProjectMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_project_member(
    project_id: UUID,
    payload: ProjectMemberCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProjectMemberResponse:
    """
    Add a user to a project's access list.
    """
    service = AccessControlService(session)
    member = await service.membership.add_project_member(
        project_id=project_id,
        target_user_id=payload.user_id,
        role=payload.role,
        current_user=user,
    )
    email = member.user.email if hasattr(member, "user") and member.user else None
    return ProjectMemberResponse(
        id=member.id,
        project_id=member.project_id,
        user_id=member.user_id,
        email=email,
        role=member.role,
        created_at=member.created_at,
    )


@router.patch("/{project_id}/members/{member_id}", response_model=ProjectMemberResponse)
async def update_project_member(
    project_id: UUID,
    member_id: UUID,
    payload: ProjectMemberUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProjectMemberResponse:
    """
    Update a project member's role (editor vs viewer).
    """
    service = AccessControlService(session)
    member = await service.membership.update_project_member(
        project_id=project_id,
        member_id=member_id,
        role=payload.role,
        current_user=user,
    )
    email = member.user.email if hasattr(member, "user") and member.user else None
    return ProjectMemberResponse(
        id=member.id,
        project_id=member.project_id,
        user_id=member.user_id,
        email=email,
        role=member.role,
        created_at=member.created_at,
    )


@router.delete("/{project_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_member(
    project_id: UUID,
    member_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Remove a user from the restricted project member list.
    """
    service = AccessControlService(session)
    await service.membership.remove_project_member(
        project_id=project_id,
        member_id=member_id,
        current_user=user,
    )
    return None
