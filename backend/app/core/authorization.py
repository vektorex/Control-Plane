from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.db.models.workspace import Workspace
from backend.app.db.models.project import Project
from backend.app.db.models.task import Task
from backend.app.db.models.run import Run
from backend.app.repositories.workspace import WorkspaceRepository
from backend.app.repositories.project import ProjectRepository
from backend.app.repositories.task import TaskRepository
from backend.app.repositories.run import RunRepository


async def verify_workspace_access(
    workspace_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Workspace:
    """
    Authorization dependency verifying that the authenticated user owns the requested workspace.
    Returns the Workspace if authorized; raises NotFoundError (404) if unowned or nonexistent.
    """
    repo = WorkspaceRepository(session)
    return await repo.get_by_id_and_owner_or_raise(workspace_id, user.id)


async def verify_project_access(
    project_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Project:
    """
    Authorization dependency verifying that the project belongs to a workspace owned by the user.
    """
    repo = ProjectRepository(session)
    return await repo.get_by_id_and_owner_or_raise(project_id, user.id)


async def verify_task_access(
    task_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Task:
    """
    Authorization dependency verifying that the task belongs to a project/workspace owned by the user.
    """
    repo = TaskRepository(session)
    return await repo.get_by_id_and_owner_or_raise(task_id, user.id)


async def verify_run_access(
    run_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Run:
    """
    Authorization dependency verifying that the run belongs to a task/project/workspace owned by the user.
    """
    repo = RunRepository(session)
    return await repo.get_by_id_and_owner_or_raise(run_id, user.id)
