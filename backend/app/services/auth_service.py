from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.logging import logger
from backend.app.db.models.user import User
from backend.app.db.models.workspace import Workspace
from backend.app.db.models.project import Project
from backend.app.repositories.user import UserRepository
from backend.app.repositories.workspace import WorkspaceRepository
from backend.app.repositories.project import ProjectRepository
from backend.app.schemas.workspace import WorkspaceCreate
from backend.app.schemas.project import ProjectCreate


class AuthService:
    """
    Service handling user profile resolution, workspace bootstrapping,
    and authentication lifecycle operations.
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
        Ensures a User profile exists for the authenticated Supabase identity
        and provisions a default workspace and starter project on first login.
        Guarantees idempotency — repeated calls will not create duplicate workspaces.
        """
        user, is_created = await self.user_repo.get_or_create(auth_user_id, email)

        if is_created:
            logger.info(f"[AuthService] Provisioned new user profile: {user.email} ({user.auth_user_id})")
            # Create default workspace
            default_workspace = Workspace(
                owner_user_id=user.id,
                name="Default Workspace",
                slug="default",
            )
            self.session.add(default_workspace)
            await self.session.flush()
            await self.session.refresh(default_workspace)

            # Create default starter project
            default_project = Project(
                workspace_id=default_workspace.id,
                name="General",
                slug="general",
                description="Default starter project for orchestrated LLM tasks.",
            )
            self.session.add(default_project)
            await self.session.flush()
            await self.session.refresh(default_workspace)
            logger.info(f"[AuthService] Initialized default workspace '{default_workspace.slug}' for user {user.id}")
        else:
            # Check if user has at least one workspace (e.g. if user was created manually)
            ws_check = await self.session.execute(
                select(Workspace.id).where(Workspace.owner_user_id == user.id).limit(1)
            )
            if not ws_check.scalar_one_or_none():
                logger.info(f"[AuthService] Backfilling default workspace for existing user {user.id}")
                default_workspace = Workspace(
                    owner_user_id=user.id,
                    name="Default Workspace",
                    slug="default",
                )
                self.session.add(default_workspace)
                await self.session.flush()
                await self.session.refresh(default_workspace)

                default_project = Project(
                    workspace_id=default_workspace.id,
                    name="General",
                    slug="general",
                    description="Default starter project for orchestrated LLM tasks.",
                )
                self.session.add(default_project)
                await self.session.flush()

        await self.session.refresh(user)
        return user
