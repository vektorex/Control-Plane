from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.errors import NotFoundError, DatabaseError
from backend.app.db.models.context import TaskContext
from backend.app.db.models.task import Task
from backend.app.db.models.project import Project
from backend.app.db.models.workspace import Workspace
from backend.app.schemas.context import TaskContextCreate, TaskContextUpdate


class ContextRepository:
    """Repository handling multi-tenant CRUD and retrieval queries for TaskContext records."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id_and_owner(self, context_id: UUID, owner_user_id: UUID) -> Optional[TaskContext]:
        stmt = (
            select(TaskContext)
            .join(Task, TaskContext.task_id == Task.id)
            .join(Project, Task.project_id == Project.id)
            .join(Workspace, Project.workspace_id == Workspace.id)
            .where(
                TaskContext.id == context_id,
                Workspace.owner_user_id == owner_user_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_and_owner_or_raise(self, context_id: UUID, owner_user_id: UUID) -> TaskContext:
        ctx = await self.get_by_id_and_owner(context_id, owner_user_id)
        if not ctx:
            raise NotFoundError(f"TaskContext with id '{context_id}' not found.")
        return ctx

    async def list_by_task(
        self,
        task_id: UUID,
        owner_user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[TaskContext], int]:
        # 1. Verify task belongs to user
        task_stmt = (
            select(Task.id)
            .join(Project, Task.project_id == Project.id)
            .join(Workspace, Project.workspace_id == Workspace.id)
            .where(
                Task.id == task_id,
                Workspace.owner_user_id == owner_user_id,
            )
        )
        task_res = await self.session.execute(task_stmt)
        if not task_res.scalar_one_or_none():
            raise NotFoundError(f"Task with id '{task_id}' not found.")

        # 2. Count
        count_stmt = select(func.count(TaskContext.id)).where(TaskContext.task_id == task_id)
        count_res = await self.session.execute(count_stmt)
        total = count_res.scalar_one() or 0

        # 3. Items ordered by priority desc, created_at desc
        stmt = (
            select(TaskContext)
            .where(TaskContext.task_id == task_id)
            .order_by(TaskContext.priority.desc(), TaskContext.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        items = list(res.scalars().all())
        return items, total

    async def create(
        self,
        task_id: UUID,
        owner_user_id: UUID,
        data: TaskContextCreate,
    ) -> TaskContext:
        # 1. Verify task belongs to user
        task_stmt = (
            select(Task.id)
            .join(Project, Task.project_id == Project.id)
            .join(Workspace, Project.workspace_id == Workspace.id)
            .where(
                Task.id == task_id,
                Workspace.owner_user_id == owner_user_id,
            )
        )
        task_res = await self.session.execute(task_stmt)
        if not task_res.scalar_one_or_none():
            raise NotFoundError(f"Task with id '{task_id}' not found.")

        ctx = TaskContext(
            task_id=task_id,
            source_type=data.source_type.strip().lower() if data.source_type else "manual",
            title=data.title.strip(),
            content=data.content.strip(),
            metadata_json=data.metadata or {},
            priority=data.priority,
        )
        self.session.add(ctx)
        try:
            await self.session.flush()
            await self.session.refresh(ctx)
            return ctx
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError("Failed to create task context item in database.", details=str(e))

    async def update(
        self,
        context_id: UUID,
        owner_user_id: UUID,
        data: TaskContextUpdate,
    ) -> TaskContext:
        ctx = await self.get_by_id_and_owner_or_raise(context_id, owner_user_id)

        if data.title is not None:
            ctx.title = data.title.strip()
        if data.content is not None:
            ctx.content = data.content.strip()
        if data.source_type is not None:
            ctx.source_type = data.source_type.strip().lower()
        if data.priority is not None:
            ctx.priority = data.priority
        if data.metadata is not None:
            ctx.metadata_json = data.metadata

        try:
            await self.session.flush()
            await self.session.refresh(ctx)
            return ctx
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to update task context '{context_id}'.", details=str(e))

    async def delete(
        self,
        context_id: UUID,
        owner_user_id: UUID,
    ) -> bool:
        ctx = await self.get_by_id_and_owner_or_raise(context_id, owner_user_id)
        await self.session.delete(ctx)
        try:
            await self.session.flush()
            return True
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to delete task context '{context_id}'.", details=str(e))
