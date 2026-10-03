"""
AccessControlService: Primary coordinator for multi-tenant organizations,
ownership transfer, workspaces, and tenant isolation in Step 27.
"""
import re
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.errors import ConflictError
from backend.app.db.models.user import User
from backend.app.db.models.workspace import Workspace
from backend.app.db.models.project import Project
from backend.app.services.access_control.constants import (
    ORGANIZATION_MAX_WORKSPACES,
    OrganizationRole,
    WorkspaceRole,
    MemberStatus,
    AccessControlAuditEvent,
)
from backend.app.services.access_control.errors import (
    AccessControlError,
    OwnershipTransferError,
    PermissionDeniedError,
    QuotaExceededError,
    ResourceNotFoundError,
)
from backend.app.services.access_control.permissions import (
    ORGANIZATION_READ,
    ORGANIZATION_UPDATE,
    ORGANIZATION_DELETE,
    WORKSPACE_CREATE,
    WORKSPACE_READ,
)
from backend.app.services.access_control.models import Organization
from backend.app.services.access_control.repository import AccessControlRepository
from backend.app.services.access_control.authorization import AuthorizationService
from backend.app.services.access_control.membership import MembershipService
from backend.app.services.access_control.invitations import InvitationService
from backend.app.services.access_control.audit import AccessControlAudit


class AccessControlService:
    """
    Main façade for multi-tenant organizations, access control, and workspace scoping.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = AccessControlRepository(session)
        self.authorization = AuthorizationService(session)
        self.membership = MembershipService(session)
        self.invitations = InvitationService(session)

    # -------------------------------------------------------------------------
    # Organization Management
    # -------------------------------------------------------------------------

    async def create_organization(
        self,
        name: str,
        user: User,
        slug: Optional[str] = None,
    ) -> Organization:
        """
        Creates a new organization owned by the caller. Caller becomes OWNER.
        """
        final_slug = slug
        if not final_slug:
            # Auto-generate URL-safe slug from name
            base_slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.lower()).strip("-")
            final_slug = base_slug or "org"

        # Ensure slug uniqueness
        existing = await self.repository.get_organization_by_slug(final_slug)
        if existing:
            import uuid
            final_slug = f"{final_slug}-{uuid.uuid4().hex[:6]}"

        org = await self.repository.create_organization(
            name=name,
            slug=final_slug,
            owner_user_id=user.id,
        )

        await AccessControlAudit.log_action(
            session=self.session,
            action=AccessControlAuditEvent.ORGANIZATION_CREATED,
            actor_user_id=user.id,
            organization_id=org.id,
            details={"name": name, "slug": final_slug},
        )
        return org

    async def get_organization(
        self,
        org_id: UUID,
        current_user: User,
    ) -> Organization:
        await self.authorization.authorize(
            user=current_user,
            permission=ORGANIZATION_READ,
            organization_id=org_id,
        )
        org = await self.repository.get_organization(org_id)
        if not org:
            raise ResourceNotFoundError(f"Organization '{org_id}' not found.")
        return org

    async def list_user_organizations(
        self,
        current_user: User,
    ) -> List[Organization]:
        return await self.repository.list_user_organizations(current_user.id)

    async def update_organization(
        self,
        org_id: UUID,
        current_user: User,
        name: Optional[str] = None,
        slug: Optional[str] = None,
    ) -> Organization:
        await self.authorization.authorize(
            user=current_user,
            permission=ORGANIZATION_UPDATE,
            organization_id=org_id,
        )
        if slug:
            existing = await self.repository.get_organization_by_slug(slug)
            if existing and existing.id != org_id:
                raise ConflictError(f"Slug '{slug}' is already taken.")

        org = await self.repository.update_organization(org_id, name=name, slug=slug)
        await AccessControlAudit.log_action(
            session=self.session,
            action=AccessControlAuditEvent.ORGANIZATION_UPDATED,
            actor_user_id=current_user.id,
            organization_id=org_id,
            details={"name": name, "slug": slug},
        )
        return org

    async def archive_organization(
        self,
        org_id: UUID,
        current_user: User,
    ) -> Organization:
        """
        Soft deletes / archives an organization. Only OWNER may delete.
        Child data is preserved.
        """
        await self.authorization.authorize(
            user=current_user,
            permission=ORGANIZATION_DELETE,
            organization_id=org_id,
        )
        org = await self.repository.archive_organization(org_id)
        await AccessControlAudit.log_action(
            session=self.session,
            action=AccessControlAuditEvent.ORGANIZATION_ARCHIVED,
            actor_user_id=current_user.id,
            organization_id=org_id,
        )
        return org

    # -------------------------------------------------------------------------
    # Ownership Transfer
    # -------------------------------------------------------------------------

    async def transfer_ownership(
        self,
        org_id: UUID,
        target_user_id: UUID,
        confirmation: bool,
        current_user: User,
    ) -> Organization:
        """
        Transfers organization ownership in an atomic transaction:
        old owner -> admin
        target member -> owner
        """
        if not confirmation:
            raise OwnershipTransferError("Explicit confirmation is required to transfer organization ownership.")

        org = await self.repository.get_organization(org_id)
        if not org:
            raise ResourceNotFoundError("Organization not found.")

        # Asserts caller is current owner
        if org.owner_user_id != current_user.id:
            raise PermissionDeniedError("Only the current Organization Owner can transfer ownership.")

        # Disallow self-transfer
        if target_user_id == current_user.id:
            raise OwnershipTransferError("Cannot transfer ownership to yourself.")

        # Target must be an ACTIVE organization member
        target_member = await self.repository.get_member(org_id, target_user_id)
        if not target_member or target_member.status != MemberStatus.ACTIVE.value:
            raise OwnershipTransferError("Target user must be an active member of this organization.")

        # Find current owner member record
        old_owner_member = await self.repository.get_member(org_id, current_user.id)

        # Atomic transaction:
        # 1. Update target member role -> owner
        await self.repository.update_member(target_member.id, role=OrganizationRole.OWNER.value)
        # 2. Update old owner role -> admin
        if old_owner_member:
            await self.repository.update_member(old_owner_member.id, role=OrganizationRole.ADMIN.value)
        # 3. Update organization owner_user_id
        org.owner_user_id = target_user_id
        await self.session.flush()
        await self.session.refresh(org)

        await AccessControlAudit.log_action(
            session=self.session,
            action=AccessControlAuditEvent.OWNERSHIP_TRANSFERRED,
            actor_user_id=current_user.id,
            organization_id=org_id,
            target_user_id=target_user_id,
            details={"previous_owner_id": str(current_user.id), "new_owner_id": str(target_user_id)},
        )
        return org

    # -------------------------------------------------------------------------
    # Organization Workspaces Management
    # -------------------------------------------------------------------------

    async def list_organization_workspaces(
        self,
        org_id: UUID,
        current_user: User,
    ) -> List[Workspace]:
        context = await self.authorization.authorize(
            user=current_user,
            permission=WORKSPACE_READ,
            organization_id=org_id,
        )

        # If org owner or admin: see all workspaces in organization
        if context.organization_role in {OrganizationRole.OWNER.value, OrganizationRole.ADMIN.value}:
            stmt = (
                select(Workspace)
                .where(Workspace.organization_id == org_id)
                .order_by(Workspace.created_at.desc())
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())

        # For members/viewers: see workspaces where they have active workspace membership
        stmt = (
            select(Workspace)
            .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
            .where(
                Workspace.organization_id == org_id,
                WorkspaceMember.user_id == current_user.id,
                WorkspaceMember.status == MemberStatus.ACTIVE.value,
            )
            .order_by(Workspace.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_organization_workspace(
        self,
        org_id: UUID,
        name: str,
        slug: str,
        current_user: User,
    ) -> Workspace:
        await self.authorization.authorize(
            user=current_user,
            permission=WORKSPACE_CREATE,
            organization_id=org_id,
        )

        # Check organization workspace limit
        ws_count_stmt = select(Workspace).where(Workspace.organization_id == org_id)
        existing_ws = (await self.session.execute(ws_count_stmt)).scalars().all()
        if len(existing_ws) >= ORGANIZATION_MAX_WORKSPACES:
            raise QuotaExceededError(
                f"Organization workspace limit reached ({ORGANIZATION_MAX_WORKSPACES} workspaces)."
            )

        workspace = Workspace(
            name=name,
            slug=slug,
            owner_user_id=current_user.id,
            organization_id=org_id,
            status="active",
        )
        self.session.add(workspace)
        await self.session.flush()

        # Add creator as workspace admin member
        await self.repository.add_workspace_member(
            workspace_id=workspace.id,
            user_id=current_user.id,
            role=WorkspaceRole.ADMIN.value,
        )

        # Create default starter project for the workspace
        default_project = Project(
            workspace_id=workspace.id,
            name="General",
            slug="general",
            description="Default starter project.",
            access_mode="workspace",
        )
        self.session.add(default_project)
        await self.session.flush()
        await self.session.refresh(workspace)

        await AccessControlAudit.log_action(
            session=self.session,
            action=AccessControlAuditEvent.WORKSPACE_CREATED,
            actor_user_id=current_user.id,
            organization_id=org_id,
            workspace_id=workspace.id,
            details={"name": name, "slug": slug},
        )
        return workspace
