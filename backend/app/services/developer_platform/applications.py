"""
Developer Application Management Service.
Step 37: Public API, Developer Platform & SDK Layer.
"""
from datetime import datetime, timezone
from typing import List, Optional
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.services.developer_platform.errors import PublicAPIException, ResourceNotFoundError
from backend.app.services.developer_platform.models import (
    APIEnvironmentConfig,
    ApplicationApproval,
    DeveloperApplication,
)
from backend.app.services.developer_platform.schemas import (
    DeveloperApplicationCreate,
    DeveloperApplicationUpdate,
)


class ApplicationService:
    """Manages DeveloperApplication lifecycles and environment configurations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_application(
        self,
        organization_id: str,
        user_id: Optional[str],
        data: DeveloperApplicationCreate,
    ) -> DeveloperApplication:
        """Creates a new developer application."""
        app_id = str(uuid.uuid4())
        env = data.environment.lower()

        # Check if environment requires approval
        status = "active"
        if env == "production":
            cfg_q = select(APIEnvironmentConfig).where(
                APIEnvironmentConfig.organization_id == organization_id,
                APIEnvironmentConfig.environment == "production",
            )
            cfg_res = await self.session.execute(cfg_q)
            cfg = cfg_res.scalars().first()
            if cfg and cfg.require_approval:
                status = "suspended"  # requires review before activation

        app = DeveloperApplication(
            id=app_id,
            organization_id=organization_id,
            name=data.name,
            description=data.description,
            environment=env,
            status=status,
            created_by=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.session.add(app)

        if status == "suspended" and env == "production":
            approval = ApplicationApproval(
                id=str(uuid.uuid4()),
                application_id=app_id,
                organization_id=organization_id,
                requested_environment=env,
                status="pending",
                requested_by=user_id or "system",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            self.session.add(approval)

        await self.session.commit()
        return app

    async def get_application(self, application_id: str, organization_id: str) -> DeveloperApplication:
        """Retrieves an application ensuring organization isolation."""
        query = (
            select(DeveloperApplication)
            .where(
                DeveloperApplication.id == application_id,
                DeveloperApplication.organization_id == organization_id,
            )
            .options(
                selectinload(DeveloperApplication.credentials),
                selectinload(DeveloperApplication.quotas),
                selectinload(DeveloperApplication.webhooks),
            )
        )
        res = await self.session.execute(query)
        app = res.scalars().first()
        if not app:
            raise ResourceNotFoundError("Developer application", application_id)
        return app

    async def list_applications(
        self,
        organization_id: str,
        environment: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[DeveloperApplication]:
        """Lists applications belonging to an organization."""
        query = select(DeveloperApplication).where(DeveloperApplication.organization_id == organization_id)
        if environment:
            query = query.where(DeveloperApplication.environment == environment)
        if status:
            query = query.where(DeveloperApplication.status == status)

        query = query.order_by(DeveloperApplication.created_at.desc()).limit(limit).offset(offset)
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def update_application(
        self,
        application_id: str,
        organization_id: str,
        data: DeveloperApplicationUpdate,
    ) -> DeveloperApplication:
        """Updates developer application attributes."""
        app = await self.get_application(application_id, organization_id)
        if data.name is not None:
            app.name = data.name
        if data.description is not None:
            app.description = data.description
        if data.status is not None:
            app.status = data.status
        app.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        return app

    async def delete_application(self, application_id: str, organization_id: str) -> None:
        """Deletes an application and cascades its credentials."""
        app = await self.get_application(application_id, organization_id)
        await self.session.delete(app)
        await self.session.commit()
