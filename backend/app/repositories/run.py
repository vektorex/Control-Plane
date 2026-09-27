from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.errors import NotFoundError, DatabaseError
from backend.app.db.models.run import Run
from backend.app.db.models.task import Task
from backend.app.schemas.run import RunCreate


class RunRepository:
    """Repository handling all CRUD and retrieval queries for Task Runs."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, run_id: UUID) -> Optional[Run]:
        stmt = select(Run).where(Run.id == run_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_or_raise(self, run_id: UUID) -> Run:
        run = await self.get_by_id(run_id)
        if not run:
            raise NotFoundError(f"Run with id '{run_id}' not found.")
        return run

    async def list_by_task(
        self, task_id: UUID, skip: int = 0, limit: int = 100
    ) -> Tuple[List[Run], int]:
        # Check task exists
        task_stmt = select(Task.id).where(Task.id == task_id)
        task_res = await self.session.execute(task_stmt)
        if not task_res.scalar_one_or_none():
            raise NotFoundError(f"Task with id '{task_id}' not found.")

        # Count
        count_stmt = select(func.count(Run.id)).where(Run.task_id == task_id)
        count_res = await self.session.execute(count_stmt)
        total = count_res.scalar_one() or 0

        # Items
        stmt = (
            select(Run)
            .where(Run.task_id == task_id)
            .order_by(Run.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        runs = list(res.scalars().all())
        return runs, total

    async def create(self, task_id: UUID, data: RunCreate) -> Run:
        # Check task exists
        task_stmt = select(Task.id).where(Task.id == task_id)
        task_res = await self.session.execute(task_stmt)
        if not task_res.scalar_one_or_none():
            raise NotFoundError(f"Task with id '{task_id}' not found.")

        run = Run(
            task_id=task_id,
            status=data.status.value if hasattr(data.status, "value") else str(data.status),
            model_provider=data.model_provider,
            model_name=data.model_name,
            input_tokens=data.input_tokens,
            output_tokens=data.output_tokens,
            total_tokens=data.total_tokens,
            latency_ms=data.latency_ms,
            error_message=data.error_message,
            completed_at=data.completed_at,
        )
        self.session.add(run)
        try:
            await self.session.flush()
            await self.session.refresh(run)
            return run
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError("Failed to create task execution run.", details=str(e))
