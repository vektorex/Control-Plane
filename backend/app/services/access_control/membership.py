"""
MembershipService for Step 27: Multi-Tenant Organizations, Teams, Roles & Access Control.
Handles member listing, role updates, suspensions, removals, and privilege escalation guards.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.user import User
from backend.app.services.access_control.constants import (
    ORGANIZATION_MAX_MEMBERS,
    WORKSPACE_MAX_MEMBERS,
    PROJECT_MAX_MEMBERS,
    OrganizationRole,
    WorkspaceRole,
    ProjectRole,
    MemberStatus,
    AccessControlAuditEvent,
)
from backend.app.services.access_control.errors import (
    AccessControlError,
    PermissionDeniedError,
    ResourceNotFoundError,
    QuotaExceededError,
)
from backend.app.services.access_control.permissions import (
    MEMBER_READ,
    MEMBER_INVITE,
    MEMBER_UPDATE,
    MEMBER_REMOVE,
    WORKSPACE_UPDATE,
    PROJECT_UPDATE,
)
from backend.app.services.access_control.models import (
    OrganizationMember,
    WorkspaceMember,
    ProjectMember,
)
from backend.app.services.access_control.repository import AccessControlRepository
from backend.app.services.access_control.authorization import AuthorizationService
from backend.app.services.access_control.audit import AccessControlAudit


# Hierarchy rank for role comparison (higher index = more privileged)
ROLE_HIERARCHY = {
    OrganizationRole.VIEWER.value: 1,
    OrganizationRole.MEMBER.value: 2,
    OrganizationRole.ADMIN.value: 3,
    OrganizationRole.OWNER.value: 4,
}


class MembershipService:
    """
    Service managing organization, workspace, and project memberships.
    Enforces server-side privilege boundaries and safety limits.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = AccessControlRepository(session)
        self.auth_service = AuthorizationService(session)

    # -------------------------------------------------------------------------
    # Organization Membership
    # -------------------------------------------------------------------------

    async def list_organization_members(
        self,
        org_id: UUID,
        current_user: User,
    ) -> List[OrganizationMember]:
        await self.auth_service.authorize(
            user=current_user,
            permission=MEMBER_READ,
            organization_id=org_id,
        )
        return await self.repository.list_members(org_id)

    async def add_organization_member(
        self,
        org_id: UUID,
        target_user_id: UUID,
        role: str,
        current_user: User,
    ) -> OrganizationMember:
        context = await self.auth_service.authorize(
            user=current_user,
            permission=MEMBER_INVITE,
            organization_id=org_id,
        )

        # Privilege escalation check: cannot assign role higher than caller's role
        caller_rank = ROLE_HIERARCHY.get(context.organization_role, 0)
        target_rank = ROLE_HIERARCHY.get(role, 0)
        if target_rank > caller_rank or role == OrganizationRole.OWNER.value:
            raise PermissionDeniedError("Cannot assign a role equal to or greater than your own, or assign Owner.")

        # Check organization membership limit
        active_count = await self.repository.count_active_members(org_id)
        if active_count >= ORGANIZATION_MAX_MEMBERS:
            raise QuotaExceededError(
                f"Organization membership limit reached ({ORGANIZATION_MAX_MEMBERS} members)."
            )

        # Check if already a member
        existing = await self.repository.get_member(org_id, target_user_id)
        if existing:
            if existing.status == MemberStatus.ACTIVE.value:
                raise AccessControlError("User is already an active member of this organization.")
            # Reactivate
            member = await self.repository.update_member(
                existing.id, role=role, status=MemberStatus.ACTIVE.value
            )
        else:
            member = await self.repository.add_member(
                org_id=org_id,
                user_id=target_user_id,
                role=role,
                status=MemberStatus.ACTIVE.value,
            )

        await AccessControlAudit.log_action(
            session=self.session,
            action=AccessControlAuditEvent.MEMBER_JOINED,
            actor_user_id=current_user.id,
            organization_id=org_id,
            target_user_id=target_user_id,
            details={"role": role},
        )
        return member

    async def update_organization_member_role(
        self,
        org_id: UUID,
        member_id: UUID,
        new_role: Optional[str],
        new_status: Optional[str],
        current_user: User,
    ) -> OrganizationMember:
        context = await self.auth_service.authorize(
            user=current_user,
            permission=MEMBER_UPDATE,
            organization_id=org_id,
        )

        target_member = await self.repository.get_member_by_id(member_id)
        if not target_member or target_member.organization_id != org_id:
            raise ResourceNotFoundError("Organization member not found.")

        # Protect the Owner: Owner role cannot be demoted or removed via member update
        if target_member.role == OrganizationRole.OWNER.value:
            if (new_role and new_role != OrganizationRole.OWNER.value) or (
                new_status and new_status != MemberStatus.ACTIVE.value
            ):
                raise AccessControlError(
                    "Organization owner cannot be demoted or deactivated. Use the ownership transfer flow."
                )

        # Caller privilege checks
        caller_rank = ROLE_HIERARCHY.get(context.organization_role, 0)
        target_current_rank = ROLE_HIERARCHY.get(target_member.role, 0)

        # Admins cannot modify other admins or the owner; only owner can modify admins
        if context.organization_role != OrganizationRole.OWNER.value and target_current_rank >= caller_rank:
            raise PermissionDeniedError("Cannot modify members with equal or higher roles.")

        if new_role:
            target_new_rank = ROLE_HIERARCHY.get(new_role, 0)
            if target_new_rank >= caller_rank and context.organization_role != OrganizationRole.OWNER.value:
                raise PermissionDeniedError("Cannot elevate members to equal or higher roles.")
            if new_role == OrganizationRole.OWNER.value:
                raise AccessControlError("Owner role can only be assigned via ownership transfer.")

        updated = await self.repository.update_member(
            member_id=member_id,
            role=new_role,
            status=new_status,
        )

        audit_action = (
            AccessControlAuditEvent.MEMBER_SUSPENDED
            if new_status == MemberStatus.SUSPENDED.value
            else AccessControlAuditEvent.MEMBER_ROLE_CHANGED
        )
        await AccessControlAudit.log_action(
            session=self.session,
            action=audit_action,
            actor_user_id=current_user.id,
            organization_id=org_id,
            target_user_id=target_member.user_id,
            details={"old_role": target_member.role, "new_role": new_role, "status": new_status},
        )
        return updated

    async def remove_organization_member(
        self,
        org_id: UUID,
        member_id: UUID,
        current_user: User,
    ) -> None:
        context = await self.auth_service.authorize(
            user=current_user,
            permission=MEMBER_REMOVE,
            organization_id=org_id,
        )

        target_member = await self.repository.get_member_by_id(member_id)
        if not target_member or target_member.organization_id != org_id:
            raise ResourceNotFoundError("Organization member not found.")

        if target_member.role == OrganizationRole.OWNER.value:
            raise AccessControlError("Organization owner cannot be removed. Transfer ownership first.")

        caller_rank = ROLE_HIERARCHY.get(context.organization_role, 0)
        target_rank = ROLE_HIERARCHY.get(target_member.role, 0)
        if target_rank >= caller_rank and context.organization_role != OrganizationRole.OWNER.value:
            raise PermissionDeniedError("Cannot remove members with equal or higher roles.")

        target_user_id = target_member.user_id
        await self.repository.remove_member(member_id)

        await AccessControlAudit.log_action(
            session=self.session,
            action=AccessControlAuditEvent.MEMBER_REMOVED,
            actor_user_id=current_user.id,
            organization_id=org_id,
            target_user_id=target_user_id,
        )

    # -------------------------------------------------------------------------
    # Workspace Membership
    # -------------------------------------------------------------------------

    async def list_workspace_members(
        self,
        workspace_id: UUID,
        current_user: User,
    ) -> List[WorkspaceMember]:
        await self.auth_service.authorize(
            user=current_user,
            permission=MEMBER_READ,
            workspace_id=workspace_id,
        )
        return await self.repository.list_workspace_members(workspace_id)

    async def add_workspace_member(
        self,
        workspace_id: UUID,
        target_user_id: UUID,
        role: str,
        current_user: User,
    ) -> WorkspaceMember:
        context = await self.auth_service.authorize(
            user=current_user,
            permission=WORKSPACE_UPDATE,
            workspace_id=workspace_id,
        )

        # Target user MUST be an active organization member first
        target_org_member = await self.repository.get_member(context.organization_id, target_user_id)
        if not target_org_member or target_org_member.status != MemberStatus.ACTIVE.value:
            raise AccessControlError("User must be an active organization member before joining a workspace.")

        # Workspace role cannot elevate beyond organization role
        # If user is a VIEWER in org, they cannot be ADMIN or MEMBER in workspace
        if target_org_member.role == OrganizationRole.VIEWER.value and role != WorkspaceRole.VIEWER.value:
            raise PermissionDeniedError("Organization viewer cannot be assigned an editor/admin workspace role.")

        members = await self.repository.list_workspace_members(workspace_id)
        if len(members) >= WORKSPACE_MAX_MEMBERS:
            raise QuotaExceededError(f"Workspace member limit reached ({WORKSPACE_MAX_MEMBERS} members).")

        existing = await self.repository.get_workspace_member(workspace_id, target_user_id)
        if existing:
            member = await self.repository.update_workspace_member(existing.id, role=role, status=MemberStatus.ACTIVE.value)
        else:
            member = await self.repository.add_workspace_member(
                workspace_id=workspace_id,
                user_id=target_user_id,
                role=role,
            )

        await AccessControlAudit.log_action(
            session=self.session,
            action=AccessControlAuditEvent.WORKSPACE_MEMBER_ADDED,
            actor_user_id=current_user.id,
            organization_id=context.organization_id,
            workspace_id=workspace_id,
            target_user_id=target_user_id,
            details={"role": role},
        )
        return member

    async def update_workspace_member(
        self,
        workspace_id: UUID,
        member_id: UUID,
        role: Optional[str],
        status: Optional[str],
        current_user: User,
    ) -> WorkspaceMember:
        context = await self.auth_service.authorize(
            user=current_user,
            permission=WORKSPACE_UPDATE,
            workspace_id=workspace_id,
        )
        member = await self.repository.get_workspace_member_by_id(member_id)
        if not member or member.workspace_id != workspace_id:
            raise ResourceNotFoundError("Workspace member not found.")

        # Check org role of target user
        if role:
            target_org_member = await self.repository.get_member(context.organization_id, member.user_id)
            if target_org_member and target_org_member.role == OrganizationRole.VIEWER.value and role != WorkspaceRole.VIEWER.value:
                raise PermissionDeniedError("Organization viewer cannot be assigned an active/admin workspace role.")

        updated = await self.repository.update_workspace_member(member_id, role=role, status=status)
        await AccessControlAudit.log_action(
            session=self.session,
            action=AccessControlAuditEvent.WORKSPACE_MEMBER_UPDATED,
            actor_user_id=current_user.id,
            organization_id=context.organization_id,
            workspace_id=workspace_id,
            target_user_id=member.user_id,
            details={"role": role, "status": status},
        )
        return updated

    async def remove_workspace_member(
        self,
        workspace_id: UUID,
        member_id: UUID,
        current_user: User,
    ) -> None:
        context = await self.auth_service.authorize(
            user=current_user,
            permission=WORKSPACE_UPDATE,
            workspace_id=workspace_id,
        )
        member = await self.repository.get_workspace_member_by_id(member_id)
        if not member or member.workspace_id != workspace_id:
            raise ResourceNotFoundError("Workspace member not found.")

        target_user_id = member.user_id
        await self.repository.remove_workspace_member(member_id)

        await AccessControlAudit.log_action(
            session=self.session,
            action=AccessControlAuditEvent.WORKSPACE_MEMBER_REMOVED,
            actor_user_id=current_user.id,
            organization_id=context.organization_id,
            workspace_id=workspace_id,
            target_user_id=target_user_id,
        )

    # -------------------------------------------------------------------------
    # Project Membership
    # -------------------------------------------------------------------------

    async def list_project_members(
        self,
        project_id: UUID,
        current_user: User,
    ) -> List[ProjectMember]:
        await self.auth_service.authorize(
            user=current_user,
            permission=MEMBER_READ,
            project_id=project_id,
        )
        return await self.repository.list_project_members(project_id)

    async def add_project_member(
        self,
        project_id: UUID,
        target_user_id: UUID,
        role: str,
        current_user: User,
    ) -> ProjectMember:
        context = await self.auth_service.authorize(
            user=current_user,
            permission=PROJECT_UPDATE,
            project_id=project_id,
        )

        members = await self.repository.list_project_members(project_id)
        if len(members) >= PROJECT_MAX_MEMBERS:
            raise QuotaExceededError(f"Project member limit reached ({PROJECT_MAX_MEMBERS} members).")

        existing = await self.repository.get_project_member(project_id, target_user_id)
        if existing:
            member = await self.repository.update_project_member(existing.id, role=role)
        else:
            member = await self.repository.add_project_member(
                project_id=project_id,
                user_id=target_user_id,
                role=role,
            )

        await AccessControlAudit.log_action(
            session=self.session,
            action=AccessControlAuditEvent.PROJECT_MEMBER_ADDED,
            actor_user_id=current_user.id,
            organization_id=context.organization_id,
            workspace_id=context.workspace_id,
            project_id=project_id,
            target_user_id=target_user_id,
            details={"role": role},
        )
        return member

    async def update_project_member(
        self,
        project_id: UUID,
        member_id: UUID,
        role: str,
        current_user: User,
    ) -> ProjectMember:
        context = await self.auth_service.authorize(
            user=current_user,
            permission=PROJECT_UPDATE,
            project_id=project_id,
        )
        member = await self.repository.get_project_member_by_id(member_id)
        if not member or member.project_id != project_id:
            raise ResourceNotFoundError("Project member not found.")

        updated = await self.repository.update_project_member(member_id, role=role)
        await AccessControlAudit.log_action(
            session=self.session,
            action=AccessControlAuditEvent.PROJECT_MEMBER_UPDATED,
            actor_user_id=current_user.id,
            organization_id=context.organization_id,
            workspace_id=context.workspace_id,
            project_id=project_id,
            target_user_id=member.user_id,
            details={"role": role},
        )
        return updated

    async def remove_project_member(
        self,
        project_id: UUID,
        member_id: UUID,
        current_user: User,
    ) -> None:
        context = await self.auth_service.authorize(
            user=current_user,
            permission=PROJECT_UPDATE,
            project_id=project_id,
        )
        member = await self.repository.get_project_member_by_id(member_id)
        if not member or member.project_id != project_id:
            raise ResourceNotFoundError("Project member not found.")

        target_user_id = member.user_id
        await self.repository.remove_project_member(member_id)

        await AccessControlAudit.log_action(
            session=self.session,
            action=AccessControlAuditEvent.PROJECT_MEMBER_REMOVED,
            actor_user_id=current_user.id,
            organization_id=context.organization_id,
            workspace_id=context.workspace_id,
            project_id=project_id,
            target_user_id=target_user_id,
        )
