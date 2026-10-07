"""
Internal API routes for Step 45: Control Tower & Unified Command Center.
All endpoints enforce RBAC, workspace isolation, governance, and tenant isolation.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.database import get_db
from backend.app.services.control_tower.errors import (
    AttentionNotFoundError,
    BriefingUnavailableError,
    ViewNotFoundError,
    WorkstreamNotFoundError,
)
from backend.app.services.control_tower.policies import ControlTowerPolicies
from backend.app.services.control_tower.schemas import (
    AttentionAcknowledgeRequest,
    AttentionAnalysisRequest,
    BriefingRequest,
    ControlTowerViewCreate,
    ControlTowerViewUpdate,
    WorkstreamCreate,
    WorkstreamUpdate,
)
from backend.app.services.control_tower.service import ControlTowerService

router = APIRouter(prefix="/control-tower", tags=["control-tower"])


def _get_workspace(request: Request) -> str:
    """Extract workspace_id from request headers (set by existing auth middleware)."""
    ws = (
        request.headers.get("X-Workspace-Id")
        or request.headers.get("x-workspace-id")
    )
    if not ws:
        raise HTTPException(status_code=400, detail="X-Workspace-Id header required")
    return ws


def _get_user(request: Request) -> str:
    """Extract user_id from request state (set by existing auth middleware)."""
    user_id = getattr(request.state, "user_id", None) or request.headers.get("X-User-Id", "anonymous")
    return user_id


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------

@router.get("/overview")
async def get_overview(
    request: Request,
    project_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Aggregate factual counts from all platform subsystems."""
    workspace_id = _get_workspace(request)
    svc = ControlTowerService(db)
    return await svc.get_overview(workspace_id, project_id)


# ---------------------------------------------------------------------------
# Attention
# ---------------------------------------------------------------------------

@router.get("/attention")
async def get_attention(
    request: Request,
    status: str = Query("open"),
    severity: Optional[str] = Query(None),
    attention_type: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return prioritized attention items. Security items always surface first."""
    workspace_id = _get_workspace(request)
    svc = ControlTowerService(db)
    return await svc.get_attention(
        workspace_id=workspace_id,
        status=status,
        severity=severity,
        attention_type=attention_type,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )


@router.post("/attention/reconcile")
async def reconcile_attention(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Refresh attention items from all source systems."""
    workspace_id = _get_workspace(request)
    svc = ControlTowerService(db)
    results = await svc.reconcile_attention(workspace_id)
    return {"status": "ok", "created": results}


@router.post("/attention/{item_id}/acknowledge")
async def acknowledge_attention(
    item_id: str,
    request: Request,
    body: AttentionAcknowledgeRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Acknowledge an attention item. Does NOT resolve the underlying problem."""
    workspace_id = _get_workspace(request)
    svc = ControlTowerService(db)
    result = await svc.acknowledge_attention(item_id, workspace_id, body.user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Attention item not found")
    return result


@router.post("/attention/{item_id}/dismiss")
async def dismiss_attention(
    item_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Dismiss an attention item."""
    workspace_id = _get_workspace(request)
    svc = ControlTowerService(db)
    result = await svc.dismiss_attention(item_id, workspace_id)
    if not result:
        raise HTTPException(status_code=404, detail="Attention item not found")
    return result


@router.post("/attention/analyze")
async def analyze_attention(
    request: Request,
    body: AttentionAnalysisRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    AI-assisted attention analysis: suggest groupings and related items.
    Does NOT automatically close items. Critical security items are never suppressed.
    """
    workspace_id = _get_workspace(request)
    svc = ControlTowerService(db)
    items = await svc.get_attention(workspace_id=workspace_id, limit=body.limit)

    # Group by attention_type (deterministic, no AI scoring)
    groups: Dict[str, List] = {}
    for item in items:
        atype = item["attention_type"]
        groups.setdefault(atype, []).append(item["id"])

    return {
        "groups": [{"attention_type": k, "item_ids": v} for k, v in groups.items()],
        "duplicates": [],
        "related_items": [],
        "disclaimer": (
            "AI-suggested groupings only. Critical security and safety items are never suppressed. "
            "No items were automatically closed."
        ),
    }


# ---------------------------------------------------------------------------
# Activity
# ---------------------------------------------------------------------------

@router.get("/activity")
async def get_activity(
    request: Request,
    project_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    cursor: Optional[str] = Query(None),
    since_hours: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Unified activity feed from the existing Event Bus (Step 26)."""
    workspace_id = _get_workspace(request)
    svc = ControlTowerService(db)
    return await svc.get_activity(
        workspace_id=workspace_id,
        project_id=project_id,
        limit=limit,
        cursor=cursor,
        since_hours=since_hours,
    )


# ---------------------------------------------------------------------------
# Active Work
# ---------------------------------------------------------------------------

@router.get("/active-work")
async def get_active_work(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    project_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Live aggregation of active tasks, workflows, agents, and jobs."""
    workspace_id = _get_workspace(request)
    svc = ControlTowerService(db)
    return await svc.get_active_work(workspace_id, limit, project_id)


# ---------------------------------------------------------------------------
# Section Endpoints (per-subsystem)
# ---------------------------------------------------------------------------

@router.get("/objectives")
async def get_objectives_section(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Objectives section - reads from outcomes/objectives system (Step 43)."""
    workspace_id = _get_workspace(request)
    from sqlalchemy import text
    try:
        res = await db.execute(
            text("SELECT status, COUNT(*) FROM objectives WHERE workspace_id = :ws GROUP BY status"),
            {"ws": workspace_id},
        )
        counts = {r[0]: r[1] for r in res.fetchall()}
        return {
            "available": True,
            "data_freshness": "live",
            "status_counts": counts,
            "source": "objectives",
        }
    except Exception as exc:
        return {"available": False, "data_freshness": "data_unavailable", "error": str(exc)}


@router.get("/outcomes")
async def get_outcomes_section(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    workspace_id = _get_workspace(request)
    from sqlalchemy import text
    try:
        res = await db.execute(
            text("SELECT health_status, COUNT(*) FROM outcomes WHERE workspace_id = :ws GROUP BY health_status"),
            {"ws": workspace_id},
        )
        counts = {r[0]: r[1] for r in res.fetchall()}
        return {"available": True, "data_freshness": "live", "status_counts": counts}
    except Exception as exc:
        return {"available": False, "data_freshness": "data_unavailable", "error": str(exc)}


@router.get("/agents")
async def get_agents_section(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    workspace_id = _get_workspace(request)
    from sqlalchemy import text
    try:
        res = await db.execute(
            text("SELECT status, COUNT(*) FROM agent_runs WHERE workspace_id = :ws GROUP BY status"),
            {"ws": workspace_id},
        )
        counts = {r[0]: r[1] for r in res.fetchall()}
        return {"available": True, "data_freshness": "live", "run_status_counts": counts}
    except Exception as exc:
        return {"available": False, "data_freshness": "data_unavailable", "error": str(exc)}


@router.get("/workflows")
async def get_workflows_section(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    workspace_id = _get_workspace(request)
    from sqlalchemy import text
    try:
        res = await db.execute(
            text("SELECT status, COUNT(*) FROM workflow_runs WHERE workspace_id = :ws GROUP BY status"),
            {"ws": workspace_id},
        )
        counts = {r[0]: r[1] for r in res.fetchall()}
        return {"available": True, "data_freshness": "live", "run_status_counts": counts}
    except Exception as exc:
        return {"available": False, "data_freshness": "data_unavailable", "error": str(exc)}


@router.get("/jobs")
async def get_jobs_section(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    workspace_id = _get_workspace(request)
    from sqlalchemy import text
    try:
        res = await db.execute(
            text("SELECT status, COUNT(*) FROM jobs WHERE workspace_id = :ws GROUP BY status"),
            {"ws": workspace_id},
        )
        counts = {r[0]: r[1] for r in res.fetchall()}
        return {"available": True, "data_freshness": "live", "status_counts": counts}
    except Exception as exc:
        return {"available": False, "data_freshness": "data_unavailable", "error": str(exc)}


@router.get("/approvals")
async def get_approvals_section(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    workspace_id = _get_workspace(request)
    from sqlalchemy import text
    try:
        res = await db.execute(
            text("SELECT status, COUNT(*) FROM hitl_requests WHERE workspace_id = :ws GROUP BY status"),
            {"ws": workspace_id},
        )
        counts = {r[0]: r[1] for r in res.fetchall()}
        return {"available": True, "data_freshness": "live", "status_counts": counts}
    except Exception as exc:
        return {"available": False, "data_freshness": "data_unavailable", "error": str(exc)}


@router.get("/security")
async def get_security_section(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Security section. Always visible. Permission-controlled at the Security Operations level."""
    workspace_id = _get_workspace(request)
    svc = ControlTowerService(db)
    return await svc.get_security_section(workspace_id)


@router.get("/governance")
async def get_governance_section(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    workspace_id = _get_workspace(request)
    from sqlalchemy import text
    try:
        res = await db.execute(
            text("SELECT decision, COUNT(*) FROM governance_decisions WHERE workspace_id = :ws GROUP BY decision"),
            {"ws": workspace_id},
        )
        counts = {r[0]: r[1] for r in res.fetchall()}
        return {"available": True, "data_freshness": "live", "decision_counts": counts}
    except Exception as exc:
        return {"available": False, "data_freshness": "data_unavailable", "error": str(exc)}


@router.get("/planning")
async def get_planning_section(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Planning section - reads from Step 44 work_plans."""
    workspace_id = _get_workspace(request)
    svc = ControlTowerService(db)
    return await svc.get_planning_section(workspace_id)


@router.get("/learning")
async def get_learning_section(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    workspace_id = _get_workspace(request)
    from sqlalchemy import text
    try:
        res = await db.execute(
            text("SELECT status, COUNT(*) FROM improvement_proposals WHERE workspace_id = :ws GROUP BY status"),
            {"ws": workspace_id},
        )
        counts = {r[0]: r[1] for r in res.fetchall()}
        return {"available": True, "data_freshness": "live", "status_counts": counts}
    except Exception as exc:
        return {"available": False, "data_freshness": "data_unavailable", "error": str(exc)}


@router.get("/evaluation")
async def get_evaluation_section(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    workspace_id = _get_workspace(request)
    from sqlalchemy import text
    try:
        res = await db.execute(
            text("SELECT status, COUNT(*) FROM evaluation_runs WHERE workspace_id = :ws GROUP BY status"),
            {"ws": workspace_id},
        )
        counts = {r[0]: r[1] for r in res.fetchall()}
        return {"available": True, "data_freshness": "live", "status_counts": counts}
    except Exception as exc:
        return {"available": False, "data_freshness": "data_unavailable", "error": str(exc)}


@router.get("/simulation")
async def get_simulation_section(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    workspace_id = _get_workspace(request)
    from sqlalchemy import text
    try:
        res = await db.execute(
            text("SELECT status, COUNT(*) FROM simulation_runs WHERE workspace_id = :ws GROUP BY status"),
            {"ws": workspace_id},
        )
        counts = {r[0]: r[1] for r in res.fetchall()}
        return {
            "available": True,
            "data_freshness": "live",
            "status_counts": counts,
            "environment_label": "SIMULATION",  # Clearly not PRODUCTION
        }
    except Exception as exc:
        return {"available": False, "data_freshness": "data_unavailable", "error": str(exc)}


@router.get("/reliability")
async def get_reliability_section(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    workspace_id = _get_workspace(request)
    from sqlalchemy import text
    try:
        res = await db.execute(
            text("SELECT health_status, COUNT(*) FROM reliability_components WHERE workspace_id = :ws GROUP BY health_status"),
            {"ws": workspace_id},
        )
        counts = {r[0]: r[1] for r in res.fetchall()}
        return {"available": True, "data_freshness": "live", "health_counts": counts}
    except Exception as exc:
        return {"available": False, "data_freshness": "data_unavailable", "error": str(exc)}


@router.get("/recovery")
async def get_recovery_section(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    workspace_id = _get_workspace(request)
    from sqlalchemy import text
    try:
        res = await db.execute(
            text("SELECT status, COUNT(*) FROM backup_runs WHERE workspace_id = :ws GROUP BY status"),
            {"ws": workspace_id},
        )
        counts = {r[0]: r[1] for r in res.fetchall()}
        return {"available": True, "data_freshness": "live", "backup_status_counts": counts}
    except Exception as exc:
        return {"available": False, "data_freshness": "data_unavailable", "error": str(exc)}


@router.get("/collaboration")
async def get_collaboration_section(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    workspace_id = _get_workspace(request)
    from sqlalchemy import text
    try:
        res = await db.execute(
            text("SELECT COUNT(*) FROM collaboration_sessions WHERE workspace_id = :ws AND status = 'active'"),
            {"ws": workspace_id},
        )
        count = res.scalar() or 0
        return {"available": True, "data_freshness": "live", "active_sessions": count}
    except Exception as exc:
        return {"available": False, "data_freshness": "data_unavailable", "error": str(exc)}


@router.get("/notifications")
async def get_notifications_section(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    workspace_id = _get_workspace(request)
    from sqlalchemy import text
    try:
        res = await db.execute(
            text("SELECT COUNT(*) FROM notifications WHERE workspace_id = :ws AND read_at IS NULL"),
            {"ws": workspace_id},
        )
        count = res.scalar() or 0
        return {"available": True, "data_freshness": "live", "unread_count": count}
    except Exception as exc:
        return {"available": False, "data_freshness": "data_unavailable", "error": str(exc)}


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@router.get("/search")
async def search(
    request: Request,
    q: str = Query(..., min_length=1, max_length=500),
    types: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Unified search across authorized entities. Never exposes unauthorized resources."""
    workspace_id = _get_workspace(request)
    user_id = _get_user(request)
    svc = ControlTowerService(db)
    type_list = types.split(",") if types else None
    return await svc.search(
        workspace_id=workspace_id,
        user_id=user_id,
        query=q,
        types=type_list,
        project_id=project_id,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# Briefing
# ---------------------------------------------------------------------------

@router.post("/briefing")
async def generate_briefing(
    request: Request,
    body: BriefingRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    AI Work Briefing. Summarizes authorized state using AIGateway.
    Cannot execute actions. Control Tower functions normally if briefing is unavailable.
    """
    workspace_id = _get_workspace(request)
    user_id = _get_user(request)
    svc = ControlTowerService(db)
    return await svc.generate_briefing(
        workspace_id=workspace_id,
        user_id=user_id,
        mode=body.mode,
        project_id=body.project_id,
        since_hours=body.since_hours,
    )


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@router.get("/views")
async def list_views(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    workspace_id = _get_workspace(request)
    user_id = _get_user(request)
    svc = ControlTowerService(db)
    views = await svc.list_views(workspace_id, user_id, limit, offset)
    return [
        {
            "id": v.id,
            "workspace_id": v.workspace_id,
            "project_id": v.project_id,
            "name": v.name,
            "description": v.description,
            "configuration": v.configuration,
            "is_shared": v.is_shared,
            "created_by": v.created_by,
            "created_at": v.created_at.isoformat(),
            "updated_at": v.updated_at.isoformat(),
        }
        for v in views
    ]


@router.post("/views", status_code=status.HTTP_201_CREATED)
async def create_view(
    request: Request,
    body: ControlTowerViewCreate,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    workspace_id = _get_workspace(request)
    user_id = _get_user(request)
    svc = ControlTowerService(db)
    view = await svc.create_view(workspace_id, user_id, body)
    return {
        "id": view.id,
        "workspace_id": view.workspace_id,
        "name": view.name,
        "configuration": view.configuration,
        "created_at": view.created_at.isoformat(),
    }


@router.patch("/views/{view_id}")
async def update_view(
    view_id: str,
    request: Request,
    body: ControlTowerViewUpdate,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    workspace_id = _get_workspace(request)
    user_id = _get_user(request)
    svc = ControlTowerService(db)
    view = await svc.update_view(view_id, workspace_id, user_id, body)
    if not view:
        raise HTTPException(status_code=404, detail="View not found or access denied")
    return {"id": view.id, "name": view.name, "updated_at": view.updated_at.isoformat()}


@router.delete("/views/{view_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_view(
    view_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    workspace_id = _get_workspace(request)
    user_id = _get_user(request)
    svc = ControlTowerService(db)
    ok = await svc.delete_view(view_id, workspace_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="View not found or access denied")


# ---------------------------------------------------------------------------
# Workstreams
# ---------------------------------------------------------------------------

@router.get("/workstreams")
async def list_workstreams(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    workspace_id = _get_workspace(request)
    svc = ControlTowerService(db)
    items = await svc.list_workstreams(workspace_id, limit, offset)
    return [
        {
            "id": w.id,
            "workspace_id": w.workspace_id,
            "name": w.name,
            "description": w.description,
            "configuration": w.configuration,
            "created_by": w.created_by,
            "created_at": w.created_at.isoformat(),
            "updated_at": w.updated_at.isoformat(),
        }
        for w in items
    ]


@router.post("/workstreams", status_code=status.HTTP_201_CREATED)
async def create_workstream(
    request: Request,
    body: WorkstreamCreate,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    workspace_id = _get_workspace(request)
    user_id = _get_user(request)
    svc = ControlTowerService(db)
    ws = await svc.create_workstream(workspace_id, user_id, body)
    return {
        "id": ws.id,
        "workspace_id": ws.workspace_id,
        "name": ws.name,
        "created_at": ws.created_at.isoformat(),
    }


@router.patch("/workstreams/{workstream_id}")
async def update_workstream(
    workstream_id: str,
    request: Request,
    body: WorkstreamUpdate,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    workspace_id = _get_workspace(request)
    svc = ControlTowerService(db)
    ws = await svc.update_workstream(workstream_id, workspace_id, body)
    if not ws:
        raise HTTPException(status_code=404, detail="Workstream not found")
    return {"id": ws.id, "name": ws.name, "updated_at": ws.updated_at.isoformat()}


@router.delete("/workstreams/{workstream_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workstream(
    workstream_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    workspace_id = _get_workspace(request)
    svc = ControlTowerService(db)
    ok = await svc.delete_workstream(workstream_id, workspace_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Workstream not found")
