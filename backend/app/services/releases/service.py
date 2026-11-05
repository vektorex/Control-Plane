import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.models.release import Release
from .schemas import ReleaseCreate, ReleaseResponse
from .enums import ReleaseStatus

class ReleaseService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_release(self, payload: ReleaseCreate, workspace_id: str, requested_by: str) -> Release:
        new_release = Release(
            id=str(uuid.uuid4()),
            organization_id="default_org",
            workspace_id=workspace_id,
            name=payload.name,
            description=payload.description,
            change_request_id=payload.change_request_id,
            release_type=payload.release_type.value,
            source_environment=payload.source_environment,
            target_environment=payload.target_environment,
            status=ReleaseStatus.draft.value,
            requested_by=requested_by
        )
        self.session.add(new_release)
        await self.session.commit()
        return new_release
