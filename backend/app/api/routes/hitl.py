"""
REST API endpoints for the Human-in-the-Loop (HITL) System (Step 18).
"""
import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.hitl import (
    ApprovalActionRequest,
    HITLExpiredError,
    HITLNotFoundError,
    HITLPermissionError,
    HITLService,
    HITLStatusError,
    HITLValidationError,
    HumanInterventionResponse,
    InterventionAssignRequest,
    InterventionCreateRequest,
    WorkspaceApprovalPolicyResponse,
    WorkspaceApprovalPolicyUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hitl", tags=["HITL"])


def _resolve_workspace_id(
    user: User,
    header_ws_id: Optional[str] = None,
    query_ws_id: Optional[UUID] = None,
) -> UUID:
    """Extracts and verifies active workspace ID for the request."""
    if query_ws_id:
        return query_ws_id
    if header_ws_id:
        try:
            return UUID(header_ws_id)
        except ValueError:
            pass
    if getattr(user, "default_workspace_id", None):
        return user.default_workspace_id
    if getattr(user, "workspaces", None) and len(user.workspaces) > 0:
        return user.workspaces[0].id
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Workspace context could not be resolved. Please specify 'X-Workspace-Id' header.",
    )


# =============================================================================
# 1. Intervention Requests Endpoints
# =============================================================================

@router.get("/requests", response_model=List[HumanInterventionResponse])
async def list_requests(
    status: Optional[str] = Query(None, description="Filter by status (pending, approved, rejected, edited, expired, cancelled)"),
    assigned_to: Optional[UUID] = Query(None, description="Filter by assigned user ID"),
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    priority: Optional[str] = Query(None, description="Filter by priority (low, normal, high, critical)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    List human intervention requests for the current workspace.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    svc = HITLService(db)
    requests = await svc.list_requests(
        workspace_id=ws_id,
        status=status,
        assigned_to=assigned_to,
        project_id=project_id,
        priority=priority,
        limit=limit,
        offset=offset,
    )
    return [HumanInterventionResponse.model_validate(r) for r in requests]


@router.post("/requests", response_model=HumanInterventionResponse, status_code=status.HTTP_201_CREATED)
async def create_request(
    request: InterventionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Create a new human intervention request.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    svc = HITLService(db)
    try:
        from backend.app.services.hitl.requests import InterventionRequestManager
        created = await InterventionRequestManager.create_request(
            session=db,
            workspace_id=ws_id,
            request=request,
            requested_by=current_user.id,
        )
        await db.commit()
        return await svc.get_request(created.id, ws_id)
    except Exception as e:
        logger.error(f"[HITL] Failed to create request: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/requests/{request_id}", response_model=HumanInterventionResponse)
async def get_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Get detailed information for a specific intervention request.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    svc = HITLService(db)
    try:
        req = await svc.get_request(request_id, ws_id)
        return HumanInterventionResponse.model_validate(req)
    except HITLNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Request '{request_id}' not found.")


@router.post("/requests/{request_id}/approve", response_model=HumanInterventionResponse)
async def approve_request(
    request_id: UUID,
    payload: Optional[ApprovalActionRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Approve an intervention request and automatically resume any paused workflow.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    svc = HITLService(db)
    try:
        req = await svc.approve_request(
            request_id=request_id,
            workspace_id=ws_id,
            user=current_user,
            request_body=payload,
        )
        return HumanInterventionResponse.model_validate(req)
    except HITLNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Request '{request_id}' not found.")
    except HITLPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HITLExpiredError as e:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(e))
    except HITLStatusError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"[HITL] Approve failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/requests/{request_id}/reject", response_model=HumanInterventionResponse)
async def reject_request(
    request_id: UUID,
    payload: Optional[ApprovalActionRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Reject an intervention request and halt any waiting workflow execution.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    svc = HITLService(db)
    try:
        req = await svc.reject_request(
            request_id=request_id,
            workspace_id=ws_id,
            user=current_user,
            request_body=payload,
        )
        return HumanInterventionResponse.model_validate(req)
    except HITLNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Request '{request_id}' not found.")
    except HITLPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HITLExpiredError as e:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(e))
    except HITLStatusError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"[HITL] Reject failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/requests/{request_id}/edit", response_model=HumanInterventionResponse)
async def edit_request(
    request_id: UUID,
    payload: ApprovalActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Edit the parameters of an intervention action and approve with the edited payload.
    """
    if not payload.edited_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field 'edited_data' is required for edit decision.",
        )
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    svc = HITLService(db)
    try:
        req = await svc.edit_request(
            request_id=request_id,
            workspace_id=ws_id,
            user=current_user,
            request_body=payload,
        )
        return HumanInterventionResponse.model_validate(req)
    except HITLNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Request '{request_id}' not found.")
    except HITLPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HITLExpiredError as e:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(e))
    except HITLStatusError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except HITLValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"[HITL] Edit failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/requests/{request_id}/cancel", response_model=HumanInterventionResponse)
async def cancel_request(
    request_id: UUID,
    payload: Optional[ApprovalActionRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Cancel an intervention request.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    svc = HITLService(db)
    try:
        req = await svc.cancel_request(
            request_id=request_id,
            workspace_id=ws_id,
            user=current_user,
            request_body=payload,
        )
        return HumanInterventionResponse.model_validate(req)
    except HITLNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Request '{request_id}' not found.")
    except HITLPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HITLExpiredError as e:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(e))
    except HITLStatusError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"[HITL] Cancel failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/requests/{request_id}/assign", response_model=HumanInterventionResponse)
async def assign_request(
    request_id: UUID,
    payload: InterventionAssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Reassign an intervention request to a specific user.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    svc = HITLService(db)
    try:
        req = await svc.assign_request(
            request_id=request_id,
            workspace_id=ws_id,
            user=current_user,
            assigned_to=payload.assigned_to,
        )
        return HumanInterventionResponse.model_validate(req)
    except HITLNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Request '{request_id}' not found.")
    except HITLPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HITLStatusError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"[HITL] Assign failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =============================================================================
# 2. Workspace Approval Policies Endpoints
# =============================================================================

@router.get("/policies", response_model=WorkspaceApprovalPolicyResponse)
async def get_policies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Get the approval policies for the current workspace.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    svc = HITLService(db)
    policy = await svc.get_or_create_policy(ws_id)
    return WorkspaceApprovalPolicyResponse.model_validate(policy)


@router.patch("/policies", response_model=WorkspaceApprovalPolicyResponse)
async def update_policies(
    payload: WorkspaceApprovalPolicyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Update workspace approval policies.
    Note: Mandatory destructive-action approval cannot be disabled.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    svc = HITLService(db)
    policy = await svc.update_policy(ws_id, payload)
    return WorkspaceApprovalPolicyResponse.model_validate(policy)
