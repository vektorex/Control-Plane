"""
FastAPI routes for Step 34: AI Security Operations, Threat Detection & Incident Response Layer.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.security.exceptions import (
    AISelfAuthorizationBlockedError,
    ContainmentActionBlockedError,
    InvalidPlaybookActionError,
    SecurityError,
    SecurityIncidentNotFoundError,
    SecuritySignalNotFoundError,
    TenantIsolationSecurityError,
    UnauthorizedContainmentError,
)
from backend.app.services.security.schemas import (
    ContainmentActionCreate,
    ContainmentActionResponse,
    IncidentInvestigationResponse,
    IncidentTimelineEventResponse,
    PlaybookTestRequest,
    PlaybookTestResponse,
    SecurityIncidentCreate,
    SecurityIncidentResponse,
    SecurityIncidentUpdate,
    SecurityIndicatorResponse,
    SecurityOverviewResponse,
    SecurityPlaybookCreate,
    SecurityPlaybookResponse,
    SecurityPlaybookUpdate,
    SecuritySignalResponse,
    SecurityStatisticsResponse,
)
from backend.app.services.security.service import SecurityService

router = APIRouter(prefix="/security", tags=["security"])


def _get_service(db: AsyncSession = Depends(get_db)) -> SecurityService:
    return SecurityService(db)


def _get_org_id(user: User) -> str:
    org_id = getattr(user, "organization_id", None)
    return str(org_id) if org_id else str(user.id)


# ---------------------------------------------------------------------------
# Overview & Statistics
# ---------------------------------------------------------------------------

@router.get("/overview", response_model=SecurityOverviewResponse)
async def get_overview(
    workspace_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    service: SecurityService = Depends(_get_service),
):
    """Returns real-time security operational overview counts."""
    return await service.get_overview(
        organization_id=_get_org_id(current_user),
        workspace_id=workspace_id,
    )


@router.get("/statistics", response_model=SecurityStatisticsResponse)
async def get_statistics(
    workspace_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    service: SecurityService = Depends(_get_service),
):
    """Returns historical incident statistics, containment breakdowns, and detector metrics."""
    return await service.get_statistics(
        organization_id=_get_org_id(current_user),
        workspace_id=workspace_id,
    )


# ---------------------------------------------------------------------------
# Security Signals
# ---------------------------------------------------------------------------

@router.get("/signals", response_model=List[SecuritySignalResponse])
async def list_signals(
    workspace_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    signal_type: Optional[str] = Query(None),
    actor_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: SecurityService = Depends(_get_service),
):
    """Lists security detection signals with optional severity and category filtering."""
    signals = await service.signals.list_signals(
        organization_id=_get_org_id(current_user),
        workspace_id=workspace_id,
        severity=severity,
        status=status,
        signal_type=signal_type,
        actor_id=actor_id,
        limit=limit,
        offset=offset,
    )
    return [SecuritySignalResponse.model_validate(s) for s in signals]


@router.get("/signals/{signal_id}", response_model=SecuritySignalResponse)
async def get_signal(
    signal_id: str,
    current_user: User = Depends(get_current_user),
    service: SecurityService = Depends(_get_service),
):
    """Retrieves a single security signal by ID."""
    try:
        sig = await service.signals.get_signal_by_id(
            signal_id=signal_id,
            organization_id=_get_org_id(current_user),
        )
        return SecuritySignalResponse.model_validate(sig)
    except SecuritySignalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ---------------------------------------------------------------------------
# Security Incidents
# ---------------------------------------------------------------------------

@router.get("/incidents", response_model=List[SecurityIncidentResponse])
async def list_incidents(
    workspace_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: SecurityService = Depends(_get_service),
):
    """Lists correlated security incidents."""
    incidents = await service.incidents.list_incidents(
        organization_id=_get_org_id(current_user),
        workspace_id=workspace_id,
        category=category,
        severity=severity,
        status=status,
        assigned_to=assigned_to,
        limit=limit,
        offset=offset,
    )
    res = []
    for inc in incidents:
        item = SecurityIncidentResponse.model_validate(inc)
        item.signal_count = len(inc.signals or [])
        res.append(item)
    return res


@router.post("/incidents", response_model=SecurityIncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    data: SecurityIncidentCreate,
    current_user: User = Depends(get_current_user),
    service: SecurityService = Depends(_get_service),
):
    """Manually creates a new security incident."""
    inc = await service.incidents.create_incident(
        organization_id=_get_org_id(current_user),
        data=data,
        created_by=str(current_user.id),
    )
    resp = SecurityIncidentResponse.model_validate(inc)
    resp.signal_count = len(data.signal_ids or [])
    return resp


@router.get("/incidents/{incident_id}", response_model=SecurityIncidentResponse)
async def get_incident(
    incident_id: str,
    current_user: User = Depends(get_current_user),
    service: SecurityService = Depends(_get_service),
):
    """Retrieves full details for a security incident."""
    try:
        inc = await service.incidents.get_incident_by_id(
            incident_id=incident_id,
            organization_id=_get_org_id(current_user),
        )
        resp = SecurityIncidentResponse.model_validate(inc)
        resp.signal_count = len(inc.signals or [])
        return resp
    except SecurityIncidentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/incidents/{incident_id}", response_model=SecurityIncidentResponse)
async def update_incident(
    incident_id: str,
    data: SecurityIncidentUpdate,
    current_user: User = Depends(get_current_user),
    service: SecurityService = Depends(_get_service),
):
    """Updates incident status, assignment, severity, or resolution summary."""
    try:
        inc = await service.incidents.update_incident(
            incident_id=incident_id,
            organization_id=_get_org_id(current_user),
            data=data,
            updated_by=str(current_user.id),
        )
        resp = SecurityIncidentResponse.model_validate(inc)
        resp.signal_count = len(inc.signals or [])
        return resp
    except SecurityIncidentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ---------------------------------------------------------------------------
# Incident Sub-resources (Timeline, Signals, Investigation, Evidence)
# ---------------------------------------------------------------------------

@router.get("/incidents/{incident_id}/timeline", response_model=List[IncidentTimelineEventResponse])
async def get_incident_timeline(
    incident_id: str,
    current_user: User = Depends(get_current_user),
    service: SecurityService = Depends(_get_service),
):
    """Retrieves the chronological, append-only timeline events for an incident."""
    try:
        inc = await service.incidents.get_incident_by_id(
            incident_id=incident_id,
            organization_id=_get_org_id(current_user),
        )
        return [IncidentTimelineEventResponse.model_validate(t) for t in inc.timeline_events]
    except SecurityIncidentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/incidents/{incident_id}/signals", response_model=List[SecuritySignalResponse])
async def get_incident_signals(
    incident_id: str,
    current_user: User = Depends(get_current_user),
    service: SecurityService = Depends(_get_service),
):
    """Retrieves all correlated signals attached to an incident."""
    try:
        inc = await service.incidents.get_incident_by_id(
            incident_id=incident_id,
            organization_id=_get_org_id(current_user),
        )
        signals = [assoc.signal for assoc in inc.signals if assoc.signal is not None]
        return [SecuritySignalResponse.model_validate(s) for s in signals]
    except SecurityIncidentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/incidents/{incident_id}/investigation", response_model=IncidentInvestigationResponse)
async def get_incident_investigation(
    incident_id: str,
    current_user: User = Depends(get_current_user),
    service: SecurityService = Depends(_get_service),
):
    """Retrieves full bounded investigation context, related assets, and compliance evidence."""
    try:
        return await service.investigation.get_investigation_context(
            incident_id=incident_id,
            organization_id=_get_org_id(current_user),
        )
    except SecurityIncidentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/incidents/{incident_id}/evidence", response_model=List[Dict[str, Any]])
async def get_incident_evidence(
    incident_id: str,
    current_user: User = Depends(get_current_user),
    service: SecurityService = Depends(_get_service),
):
    """Retrieves Step 33 compliance evidence records bound to the incident."""
    investigation = await service.investigation.get_investigation_context(
        incident_id=incident_id,
        organization_id=_get_org_id(current_user),
    )
    return investigation.compliance_evidence


# ---------------------------------------------------------------------------
# Containment Actions
# ---------------------------------------------------------------------------

@router.post("/incidents/{incident_id}/containment", response_model=ContainmentActionResponse, status_code=status.HTTP_201_CREATED)
async def request_containment(
    incident_id: str,
    data: ContainmentActionCreate,
    current_user: User = Depends(get_current_user),
    service: SecurityService = Depends(_get_service),
):
    """Requests a containment action on an affected target with allowlist verification."""
    org_id = _get_org_id(current_user)
    try:
        req_hitl = await service.policy_bridge.does_containment_require_approval(
            organization_id=org_id,
            workspace_id=None,
            action_type=data.action_type,
            target_type=data.target_type,
        )
        action = await service.containment.request_containment(
            incident_id=incident_id,
            organization_id=org_id,
            requested_by=str(current_user.id),
            actor_type="user",
            data=data,
            requires_hitl=req_hitl,
        )
        return ContainmentActionResponse.model_validate(action)
    except (InvalidPlaybookActionError, AISelfAuthorizationBlockedError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except SecurityIncidentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/incidents/{incident_id}/containment", response_model=List[ContainmentActionResponse])
async def list_incident_containments(
    incident_id: str,
    current_user: User = Depends(get_current_user),
    service: SecurityService = Depends(_get_service),
):
    """Lists all containment actions initiated for an incident."""
    actions = await service.containment.list_actions_for_incident(
        incident_id=incident_id,
        organization_id=_get_org_id(current_user),
    )
    return [ContainmentActionResponse.model_validate(a) for a in actions]


# ---------------------------------------------------------------------------
# Threat Indicators
# ---------------------------------------------------------------------------

@router.get("/indicators", response_model=List[SecurityIndicatorResponse])
async def list_indicators(
    indicator_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: SecurityService = Depends(_get_service),
):
    """Lists threat indicators and fingerprints."""
    inds = await service.indicators.list_indicators(
        organization_id=_get_org_id(current_user),
        indicator_type=indicator_type,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [SecurityIndicatorResponse.model_validate(i) for i in inds]


# ---------------------------------------------------------------------------
# Response Playbooks
# ---------------------------------------------------------------------------

@router.get("/playbooks", response_model=List[SecurityPlaybookResponse])
async def list_playbooks(
    enabled_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    service: SecurityService = Depends(_get_service),
):
    """Lists active response playbooks."""
    pbs = await service.playbooks.list_playbooks(
        organization_id=_get_org_id(current_user),
        enabled_only=enabled_only,
    )
    return [SecurityPlaybookResponse.model_validate(p) for p in pbs]


@router.post("/playbooks", response_model=SecurityPlaybookResponse, status_code=status.HTTP_201_CREATED)
async def create_playbook(
    data: SecurityPlaybookCreate,
    current_user: User = Depends(get_current_user),
    service: SecurityService = Depends(_get_service),
):
    """Creates a new response playbook with strictly allowlisted actions."""
    try:
        pb = await service.playbooks.create_playbook(
            organization_id=_get_org_id(current_user),
            created_by=str(current_user.id),
            data=data,
        )
        return SecurityPlaybookResponse.model_validate(pb)
    except InvalidPlaybookActionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.patch("/playbooks/{id}", response_model=SecurityPlaybookResponse)
async def update_playbook(
    id: str,
    data: SecurityPlaybookUpdate,
    current_user: User = Depends(get_current_user),
    service: SecurityService = Depends(_get_service),
):
    """Updates a response playbook."""
    try:
        pb = await service.playbooks.update_playbook(
            playbook_id=id,
            organization_id=_get_org_id(current_user),
            data=data,
        )
        return SecurityPlaybookResponse.model_validate(pb)
    except InvalidPlaybookActionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/playbooks/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playbook(
    id: str,
    current_user: User = Depends(get_current_user),
    service: SecurityService = Depends(_get_service),
):
    """Deletes a response playbook."""
    deleted = await service.playbooks.delete_playbook(
        playbook_id=id,
        organization_id=_get_org_id(current_user),
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Playbook not found.")
    return None


@router.post("/playbooks/{id}/test", response_model=PlaybookTestResponse)
async def test_playbook(
    id: str,
    req: PlaybookTestRequest,
    current_user: User = Depends(get_current_user),
    service: SecurityService = Depends(_get_service),
):
    """Simulates playbook trigger matching against a test signal."""
    pb = await service.playbooks.get_playbook_by_id(
        playbook_id=id,
        organization_id=_get_org_id(current_user),
    )
    if not pb:
        raise HTTPException(status_code=404, detail="Playbook not found.")
    return service.playbooks.test_playbook_match(pb, req)


# ---------------------------------------------------------------------------
# Detections
# ---------------------------------------------------------------------------

@router.get("/detections", response_model=List[Dict[str, Any]])
async def list_available_detectors(
    current_user: User = Depends(get_current_user),
    service: SecurityService = Depends(_get_service),
):
    """Lists all 16 registered deterministic security detectors."""
    return [
        {"detector_name": d.detector_name, "deterministic": True, "active": True}
        for d in service.signals.detection_engine.detectors
    ]
