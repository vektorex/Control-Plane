"""
Repository for Step 45: Control Tower persistent entities.
Handles ControlTowerView, AttentionItem, ControlTowerSnapshot, Workstream, WorkstreamMember.
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import and_, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.control_tower.models import (
    AttentionItem,
    ControlTowerSnapshot,
    ControlTowerView,
    Workstream,
    WorkstreamMember,
)


class ControlTowerRepository:
    """Async repository for Control Tower domain with strict workspace tenant isolation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # -----------------------------------------------------------------------
    # Views
    # -----------------------------------------------------------------------

    async def create_view(self, view: ControlTowerView) -> ControlTowerView:
        self.session.add(view)
        await self.session.flush()
        return view

    async def get_view(self, view_id: str, workspace_id: str) -> Optional[ControlTowerView]:
        q = select(ControlTowerView).where(
            ControlTowerView.id == view_id,
            ControlTowerView.workspace_id == workspace_id,
        )
        res = await self.session.execute(q)
        return res.scalars().first()

    async def list_views(
        self,
        workspace_id: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ControlTowerView]:
        """List views owned by the user OR shared with the workspace."""
        q = (
            select(ControlTowerView)
            .where(
                ControlTowerView.workspace_id == workspace_id,
                (ControlTowerView.created_by == user_id)
                | (ControlTowerView.shared_with_workspace == True),
            )
            .order_by(desc(ControlTowerView.updated_at))
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(q)
        return list(res.scalars().all())

    async def update_view(self, view_id: str, workspace_id: str, updates: dict) -> Optional[ControlTowerView]:
        updates["updated_at"] = datetime.now(timezone.utc)
        await self.session.execute(
            update(ControlTowerView)
            .where(ControlTowerView.id == view_id, ControlTowerView.workspace_id == workspace_id)
            .values(**updates)
        )
        return await self.get_view(view_id, workspace_id)

    async def delete_view(self, view_id: str, workspace_id: str, user_id: str) -> bool:
        view = await self.get_view(view_id, workspace_id)
        if not view or view.created_by != user_id:
            return False
        await self.session.delete(view)
        await self.session.flush()
        return True

    # -----------------------------------------------------------------------
    # Attention Items
    # -----------------------------------------------------------------------

    async def create_attention(self, item: AttentionItem) -> AttentionItem:
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_attention(self, item_id: str, workspace_id: str) -> Optional[AttentionItem]:
        q = select(AttentionItem).where(
            AttentionItem.id == item_id,
            AttentionItem.workspace_id == workspace_id,
        )
        res = await self.session.execute(q)
        return res.scalars().first()

    async def find_active_attention(
        self,
        workspace_id: str,
        source_type: str,
        source_id: str,
        attention_type: str,
    ) -> Optional[AttentionItem]:
        """Find existing active attention item to prevent duplicates."""
        q = select(AttentionItem).where(
            AttentionItem.workspace_id == workspace_id,
            AttentionItem.source_type == source_type,
            AttentionItem.source_id == source_id,
            AttentionItem.attention_type == attention_type,
            AttentionItem.status == "open",
        )
        res = await self.session.execute(q)
        return res.scalars().first()

    async def list_attention(
        self,
        workspace_id: str,
        status: Optional[str] = "open",
        severity: Optional[str] = None,
        attention_type: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AttentionItem]:
        conditions = [AttentionItem.workspace_id == workspace_id]
        if status:
            conditions.append(AttentionItem.status == status)
        if severity:
            conditions.append(AttentionItem.severity == severity)
        if attention_type:
            conditions.append(AttentionItem.attention_type == attention_type)
        if project_id:
            conditions.append(AttentionItem.project_id == project_id)

        q = (
            select(AttentionItem)
            .where(and_(*conditions))
            .order_by(desc(AttentionItem.created_at))
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(q)
        return list(res.scalars().all())

    async def acknowledge_attention(
        self, item_id: str, workspace_id: str, user_id: str
    ) -> Optional[AttentionItem]:
        """Acknowledge does not resolve the underlying source problem."""
        now = datetime.now(timezone.utc)
        await self.session.execute(
            update(AttentionItem)
            .where(AttentionItem.id == item_id, AttentionItem.workspace_id == workspace_id)
            .values(
                status="acknowledged",
                acknowledged_by=user_id,
                acknowledged_at=now,
                updated_at=now,
            )
        )
        return await self.get_attention(item_id, workspace_id)

    async def resolve_attention(self, item_id: str, workspace_id: str) -> Optional[AttentionItem]:
        """Resolution reflects actual source state change."""
        now = datetime.now(timezone.utc)
        await self.session.execute(
            update(AttentionItem)
            .where(AttentionItem.id == item_id, AttentionItem.workspace_id == workspace_id)
            .values(status="resolved", resolved_at=now, updated_at=now)
        )
        return await self.get_attention(item_id, workspace_id)

    async def dismiss_attention(self, item_id: str, workspace_id: str) -> Optional[AttentionItem]:
        now = datetime.now(timezone.utc)
        await self.session.execute(
            update(AttentionItem)
            .where(AttentionItem.id == item_id, AttentionItem.workspace_id == workspace_id)
            .values(status="dismissed", updated_at=now)
        )
        return await self.get_attention(item_id, workspace_id)

    # -----------------------------------------------------------------------
    # Snapshots
    # -----------------------------------------------------------------------

    async def create_snapshot(self, snapshot: ControlTowerSnapshot) -> ControlTowerSnapshot:
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot

    async def get_latest_snapshot(self, workspace_id: str) -> Optional[ControlTowerSnapshot]:
        q = (
            select(ControlTowerSnapshot)
            .where(ControlTowerSnapshot.workspace_id == workspace_id)
            .order_by(desc(ControlTowerSnapshot.generated_at))
            .limit(1)
        )
        res = await self.session.execute(q)
        return res.scalars().first()

    async def mark_snapshot_stale(self, snapshot_id: str) -> None:
        await self.session.execute(
            update(ControlTowerSnapshot)
            .where(ControlTowerSnapshot.id == snapshot_id)
            .values(is_stale=True)
        )

    # -----------------------------------------------------------------------
    # Workstreams
    # -----------------------------------------------------------------------

    async def create_workstream(self, ws: Workstream) -> Workstream:
        self.session.add(ws)
        await self.session.flush()
        return ws

    async def get_workstream(self, workstream_id: str, workspace_id: str) -> Optional[Workstream]:
        q = select(Workstream).where(
            Workstream.id == workstream_id,
            Workstream.workspace_id == workspace_id,
        )
        res = await self.session.execute(q)
        return res.scalars().first()

    async def list_workstreams(
        self, workspace_id: str, limit: int = 50, offset: int = 0
    ) -> List[Workstream]:
        q = (
            select(Workstream)
            .where(Workstream.workspace_id == workspace_id)
            .order_by(desc(Workstream.updated_at))
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(q)
        return list(res.scalars().all())

    async def update_workstream(
        self, workstream_id: str, workspace_id: str, updates: dict
    ) -> Optional[Workstream]:
        updates["updated_at"] = datetime.now(timezone.utc)
        await self.session.execute(
            update(Workstream)
            .where(Workstream.id == workstream_id, Workstream.workspace_id == workspace_id)
            .values(**updates)
        )
        return await self.get_workstream(workstream_id, workspace_id)

    async def delete_workstream(self, workstream_id: str, workspace_id: str) -> bool:
        ws = await self.get_workstream(workstream_id, workspace_id)
        if not ws:
            return False
        await self.session.delete(ws)
        await self.session.flush()
        return True
