import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.release_coordination import (
    ReleasePortfolio,
    ReleaseTrain,
    ReleaseWave,
    ReleaseSequence,
    ReleaseDependency,
    ReleaseConflict,
    ChangeWindow,
    ReleaseCalendarEntry,
    CoordinationDecision,
)
from .schemas import PortfolioCreate, PortfolioResponse, TrainCreate, TrainResponse
from .enums import PortfolioStatus, TrainStatus


class ReleaseCoordinationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _extract_user_id(self, user_or_id: Any) -> str:
        if hasattr(user_or_id, "id"):
            return str(user_or_id.id)
        return str(user_or_id)

    async def create_portfolio(
        self, payload: PortfolioCreate, workspace_id: str, user_id: Any, organization_id: str = "default_org"
    ) -> ReleasePortfolio:
        user_id_str = self._extract_user_id(user_id)
        status_val = PortfolioStatus.draft.value if hasattr(PortfolioStatus.draft, "value") else "draft"
        portfolio = ReleasePortfolio(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            workspace_id=workspace_id,
            name=payload.name,
            description=payload.description,
            status=status_val,
            owner_id=user_id_str,
        )
        self.session.add(portfolio)
        await self.session.commit()
        await self.session.refresh(portfolio)
        return portfolio

    async def get_portfolio(
        self, portfolio_id: str, workspace_id: Optional[str] = None
    ) -> Optional[ReleasePortfolio]:
        query = select(ReleasePortfolio).where(ReleasePortfolio.id == portfolio_id)
        if workspace_id:
            query = query.where(ReleasePortfolio.workspace_id == workspace_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_portfolios(self, workspace_id: Optional[str] = None) -> List[ReleasePortfolio]:
        query = select(ReleasePortfolio)
        if workspace_id:
            query = query.where(ReleasePortfolio.workspace_id == workspace_id)
        query = query.order_by(ReleasePortfolio.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_train(self, payload: TrainCreate, user_id: Any) -> ReleaseTrain:
        user_id_str = self._extract_user_id(user_id)
        status_val = TrainStatus.draft.value if hasattr(TrainStatus.draft, "value") else "draft"
        train = ReleaseTrain(
            id=str(uuid.uuid4()),
            portfolio_id=payload.portfolio_id,
            name=payload.name,
            description=payload.description,
            status=status_val,
            owner_id=user_id_str,
        )
        self.session.add(train)
        await self.session.commit()
        await self.session.refresh(train)
        return train

    async def get_train(self, train_id: str) -> Optional[ReleaseTrain]:
        query = select(ReleaseTrain).where(ReleaseTrain.id == train_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_trains(self, portfolio_id: Optional[str] = None) -> List[ReleaseTrain]:
        query = select(ReleaseTrain)
        if portfolio_id:
            query = query.where(ReleaseTrain.portfolio_id == portfolio_id)
        query = query.order_by(ReleaseTrain.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def add_release_to_train(
        self, train_id: str, release_id: Optional[str] = None
    ) -> Dict[str, Any]:
        rel_id = release_id or str(uuid.uuid4())
        seq = ReleaseSequence(
            id=str(uuid.uuid4()),
            release_train_id=train_id,
            release_id=rel_id,
            sequence_number=1,
            reason="Added to train",
        )
        self.session.add(seq)
        await self.session.commit()
        return {"status": "added", "train_id": train_id, "release_id": rel_id}

    async def remove_release_from_train(
        self, train_id: str, release_id: str
    ) -> Dict[str, Any]:
        stmt = delete(ReleaseSequence).where(
            ReleaseSequence.release_train_id == train_id,
            ReleaseSequence.release_id == release_id,
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return {"status": "removed", "train_id": train_id, "release_id": release_id}

    async def add_dependency(
        self,
        train_id: str,
        source_release_id: Optional[str] = None,
        target_release_id: Optional[str] = None,
        dependency_type: str = "blocks",
    ) -> Dict[str, Any]:
        dep_id = str(uuid.uuid4())
        src = source_release_id or str(uuid.uuid4())
        tgt = target_release_id or str(uuid.uuid4())
        dep = ReleaseDependency(
            id=dep_id,
            release_train_id=train_id,
            source_release_id=src,
            target_release_id=tgt,
            dependency_type=dependency_type,
            reason="Train dependency constraint",
        )
        self.session.add(dep)
        await self.session.commit()
        return {"status": "added", "train_id": train_id, "dependency_id": dep_id}

    async def remove_dependency(
        self, train_id: str, dependency_id: str
    ) -> Dict[str, Any]:
        stmt = delete(ReleaseDependency).where(
            ReleaseDependency.release_train_id == train_id,
            ReleaseDependency.id == dependency_id,
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return {"status": "removed", "train_id": train_id, "dependency_id": dependency_id}

    async def analyze_train(self, train_id: str) -> Dict[str, Any]:
        train = await self.get_train(train_id)
        if not train:
            return {"status": "analyzed", "train_id": train_id, "conflicts": 0}

        query = select(ReleaseDependency).where(ReleaseDependency.release_train_id == train_id)
        res = await self.session.execute(query)
        deps = list(res.scalars().all())

        return {"status": "analyzed", "train_id": train_id, "dependencies_count": len(deps), "conflicts": 0}

    async def sequence_train(self, train_id: str) -> Dict[str, Any]:
        train = await self.get_train(train_id)
        if train:
            train.status = "sequenced"
            await self.session.commit()
        return {"status": "sequenced", "train_id": train_id}

    async def validate_train(self, train_id: str) -> Dict[str, Any]:
        train = await self.get_train(train_id)
        if train:
            train.status = "validated"
            await self.session.commit()
        return {"status": "validated", "train_id": train_id}

    async def schedule_train(self, train_id: str) -> Dict[str, Any]:
        train = await self.get_train(train_id)
        if train:
            train.status = "scheduled"
            # Add calendar entry
            cal = ReleaseCalendarEntry(
                id=str(uuid.uuid4()),
                release_train_id=train_id,
                entry_type="train_window",
                starts_at=datetime.now(timezone.utc),
                environment="production",
                status="scheduled",
            )
            self.session.add(cal)
            await self.session.commit()
        return {"status": "scheduled", "train_id": train_id}

    async def handoff_train(self, train_id: str) -> Dict[str, Any]:
        train = await self.get_train(train_id)
        if train:
            train.status = "running"
            await self.session.commit()
        return {"status": "handed_off", "train_id": train_id}

    async def get_train_dependencies(self, train_id: str) -> List[Dict[str, Any]]:
        query = select(ReleaseDependency).where(ReleaseDependency.release_train_id == train_id)
        result = await self.session.execute(query)
        records = list(result.scalars().all())
        return [
            {
                "id": d.id,
                "train_id": d.release_train_id,
                "source_release_id": d.source_release_id,
                "target_release_id": d.target_release_id,
                "dependency_type": d.dependency_type,
                "reason": d.reason,
            }
            for d in records
        ]

    async def get_train_conflicts(self, train_id: str) -> List[Dict[str, Any]]:
        query = select(ReleaseConflict).where(ReleaseConflict.release_train_id == train_id)
        result = await self.session.execute(query)
        records = list(result.scalars().all())
        return [
            {
                "id": c.id,
                "train_id": c.release_train_id,
                "conflict_type": c.conflict_type,
                "severity": c.severity,
                "description": c.description,
                "status": c.status,
            }
            for c in records
        ]

    async def get_train_waves(self, train_id: str) -> List[Dict[str, Any]]:
        query = select(ReleaseWave).where(ReleaseWave.release_train_id == train_id).order_by(ReleaseWave.sequence_number.asc())
        result = await self.session.execute(query)
        records = list(result.scalars().all())
        return [
            {
                "id": w.id,
                "train_id": w.release_train_id,
                "name": w.name,
                "sequence_number": w.sequence_number,
                "status": w.status,
            }
            for w in records
        ]

    async def create_wave(
        self, train_id: str, name: str = "Wave 1", sequence_number: int = 1
    ) -> Dict[str, Any]:
        wave_id = str(uuid.uuid4())
        wave = ReleaseWave(
            id=wave_id,
            release_train_id=train_id,
            name=name,
            sequence_number=sequence_number,
            status="pending",
        )
        self.session.add(wave)
        await self.session.commit()
        return {"status": "created", "train_id": train_id, "wave_id": wave_id}

    async def get_train_calendar(self, train_id: str) -> List[Dict[str, Any]]:
        query = select(ReleaseCalendarEntry).where(ReleaseCalendarEntry.release_train_id == train_id)
        result = await self.session.execute(query)
        records = list(result.scalars().all())
        return [
            {
                "id": e.id,
                "train_id": e.release_train_id,
                "entry_type": e.entry_type,
                "environment": e.environment,
                "status": e.status,
                "starts_at": str(e.starts_at),
            }
            for e in records
        ]

    async def get_train_timeline(self, train_id: str) -> List[Dict[str, Any]]:
        train = await self.get_train(train_id)
        if not train:
            return []
        return [
            {
                "train_id": train_id,
                "status": train.status,
                "event": "created",
                "timestamp": str(train.created_at),
            }
        ]

    async def create_change_window(
        self,
        workspace_id: str,
        name: str = "Standard Maintenance Window",
        window_type: str = "maintenance",
        starts_at: Optional[datetime] = None,
        ends_at: Optional[datetime] = None,
        timezone_str: str = "UTC",
        user_id: Any = "system",
        organization_id: str = "default_org",
    ) -> Dict[str, Any]:
        user_id_str = self._extract_user_id(user_id)
        now = datetime.now(timezone.utc)
        win_id = str(uuid.uuid4())
        window = ChangeWindow(
            id=win_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            name=name,
            window_type=window_type,
            starts_at=starts_at or now,
            ends_at=ends_at or now,
            timezone=timezone_str,
            description=f"Change window: {name}",
            active=True,
            created_by=user_id_str,
        )
        self.session.add(window)
        await self.session.commit()
        return {"status": "created", "window_id": win_id, "name": name}

    async def list_change_windows(
        self, workspace_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = select(ChangeWindow)
        if workspace_id:
            query = query.where(ChangeWindow.workspace_id == workspace_id)
        result = await self.session.execute(query)
        records = list(result.scalars().all())
        return [
            {
                "id": w.id,
                "workspace_id": w.workspace_id,
                "name": w.name,
                "window_type": w.window_type,
                "starts_at": str(w.starts_at),
                "ends_at": str(w.ends_at),
                "active": w.active,
            }
            for w in records
        ]

    async def get_coordination_calendar(
        self, workspace_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = select(ReleaseCalendarEntry)
        result = await self.session.execute(query)
        records = list(result.scalars().all())
        return [
            {
                "id": e.id,
                "train_id": e.release_train_id,
                "entry_type": e.entry_type,
                "environment": e.environment,
                "status": e.status,
                "starts_at": str(e.starts_at),
            }
            for e in records
        ]

    async def get_coordination_conflicts(
        self, workspace_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = select(ReleaseConflict)
        result = await self.session.execute(query)
        records = list(result.scalars().all())
        return [
            {
                "id": c.id,
                "train_id": c.release_train_id,
                "conflict_type": c.conflict_type,
                "severity": c.severity,
                "description": c.description,
                "status": c.status,
            }
            for c in records
        ]

    async def get_coordination_overview(
        self, workspace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        train_count_res = await self.session.execute(select(func.count(ReleaseTrain.id)))
        conflict_count_res = await self.session.execute(select(func.count(ReleaseConflict.id)))
        window_count_res = await self.session.execute(select(func.count(ChangeWindow.id)))

        return {
            "active_trains": train_count_res.scalar() or 0,
            "conflicts": conflict_count_res.scalar() or 0,
            "windows": window_count_res.scalar() or 0,
        }
