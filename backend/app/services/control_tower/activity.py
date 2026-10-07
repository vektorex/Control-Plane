"""
Activity feed for Step 45: Control Tower.
Reuses Step 26 Event Bus - does NOT create a second event system.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger

# Actor type labels – clearly distinguishes AI from human
ACTOR_TYPE_LABELS = {
    "human": "HUMAN",
    "ai_agent": "AI_AGENT",
    "ai_team": "AI_TEAM",
    "system": "SYSTEM",
    "integration": "INTEGRATION",
}


class ActivityService:
    """
    Unified activity feed sourced exclusively from the existing Event Bus (Step 26).
    Does NOT create a second event table or event system.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_activity_feed(
        self,
        workspace_id: str,
        project_id: Optional[str] = None,
        limit: int = 50,
        cursor: Optional[str] = None,  # event_id for cursor-based pagination
        event_types: Optional[List[str]] = None,
        actor_types: Optional[List[str]] = None,
        since_hours: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Reads from the existing events table (Step 26).
        Returns bounded, cursor-paginated results.
        """
        fetched_at = datetime.now(timezone.utc)
        try:
            conditions = ["e.workspace_id = :ws"]
            params: Dict[str, Any] = {"ws": workspace_id, "lim": limit}

            if project_id:
                conditions.append("e.project_id = :proj")
                params["proj"] = project_id

            if cursor:
                conditions.append("e.id < :cursor")
                params["cursor"] = cursor

            if since_hours:
                conditions.append(
                    "e.created_at >= NOW() - INTERVAL ':hours hours'"
                )
                params["hours"] = since_hours

            where = " AND ".join(conditions)

            q = text(
                f"SELECT e.id, e.event_type, e.actor_type, e.actor_id, "
                f"e.aggregate_type, e.aggregate_id, e.workspace_id, e.project_id, "
                f"e.created_at, e.payload "
                f"FROM events e WHERE {where} "
                f"ORDER BY e.created_at DESC LIMIT :lim"
            )
            res = await self.session.execute(q, params)
            rows = res.fetchall()

            items = []
            for row in rows:
                actor_type_raw = str(row[2]).lower() if row[2] else "system"
                actor_type_label = ACTOR_TYPE_LABELS.get(actor_type_raw, "SYSTEM")

                payload = row[9] or {}
                summary = self._derive_summary(str(row[1]), actor_type_label, payload)

                items.append({
                    "event_id": str(row[0]),
                    "event_type": str(row[1]),
                    "actor_type": actor_type_label,  # Always explicit, never mislabeled
                    "actor_id": str(row[3]) if row[3] else None,
                    "source_type": str(row[4]),
                    "source_id": str(row[5]),
                    "workspace_id": str(row[6]),
                    "project_id": str(row[7]) if row[7] else None,
                    "timestamp": row[8].isoformat() if row[8] else None,
                    "summary": summary,
                    "metadata": {},
                })

            next_cursor = items[-1]["event_id"] if len(items) == limit else None

            return {
                "items": items,
                "total": len(items),
                "cursor": next_cursor,
                "data_freshness": "live",
            }

        except Exception as exc:
            logger.warning(f"[Activity] get_activity_feed failed: {exc}")
            return {
                "items": [],
                "total": 0,
                "cursor": None,
                "data_freshness": "data_unavailable",
            }

    def _derive_summary(self, event_type: str, actor_type: str, payload: dict) -> str:
        """Derive a human-readable summary from event data. No fabrication."""
        label_map = {
            "task.created": "Task created",
            "task.completed": "Task completed",
            "task.failed": "Task failed",
            "workflow.run.started": "Workflow run started",
            "workflow.run.completed": "Workflow run completed",
            "workflow.run.failed": "Workflow run failed",
            "agent.run.started": "Agent run started",
            "agent.run.completed": "Agent run completed",
            "agent.run.failed": "Agent run failed",
            "hitl.request.created": "Approval request created",
            "hitl.request.approved": "Approval granted",
            "hitl.request.rejected": "Approval rejected",
            "job.failed": "Job failed",
            "job.completed": "Job completed",
            "security.incident.created": "Security incident created",
            "security.incident.contained": "Security incident contained",
            "plan.activated": "Work plan activated",
            "plan.stale": "Work plan became stale",
            "outcome.verified": "Outcome verified",
            "outcome.blocked": "Outcome blocked",
        }
        base = label_map.get(event_type, event_type.replace(".", " ").title())
        return f"[{actor_type}] {base}"
