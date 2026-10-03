from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from backend.app.core.errors import ConflictError, NotFoundError, DatabaseError
from backend.app.db.models.workspace import Workspace
from backend.app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate, slugify


class WorkspaceRepository:
    """Repository handling multi-tenant CRUD queries and persistence logic for Workspaces."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id_and_owner(self, workspace_id: UUID, owner_user_id: UUID) -> Optional[Workspace]:
        # 1. Direct owner match
        stmt = select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.owner_user_id == owner_user_id,
        )
        result = await self.session.execute(stmt)
        ws = result.scalar_one_or_none()
        if ws:
            return ws

        # 2. Workspace member match
        from backend.app.services.access_control.models import WorkspaceMember, OrganizationMember
        from backend.app.services.access_control.constants import MemberStatus, OrganizationRole

        wm_stmt = (
            select(Workspace)
            .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
            .where(
                Workspace.id == workspace_id,
                WorkspaceMember.user_id == owner_user_id,
                WorkspaceMember.status == MemberStatus.ACTIVE.value,
            )
        )
        wm_res = await self.session.execute(wm_stmt)
        ws = wm_res.scalar_one_or_none()
        if ws:
            return ws

        # 3. Organization Member match (active members of the organization)
        om_stmt = (
            select(Workspace)
            .join(OrganizationMember, Workspace.organization_id == OrganizationMember.organization_id)
            .where(
                Workspace.id == workspace_id,
                OrganizationMember.user_id == owner_user_id,
                OrganizationMember.status == MemberStatus.ACTIVE.value,
            )
        )
        om_res = await self.session.execute(om_stmt)
        return om_res.scalar_one_or_none()

    async def get_by_id_and_owner_or_raise(self, workspace_id: UUID, owner_user_id: UUID) -> Workspace:
        workspace = await self.get_by_id_and_owner(workspace_id, owner_user_id)
        if not workspace:
            raise NotFoundError(f"Workspace with id '{workspace_id}' not found.")
        return workspace

    async def get_by_slug_and_owner(self, slug: str, owner_user_id: UUID) -> Optional[Workspace]:
        stmt = select(Workspace).where(
            Workspace.slug == slug,
            Workspace.owner_user_id == owner_user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_owner(
        self, owner_user_id: UUID, skip: int = 0, limit: int = 100
    ) -> Tuple[List[Workspace], int]:
        from backend.app.services.access_control.models import WorkspaceMember, OrganizationMember
        from backend.app.services.access_control.constants import MemberStatus, OrganizationRole

        owned_query = select(Workspace.id).where(Workspace.owner_user_id == owner_user_id)
        member_query = select(WorkspaceMember.workspace_id).where(
            WorkspaceMember.user_id == owner_user_id,
            WorkspaceMember.status == MemberStatus.ACTIVE.value,
        )
        org_member_query = (
            select(Workspace.id)
            .join(OrganizationMember, Workspace.organization_id == OrganizationMember.organization_id)
            .where(
                OrganizationMember.user_id == owner_user_id,
                OrganizationMember.status == MemberStatus.ACTIVE.value,
            )
        )

        all_ids_stmt = owned_query.union(member_query, org_member_query)
        all_ids_res = await self.session.execute(all_ids_stmt)
        accessible_ids = list(set(all_ids_res.scalars().all()))

        if not accessible_ids:
            return [], 0

        total = len(accessible_ids)

        stmt = (
            select(Workspace)
            .where(Workspace.id.in_(accessible_ids))
            .order_by(Workspace.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        workspaces = list(res.scalars().all())
        return workspaces, total

    async def create(self, owner_user_id: UUID, data: WorkspaceCreate) -> Workspace:
        slug = data.slug or slugify(data.name)
        if not slug:
            slug = "default-workspace"

        # Check existing slug scoped to this user
        existing = await self.get_by_slug_and_owner(slug, owner_user_id)
        if existing:
            raise ConflictError(f"A workspace with slug '{slug}' already exists in your account.")

        org_id = getattr(data, "organization_id", None)
        if not org_id:
            from backend.app.services.access_control.models import Organization
            org_res = await self.session.execute(
                select(Organization.id).where(Organization.owner_user_id == owner_user_id).limit(1)
            )
            org_id = org_res.scalar_one_or_none()

        workspace = Workspace(
            owner_user_id=owner_user_id,
            organization_id=org_id,
            name=data.name.strip(),
            slug=slug,
            status="active",
        )
        self.session.add(workspace)
        try:
            await self.session.flush()

            # Add creator as workspace admin member
            from backend.app.services.access_control.models import WorkspaceMember
            ws_member = WorkspaceMember(
                workspace_id=workspace.id,
                user_id=owner_user_id,
                role="admin",
                status="active",
            )
            self.session.add(ws_member)
            await self.session.flush()

            await self.session.refresh(workspace)
            return workspace
        except IntegrityError as e:
            await self.session.rollback()
            raise ConflictError(f"A workspace with slug '{slug}' already exists.", details=str(e))
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError("Failed to create workspace in database.", details=str(e))

    async def update(self, workspace_id: UUID, owner_user_id: UUID, data: WorkspaceUpdate) -> Workspace:
        workspace = await self.get_by_id_and_owner_or_raise(workspace_id, owner_user_id)

        if data.name is not None:
            workspace.name = data.name.strip()

        if data.slug is not None:
            new_slug = slugify(data.slug)
            if new_slug != workspace.slug:
                existing = await self.get_by_slug_and_owner(new_slug, owner_user_id)
                if existing and existing.id != workspace.id:
                    raise ConflictError(f"A workspace with slug '{new_slug}' already exists in your account.")
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

    async def delete(self, workspace_id: UUID, owner_user_id: UUID) -> bool:
        workspace = await self.get_by_id_and_owner_or_raise(workspace_id, owner_user_id)
        await self.session.delete(workspace)
        try:
            await self.session.flush()
            return True
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to delete workspace '{workspace_id}'.", details=str(e))
