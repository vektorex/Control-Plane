from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.logging import logger
from backend.app.db.models.user import User
from backend.app.db.models.workspace import Workspace
from backend.app.db.models.project import Project
from backend.app.services.access_control.models import (
    Organization,
    OrganizationMember,
    WorkspaceMember,
)
from backend.app.repositories.user import UserRepository
from backend.app.repositories.workspace import WorkspaceRepository
from backend.app.repositories.project import ProjectRepository


class AuthService:
    """
    Service handling user profile resolution, workspace bootstrapping,
    and authentication lifecycle operations with Step 27 Organization tenancy.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.workspace_repo = WorkspaceRepository(session)
        self.project_repo = ProjectRepository(session)

    async def get_or_create_user_with_default_workspace(
        self, auth_user_id: str, email: str
    ) -> User:
        """
        Ensures a User profile exists for the authenticated Supabase identity,
        provisions a personal Organization, default workspace, and starter project on first login.
        Guarantees idempotency — repeated calls will not create duplicate workspaces or orgs.
        """
        user, is_created = await self.user_repo.get_or_create(auth_user_id, email)

        # 1. Ensure personal Organization exists
        org_stmt = select(Organization).where(Organization.owner_user_id == user.id).limit(1)
        org_res = await self.session.execute(org_stmt)
        personal_org = org_res.scalar_one_or_none()

        if not personal_org:
            clean_email_prefix = user.email.split("@")[0]
            org_name = f"{clean_email_prefix.capitalize()}'s Organization"
            org_slug = f"{clean_email_prefix.lower()}-org-{user.id.hex[:6]}"
            personal_org = Organization(
                name=org_name,
                slug=org_slug,
                owner_user_id=user.id,
                status="active",
            )
            self.session.add(personal_org)
            await self.session.flush()

            org_member = OrganizationMember(
                organization_id=personal_org.id,
                user_id=user.id,
                role="owner",
                status="active",
            )
            self.session.add(org_member)
            await self.session.flush()
            logger.info(f"[AuthService] Provisioned personal organization '{personal_org.name}' ({personal_org.id}) for user {user.id}")

        # 2. Check existing workspaces
        ws_check = await self.session.execute(
            select(Workspace).where(Workspace.owner_user_id == user.id).limit(1)
        )
        existing_ws = ws_check.scalar_one_or_none()

        if not existing_ws:
            default_workspace = Workspace(
                owner_user_id=user.id,
                organization_id=personal_org.id,
                name="Default Workspace",
                slug="default",
                status="active",
            )
            self.session.add(default_workspace)
            await self.session.flush()
            await self.session.refresh(default_workspace)

            # Create default workspace admin member
            ws_member = WorkspaceMember(
                workspace_id=default_workspace.id,
                user_id=user.id,
                role="admin",
                status="active",
            )
            self.session.add(ws_member)

            # Create default starter project
            default_project = Project(
                workspace_id=default_workspace.id,
                name="General",
                slug="general",
                description="Default starter project for orchestrated LLM tasks.",
                access_mode="workspace",
            )
            self.session.add(default_project)
            await self.session.flush()
            logger.info(f"[AuthService] Initialized default workspace '{default_workspace.slug}' in org {personal_org.id} for user {user.id}")
        else:
            # Backfill organization_id if null on legacy workspaces
            if not existing_ws.organization_id:
                existing_ws.organization_id = personal_org.id
                self.session.add(existing_ws)

            # Ensure user has workspace membership
            wm_stmt = select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == existing_ws.id,
                WorkspaceMember.user_id == user.id,
            )
            if not (await self.session.execute(wm_stmt)).scalar_one_or_none():
                wm = WorkspaceMember(
                    workspace_id=existing_ws.id,
                    user_id=user.id,
                    role="admin",
                    status="active",
                )
                self.session.add(wm)
                await self.session.flush()

        await self.session.refresh(user)
        return user
