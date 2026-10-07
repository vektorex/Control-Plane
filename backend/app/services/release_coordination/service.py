import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.models.release_coordination import ReleasePortfolio, ReleaseTrain
from .schemas import PortfolioCreate, PortfolioResponse, TrainCreate, TrainResponse
from .enums import PortfolioStatus, TrainStatus

class ReleaseCoordinationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_portfolio(self, payload: PortfolioCreate, workspace_id: str, user_id: str) -> ReleasePortfolio:
        portfolio = ReleasePortfolio(
            id=str(uuid.uuid4()),
            organization_id="default_org",
            workspace_id=workspace_id,
            name=payload.name,
            description=payload.description,
            status=PortfolioStatus.draft.value,
            owner_id=user_id
        )
        self.session.add(portfolio)
        await self.session.commit()
        return portfolio

    async def create_train(self, payload: TrainCreate, user_id: str) -> ReleaseTrain:
        train = ReleaseTrain(
            id=str(uuid.uuid4()),
            portfolio_id=payload.portfolio_id,
            name=payload.name,
            description=payload.description,
            status=TrainStatus.draft.value,
            owner_id=user_id
        )
        self.session.add(train)
        await self.session.commit()
        return train
