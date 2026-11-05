import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.models.progressive_delivery import ProgressiveRollout
from .schemas import RolloutCreate, RolloutResponse
from .enums import RolloutStatus

class ProgressiveDeliveryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_rollout(self, payload: RolloutCreate, workspace_id: str, user_id: str) -> ProgressiveRollout:
        rollout = ProgressiveRollout(
            id=str(uuid.uuid4()),
            organization_id="default_org",
            workspace_id=workspace_id,
            release_id=payload.release_id,
            name=payload.name,
            description=payload.description,
            strategy_type=payload.strategy_type.value,
            status=RolloutStatus.draft.value,
            target_scope=payload.target_scope,
            policy=payload.policy,
            created_by=user_id
        )
        self.session.add(rollout)
        await self.session.commit()
        return rollout
