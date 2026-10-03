"""
Database repository for Step 27: Multi-Tenant Organizations, Teams, Roles & Access Control.
Provides tenant-scoped queries, membership lookups, and transactional data operations.
"""
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.db.models.user import User
from backend.app.db.models.workspace import Workspace
from backend.app.db.models.project import Project
from backend.app.db.models.task import Task
from backend.app.db.models.workflow import Workflow
from backend.app.services.access_control.constants import (
    OrganizationStatus,
    MemberStatus,
    OrganizationRole,
    WorkspaceRole,
    ProjectRole,
    ProjectAccessMode,
)
from backend.app.services.access_control.models import (
    Organization,
    OrganizationMember,
    OrganizationInvitation,
    WorkspaceMember,
    ProjectMember,
)
from backend.app.services.access_control.errors import (
    ResourceNotFoundError,
    PermissionDeniedError,
)


class AccessControlRepository:
    """
    Direct database interaction layer for organizations, memberships, invitations,
    and scoped multi-tenant resource resolution.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # -------------------------------------------------------------------------
    # Organization Operations
    # -------------------------------------------------------------------------

    async def create_organization(
        self,
        name: str,
        slug: str,
        owner_user_id: UUID,
        status: str = OrganizationStatus.ACTIVE.value,
    ) -> Organization:
        org = Organization(
            name=name,
            slug=slug,
            owner_user_id=owner_user_id,
            status=status,
        )
        self.session.add(org)
        await self.session.flush()

        # Add creator as OWNER member
        member = OrganizationMember(
            organization_id=org.id,
            user_id=owner_user_id,
            role=OrganizationRole.OWNER.value,
            status=MemberStatus.ACTIVE.value,
            joined_at=func.now(),
        )
        self.session.add(member)
        await self.session.flush()
        await self.session.refresh(org)
        return org

    async def get_organization(self, org_id: UUID) -> Optional[Organization]:
        stmt = (
            select(Organization)
            .where(Organization.id == org_id)
            .options(
                selectinload(Organization.members),
                selectinload(Organization.workspaces),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_organization_by_slug(self, slug: str) -> Optional[Organization]:
        stmt = select(Organization).where(Organization.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_user_organizations(self, user_id: UUID) -> List[Organization]:
        """Lists all organizations where user is an active member or owner."""
        stmt = (
            select(Organization)
            .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
            .where(
                OrganizationMember.user_id == user_id,
                OrganizationMember.status == MemberStatus.ACTIVE.value,
                Organization.status != OrganizationStatus.ARCHIVED.value,
            )
            .options(
                selectinload(Organization.members),
                selectinload(Organization.workspaces),
            )
            .order_by(Organization.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_organization(
        self,
        org_id: UUID,
        name: Optional[str] = None,
        slug: Optional[str] = None,
    ) -> Organization:
        org = await self.get_organization(org_id)
        if not org:
            raise ResourceNotFoundError(f"Organization '{org_id}' not found.")
        if name is not None:
            org.name = name
        if slug is not None:
            org.slug = slug
        await self.session.flush()
        await self.session.refresh(org)
        return org

    async def archive_organization(self, org_id: UUID) -> Organization:
        org = await self.get_organization(org_id)
        if not org:
            raise ResourceNotFoundError(f"Organization '{org_id}' not found.")
        org.status = OrganizationStatus.ARCHIVED.value
        await self.session.flush()
        await self.session.refresh(org)
        return org

    # -------------------------------------------------------------------------
    # Organization Membership Operations
    # -------------------------------------------------------------------------

    async def get_member(self, org_id: UUID, user_id: UUID) -> Optional[OrganizationMember]:
        stmt = (
            select(OrganizationMember)
            .where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
            )
            .options(selectinload(OrganizationMember.user))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_member_by_id(self, member_id: UUID) -> Optional[OrganizationMember]:
        stmt = (
            select(OrganizationMember)
            .where(OrganizationMember.id == member_id)
            .options(selectinload(OrganizationMember.user))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_members(self, org_id: UUID) -> List[OrganizationMember]:
        stmt = (
            select(OrganizationMember)
            .where(OrganizationMember.organization_id == org_id)
            .options(selectinload(OrganizationMember.user))
            .order_by(OrganizationMember.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_active_members(self, org_id: UUID) -> int:
        stmt = (
            select(func.count(OrganizationMember.id))
            .where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.status == MemberStatus.ACTIVE.value,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def add_member(
        self,
        org_id: UUID,
        user_id: UUID,
        role: str = OrganizationRole.MEMBER.value,
        status: str = MemberStatus.ACTIVE.value,
    ) -> OrganizationMember:
        member = OrganizationMember(
            organization_id=org_id,
            user_id=user_id,
            role=role,
            status=status,
            joined_at=func.now() if status == MemberStatus.ACTIVE.value else None,
        )
        self.session.add(member)
        await self.session.flush()
        await self.session.refresh(member)
        return member

    async def update_member(
        self,
        member_id: UUID,
        role: Optional[str] = None,
        status: Optional[str] = None,
    ) -> OrganizationMember:
        member = await self.get_member_by_id(member_id)
        if not member:
            raise ResourceNotFoundError(f"Member '{member_id}' not found.")
        if role is not None:
            member.role = role
        if status is not None:
            member.status = status
            if status == MemberStatus.ACTIVE.value and not member.joined_at:
                member.joined_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(member)
        return member

    async def remove_member(self, member_id: UUID) -> None:
        member = await self.get_member_by_id(member_id)
        if member:
            await self.session.delete(member)
            await self.session.flush()

    # -------------------------------------------------------------------------
    # Invitation Operations
    # -------------------------------------------------------------------------

    async def create_invitation(
        self,
        org_id: UUID,
        email: str,
        role: str,
        token_hash: str,
        invited_by: UUID,
        expires_at: datetime,
    ) -> OrganizationInvitation:
        invitation = OrganizationInvitation(
            organization_id=org_id,
            email=email.strip().lower(),
            role=role,
            token_hash=token_hash,
            invited_by=invited_by,
            expires_at=expires_at,
        )
        self.session.add(invitation)
        await self.session.flush()
        await self.session.refresh(invitation)
        return invitation

    async def get_invitation_by_token_hash(self, token_hash: str) -> Optional[OrganizationInvitation]:
        stmt = (
            select(OrganizationInvitation)
            .where(OrganizationInvitation.token_hash == token_hash)
            .options(selectinload(OrganizationInvitation.organization))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_invitation_by_id(self, invitation_id: UUID) -> Optional[OrganizationInvitation]:
        stmt = select(OrganizationInvitation).where(OrganizationInvitation.id == invitation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_invitations(self, org_id: UUID) -> List[OrganizationInvitation]:
        stmt = (
            select(OrganizationInvitation)
            .where(
                OrganizationInvitation.organization_id == org_id,
                OrganizationInvitation.revoked_at.is_(None),
                OrganizationInvitation.accepted_at.is_(None),
            )
            .order_by(OrganizationInvitation.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def revoke_invitation(self, invitation_id: UUID) -> OrganizationInvitation:
        invitation = await self.get_invitation_by_id(invitation_id)
        if not invitation:
            raise ResourceNotFoundError(f"Invitation '{invitation_id}' not found.")
        invitation.revoked_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(invitation)
        return invitation

    async def mark_invitation_accepted(self, invitation_id: UUID) -> OrganizationInvitation:
        invitation = await self.get_invitation_by_id(invitation_id)
        if not invitation:
            raise ResourceNotFoundError(f"Invitation '{invitation_id}' not found.")
        invitation.accepted_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(invitation)
        return invitation

    # -------------------------------------------------------------------------
    # Workspace Member Operations
    # -------------------------------------------------------------------------

    async def get_workspace_member(self, workspace_id: UUID, user_id: UUID) -> Optional[WorkspaceMember]:
        stmt = (
            select(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
            .options(selectinload(WorkspaceMember.user))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_workspace_member_by_id(self, member_id: UUID) -> Optional[WorkspaceMember]:
        stmt = select(WorkspaceMember).where(WorkspaceMember.id == member_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_workspace_members(self, workspace_id: UUID) -> List[WorkspaceMember]:
        stmt = (
            select(WorkspaceMember)
            .where(WorkspaceMember.workspace_id == workspace_id)
            .options(selectinload(WorkspaceMember.user))
            .order_by(WorkspaceMember.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_workspace_member(
        self,
        workspace_id: UUID,
        user_id: UUID,
        role: str = WorkspaceRole.MEMBER.value,
        status: str = MemberStatus.ACTIVE.value,
    ) -> WorkspaceMember:
        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=user_id,
            role=role,
            status=status,
        )
        self.session.add(member)
        await self.session.flush()
        await self.session.refresh(member)
        return member

    async def update_workspace_member(
        self,
        member_id: UUID,
        role: Optional[str] = None,
        status: Optional[str] = None,
    ) -> WorkspaceMember:
        member = await self.get_workspace_member_by_id(member_id)
        if not member:
            raise ResourceNotFoundError(f"Workspace member '{member_id}' not found.")
        if role is not None:
            member.role = role
        if status is not None:
            member.status = status
        await self.session.flush()
        await self.session.refresh(member)
        return member

    async def remove_workspace_member(self, member_id: UUID) -> None:
        member = await self.get_workspace_member_by_id(member_id)
        if member:
            await self.session.delete(member)
            await self.session.flush()

    # -------------------------------------------------------------------------
    # Project Member Operations
    # -------------------------------------------------------------------------

    async def get_project_member(self, project_id: UUID, user_id: UUID) -> Optional[ProjectMember]:
        stmt = (
            select(ProjectMember)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
            .options(selectinload(ProjectMember.user))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_project_member_by_id(self, member_id: UUID) -> Optional[ProjectMember]:
        stmt = select(ProjectMember).where(ProjectMember.id == member_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_project_members(self, project_id: UUID) -> List[ProjectMember]:
        stmt = (
            select(ProjectMember)
            .where(ProjectMember.project_id == project_id)
            .options(selectinload(ProjectMember.user))
            .order_by(ProjectMember.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_project_member(
        self,
        project_id: UUID,
        user_id: UUID,
        role: str = ProjectRole.EDITOR.value,
    ) -> ProjectMember:
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role,
        )
        self.session.add(member)
        await self.session.flush()
        await self.session.refresh(member)
        return member

    async def update_project_member(
        self,
        member_id: UUID,
        role: str,
    ) -> ProjectMember:
        member = await self.get_project_member_by_id(member_id)
        if not member:
            raise ResourceNotFoundError(f"Project member '{member_id}' not found.")
        member.role = role
        await self.session.flush()
        await self.session.refresh(member)
        return member

    async def remove_project_member(self, member_id: UUID) -> None:
        member = await self.get_project_member_by_id(member_id)
        if member:
            await self.session.delete(member)
            await self.session.flush()

    # -------------------------------------------------------------------------
    # Tenant Scope & Authorization Resolution
    # -------------------------------------------------------------------------

    async def resolve_authorization_chain(
        self,
        user_id: UUID,
        organization_id: Optional[UUID] = None,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
    ) -> Tuple[Optional[UUID], Optional[str], Optional[UUID], Optional[str], Optional[UUID], Optional[str], str]:
        """
        Resolves the full authorization chain for a user:
        (resolved_org_id, org_role, resolved_ws_id, ws_role, resolved_proj_id, proj_role, proj_access_mode)
        """
        # If project_id provided, infer workspace and org
        if project_id:
            p_stmt = select(Project).where(Project.id == project_id)
            p_res = await self.session.execute(p_stmt)
            project = p_res.scalar_one_or_none()
            if project:
                workspace_id = project.workspace_id

        # If workspace_id provided, infer org
        if workspace_id:
            w_stmt = select(Workspace).where(Workspace.id == workspace_id)
            w_res = await self.session.execute(w_stmt)
            workspace = w_res.scalar_one_or_none()
            if workspace and workspace.organization_id:
                organization_id = workspace.organization_id

        # If organization_id is still not known, find user's primary/first organization
        if not organization_id:
            orgs = await self.list_user_organizations(user_id)
            if orgs:
                organization_id = orgs[0].id

        if not organization_id:
            return None, None, None, None, None, None, ProjectAccessMode.WORKSPACE.value

        # Resolve organization role
        org_member = await self.get_member(organization_id, user_id)
        if not org_member or org_member.status != MemberStatus.ACTIVE.value:
            # Check if user is the direct owner of the organization
            org = await self.get_organization(organization_id)
            if org and org.owner_user_id == user_id:
                org_role = OrganizationRole.OWNER.value
            else:
                return organization_id, None, workspace_id, None, project_id, None, ProjectAccessMode.WORKSPACE.value
        else:
            org_role = org_member.role

        # Resolve workspace role
        ws_role = None
        if workspace_id:
            ws_member = await self.get_workspace_member(workspace_id, user_id)
            if ws_member and ws_member.status == MemberStatus.ACTIVE.value:
                ws_role = ws_member.role
            else:
                # If org owner or admin, they inherit workspace admin capabilities
                if org_role in {OrganizationRole.OWNER.value, OrganizationRole.ADMIN.value}:
                    ws_role = WorkspaceRole.ADMIN.value
                else:
                    # Check if user is owner_user_id on workspace
                    w_check = await self.session.execute(select(Workspace).where(Workspace.id == workspace_id))
                    w_obj = w_check.scalar_one_or_none()
                    if w_obj and w_obj.owner_user_id == user_id:
                        ws_role = WorkspaceRole.ADMIN.value

        # Resolve project role and access mode
        proj_role = None
        proj_access_mode = ProjectAccessMode.WORKSPACE.value
        if project_id:
            p_check = await self.session.execute(select(Project).where(Project.id == project_id))
            p_obj = p_check.scalar_one_or_none()
            if p_obj:
                proj_access_mode = getattr(p_obj, "access_mode", ProjectAccessMode.WORKSPACE.value)
                p_member = await self.get_project_member(project_id, user_id)
                if p_member:
                    proj_role = p_member.role
                elif org_role in {OrganizationRole.OWNER.value, OrganizationRole.ADMIN.value} or ws_role == WorkspaceRole.ADMIN.value:
                    proj_role = ProjectRole.EDITOR.value

        return organization_id, org_role, workspace_id, ws_role, project_id, proj_role, proj_access_mode
