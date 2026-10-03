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
    """Repository handling multi-tenant CRUD queries and persistence logic for Projects."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id_and_owner(self, project_id: UUID, owner_user_id: UUID) -> Optional[Project]:
        stmt = select(Project).where(Project.id == project_id)
        result = await self.session.execute(stmt)
        project = result.scalar_one_or_none()
        if not project:
            return None

        # Verify access to parent workspace
        from backend.app.repositories.workspace import WorkspaceRepository
        ws_repo = WorkspaceRepository(self.session)
        ws = await ws_repo.get_by_id_and_owner(project.workspace_id, owner_user_id)
        if not ws:
            return None

        # If project is restricted, verify project membership or admin privileges
        if getattr(project, "access_mode", "workspace") == "restricted":
            from backend.app.services.access_control.models import ProjectMember, WorkspaceMember, OrganizationMember
            from backend.app.services.access_control.constants import MemberStatus, OrganizationRole, WorkspaceRole

            # 1. Project member
            pm_stmt = select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == owner_user_id,
            )
            if (await self.session.execute(pm_stmt)).scalar_one_or_none():
                return project

            # 2. Workspace admin
            wm_stmt = select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == project.workspace_id,
                WorkspaceMember.user_id == owner_user_id,
                WorkspaceMember.role == WorkspaceRole.ADMIN.value,
                WorkspaceMember.status == MemberStatus.ACTIVE.value,
            )
            if (await self.session.execute(wm_stmt)).scalar_one_or_none():
                return project

            # 3. Workspace direct owner
            if ws.owner_user_id == owner_user_id:
                return project

            # 4. Org owner/admin
            if ws.organization_id:
                om_stmt = select(OrganizationMember).where(
                    OrganizationMember.organization_id == ws.organization_id,
                    OrganizationMember.user_id == owner_user_id,
                    OrganizationMember.role.in_([OrganizationRole.OWNER.value, OrganizationRole.ADMIN.value]),
                    OrganizationMember.status == MemberStatus.ACTIVE.value,
                )
                if (await self.session.execute(om_stmt)).scalar_one_or_none():
                    return project

            # Restricted and unauthorized
            return None

        return project

    async def get_by_id_and_owner_or_raise(self, project_id: UUID, owner_user_id: UUID) -> Project:
        project = await self.get_by_id_and_owner(project_id, owner_user_id)
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
        self, workspace_id: UUID, owner_user_id: UUID, skip: int = 0, limit: int = 100
    ) -> Tuple[List[Project], int]:
        from backend.app.repositories.workspace import WorkspaceRepository
        ws_repo = WorkspaceRepository(self.session)
        ws = await ws_repo.get_by_id_and_owner(workspace_id, owner_user_id)
        if not ws:
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
        all_projects = list(res.scalars().all())

        # Filter out restricted projects if user is not authorized
        visible = []
        for p in all_projects:
            if getattr(p, "access_mode", "workspace") == "restricted":
                authorized = await self.get_by_id_and_owner(p.id, owner_user_id)
                if authorized:
                    visible.append(p)
            else:
                visible.append(p)

        return visible, len(visible)

    async def list_by_owner(
        self, owner_user_id: UUID, skip: int = 0, limit: int = 100
    ) -> Tuple[List[Project], int]:
        from backend.app.repositories.workspace import WorkspaceRepository
        ws_repo = WorkspaceRepository(self.session)
        workspaces, _ = await ws_repo.list_by_owner(owner_user_id, skip=0, limit=1000)
        ws_ids = [w.id for w in workspaces]
        if not ws_ids:
            return [], 0

        stmt = (
            select(Project)
            .where(Project.workspace_id.in_(ws_ids))
            .order_by(Project.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        all_projs = list(res.scalars().all())
        visible = []
        for p in all_projs:
            authorized = await self.get_by_id_and_owner(p.id, owner_user_id)
            if authorized:
                visible.append(p)

        return visible, len(visible)

    async def create(self, workspace_id: UUID, owner_user_id: UUID, data: ProjectCreate) -> Project:
        from backend.app.repositories.workspace import WorkspaceRepository
        ws_repo = WorkspaceRepository(self.session)
        ws = await ws_repo.get_by_id_and_owner(workspace_id, owner_user_id)
        if not ws:
            raise NotFoundError(f"Workspace with id '{workspace_id}' not found.")

        slug = data.slug or slugify(data.name)
        if not slug:
            slug = "default-project"

        existing = await self.get_by_slug(workspace_id, slug)
        if existing:
            raise ConflictError(f"A project with slug '{slug}' already exists in this workspace.")

        project = Project(
            workspace_id=workspace_id,
            name=data.name.strip(),
            slug=slug,
            description=data.description.strip() if data.description else None,
            access_mode=getattr(data, "access_mode", "workspace") or "workspace",
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

    async def update(self, project_id: UUID, owner_user_id: UUID, data: ProjectUpdate) -> Project:
        project = await self.get_by_id_and_owner_or_raise(project_id, owner_user_id)

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

        if data.access_mode is not None:
            project.access_mode = data.access_mode

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

    async def delete(self, project_id: UUID, owner_user_id: UUID) -> bool:
        project = await self.get_by_id_and_owner_or_raise(project_id, owner_user_id)
        await self.session.delete(project)
        try:
            await self.session.flush()
            return True
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to delete project '{project_id}'.", details=str(e))
