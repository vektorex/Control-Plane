from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from backend.app.core.errors import ConflictError, NotFoundError, DatabaseError
from backend.app.db.models.project import Project
from backend.app.db.models.workspace import Workspace
from backend.app.schemas.project import ProjectCreate, ProjectUpdate
from backend.app.schemas.workspace import slugify


class ProjectRepository:
    """Repository handling all CRUD queries and persistence logic for Projects."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, project_id: UUID) -> Optional[Project]:
        stmt = select(Project).where(Project.id == project_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_or_raise(self, project_id: UUID) -> Project:
        project = await self.get_by_id(project_id)
        if not project:
            raise NotFoundError(f"Project with id '{project_id}' not found.")
        return project

    async def get_by_slug(self, workspace_id: UUID, slug: str) -> Optional[Project]:
        stmt = select(Project).where(
            Project.workspace_id == workspace_id,
            Project.slug == slug,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_workspace(
        self, workspace_id: UUID, skip: int = 0, limit: int = 100
    ) -> Tuple[List[Project], int]:
        # Verify workspace exists
        ws_stmt = select(Workspace.id).where(Workspace.id == workspace_id)
        ws_res = await self.session.execute(ws_stmt)
        if not ws_res.scalar_one_or_none():
            raise NotFoundError(f"Workspace with id '{workspace_id}' not found.")

        # Count
        count_stmt = select(func.count(Project.id)).where(Project.workspace_id == workspace_id)
        count_res = await self.session.execute(count_stmt)
        total = count_res.scalar_one() or 0

        # Items
        stmt = (
            select(Project)
            .where(Project.workspace_id == workspace_id)
            .order_by(Project.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        projects = list(res.scalars().all())
        return projects, total

    async def list_all(self, skip: int = 0, limit: int = 100) -> Tuple[List[Project], int]:
        count_stmt = select(func.count(Project.id))
        count_res = await self.session.execute(count_stmt)
        total = count_res.scalar_one() or 0

        stmt = (
            select(Project)
            .order_by(Project.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all()), total

    async def create(self, workspace_id: UUID, data: ProjectCreate) -> Project:
        # Check workspace exists
        ws_stmt = select(Workspace.id).where(Workspace.id == workspace_id)
        ws_res = await self.session.execute(ws_stmt)
        if not ws_res.scalar_one_or_none():
            raise NotFoundError(f"Workspace with id '{workspace_id}' not found.")

        slug = data.slug or slugify(data.name)
        if not slug:
            slug = "default-project"

        # Check existing slug in same workspace
        existing = await self.get_by_slug(workspace_id, slug)
        if existing:
            raise ConflictError(f"A project with slug '{slug}' already exists in this workspace.")

        project = Project(
            workspace_id=workspace_id,
            name=data.name.strip(),
            slug=slug,
            description=data.description.strip() if data.description else None,
        )
        self.session.add(project)
        try:
            await self.session.flush()
            await self.session.refresh(project)
            return project
        except IntegrityError as e:
            await self.session.rollback()
            raise ConflictError(f"A project with slug '{slug}' already exists in this workspace.", details=str(e))
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError("Failed to create project in database.", details=str(e))

    async def update(self, project_id: UUID, data: ProjectUpdate) -> Project:
        project = await self.get_by_id_or_raise(project_id)

        if data.name is not None:
            project.name = data.name.strip()

        if data.description is not None:
            project.description = data.description.strip() if data.description else None

        if data.slug is not None:
            new_slug = slugify(data.slug)
            if new_slug != project.slug:
                existing = await self.get_by_slug(project.workspace_id, new_slug)
                if existing and existing.id != project.id:
                    raise ConflictError(f"A project with slug '{new_slug}' already exists in this workspace.")
                project.slug = new_slug

        try:
            await self.session.flush()
            await self.session.refresh(project)
            return project
        except IntegrityError as e:
            await self.session.rollback()
            raise ConflictError("Uniqueness constraint violation during project update.", details=str(e))
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError("Failed to update project.", details=str(e))

    async def delete(self, project_id: UUID) -> bool:
        project = await self.get_by_id_or_raise(project_id)
        await self.session.delete(project)
        try:
            await self.session.flush()
            return True
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to delete project '{project_id}'.", details=str(e))
