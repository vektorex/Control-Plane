"""
InvitationService for Step 27: Multi-Tenant Organizations, Teams, Roles & Access Control.
Provides cryptographically secure token generation, hashing, rate limiting, and acceptance.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import time
from typing import Dict, List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.user import User
from backend.app.services.access_control.constants import (
    INVITATION_EXPIRATION_DAYS,
    ORGANIZATION_MAX_MEMBERS,
    OrganizationRole,
    MemberStatus,
    AccessControlAuditEvent,
)
from backend.app.services.access_control.errors import (
    InvitationError,
    PermissionDeniedError,
    QuotaExceededError,
    ResourceNotFoundError,
)
from backend.app.services.access_control.permissions import MEMBER_INVITE, MEMBER_READ
from backend.app.services.access_control.models import OrganizationInvitation, OrganizationMember
from backend.app.services.access_control.repository import AccessControlRepository
from backend.app.services.access_control.authorization import AuthorizationService
from backend.app.services.access_control.audit import AccessControlAudit


# In-memory rate limiting for invitation acceptance (sliding window by IP / user)
_ACCEPT_ATTEMPTS: Dict[str, List[float]] = {}
MAX_ACCEPT_ATTEMPTS = 10
ACCEPT_WINDOW_SECONDS = 60.0


def _check_rate_limit(key: str) -> None:
    now = time.time()
    attempts = _ACCEPT_ATTEMPTS.get(key, [])
    # Filter attempts within the window
    valid_attempts = [t for t in attempts if now - t < ACCEPT_WINDOW_SECONDS]
    if len(valid_attempts) >= MAX_ACCEPT_ATTEMPTS:
        raise InvitationError("Rate limit exceeded for invitation acceptance. Please wait.")
    valid_attempts.append(now)
    _ACCEPT_ATTEMPTS[key] = valid_attempts


class InvitationService:
    """
    Manages organization invitations securely using SHA-256 hashed tokens.
    Plaintext tokens are never stored in the database.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = AccessControlRepository(session)
        self.auth_service = AuthorizationService(session)

    @staticmethod
    def hash_token(raw_token: str) -> str:
        """Computes secure SHA-256 hash of an invitation token."""
        return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()

    async def create_invitation(
        self,
        org_id: UUID,
        email: str,
        role: str,
        current_user: User,
    ) -> Tuple[OrganizationInvitation, str]:
        """
        Creates an invitation, hashes the token, and returns (invitation, raw_token).
        """
        # Validate caller permission
        await self.auth_service.authorize(
            user=current_user,
            permission=MEMBER_INVITE,
            organization_id=org_id,
        )

        cleaned_email = email.strip().lower()

        # Validate role
        if role not in {OrganizationRole.ADMIN.value, OrganizationRole.MEMBER.value, OrganizationRole.VIEWER.value}:
            raise InvitationError(f"Invalid invitation role '{role}'.")

        # Quota check
        active_count = await self.repository.count_active_members(org_id)
        if active_count >= ORGANIZATION_MAX_MEMBERS:
            raise QuotaExceededError(
                f"Organization member limit reached ({ORGANIZATION_MAX_MEMBERS} members)."
            )

        # Check for duplicate pending invitation
        existing_invitations = await self.repository.list_invitations(org_id)
        for inv in existing_invitations:
            if inv.email.lower() == cleaned_email and inv.expires_at > datetime.now(timezone.utc):
                raise InvitationError(f"A pending invitation already exists for '{cleaned_email}'.")

        # Generate secure random token
        raw_token = secrets.token_urlsafe(32)
        token_hash = self.hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=INVITATION_EXPIRATION_DAYS)

        invitation = await self.repository.create_invitation(
            org_id=org_id,
            email=cleaned_email,
            role=role,
            token_hash=token_hash,
            invited_by=current_user.id,
            expires_at=expires_at,
        )

        await AccessControlAudit.log_action(
            session=self.session,
            action=AccessControlAuditEvent.MEMBER_INVITED,
            actor_user_id=current_user.id,
            organization_id=org_id,
            details={"email": cleaned_email, "role": role},
        )

        return invitation, raw_token

    async def accept_invitation(
        self,
        raw_token: str,
        current_user: User,
        client_ip: str = "unknown",
    ) -> OrganizationMember:
        """
        Validates token, checks unexpired, unrevoked, unaccepted, and provisions membership.
        """
        _check_rate_limit(f"{client_ip}:{current_user.id}")

        if not raw_token or not raw_token.strip():
            raise InvitationError("Invitation token is required.")

        token_hash = self.hash_token(raw_token)
        invitation = await self.repository.get_invitation_by_token_hash(token_hash)
        if not invitation:
            raise InvitationError("Invalid or expired invitation token.")

        # Check revoked
        if invitation.revoked_at is not None:
            raise InvitationError("This invitation has been revoked.")

        # Check already accepted
        if invitation.accepted_at is not None:
            raise InvitationError("This invitation has already been accepted.")

        # Check expiration
        now = datetime.now(timezone.utc)
        if invitation.expires_at.replace(tzinfo=timezone.utc) < now:
            raise InvitationError("This invitation has expired.")

        # Check if user is already an active member
        org_id = invitation.organization_id
        existing_member = await self.repository.get_member(org_id, current_user.id)
        if existing_member and existing_member.status == MemberStatus.ACTIVE.value:
            await self.repository.mark_invitation_accepted(invitation.id)
            return existing_member

        # Check organization quota
        active_count = await self.repository.count_active_members(org_id)
        if active_count >= ORGANIZATION_MAX_MEMBERS:
            raise QuotaExceededError(
                f"Organization member limit reached ({ORGANIZATION_MAX_MEMBERS} members)."
            )

        # Create or reactivate membership
        if existing_member:
            member = await self.repository.update_member(
                existing_member.id,
                role=invitation.role,
                status=MemberStatus.ACTIVE.value,
            )
        else:
            member = await self.repository.add_member(
                org_id=org_id,
                user_id=current_user.id,
                role=invitation.role,
                status=MemberStatus.ACTIVE.value,
            )

        await self.repository.mark_invitation_accepted(invitation.id)

        await AccessControlAudit.log_action(
            session=self.session,
            action=AccessControlAuditEvent.MEMBER_JOINED,
            actor_user_id=current_user.id,
            organization_id=org_id,
            target_user_id=current_user.id,
            details={"via": "invitation", "role": invitation.role},
        )

        return member

    async def revoke_invitation(
        self,
        org_id: UUID,
        invitation_id: UUID,
        current_user: User,
    ) -> OrganizationInvitation:
        await self.auth_service.authorize(
            user=current_user,
            permission=MEMBER_INVITE,
            organization_id=org_id,
        )
        invitation = await self.repository.get_invitation_by_id(invitation_id)
        if not invitation or invitation.organization_id != org_id:
            raise ResourceNotFoundError("Invitation not found.")

        revoked = await self.repository.revoke_invitation(invitation_id)
        return revoked

    async def list_invitations(
        self,
        org_id: UUID,
        current_user: User,
    ) -> List[OrganizationInvitation]:
        await self.auth_service.authorize(
            user=current_user,
            permission=MEMBER_READ,
            organization_id=org_id,
        )
        return await self.repository.list_invitations(org_id)
