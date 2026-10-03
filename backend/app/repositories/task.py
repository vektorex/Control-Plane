from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm import joinedload

from backend.app.core.errors import NotFoundError, DatabaseError
from backend.app.db.models.task import Task
from backend.app.db.models.project import Project
from backend.app.db.models.workspace import Workspace
from backend.app.schemas.task import TaskCreate, TaskUpdate


class TaskRepository:
    """Repository handling multi-tenant CRUD queries and persistence logic for Tasks."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id_and_owner(self, task_id: UUID, owner_user_id: UUID) -> Optional[Task]:
        stmt = (
            select(Task)
            .join(Project, Task.project_id == Project.id)
            .join(Workspace, Project.workspace_id == Workspace.id)
            .options(joinedload(Task.project))
            .where(
                Task.id == task_id,
                Workspace.owner_user_id == owner_user_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_and_owner_or_raise(self, task_id: UUID, owner_user_id: UUID) -> Task:
        task = await self.get_by_id_and_owner(task_id, owner_user_id)
        if not task:
            raise NotFoundError(f"Task with id '{task_id}' not found.")
        return task

    async def list_by_project(
        self,
        project_id: UUID,
        owner_user_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Task], int]:
        # Verify project belongs to user
        proj_stmt = (
            select(Project.id)
            .join(Workspace, Project.workspace_id == Workspace.id)
            .where(
                Project.id == project_id,
                Workspace.owner_user_id == owner_user_id,
            )
        )
        proj_res = await self.session.execute(proj_stmt)
        if not proj_res.scalar_one_or_none():
            raise NotFoundError(f"Project with id '{project_id}' not found.")

        # Count
        count_stmt = select(func.count(Task.id)).where(Task.project_id == project_id)
        if status:
            count_stmt = count_stmt.where(Task.status == status)
        count_res = await self.session.execute(count_stmt)
        total = count_res.scalar_one() or 0

        # Items
        stmt = select(Task).where(Task.project_id == project_id)
        if status:
            stmt = stmt.where(Task.status == status)
        stmt = stmt.order_by(Task.created_at.desc()).offset(skip).limit(limit)

        res = await self.session.execute(stmt)
        tasks = list(res.scalars().all())
        return tasks, total

    async def list_by_owner(
        self,
        owner_user_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Task], int]:
        count_stmt = (
            select(func.count(Task.id))
            .join(Project, Task.project_id == Project.id)
            .join(Workspace, Project.workspace_id == Workspace.id)
            .where(Workspace.owner_user_id == owner_user_id)
        )
        if status:
            count_stmt = count_stmt.where(Task.status == status)
        count_res = await self.session.execute(count_stmt)
        total = count_res.scalar_one() or 0

        stmt = (
            select(Task)
            .join(Project, Task.project_id == Project.id)
            .join(Workspace, Project.workspace_id == Workspace.id)
            .where(Workspace.owner_user_id == owner_user_id)
        )
        if status:
            stmt = stmt.where(Task.status == status)
        stmt = stmt.order_by(Task.created_at.desc()).offset(skip).limit(limit)

        res = await self.session.execute(stmt)
        return list(res.scalars().all()), total

    async def create(self, project_id: UUID, owner_user_id: UUID, data: TaskCreate) -> Task:
        # Check project belongs to user
        proj_stmt = (
            select(Project.id)
            .join(Workspace, Project.workspace_id == Workspace.id)
            .where(
                Project.id == project_id,
                Workspace.owner_user_id == owner_user_id,
            )
        )
        proj_res = await self.session.execute(proj_stmt)
        if not proj_res.scalar_one_or_none():
            raise NotFoundError(f"Project with id '{project_id}' not found.")

        task = Task(
            project_id=project_id,
            title=data.title.strip(),
            description=data.description.strip() if data.description else None,
            instructions=data.instructions.strip() if data.instructions else None,
            context_text=data.context_text.strip() if data.context_text else None,
            status=data.status.value if hasattr(data.status, "value") else str(data.status),
        )
        self.session.add(task)
        try:
            await self.session.flush()
            await self.session.refresh(task)
            return task
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError("Failed to create task in database.", details=str(e))

    async def update(self, task_id: UUID, owner_user_id: UUID, data: TaskUpdate) -> Task:
        task = await self.get_by_id_and_owner_or_raise(task_id, owner_user_id)

        if data.title is not None:
            task.title = data.title.strip()

        if data.description is not None:
            task.description = data.description.strip() if data.description else None

        if data.instructions is not None:
            task.instructions = data.instructions.strip() if data.instructions else None

        if data.context_text is not None:
            task.context_text = data.context_text.strip() if data.context_text else None

        if data.status is not None:
            task.status = data.status.value if hasattr(data.status, "value") else str(data.status)


        try:
            await self.session.flush()
            await self.session.refresh(task)
            return task
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError("Failed to update task.", details=str(e))

    async def delete(self, task_id: UUID, owner_user_id: UUID) -> bool:
        task = await self.get_by_id_and_owner_or_raise(task_id, owner_user_id)
        await self.session.delete(task)
        try:
            await self.session.flush()
            return True
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to delete task '{task_id}'.", details=str(e))
