"""
Aggregation engine for Step 45: Control Tower.
Reads from existing platform systems - does NOT duplicate source-of-truth records.
Each subsystem is queried independently; failures in one do not cascade.
"""
import asyncio
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.control_tower.schemas import SectionStatus


class ControlTowerAggregator:
    """
    Reads from existing system tables to produce the Control Tower overview.
    Every result is clearly labeled DERIVED or LIVE.
    Missing data is never silently treated as zero.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def _safe_count(self, query: str, params: dict, section_name: str) -> Tuple[Optional[int], bool]:
        """Execute a count query safely; returns (count, success)."""
        try:
            result = await self.session.execute(text(query), params)
            row = result.fetchone()
            return (row[0] if row else 0), True
        except Exception as exc:
            logger.warning(f"[ControlTower] Section '{section_name}' unavailable: {exc}")
            return None, False

    async def aggregate_overview(
        self, workspace_id: str, project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Aggregate counts from all existing systems.
        Returns summary with freshness indicators and partial failure markers.
        """
        fetched_at = datetime.now(timezone.utc)
        sections: Dict[str, SectionStatus] = {}
        partial_sections: List[str] = []

        ws_param = {"workspace_id": workspace_id}

        async def count_section(name: str, query: str, params: dict) -> SectionStatus:
            count, ok = await self._safe_count(query, params, name)
            if ok:
                return SectionStatus(
                    available=True,
                    data_freshness="live",
                    fetched_at=fetched_at,
                    count=count,
                )
            else:
                partial_sections.append(name)
                return SectionStatus(
                    available=False,
                    data_freshness="data_unavailable",
                    fetched_at=fetched_at,
                    count=None,
                )

        # Run all section queries concurrently - failure in one does not block others
        results = await asyncio.gather(
            count_section(
                "active_tasks",
                "SELECT COUNT(*) FROM tasks WHERE workspace_id = :workspace_id AND status IN ('pending','running','in_progress')",
                ws_param,
            ),
            count_section(
                "active_workflows",
                "SELECT COUNT(*) FROM workflow_runs WHERE workspace_id = :workspace_id AND status IN ('running','pending')",
                ws_param,
            ),
            count_section(
                "pending_approvals",
                "SELECT COUNT(*) FROM hitl_requests WHERE workspace_id = :workspace_id AND status = 'pending'",
                ws_param,
            ),
            count_section(
                "failed_jobs",
                "SELECT COUNT(*) FROM jobs WHERE workspace_id = :workspace_id AND status = 'failed'",
                ws_param,
            ),
            count_section(
                "active_agents",
                "SELECT COUNT(*) FROM agent_runs WHERE workspace_id = :workspace_id AND status IN ('running','pending')",
                ws_param,
            ),
            count_section(
                "open_security_incidents",
                "SELECT COUNT(*) FROM security_incidents WHERE workspace_id = :workspace_id AND status NOT IN ('closed','resolved')",
                ws_param,
            ),
            count_section(
                "stale_plans",
                "SELECT COUNT(*) FROM work_plans WHERE workspace_id = :workspace_id AND status = 'stale'",
                ws_param,
            ),
            count_section(
                "blocked_outcomes",
                "SELECT COUNT(*) FROM outcomes WHERE workspace_id = :workspace_id AND health_status = 'blocked'",
                ws_param,
            ),
            count_section(
                "open_attention_items",
                "SELECT COUNT(*) FROM attention_items WHERE workspace_id = :workspace_id AND status = 'open'",
                ws_param,
            ),
            count_section(
                "unread_notifications",
                "SELECT COUNT(*) FROM notifications WHERE workspace_id = :workspace_id AND read_at IS NULL",
                ws_param,
            ),
            return_exceptions=False,
        )

        section_names = [
            "active_tasks", "active_workflows", "pending_approvals", "failed_jobs",
            "active_agents", "open_security_incidents", "stale_plans",
            "blocked_outcomes", "open_attention_items", "unread_notifications",
        ]
        for name, result in zip(section_names, results):
            sections[name] = result

        return {
            "workspace_id": workspace_id,
            "generated_at": fetched_at.isoformat(),
            "is_partial": len(partial_sections) > 0,
            "partial_sections": partial_sections,
            "sections": {k: v.dict() for k, v in sections.items()},
        }

    async def aggregate_active_work(
        self, workspace_id: str, limit: int = 50, project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Aggregate active work items from tasks, workflows, agents, jobs."""
        fetched_at = datetime.now(timezone.utc)
        items = []
        partial_sections = []

        async def fetch_tasks():
            try:
                q = text(
                    "SELECT id, title, status, created_by, project_id, started_at, updated_at "
                    "FROM tasks WHERE workspace_id = :ws AND status IN ('running','in_progress','pending') "
                    "ORDER BY updated_at DESC LIMIT :lim"
                )
                res = await self.session.execute(q, {"ws": workspace_id, "lim": limit // 4})
                for row in res.fetchall():
                    items.append({
                        "type": "task",
                        "id": str(row[0]),
                        "title": row[1] or "Untitled Task",
                        "status": row[2],
                        "actor_type": "HUMAN",
                        "actor_id": str(row[3]) if row[3] else None,
                        "owner": str(row[3]) if row[3] else None,
                        "resource": None,
                        "project_id": str(row[4]) if row[4] else None,
                        "started_at": row[5].isoformat() if row[5] else None,
                        "elapsed_seconds": None,
                        "current_stage": row[2],
                        "waiting_reason": None,
                        "source_url": f"/app/tasks/{row[0]}",
                    })
            except Exception as exc:
                logger.warning(f"[ControlTower] tasks active_work failed: {exc}")
                partial_sections.append("tasks")

        async def fetch_workflow_runs():
            try:
                q = text(
                    "SELECT wr.id, w.name, wr.status, wr.started_at, wr.workspace_id, wr.project_id "
                    "FROM workflow_runs wr LEFT JOIN workflows w ON wr.workflow_id = w.id "
                    "WHERE wr.workspace_id = :ws AND wr.status IN ('running','pending') "
                    "ORDER BY wr.started_at DESC LIMIT :lim"
                )
                res = await self.session.execute(q, {"ws": workspace_id, "lim": limit // 4})
                for row in res.fetchall():
                    items.append({
                        "type": "workflow",
                        "id": str(row[0]),
                        "title": row[1] or "Untitled Workflow",
                        "status": row[2],
                        "actor_type": "SYSTEM",
                        "actor_id": None,
                        "owner": None,
                        "resource": None,
                        "project_id": str(row[5]) if row[5] else None,
                        "started_at": row[3].isoformat() if row[3] else None,
                        "elapsed_seconds": None,
                        "current_stage": row[2],
                        "waiting_reason": None,
                        "source_url": f"/app/workflows/{row[0]}",
                    })
            except Exception as exc:
                logger.warning(f"[ControlTower] workflow_runs active_work failed: {exc}")
                partial_sections.append("workflow_runs")

        async def fetch_agent_runs():
            try:
                q = text(
                    "SELECT ar.id, a.name, ar.status, ar.started_at, ar.project_id "
                    "FROM agent_runs ar LEFT JOIN agents a ON ar.agent_id = a.id "
                    "WHERE ar.workspace_id = :ws AND ar.status IN ('running','pending') "
                    "ORDER BY ar.started_at DESC LIMIT :lim"
                )
                res = await self.session.execute(q, {"ws": workspace_id, "lim": limit // 4})
                for row in res.fetchall():
                    items.append({
                        "type": "agent_run",
                        "id": str(row[0]),
                        "title": f"Agent: {row[1] or 'Unknown'}",
                        "status": row[2],
                        "actor_type": "AI_AGENT",
                        "actor_id": None,
                        "owner": None,
                        "resource": None,
                        "project_id": str(row[4]) if row[4] else None,
                        "started_at": row[3].isoformat() if row[3] else None,
                        "elapsed_seconds": None,
                        "current_stage": row[2],
                        "waiting_reason": None,
                        "source_url": f"/app/agent-runs/{row[0]}",
                    })
            except Exception as exc:
                logger.warning(f"[ControlTower] agent_runs active_work failed: {exc}")
                partial_sections.append("agent_runs")

        await asyncio.gather(fetch_tasks(), fetch_workflow_runs(), fetch_agent_runs())

        return {
            "items": items[:limit],
            "total": len(items),
            "data_freshness": "live" if not partial_sections else f"partial (unavailable: {', '.join(partial_sections)})",
        }

    async def aggregate_planning_section(self, workspace_id: str) -> Dict[str, Any]:
        """Reads from work_plans - does not duplicate planning calculations."""
        fetched_at = datetime.now(timezone.utc)
        try:
            q = text(
                "SELECT status, COUNT(*) as cnt FROM work_plans "
                "WHERE workspace_id = :ws GROUP BY status"
            )
            res = await self.session.execute(q, {"ws": workspace_id})
            status_counts = {row[0]: row[1] for row in res.fetchall()}

            stale_q = text(
                "SELECT id, name, status, updated_at FROM work_plans "
                "WHERE workspace_id = :ws AND status IN ('stale', 'active') "
                "ORDER BY updated_at ASC LIMIT 10"
            )
            stale_res = await self.session.execute(stale_q, {"ws": workspace_id})
            plans = []
            for row in stale_res.fetchall():
                plans.append({
                    "id": str(row[0]),
                    "name": row[1],
                    "status": row[2],
                    "updated_at": row[3].isoformat() if row[3] else None,
                    "source_url": f"/app/planning/{row[0]}",
                })

            return {
                "available": True,
                "data_freshness": "live",
                "fetched_at": fetched_at.isoformat(),
                "status_counts": status_counts,
                "notable_plans": plans,
            }
        except Exception as exc:
            logger.warning(f"[ControlTower] planning section failed: {exc}")
            return {
                "available": False,
                "data_freshness": "data_unavailable",
                "fetched_at": fetched_at.isoformat(),
                "status_counts": {},
                "notable_plans": [],
            }

    async def aggregate_security_section(self, workspace_id: str) -> Dict[str, Any]:
        """Security info must always be shown regardless of other dashboard filters."""
        fetched_at = datetime.now(timezone.utc)
        try:
            q = text(
                "SELECT severity, COUNT(*) as cnt FROM security_incidents "
                "WHERE workspace_id = :ws AND status NOT IN ('closed','resolved') "
                "GROUP BY severity"
            )
            res = await self.session.execute(q, {"ws": workspace_id})
            by_severity = {row[0]: row[1] for row in res.fetchall()}

            recent_q = text(
                "SELECT id, title, severity, status, created_at FROM security_incidents "
                "WHERE workspace_id = :ws AND status NOT IN ('closed','resolved') "
                "ORDER BY created_at DESC LIMIT 5"
            )
            recent_res = await self.session.execute(recent_q, {"ws": workspace_id})
            incidents = []
            for row in recent_res.fetchall():
                incidents.append({
                    "id": str(row[0]),
                    "title": row[1],
                    "severity": row[2],
                    "status": row[3],
                    "created_at": row[4].isoformat() if row[4] else None,
                    "source_url": f"/app/security/{row[0]}",
                })

            return {
                "available": True,
                "data_freshness": "live",
                "fetched_at": fetched_at.isoformat(),
                "by_severity": by_severity,
                "recent_incidents": incidents,
            }
        except Exception as exc:
            logger.warning(f"[ControlTower] security section failed: {exc}")
            return {
                "available": False,
                "data_freshness": "data_unavailable",
                "fetched_at": fetched_at.isoformat(),
                "by_severity": {},
                "recent_incidents": [],
            }
