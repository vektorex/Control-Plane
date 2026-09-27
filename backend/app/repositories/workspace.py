from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from backend.app.core.errors import ConflictError, NotFoundError, DatabaseError
from backend.app.db.models.workspace import Workspace
from backend.app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate, slugify


class WorkspaceRepository:
    """Repository handling all CRUD queries and persistence logic for Workspaces."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, workspace_id: UUID) -> Optional[Workspace]:
        stmt = select(Workspace).where(Workspace.id == workspace_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_or_raise(self, workspace_id: UUID) -> Workspace:
        workspace = await self.get_by_id(workspace_id)
        if not workspace:
            raise NotFoundError(f"Workspace with id '{workspace_id}' not found.")
        return workspace

    async def get_by_slug(self, slug: str) -> Optional[Workspace]:
        stmt = select(Workspace).where(Workspace.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, skip: int = 0, limit: int = 100) -> Tuple[List[Workspace], int]:
        # Count query
        count_stmt = select(func.count(Workspace.id))
        count_res = await self.session.execute(count_stmt)
        total = count_res.scalar_one() or 0

        # Items query ordered by created_at desc
        stmt = (
            select(Workspace)
            .order_by(Workspace.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        workspaces = list(res.scalars().all())
        return workspaces, total

    async def create(self, data: WorkspaceCreate) -> Workspace:
        slug = data.slug or slugify(data.name)
        if not slug:
            slug = "default-workspace"

        # Check existing slug
        existing = await self.get_by_slug(slug)
        if existing:
            raise ConflictError(f"A workspace with slug '{slug}' already exists.")

        workspace = Workspace(
            name=data.name.strip(),
            slug=slug,
        )
        self.session.add(workspace)
        try:
            await self.session.flush()
            await self.session.refresh(workspace)
            return workspace
        except IntegrityError as e:
            await self.session.rollback()
            raise ConflictError(f"A workspace with slug '{slug}' already exists.", details=str(e))
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError("Failed to create workspace in database.", details=str(e))

    async def update(self, workspace_id: UUID, data: WorkspaceUpdate) -> Workspace:
        workspace = await self.get_by_id_or_raise(workspace_id)

        if data.name is not None:
            workspace.name = data.name.strip()

        if data.slug is not None:
            new_slug = slugify(data.slug)
            if new_slug != workspace.slug:
                existing = await self.get_by_slug(new_slug)
                if existing and existing.id != workspace.id:
                    raise ConflictError(f"A workspace with slug '{new_slug}' already exists.")
                workspace.slug = new_slug

        try:
            await self.session.flush()
            await self.session.refresh(workspace)
            return workspace
        except IntegrityError as e:
            await self.session.rollback()
            raise ConflictError("Uniqueness constraint violation during workspace update.", details=str(e))
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError("Failed to update workspace.", details=str(e))

    async def delete(self, workspace_id: UUID) -> bool:
        workspace = await self.get_by_id_or_raise(workspace_id)
        await self.session.delete(workspace)
        try:
            await self.session.flush()
            return True
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to delete workspace '{workspace_id}'.", details=str(e))
