"""
Workflow System API endpoints for CRUD, validation, publishing, templates, and execution.
"""
from typing import Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.llm.factory import LLMProviderFactory, get_llm_factory
from backend.app.services.observability.schemas import ExecutionTraceEventResponse
from backend.app.services.observability.service import ObservabilityService
from backend.app.services.workflows.schemas import (
    WorkflowCreateRequest,
    WorkflowDefinition,
    WorkflowDefinitionUpdateRequest,
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowRunListResponse,
    WorkflowRunRequest,
    WorkflowRunResponse,
    WorkflowTemplateListResponse,
    WorkflowTemplateResponse,
    WorkflowUpdateRequest,
    WorkflowValidationResponse,
)
from backend.app.services.workflows.service import WorkflowService
from backend.app.services.workflows.templates import WorkflowTemplateRegistry

router = APIRouter(tags=["workflows"])


def get_workflow_service(
    session: AsyncSession = Depends(get_db),
    llm_factory: LLMProviderFactory = Depends(get_llm_factory),
) -> WorkflowService:
    return WorkflowService(session=session, llm_factory=llm_factory)


# --- TEMPLATE ENDPOINTS ---

@router.get("/workflow-templates", response_model=WorkflowTemplateListResponse)
async def list_workflow_templates(
    user: User = Depends(get_current_user),
) -> WorkflowTemplateListResponse:
    """
    List all pre-configured built-in workflow templates.
    """
    templates = WorkflowTemplateRegistry.get_all_templates()
    return WorkflowTemplateListResponse(templates=templates)


@router.post("/workflow-templates/{template_id}/install", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def install_workflow_template(
    template_id: str,
    workspace_id: UUID = Query(..., description="Target workspace ID"),
    project_id: Optional[UUID] = Query(None, description="Optional target project ID"),
    user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    """
    Installs a built-in workflow template into the active workspace as a customizable draft workflow.
    """
    return await service.install_template(
        template_id=template_id,
        workspace_id=workspace_id,
        user=user,
        project_id=project_id,
    )


# --- WORKFLOW CRUD & BUILDER ENDPOINTS ---

@router.post("/workflows", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    request: WorkflowCreateRequest,
    workspace_id: UUID = Query(..., description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    """
    Create a new AI workflow in the active workspace.
    """
    return await service.create_workflow(
        workspace_id=workspace_id,
        request=request,
        user=user,
    )


@router.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows(
    workspace_id: UUID = Query(..., description="Active workspace ID"),
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    status: Optional[str] = Query(None, description="Filter by status (draft, published, archived)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowListResponse:
    """
    List workflows within a workspace with optional project and status filters.
    """
    return await service.list_workflows(
        workspace_id=workspace_id,
        project_id=project_id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: UUID,
    workspace_id: UUID = Query(..., description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    """
    Retrieve workflow details with ordered step list and run statistics.
    """
    return await service.get_workflow(
        workflow_id=workflow_id,
        workspace_id=workspace_id,
    )


@router.patch("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: UUID,
    request: WorkflowUpdateRequest,
    workspace_id: UUID = Query(..., description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    """
    Update workflow metadata, schemas, or status.
    """
    return await service.update_workflow(
        workflow_id=workflow_id,
        workspace_id=workspace_id,
        request=request,
        user=user,
    )


@router.delete("/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: UUID,
    workspace_id: UUID = Query(..., description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> None:
    """
    Delete a workflow and its associated steps and version history.
    """
    await service.delete_workflow(
        workflow_id=workflow_id,
        workspace_id=workspace_id,
    )


@router.get("/workflows/{workflow_id}/definition", response_model=WorkflowDefinition)
async def get_workflow_definition(
    workflow_id: UUID,
    workspace_id: UUID = Query(..., description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowDefinition:
    """
    Retrieve serializable workflow definition for visual builder and validation.
    """
    return await service.get_workflow_definition(
        workflow_id=workflow_id,
        workspace_id=workspace_id,
    )


@router.patch("/workflows/{workflow_id}/definition", response_model=WorkflowResponse)
async def update_workflow_definition(
    workflow_id: UUID,
    request: WorkflowDefinitionUpdateRequest,
    workspace_id: UUID = Query(..., description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    """
    Update workflow steps and configuration. If published, creates a new draft version.
    """
    return await service.update_workflow_definition(
        workflow_id=workflow_id,
        workspace_id=workspace_id,
        request=request,
        user=user,
    )


@router.post("/workflows/{workflow_id}/validate", response_model=WorkflowValidationResponse)
async def validate_workflow(
    workflow_id: UUID,
    workspace_id: UUID = Query(..., description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowValidationResponse:
    """
    Validate a workflow against schema contracts, step limits, branch integrity, and cycle bounds.
    """
    return await service.validate_workflow(
        workflow_id=workflow_id,
        workspace_id=workspace_id,
    )


@router.post("/workflows/{workflow_id}/publish", response_model=WorkflowResponse)
async def publish_workflow(
    workflow_id: UUID,
    workspace_id: UUID = Query(..., description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    """
    Publish a validated workflow, locking the current version as an immutable snapshot.
    """
    return await service.publish_workflow(
        workflow_id=workflow_id,
        workspace_id=workspace_id,
        user=user,
    )


@router.post("/workflows/{workflow_id}/duplicate", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_workflow(
    workflow_id: UUID,
    workspace_id: UUID = Query(..., description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    """
    Clone an existing workflow into a new editable draft workflow.
    """
    return await service.duplicate_workflow(
        workflow_id=workflow_id,
        workspace_id=workspace_id,
        user=user,
    )


# --- EXECUTION & RUNS ENDPOINTS ---

@router.post("/workflows/{workflow_id}/run", status_code=status.HTTP_201_CREATED)
async def run_workflow(
    workflow_id: UUID,
    request: Optional[WorkflowRunRequest] = None,
    workspace_id: UUID = Query(..., description="Active workspace ID"),
    mode: str = Query("sync", description="Execution mode: 'sync' or 'async'"),
    user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> Any:
    """
    Execute a workflow run with runtime input parameters (sync or async durable job).
    """
    req = request or WorkflowRunRequest()
    if mode == "async":
        return await service.run_workflow_async(
            workflow_id=workflow_id,
            workspace_id=workspace_id,
            user=user,
            request=req,
        )

    return await service.run_workflow(
        workflow_id=workflow_id,
        workspace_id=workspace_id,
        user=user,
        request=req,
    )


@router.get("/workflows/{workflow_id}/runs", response_model=WorkflowRunListResponse)
async def list_workflow_runs(
    workflow_id: UUID,
    workspace_id: UUID = Query(..., description="Active workspace ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowRunListResponse:
    """
    List historical execution runs for a specific workflow.
    """
    return await service.list_workflow_runs(
        workspace_id=workspace_id,
        workflow_id=workflow_id,
        limit=limit,
        offset=offset,
    )


@router.get("/workflow-runs/{run_id}", response_model=WorkflowRunResponse)
async def get_workflow_run(
    run_id: UUID,
    workspace_id: UUID = Query(..., description="Active workspace ID"),
    user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowRunResponse:
    """
    Retrieve workflow run detail and execution output.
    """
    return await service.get_workflow_run(
        run_id=run_id,
        workspace_id=workspace_id,
    )


@router.get("/workflow-runs/{run_id}/trace")
async def get_workflow_run_trace(
    run_id: UUID,
    workspace_id: UUID = Query(..., description="Active workspace ID"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Retrieve sequential execution trace events for a workflow run.
    """
    obs_service = ObservabilityService(session)
    return await obs_service.get_run_trace_events(run_id, workspace_id)
