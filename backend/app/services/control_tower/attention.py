"""
Attention service for Step 45: Control Tower.
Derives attention items from existing platform systems.
Never fabricates attention items. Always references real source records.
Uses deterministic priority ordering (no opaque AI scoring).
"""
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.control_tower.models import AttentionItem
from backend.app.services.control_tower.repository import ControlTowerRepository


# Deterministic priority ordering (spec §6)
# Security and safety always take precedence
SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}

ATTENTION_TYPE_PRIORITY = {
    "security_incident": 0,
    "recovery_required": 1,
    "approval_required": 2,     # HITL/security approval
    "job_failed": 3,
    "workflow_failed": 3,
    "task_failed": 3,
    "agent_failed": 3,
    "governance_block": 4,
    "objective_at_risk": 5,
    "outcome_blocked": 5,
    "outcome_stale": 6,
    "plan_stale": 7,
    "planning_conflict": 7,
    "agent_waiting": 7,
    "team_conflict": 7,
    "simulation_failure": 8,
    "regression_detected": 8,
    "evaluation_failure": 8,
    "capacity_conflict": 9,
    "budget_warning": 9,
    "connector_failure": 9,
    "data_governance_request": 9,
    "notification_failure": 10,
}


def _get_priority(item: AttentionItem) -> int:
    """Deterministic priority: lower = higher priority."""
    type_pri = ATTENTION_TYPE_PRIORITY.get(item.attention_type, 99)
    sev_pri = SEVERITY_ORDER.get(item.severity, 99)
    return type_pri * 10 + sev_pri


class AttentionService:
    """
    Derives and manages attention items from existing platform systems.
    Uses deduplication via source_type + source_id + attention_type + status.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ControlTowerRepository(session)

    async def upsert_attention(
        self,
        workspace_id: str,
        source_type: str,
        source_id: str,
        attention_type: str,
        severity: str,
        title: str,
        description: Optional[str] = None,
        reason: Optional[str] = None,
        evidence_ids: Optional[List[str]] = None,
        project_id: Optional[str] = None,
    ) -> AttentionItem:
        """Create or return existing active attention item (deduplication)."""
        existing = await self.repo.find_active_attention(
            workspace_id, source_type, source_id, attention_type
        )
        if existing:
            return existing

        item = AttentionItem(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            project_id=project_id,
            source_type=source_type,
            source_id=source_id,
            attention_type=attention_type,
            severity=severity,
            title=title,
            description=description,
            reason=reason,
            evidence_ids=evidence_ids or [],
            status="open",
        )
        return await self.repo.create_attention(item)

    async def reconcile_from_jobs(self, workspace_id: str) -> int:
        """
        Create attention items for failed jobs.
        Reads directly from jobs table (existing system).
        """
        created = 0
        try:
            q = text(
                "SELECT id, job_type, error_message FROM jobs "
                "WHERE workspace_id = :ws AND status = 'failed' "
                "ORDER BY updated_at DESC LIMIT 100"
            )
            res = await self.session.execute(q, {"ws": workspace_id})
            for row in res.fetchall():
                await self.upsert_attention(
                    workspace_id=workspace_id,
                    source_type="job",
                    source_id=str(row[0]),
                    attention_type="job_failed",
                    severity="high",
                    title=f"Job failed: {row[1]}",
                    reason=str(row[2]) if row[2] else "Job execution failed",
                )
                created += 1
        except Exception as exc:
            logger.warning(f"[Attention] reconcile_from_jobs failed: {exc}")
        return created

    async def reconcile_from_approvals(self, workspace_id: str) -> int:
        """Create attention items for pending HITL approvals."""
        created = 0
        try:
            q = text(
                "SELECT id, action_type, risk_level FROM hitl_requests "
                "WHERE workspace_id = :ws AND status = 'pending' "
                "ORDER BY created_at DESC LIMIT 100"
            )
            res = await self.session.execute(q, {"ws": workspace_id})
            for row in res.fetchall():
                severity = "critical" if str(row[2]) in ("critical", "high") else "high"
                await self.upsert_attention(
                    workspace_id=workspace_id,
                    source_type="hitl_request",
                    source_id=str(row[0]),
                    attention_type="approval_required",
                    severity=severity,
                    title=f"Approval required: {row[1]}",
                    reason="Human approval is required before this action can proceed.",
                )
                created += 1
        except Exception as exc:
            logger.warning(f"[Attention] reconcile_from_approvals failed: {exc}")
        return created

    async def reconcile_from_security(self, workspace_id: str) -> int:
        """Security incidents always get attention items regardless of other filters."""
        created = 0
        try:
            q = text(
                "SELECT id, title, severity FROM security_incidents "
                "WHERE workspace_id = :ws AND status NOT IN ('closed','resolved') "
                "ORDER BY created_at DESC LIMIT 100"
            )
            res = await self.session.execute(q, {"ws": workspace_id})
            for row in res.fetchall():
                await self.upsert_attention(
                    workspace_id=workspace_id,
                    source_type="security_incident",
                    source_id=str(row[0]),
                    attention_type="security_incident",
                    severity=str(row[2]) if row[2] else "high",
                    title=f"Security incident: {row[1]}",
                    reason="Active security incident requires review by Security Operations.",
                )
                created += 1
        except Exception as exc:
            logger.warning(f"[Attention] reconcile_from_security failed: {exc}")
        return created

    async def reconcile_from_plans(self, workspace_id: str) -> int:
        """Create attention for stale plans."""
        created = 0
        try:
            q = text(
                "SELECT id, name FROM work_plans "
                "WHERE workspace_id = :ws AND status = 'stale' "
                "ORDER BY updated_at ASC LIMIT 50"
            )
            res = await self.session.execute(q, {"ws": workspace_id})
            for row in res.fetchall():
                await self.upsert_attention(
                    workspace_id=workspace_id,
                    source_type="work_plan",
                    source_id=str(row[0]),
                    attention_type="plan_stale",
                    severity="medium",
                    title=f"Plan is stale: {row[1]}",
                    reason="This plan's data is no longer current. Review and revalidate before use.",
                )
                created += 1
        except Exception as exc:
            logger.warning(f"[Attention] reconcile_from_plans failed: {exc}")
        return created

    async def get_prioritized_attention(
        self,
        workspace_id: str,
        limit: int = 50,
        status: str = "open",
        severity: Optional[str] = None,
        attention_type: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return deterministically sorted attention items for the Control Tower.
        Security items always appear first and are never hidden.
        """
        items = await self.repo.list_attention(
            workspace_id=workspace_id,
            status=status,
            severity=severity,
            attention_type=attention_type,
            project_id=project_id,
            limit=limit,
        )
        # Sort deterministically by priority
        items.sort(key=_get_priority)
        return [self._serialize(item) for item in items]

    def _serialize(self, item: AttentionItem) -> Dict[str, Any]:
        return {
            "id": item.id,
            "workspace_id": item.workspace_id,
            "project_id": item.project_id,
            "source_type": item.source_type,
            "source_id": item.source_id,
            "attention_type": item.attention_type,
            "severity": item.severity,
            "title": item.title,
            "description": item.description,
            "reason": item.reason,
            "evidence_ids": item.evidence_ids or [],
            "status": item.status,
            "acknowledged_by": item.acknowledged_by,
            "acknowledged_at": item.acknowledged_at.isoformat() if item.acknowledged_at else None,
            "resolved_at": item.resolved_at.isoformat() if item.resolved_at else None,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
            # Navigation link to source system (no duplicate detail page)
            "source_url": self._source_url(item.source_type, item.source_id),
        }

    def _source_url(self, source_type: str, source_id: str) -> str:
        mapping = {
            "job": f"/app/jobs/{source_id}",
            "hitl_request": f"/app/approvals/{source_id}",
            "security_incident": f"/app/security/{source_id}",
            "work_plan": f"/app/planning/{source_id}",
            "workflow_run": f"/app/workflows/{source_id}",
            "agent_run": f"/app/agent-runs/{source_id}",
            "task": f"/app/tasks/{source_id}",
            "outcome": f"/app/outcomes/{source_id}",
            "objective": f"/app/objectives/{source_id}",
            "simulation": f"/app/simulations/{source_id}",
            "evaluation": f"/app/evaluation/{source_id}",
            "connector": f"/app/connectors/{source_id}",
        }
        return mapping.get(source_type, f"/app/{source_type.replace('_', '-')}s/{source_id}")
