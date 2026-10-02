"""
API routes for Workflow Triggers, Event Automation, and Webhook Ingestion.
"""
import json
import uuid
from typing import Any, Dict, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.triggers.schemas import (
    ManualTriggerRunRequest,
    TriggerRunListResponse,
    TriggerRunResponse,
    TriggerTestRequest,
    TriggerTestResponse,
    WebhookSecretResponse,
    WebhookStatusResponse,
    WorkflowTriggerCreateRequest,
    WorkflowTriggerListResponse,
    WorkflowTriggerResponse,
    WorkflowTriggerUpdateRequest,
)
from backend.app.services.triggers.service import TriggerService

router = APIRouter(tags=["triggers"])


def get_trigger_service(session: AsyncSession = Depends(get_db)) -> TriggerService:
    return TriggerService(session=session)


# --- 1. WORKFLOW TRIGGER CRUD & RUN ---

@router.post(
    "/workflows/{workflow_id}/triggers",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow_trigger(
    workflow_id: UUID,
    request: WorkflowTriggerCreateRequest,
    workspace_id: Optional[UUID] = Query(None, description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: TriggerService = Depends(get_trigger_service),
) -> Dict[str, Any]:
    """Creates a trigger for a specific workflow."""
    ws_id = workspace_id or user.workspace_id
    trigger_resp, plain_secret = await service.create_trigger(
        workspace_id=ws_id,
        workflow_id=workflow_id,
        request=request,
        user=user,
    )
    result = trigger_resp.model_dump()
    if plain_secret:
        result["webhook_secret"] = plain_secret
    return result


@router.get(
    "/workflows/{workflow_id}/triggers",
    response_model=WorkflowTriggerListResponse,
)
async def list_workflow_triggers(
    workflow_id: UUID,
    workspace_id: Optional[UUID] = Query(None, description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: TriggerService = Depends(get_trigger_service),
) -> WorkflowTriggerListResponse:
    """Lists all triggers configured for a given workflow."""
    ws_id = workspace_id or user.workspace_id
    return await service.list_triggers(workspace_id=ws_id, workflow_id=workflow_id)


@router.post(
    "/workflows/{workflow_id}/triggers/{trigger_id}/run",
    response_model=TriggerRunResponse,
    status_code=status.HTTP_200_OK,
)
async def run_manual_workflow_trigger(
    workflow_id: UUID,
    trigger_id: UUID,
    request: Optional[ManualTriggerRunRequest] = None,
    workspace_id: Optional[UUID] = Query(None, description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: TriggerService = Depends(get_trigger_service),
) -> TriggerRunResponse:
    """Explicitly executes a trigger through the workflow engine."""
    ws_id = workspace_id or user.workspace_id
    input_data = request.input_data if request else {}
    return await service.run_manual_trigger(
        workflow_id=workflow_id,
        trigger_id=trigger_id,
        workspace_id=ws_id,
        user=user,
        input_data=input_data,
    )


# --- 2. TRIGGER MANAGEMENT ---

@router.get("/triggers/{trigger_id}", response_model=WorkflowTriggerResponse)
async def get_trigger(
    trigger_id: UUID,
    workspace_id: Optional[UUID] = Query(None, description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: TriggerService = Depends(get_trigger_service),
) -> WorkflowTriggerResponse:
    ws_id = workspace_id or user.workspace_id
    return await service.get_trigger(trigger_id=trigger_id, workspace_id=ws_id)


@router.patch("/triggers/{trigger_id}", response_model=WorkflowTriggerResponse)
async def update_trigger(
    trigger_id: UUID,
    request: WorkflowTriggerUpdateRequest,
    workspace_id: Optional[UUID] = Query(None, description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: TriggerService = Depends(get_trigger_service),
) -> WorkflowTriggerResponse:
    ws_id = workspace_id or user.workspace_id
    return await service.update_trigger(trigger_id=trigger_id, workspace_id=ws_id, request=request)


@router.delete("/triggers/{trigger_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trigger(
    trigger_id: UUID,
    workspace_id: Optional[UUID] = Query(None, description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: TriggerService = Depends(get_trigger_service),
) -> None:
    ws_id = workspace_id or user.workspace_id
    await service.delete_trigger(trigger_id=trigger_id, workspace_id=ws_id)


@router.post("/triggers/{trigger_id}/pause", response_model=WorkflowTriggerResponse)
async def pause_trigger(
    trigger_id: UUID,
    workspace_id: Optional[UUID] = Query(None, description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: TriggerService = Depends(get_trigger_service),
) -> WorkflowTriggerResponse:
    ws_id = workspace_id or user.workspace_id
    return await service.pause_trigger(trigger_id=trigger_id, workspace_id=ws_id)


@router.post("/triggers/{trigger_id}/resume", response_model=WorkflowTriggerResponse)
async def resume_trigger(
    trigger_id: UUID,
    workspace_id: Optional[UUID] = Query(None, description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: TriggerService = Depends(get_trigger_service),
) -> WorkflowTriggerResponse:
    ws_id = workspace_id or user.workspace_id
    return await service.resume_trigger(trigger_id=trigger_id, workspace_id=ws_id)


@router.post("/triggers/{trigger_id}/test", response_model=TriggerTestResponse)
async def test_trigger(
    trigger_id: UUID,
    request: TriggerTestRequest,
    workspace_id: Optional[UUID] = Query(None, description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: TriggerService = Depends(get_trigger_service),
) -> TriggerTestResponse:
    """Evaluates filters and input mapping in dry-run mode without external side effects."""
    ws_id = workspace_id or user.workspace_id
    return await service.test_trigger(trigger_id=trigger_id, workspace_id=ws_id, request=request)


@router.get("/triggers/{trigger_id}/runs", response_model=TriggerRunListResponse)
async def list_trigger_runs(
    trigger_id: UUID,
    workspace_id: Optional[UUID] = Query(None, description="Active workspace ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    service: TriggerService = Depends(get_trigger_service),
) -> TriggerRunListResponse:
    ws_id = workspace_id or user.workspace_id
    return await service.list_trigger_runs(
        trigger_id=trigger_id,
        workspace_id=ws_id,
        limit=limit,
        offset=offset,
    )


@router.get("/trigger-runs/{trigger_run_id}", response_model=TriggerRunResponse)
async def get_trigger_run(
    trigger_run_id: UUID,
    workspace_id: Optional[UUID] = Query(None, description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: TriggerService = Depends(get_trigger_service),
) -> TriggerRunResponse:
    ws_id = workspace_id or user.workspace_id
    return await service.get_trigger_run(trigger_run_id=trigger_run_id, workspace_id=ws_id)


# --- 3. WEBHOOK MANAGEMENT ---

@router.post("/triggers/{trigger_id}/webhook/regenerate-secret", response_model=WebhookSecretResponse)
async def regenerate_webhook_secret(
    trigger_id: UUID,
    workspace_id: Optional[UUID] = Query(None, description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: TriggerService = Depends(get_trigger_service),
) -> WebhookSecretResponse:
    ws_id = workspace_id or user.workspace_id
    return await service.regenerate_webhook_secret(trigger_id=trigger_id, workspace_id=ws_id)


@router.get("/triggers/{trigger_id}/webhook/status", response_model=WebhookStatusResponse)
async def get_webhook_status(
    trigger_id: UUID,
    workspace_id: Optional[UUID] = Query(None, description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: TriggerService = Depends(get_trigger_service),
) -> WebhookStatusResponse:
    ws_id = workspace_id or user.workspace_id
    return await service.get_webhook_status(trigger_id=trigger_id, workspace_id=ws_id)


@router.post("/triggers/{trigger_id}/webhook/test", response_model=TriggerTestResponse)
async def test_webhook_trigger(
    trigger_id: UUID,
    request: TriggerTestRequest,
    workspace_id: Optional[UUID] = Query(None, description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: TriggerService = Depends(get_trigger_service),
) -> TriggerTestResponse:
    ws_id = workspace_id or user.workspace_id
    return await service.test_trigger(trigger_id=trigger_id, workspace_id=ws_id, request=request)


# --- 4. PUBLIC WEBHOOK INGESTION ENDPOINTS ---

@router.post(
    "/webhooks/{trigger_id}",
    status_code=status.HTTP_202_ACCEPTED,
)
async def handle_public_webhook(
    trigger_id: str,
    request: Request,
    service: TriggerService = Depends(get_trigger_service),
) -> Dict[str, Any]:
    """
    Public webhook receiver endpoint.
    Accepts incoming events, validates signature, filters, and queues execution.
    Returns immediately without synchronous long-running execution.
    """
    raw_body = await request.body()
    headers_dict = dict(request.headers)

    parsed_payload: Dict[str, Any] = {}
    if raw_body:
        try:
            parsed_payload = json.loads(raw_body.decode("utf-8"))
        except Exception:
            parsed_payload = {"raw_text": raw_body.decode("utf-8", errors="replace")}

    return await service.handle_webhook_event(
        identifier=trigger_id,
        raw_body=raw_body,
        headers=headers_dict,
        parsed_payload=parsed_payload,
    )
