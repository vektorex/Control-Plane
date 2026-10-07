"""
Main Control Tower service orchestrating all subsystems for Step 45.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.control_tower.activity import ActivityService
from backend.app.services.control_tower.aggregation import ControlTowerAggregator
from backend.app.services.control_tower.attention import AttentionService
from backend.app.services.control_tower.briefing import ControlTowerBriefingService
from backend.app.services.control_tower.models import (
    ControlTowerSnapshot,
    ControlTowerView,
    Workstream,
    WorkstreamMember,
)
from backend.app.services.control_tower.repository import ControlTowerRepository
from backend.app.services.control_tower.schemas import (
    ControlTowerViewCreate,
    ControlTowerViewUpdate,
    WorkstreamCreate,
    WorkstreamUpdate,
)
from backend.app.services.control_tower.search import ControlTowerSearch


class ControlTowerService:
    """
    Master orchestrator for Control Tower.
    Aggregates from existing systems without duplicating them.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ControlTowerRepository(session)
        self.aggregator = ControlTowerAggregator(session)
        self.attention_svc = AttentionService(session)
        self.activity_svc = ActivityService(session)
        self.search_svc = ControlTowerSearch(session)
        self.briefing_svc = ControlTowerBriefingService(session)

    # -----------------------------------------------------------------------
    # Overview
    # -----------------------------------------------------------------------

    async def get_overview(
        self, workspace_id: str, project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Aggregate factual counts from all subsystems."""
        return await self.aggregator.aggregate_overview(workspace_id, project_id)

    async def get_snapshot(self, workspace_id: str) -> Optional[ControlTowerSnapshot]:
        return await self.repo.get_latest_snapshot(workspace_id)

    async def refresh_snapshot(self, workspace_id: str) -> ControlTowerSnapshot:
        """Generate a fresh derived snapshot. Labels it DERIVED with source watermarks."""
        overview = await self.aggregator.aggregate_overview(workspace_id)
        snapshot = ControlTowerSnapshot(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            generated_at=datetime.now(timezone.utc),
            source_watermarks={},
            summary=overview.get("sections", {}),
            partial_failures=overview.get("partial_sections", []),
            is_stale=False,
        )
        return await self.repo.create_snapshot(snapshot)

    # -----------------------------------------------------------------------
    # Active Work
    # -----------------------------------------------------------------------

    async def get_active_work(
        self, workspace_id: str, limit: int = 50, project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        return await self.aggregator.aggregate_active_work(workspace_id, limit, project_id)

    # -----------------------------------------------------------------------
    # Section Aggregations
    # -----------------------------------------------------------------------

    async def get_planning_section(self, workspace_id: str) -> Dict[str, Any]:
        return await self.aggregator.aggregate_planning_section(workspace_id)

    async def get_security_section(self, workspace_id: str) -> Dict[str, Any]:
        return await self.aggregator.aggregate_security_section(workspace_id)

    # -----------------------------------------------------------------------
    # Attention
    # -----------------------------------------------------------------------

    async def get_attention(
        self,
        workspace_id: str,
        status: str = "open",
        severity: Optional[str] = None,
        attention_type: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        return await self.attention_svc.get_prioritized_attention(
            workspace_id=workspace_id,
            limit=limit,
            status=status,
            severity=severity,
            attention_type=attention_type,
            project_id=project_id,
        )

    async def reconcile_attention(self, workspace_id: str) -> Dict[str, int]:
        """Refresh attention items from all source systems."""
        results = {}
        results["jobs"] = await self.attention_svc.reconcile_from_jobs(workspace_id)
        results["approvals"] = await self.attention_svc.reconcile_from_approvals(workspace_id)
        results["security"] = await self.attention_svc.reconcile_from_security(workspace_id)
        results["plans"] = await self.attention_svc.reconcile_from_plans(workspace_id)
        await self.session.commit()
        return results

    async def acknowledge_attention(
        self, item_id: str, workspace_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Acknowledgement does NOT resolve the underlying source problem."""
        item = await self.repo.acknowledge_attention(item_id, workspace_id, user_id)
        await self.session.commit()
        return self.attention_svc._serialize(item) if item else None

    async def dismiss_attention(
        self, item_id: str, workspace_id: str
    ) -> Optional[Dict[str, Any]]:
        item = await self.repo.dismiss_attention(item_id, workspace_id)
        await self.session.commit()
        return self.attention_svc._serialize(item) if item else None

    # -----------------------------------------------------------------------
    # Activity
    # -----------------------------------------------------------------------

    async def get_activity(
        self,
        workspace_id: str,
        project_id: Optional[str] = None,
        limit: int = 50,
        cursor: Optional[str] = None,
        since_hours: Optional[int] = None,
    ) -> Dict[str, Any]:
        return await self.activity_svc.get_activity_feed(
            workspace_id=workspace_id,
            project_id=project_id,
            limit=limit,
            cursor=cursor,
            since_hours=since_hours,
        )

    # -----------------------------------------------------------------------
    # Search
    # -----------------------------------------------------------------------

    async def search(
        self,
        workspace_id: str,
        user_id: str,
        query: str,
        types: Optional[List[str]] = None,
        project_id: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        return await self.search_svc.search(
            workspace_id=workspace_id,
            user_id=user_id,
            query=query,
            types=types,
            project_id=project_id,
            limit=limit,
        )

    # -----------------------------------------------------------------------
    # Briefing
    # -----------------------------------------------------------------------

    async def generate_briefing(
        self,
        workspace_id: str,
        user_id: str,
        mode: str = "standard",
        project_id: Optional[str] = None,
        since_hours: int = 24,
    ) -> Dict[str, Any]:
        return await self.briefing_svc.generate_briefing(
            workspace_id=workspace_id,
            user_id=user_id,
            mode=mode,
            project_id=project_id,
            since_hours=since_hours,
        )

    # -----------------------------------------------------------------------
    # Views
    # -----------------------------------------------------------------------

    async def create_view(
        self, workspace_id: str, user_id: str, data: ControlTowerViewCreate
    ) -> ControlTowerView:
        view = ControlTowerView(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            project_id=data.project_id,
            name=data.name,
            description=data.description,
            configuration=data.configuration,
            is_shared=data.is_shared,
            shared_with_workspace=data.shared_with_workspace,
            created_by=user_id,
        )
        result = await self.repo.create_view(view)
        await self.session.commit()
        return result

    async def list_views(
        self, workspace_id: str, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[ControlTowerView]:
        return await self.repo.list_views(workspace_id, user_id, limit, offset)

    async def update_view(
        self, view_id: str, workspace_id: str, user_id: str, data: ControlTowerViewUpdate
    ) -> Optional[ControlTowerView]:
        view = await self.repo.get_view(view_id, workspace_id)
        if not view or view.created_by != user_id:
            return None
        updates = {k: v for k, v in data.dict(exclude_none=True).items()}
        result = await self.repo.update_view(view_id, workspace_id, updates)
        await self.session.commit()
        return result

    async def delete_view(self, view_id: str, workspace_id: str, user_id: str) -> bool:
        ok = await self.repo.delete_view(view_id, workspace_id, user_id)
        if ok:
            await self.session.commit()
        return ok

    # -----------------------------------------------------------------------
    # Workstreams
    # -----------------------------------------------------------------------

    async def create_workstream(
        self, workspace_id: str, user_id: str, data: WorkstreamCreate
    ) -> Workstream:
        ws = Workstream(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            project_id=data.project_id,
            name=data.name,
            description=data.description,
            configuration=data.configuration,
            created_by=user_id,
        )
        result = await self.repo.create_workstream(ws)
        await self.session.commit()
        return result

    async def list_workstreams(
        self, workspace_id: str, limit: int = 50, offset: int = 0
    ) -> List[Workstream]:
        return await self.repo.list_workstreams(workspace_id, limit, offset)

    async def get_workstream(self, workstream_id: str, workspace_id: str) -> Optional[Workstream]:
        return await self.repo.get_workstream(workstream_id, workspace_id)

    async def update_workstream(
        self, workstream_id: str, workspace_id: str, data: WorkstreamUpdate
    ) -> Optional[Workstream]:
        updates = {k: v for k, v in data.dict(exclude_none=True).items()}
        result = await self.repo.update_workstream(workstream_id, workspace_id, updates)
        if result:
            await self.session.commit()
        return result

    async def delete_workstream(self, workstream_id: str, workspace_id: str) -> bool:
        ok = await self.repo.delete_workstream(workstream_id, workspace_id)
        if ok:
            await self.session.commit()
        return ok
