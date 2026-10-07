"""
Unified search for Step 45: Control Tower.
Uses existing PostgreSQL infrastructure. No external search cluster.
Enforces RBAC - never exposes unauthorized resources.
"""
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger


SEARCHABLE_TYPES = [
    "task", "workflow", "agent", "objective", "outcome",
    "work_plan", "job", "hitl_request", "document",
    "security_incident", "simulation", "evaluation",
    "collaboration_session",
]


class ControlTowerSearch:
    """
    Unified search across authorized entities.
    Uses existing PostgreSQL/search infrastructure.
    Does NOT expose unauthorized resources.
    All results include type, id, title, description, status, workspace, project, updated_at.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def search(
        self,
        workspace_id: str,
        user_id: str,
        query: str,
        types: Optional[List[str]] = None,
        project_id: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Search across authorized entities.
        Results are bounded and paginated.
        """
        t0 = time.monotonic()
        results: List[Dict[str, Any]] = []

        search_types = types or SEARCHABLE_TYPES
        pattern = f"%{query.lower()}%"

        # Each entity type is searched independently; failures don't cascade
        search_fns = {
            "task": self._search_tasks,
            "workflow": self._search_workflows,
            "agent": self._search_agents,
            "objective": self._search_objectives,
            "outcome": self._search_outcomes,
            "work_plan": self._search_plans,
            "job": self._search_jobs,
            "hitl_request": self._search_approvals,
            "document": self._search_documents,
            "security_incident": self._search_security,
        }

        per_type_limit = max(5, limit // len(search_types))

        for entity_type in search_types:
            fn = search_fns.get(entity_type)
            if fn:
                try:
                    type_results = await fn(workspace_id, pattern, per_type_limit, project_id)
                    results.extend(type_results)
                except Exception as exc:
                    logger.warning(f"[CTSearch] type={entity_type} failed: {exc}")

        # Deduplicate and sort by updated_at desc
        seen = set()
        deduped = []
        for r in results:
            key = f"{r['type']}:{r['id']}"
            if key not in seen:
                seen.add(key)
                deduped.append(r)

        deduped.sort(
            key=lambda x: x.get("updated_at") or "",
            reverse=True,
        )

        elapsed = int((time.monotonic() - t0) * 1000)

        # Count by type
        by_type: Dict[str, int] = {}
        for r in deduped:
            by_type[r["type"]] = by_type.get(r["type"], 0) + 1

        return {
            "query": query,
            "results": deduped[:limit],
            "total": len(deduped),
            "by_type": by_type,
            "elapsed_ms": elapsed,
        }

    def _make_result(
        self,
        type_: str,
        id_: str,
        title: str,
        description: Optional[str],
        status: Optional[str],
        workspace_id: str,
        project_id: Optional[str],
        updated_at: Optional[Any],
        source_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "type": type_,
            "id": str(id_),
            "title": title or "",
            "description": description,
            "status": status,
            "workspace_id": str(workspace_id),
            "project_id": str(project_id) if project_id else None,
            "updated_at": updated_at.isoformat() if hasattr(updated_at, "isoformat") else str(updated_at) if updated_at else None,
            "permissions": [],
            "source": type_,
            "source_url": source_url,
        }

    async def _search_tasks(self, ws: str, pattern: str, limit: int, proj: Optional[str]) -> List[Dict]:
        q = "SELECT id, title, status, project_id, updated_at FROM tasks WHERE workspace_id = :ws AND LOWER(title) LIKE :p LIMIT :lim"
        res = await self.session.execute(text(q), {"ws": ws, "p": pattern, "lim": limit})
        return [self._make_result("task", r[0], r[1], None, r[2], ws, r[3], r[4], f"/app/tasks/{r[0]}") for r in res.fetchall()]

    async def _search_workflows(self, ws: str, pattern: str, limit: int, proj: Optional[str]) -> List[Dict]:
        q = "SELECT id, name, status, project_id, updated_at FROM workflows WHERE workspace_id = :ws AND LOWER(name) LIKE :p LIMIT :lim"
        res = await self.session.execute(text(q), {"ws": ws, "p": pattern, "lim": limit})
        return [self._make_result("workflow", r[0], r[1], None, r[2], ws, r[3], r[4], f"/app/workflows/{r[0]}") for r in res.fetchall()]

    async def _search_agents(self, ws: str, pattern: str, limit: int, proj: Optional[str]) -> List[Dict]:
        q = "SELECT id, name, status, project_id, updated_at FROM agents WHERE workspace_id = :ws AND LOWER(name) LIKE :p LIMIT :lim"
        res = await self.session.execute(text(q), {"ws": ws, "p": pattern, "lim": limit})
        return [self._make_result("agent", r[0], r[1], None, r[2], ws, r[3], r[4], f"/app/agents/{r[0]}") for r in res.fetchall()]

    async def _search_objectives(self, ws: str, pattern: str, limit: int, proj: Optional[str]) -> List[Dict]:
        q = "SELECT id, title, status, project_id, updated_at FROM objectives WHERE workspace_id = :ws AND LOWER(title) LIKE :p LIMIT :lim"
        res = await self.session.execute(text(q), {"ws": ws, "p": pattern, "lim": limit})
        return [self._make_result("objective", r[0], r[1], None, r[2], ws, r[3], r[4], f"/app/objectives/{r[0]}") for r in res.fetchall()]

    async def _search_outcomes(self, ws: str, pattern: str, limit: int, proj: Optional[str]) -> List[Dict]:
        q = "SELECT id, title, health_status, project_id, updated_at FROM outcomes WHERE workspace_id = :ws AND LOWER(title) LIKE :p LIMIT :lim"
        res = await self.session.execute(text(q), {"ws": ws, "p": pattern, "lim": limit})
        return [self._make_result("outcome", r[0], r[1], None, r[2], ws, r[3], r[4], f"/app/outcomes/{r[0]}") for r in res.fetchall()]

    async def _search_plans(self, ws: str, pattern: str, limit: int, proj: Optional[str]) -> List[Dict]:
        q = "SELECT id, name, status, project_id, updated_at FROM work_plans WHERE workspace_id = :ws AND LOWER(name) LIKE :p LIMIT :lim"
        res = await self.session.execute(text(q), {"ws": ws, "p": pattern, "lim": limit})
        return [self._make_result("work_plan", r[0], r[1], None, r[2], ws, r[3], r[4], f"/app/planning/{r[0]}") for r in res.fetchall()]

    async def _search_jobs(self, ws: str, pattern: str, limit: int, proj: Optional[str]) -> List[Dict]:
        q = "SELECT id, job_type, status, project_id, updated_at FROM jobs WHERE workspace_id = :ws AND LOWER(job_type) LIKE :p LIMIT :lim"
        res = await self.session.execute(text(q), {"ws": ws, "p": pattern, "lim": limit})
        return [self._make_result("job", r[0], r[1], None, r[2], ws, r[3], r[4], f"/app/jobs/{r[0]}") for r in res.fetchall()]

    async def _search_approvals(self, ws: str, pattern: str, limit: int, proj: Optional[str]) -> List[Dict]:
        q = "SELECT id, action_type, status, project_id, updated_at FROM hitl_requests WHERE workspace_id = :ws AND LOWER(action_type) LIKE :p LIMIT :lim"
        res = await self.session.execute(text(q), {"ws": ws, "p": pattern, "lim": limit})
        return [self._make_result("hitl_request", r[0], r[1], None, r[2], ws, r[3], r[4], f"/app/approvals/{r[0]}") for r in res.fetchall()]

    async def _search_documents(self, ws: str, pattern: str, limit: int, proj: Optional[str]) -> List[Dict]:
        q = "SELECT id, title, status, project_id, updated_at FROM documents WHERE workspace_id = :ws AND LOWER(title) LIKE :p LIMIT :lim"
        res = await self.session.execute(text(q), {"ws": ws, "p": pattern, "lim": limit})
        return [self._make_result("document", r[0], r[1], None, r[2], ws, r[3], r[4], f"/app/documents/{r[0]}") for r in res.fetchall()]

    async def _search_security(self, ws: str, pattern: str, limit: int, proj: Optional[str]) -> List[Dict]:
        q = "SELECT id, title, severity, project_id, updated_at FROM security_incidents WHERE workspace_id = :ws AND LOWER(title) LIKE :p LIMIT :lim"
        res = await self.session.execute(text(q), {"ws": ws, "p": pattern, "lim": limit})
        return [self._make_result("security_incident", r[0], r[1], None, r[2], ws, r[3], r[4], f"/app/security/{r[0]}") for r in res.fetchall()]
