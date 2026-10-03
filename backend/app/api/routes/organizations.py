"""
REST API endpoints for Step 27: Multi-Tenant Organizations, Teams, Roles & Access Control.
Covers Organizations, Memberships, Invitations, and Ownership Transfer.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.schemas.workspace import WorkspaceCreate, WorkspaceResponse
from backend.app.services.access_control.authorization import AuthorizationService
from backend.app.services.access_control.service import AccessControlService
from backend.app.services.access_control.schemas import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationListResponse,
    OrganizationMemberResponse,
    OrganizationMemberListResponse,
    OrganizationMemberUpdate,
    OrganizationInvitationCreate,
    OrganizationInvitationResponse,
    OrganizationInvitationListResponse,
    OwnershipTransferRequest,
)

organizations_router = APIRouter(prefix="/organizations", tags=["Organizations & Access Control"])
invitations_router = APIRouter(prefix="/invitations", tags=["Invitations"])


# -----------------------------------------------------------------------------
# 1. Organization Endpoints
# -----------------------------------------------------------------------------

@organizations_router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OrganizationResponse:
    """
    Creates a new multi-tenant organization. The caller is provisioned as Owner.
    """
    service = AccessControlService(session)
    org = await service.create_organization(
        name=payload.name,
        slug=payload.slug,
        user=user,
    )
    auth = AuthorizationService(session)
    ctx = await auth.resolve_context(user, organization_id=org.id)

    res = OrganizationResponse.model_validate(org)
    res.capabilities = ctx.get_capabilities()
    res.member_count = 1
    res.workspace_count = 0
    return res


@organizations_router.get("", response_model=OrganizationListResponse)
async def list_organizations(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OrganizationListResponse:
    """
    List all organizations where the authenticated user is an active member or owner.
    """
    service = AccessControlService(session)
    auth = AuthorizationService(session)
    orgs = await service.list_user_organizations(user)

    items = []
    for org in orgs:
        ctx = await auth.resolve_context(user, organization_id=org.id)
        item = OrganizationResponse.model_validate(org)
        item.capabilities = ctx.get_capabilities()
        item.member_count = len(org.members) if hasattr(org, "members") and org.members else 1
        item.workspace_count = len(org.workspaces) if hasattr(org, "workspaces") and org.workspaces else 0
        items.append(item)

    return OrganizationListResponse(organizations=items, total=len(items))


@organizations_router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OrganizationResponse:
    """
    Retrieve organization metadata and UI capability hints. Returns 403/404 if unauthorized.
    """
    service = AccessControlService(session)
    auth = AuthorizationService(session)
    org = await service.get_organization(org_id, user)
    ctx = await auth.resolve_context(user, organization_id=org_id)

    res = OrganizationResponse.model_validate(org)
    res.capabilities = ctx.get_capabilities()
    res.member_count = len(org.members) if hasattr(org, "members") and org.members else 1
    res.workspace_count = len(org.workspaces) if hasattr(org, "workspaces") and org.workspaces else 0
    return res


@organizations_router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: UUID,
    payload: OrganizationUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OrganizationResponse:
    """
    Update organization name or slug. Requires organization.update permission.
    """
    service = AccessControlService(session)
    auth = AuthorizationService(session)
    org = await service.update_organization(
        org_id=org_id,
        current_user=user,
        name=payload.name,
        slug=payload.slug,
    )
    ctx = await auth.resolve_context(user, organization_id=org_id)
    res = OrganizationResponse.model_validate(org)
    res.capabilities = ctx.get_capabilities()
    return res


@organizations_router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Soft-deletes / archives an organization. Requires Owner role.
    """
    service = AccessControlService(session)
    await service.archive_organization(org_id=org_id, current_user=user)
    return None


@organizations_router.post("/{org_id}/transfer-ownership", response_model=OrganizationResponse)
async def transfer_ownership(
    org_id: UUID,
    payload: OwnershipTransferRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OrganizationResponse:
    """
    Transfers organization ownership in an atomic transaction:
    current owner -> admin
    target active member -> owner
    """
    service = AccessControlService(session)
    auth = AuthorizationService(session)
    org = await service.transfer_ownership(
        org_id=org_id,
        target_user_id=payload.target_user_id,
        confirmation=payload.confirmation,
        current_user=user,
    )
    ctx = await auth.resolve_context(user, organization_id=org_id)
    res = OrganizationResponse.model_validate(org)
    res.capabilities = ctx.get_capabilities()
    return res


# -----------------------------------------------------------------------------
# 2. Organization Members
# -----------------------------------------------------------------------------

@organizations_router.get("/{org_id}/members", response_model=OrganizationMemberListResponse)
async def list_members(
    org_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OrganizationMemberListResponse:
    """
    Lists members of an organization. Requires member.read permission.
    """
    service = AccessControlService(session)
    members = await service.membership.list_organization_members(org_id=org_id, current_user=user)

    items = []
    for m in members:
        email = m.user.email if hasattr(m, "user") and m.user else None
        item = OrganizationMemberResponse(
            id=m.id,
            organization_id=m.organization_id,
            user_id=m.user_id,
            email=email,
            role=m.role,
            status=m.status,
            joined_at=m.joined_at,
            created_at=m.created_at,
            capabilities={
                "is_owner": m.role == "owner",
                "can_demote": m.role != "owner",
                "can_remove": m.role != "owner",
            },
        )
        items.append(item)

    return OrganizationMemberListResponse(members=items, total=len(items))


@organizations_router.patch("/{org_id}/members/{member_id}", response_model=OrganizationMemberResponse)
async def update_member(
    org_id: UUID,
    member_id: UUID,
    payload: OrganizationMemberUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OrganizationMemberResponse:
    """
    Updates role or suspension status of an organization member.
    Owner demotion is prohibited here (use /transfer-ownership).
    """
    service = AccessControlService(session)
    m = await service.membership.update_organization_member_role(
        org_id=org_id,
        member_id=member_id,
        new_role=payload.role,
        new_status=payload.status,
        current_user=user,
    )
    email = m.user.email if hasattr(m, "user") and m.user else None
    return OrganizationMemberResponse(
        id=m.id,
        organization_id=m.organization_id,
        user_id=m.user_id,
        email=email,
        role=m.role,
        status=m.status,
        joined_at=m.joined_at,
        created_at=m.created_at,
    )


@organizations_router.delete("/{org_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    org_id: UUID,
    member_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Removes a member from the organization.
    Owner cannot be removed.
    """
    service = AccessControlService(session)
    await service.membership.remove_organization_member(
        org_id=org_id,
        member_id=member_id,
        current_user=user,
    )
    return None


# -----------------------------------------------------------------------------
# 3. Organization Invitations
# -----------------------------------------------------------------------------

@organizations_router.post("/{org_id}/invitations", response_model=OrganizationInvitationResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    org_id: UUID,
    payload: OrganizationInvitationCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OrganizationInvitationResponse:
    """
    Sends an invitation to join an organization.
    Stores cryptographically hashed token. Returns raw token for email/link delivery.
    """
    service = AccessControlService(session)
    inv, raw_token = await service.invitations.create_invitation(
        org_id=org_id,
        email=payload.email,
        role=payload.role,
        current_user=user,
    )
    return OrganizationInvitationResponse(
        id=inv.id,
        organization_id=inv.organization_id,
        email=inv.email,
        role=inv.role,
        invited_by=inv.invited_by,
        expires_at=inv.expires_at,
        accepted_at=inv.accepted_at,
        revoked_at=inv.revoked_at,
        created_at=inv.created_at,
        invite_token=raw_token,
    )


@organizations_router.get("/{org_id}/invitations", response_model=OrganizationInvitationListResponse)
async def list_invitations(
    org_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OrganizationInvitationListResponse:
    """
    Lists pending, unrevoked invitations for the organization.
    Never exposes raw tokens or hashes.
    """
    service = AccessControlService(session)
    invs = await service.invitations.list_invitations(org_id=org_id, current_user=user)
    items = [OrganizationInvitationResponse.model_validate(inv) for inv in invs]
    return OrganizationInvitationListResponse(invitations=items, total=len(items))


@organizations_router.delete("/{org_id}/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invitation(
    org_id: UUID,
    invitation_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Revokes a pending invitation.
    """
    service = AccessControlService(session)
    await service.invitations.revoke_invitation(
        org_id=org_id,
        invitation_id=invitation_id,
        current_user=user,
    )
    return None


@invitations_router.post("/{token}/accept", response_model=OrganizationMemberResponse)
async def accept_invitation(
    token: str,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OrganizationMemberResponse:
    """
    Accepts an organization invitation. Validates token hash, expiry, and revocation.
    """
    client_ip = request.client.host if request.client else "unknown"
    service = AccessControlService(session)
    member = await service.invitations.accept_invitation(
        raw_token=token,
        current_user=user,
        client_ip=client_ip,
    )
    email = user.email
    return OrganizationMemberResponse(
        id=member.id,
        organization_id=member.organization_id,
        user_id=member.user_id,
        email=email,
        role=member.role,
        status=member.status,
        joined_at=member.joined_at,
        created_at=member.created_at,
    )


# -----------------------------------------------------------------------------
# 4. Organization Workspaces
# -----------------------------------------------------------------------------

@organizations_router.get("/{org_id}/workspaces", response_model=List[WorkspaceResponse])
async def list_organization_workspaces(
    org_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[WorkspaceResponse]:
    """
    List all workspaces in this organization that the user is authorized to access.
    """
    service = AccessControlService(session)
    workspaces = await service.list_organization_workspaces(org_id=org_id, current_user=user)
    items = []
    for w in workspaces:
        item = WorkspaceResponse.model_validate(w)
        item.project_count = len(w.projects) if hasattr(w, "projects") and w.projects else 0
        items.append(item)
    return items


@organizations_router.post("/{org_id}/workspaces", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_organization_workspace(
    org_id: UUID,
    payload: WorkspaceCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> WorkspaceResponse:
    """
    Creates a new workspace within the organization. Enforces workspace safety limits.
    """
    service = AccessControlService(session)
    workspace = await service.create_organization_workspace(
        org_id=org_id,
        name=payload.name,
        slug=payload.slug,
        current_user=user,
    )
    res = WorkspaceResponse.model_validate(workspace)
    res.project_count = 1
    return res
