"""
API endpoints for AI Evaluation Lab (Step 22).

Provides routes for:
- Dataset creation, versioning, list, update, and export
- Evaluation case creation, update, and deletion
- Dataset import (JSON, JSONL, CSV)
- Experiment creation, execution, cancellation, and results
- Factual A/B comparison
- Deterministic regression detection
"""

import json
from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, Response, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.evaluation_lab import (
    CaseNotFoundError,
    DatasetImportError,
    DatasetNotFoundError,
    DatasetValidationError,
    DatasetVersionLockedError,
    DatasetVersionNotFoundError,
    EvaluationCaseCreate,
    EvaluationCaseListResponse,
    EvaluationCaseResponse,
    EvaluationCaseUpdate,
    EvaluationComparisonRequest,
    EvaluationComparisonResponse,
    EvaluationDatasetCreate,
    EvaluationDatasetListResponse,
    EvaluationDatasetResponse,
    EvaluationDatasetUpdate,
    EvaluationDatasetVersionCreate,
    EvaluationDatasetVersionResponse,
    EvaluationExperimentCreate,
    EvaluationExperimentListResponse,
    EvaluationExperimentResponse,
    EvaluationLabError,
    EvaluationLabService,
    ExperimentNotFoundError,
    ExperimentStateError,
    InvalidTargetError,
    RegressionCheckRequest,
    RegressionCheckResponse,
    SideEffectBlockedError,
)

router = APIRouter(prefix="/evaluation", tags=["AI Evaluation Lab"])
eval_lab_service = EvaluationLabService()


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


# ---------------------------------------------------------------------------
# Dataset Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/datasets",
    response_model=EvaluationDatasetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create evaluation dataset",
)
async def create_dataset(
    dataset_in: EvaluationDatasetCreate,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    workspace_id = _resolve_workspace_id(user, header_ws_id=x_workspace_id)
    try:
        dataset, version = await eval_lab_service.create_dataset(
            session=session,
            workspace_id=workspace_id,
            dataset_in=dataset_in,
            created_by=user.id,
        )
        return EvaluationDatasetResponse(
            id=dataset.id,
            workspace_id=dataset.workspace_id,
            project_id=dataset.project_id,
            name=dataset.name,
            description=dataset.description,
            version=dataset.version,
            status=dataset.status,
            created_by=dataset.created_by,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
            case_count=0,
            active_version_id=version.id,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/datasets",
    response_model=EvaluationDatasetListResponse,
    summary="List evaluation datasets",
)
async def list_datasets(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    workspace_id = _resolve_workspace_id(user, header_ws_id=x_workspace_id)
    datasets, total = await eval_lab_service.list_datasets(
        session=session,
        workspace_id=workspace_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    items = []
    for d in datasets:
        items.append(
            EvaluationDatasetResponse(
                id=d.id,
                workspace_id=d.workspace_id,
                project_id=d.project_id,
                name=d.name,
                description=d.description,
                version=d.version,
                status=d.status,
                created_by=d.created_by,
                created_at=d.created_at,
                updated_at=d.updated_at,
                case_count=0,
                active_version_id=d.versions[0].id if d.versions else None,
            )
        )
    return EvaluationDatasetListResponse(items=items, total=total)


@router.get(
    "/datasets/{dataset_id}",
    response_model=EvaluationDatasetResponse,
    summary="Get evaluation dataset details",
)
async def get_dataset(
    dataset_id: UUID,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    workspace_id = _resolve_workspace_id(user, header_ws_id=x_workspace_id)
    try:
        dataset = await eval_lab_service.get_dataset(
            session=session, dataset_id=dataset_id, workspace_id=workspace_id
        )
        latest_version = dataset.versions[0] if dataset.versions else None
        case_count = len(latest_version.cases) if latest_version and latest_version.cases else 0
        return EvaluationDatasetResponse(
            id=dataset.id,
            workspace_id=dataset.workspace_id,
            project_id=dataset.project_id,
            name=dataset.name,
            description=dataset.description,
            version=dataset.version,
            status=dataset.status,
            created_by=dataset.created_by,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
            case_count=case_count,
            active_version_id=latest_version.id if latest_version else None,
        )
    except DatasetNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/datasets/{dataset_id}",
    response_model=EvaluationDatasetResponse,
    summary="Update evaluation dataset",
)
async def update_dataset(
    dataset_id: UUID,
    dataset_in: EvaluationDatasetUpdate,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    workspace_id = _resolve_workspace_id(user, header_ws_id=x_workspace_id)
    try:
        dataset = await eval_lab_service.update_dataset(
            session=session,
            dataset_id=dataset_id,
            dataset_in=dataset_in,
            workspace_id=workspace_id,
        )
        return EvaluationDatasetResponse(
            id=dataset.id,
            workspace_id=dataset.workspace_id,
            project_id=dataset.project_id,
            name=dataset.name,
            description=dataset.description,
            version=dataset.version,
            status=dataset.status,
            created_by=dataset.created_by,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
        )
    except DatasetNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/datasets/{dataset_id}/versions",
    response_model=EvaluationDatasetVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new immutable dataset version",
)
async def create_dataset_version(
    dataset_id: UUID,
    version_in: EvaluationDatasetVersionCreate,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    workspace_id = _resolve_workspace_id(user, header_ws_id=x_workspace_id)
    try:
        version = await eval_lab_service.create_dataset_version(
            session=session,
            dataset_id=dataset_id,
            version_in=version_in,
            created_by=user.id,
            workspace_id=workspace_id,
        )
        return EvaluationDatasetVersionResponse(
            id=version.id,
            dataset_id=version.dataset_id,
            version=version.version,
            created_by=version.created_by,
            description=version.description,
            created_at=version.created_at,
            case_count=len(version.cases) if version.cases else 0,
            is_locked=False,
        )
    except DatasetNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


class ImportPayload(BaseModel):
    file_format: str = "json"  # json | jsonl | csv
    content: str
    target_version_id: Optional[UUID] = None


@router.post(
    "/datasets/{dataset_id}/import",
    summary="Import evaluation cases from JSON, JSONL, or CSV",
)
async def import_cases(
    dataset_id: UUID,
    payload: ImportPayload,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    workspace_id = _resolve_workspace_id(user, header_ws_id=x_workspace_id)
    try:
        raw_bytes = payload.content.encode("utf-8")
        result = await eval_lab_service.import_cases(
            session=session,
            dataset_id=dataset_id,
            raw_bytes=raw_bytes,
            file_format=payload.file_format,
            target_version_id=payload.target_version_id,
            workspace_id=workspace_id,
        )
        return result
    except (DatasetNotFoundError, DatasetVersionNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (DatasetImportError, DatasetValidationError, DatasetVersionLockedError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/datasets/{dataset_id}/export",
    summary="Export evaluation cases as JSON or JSONL",
)
async def export_cases(
    dataset_id: UUID,
    format: str = Query("json", description="json | jsonl"),
    version_id: Optional[UUID] = Query(None),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    workspace_id = _resolve_workspace_id(user, header_ws_id=x_workspace_id)
    try:
        exported_str = await eval_lab_service.export_cases(
            session=session,
            dataset_id=dataset_id,
            export_format=format,
            version_id=version_id,
            workspace_id=workspace_id,
        )
        media_type = "application/json" if format == "json" else "text/plain"
        return Response(content=exported_str, media_type=media_type)
    except DatasetNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ---------------------------------------------------------------------------
# Evaluation Case Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/datasets/{dataset_id}/cases",
    response_model=EvaluationCaseListResponse,
    summary="List cases for a dataset version",
)
async def list_cases(
    dataset_id: UUID,
    version_id: Optional[UUID] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    workspace_id = _resolve_workspace_id(user, header_ws_id=x_workspace_id)
    dataset = await eval_lab_service.get_dataset(session, dataset_id, workspace_id=workspace_id)
    target_v_id = version_id
    if not target_v_id:
        latest = await eval_lab_service.create_dataset_version(
            session, dataset_id, EvaluationDatasetVersionCreate(), workspace_id=workspace_id
        ) if not dataset.versions else dataset.versions[0]
        target_v_id = latest.id

    cases = await eval_lab_service.list_cases(session, target_v_id, limit=limit, offset=offset)
    items = []
    for c in cases:
        items.append(
            EvaluationCaseResponse(
                id=c.id,
                dataset_version_id=c.dataset_version_id,
                case_key=c.case_key,
                name=c.name,
                input_data=c.input_data,
                expected_output=c.expected_output,
                expected_context=c.expected_context,
                expected_sources=c.expected_sources,
                assertions=c.assertions,
                metadata=c.case_metadata,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
        )
    return EvaluationCaseListResponse(items=items, total=len(items))


@router.post(
    "/datasets/{dataset_id}/cases",
    response_model=EvaluationCaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new evaluation case",
)
async def create_case(
    dataset_id: UUID,
    case_in: EvaluationCaseCreate,
    version_id: Optional[UUID] = Query(None),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    workspace_id = _resolve_workspace_id(user, header_ws_id=x_workspace_id)
    dataset = await eval_lab_service.get_dataset(session, dataset_id, workspace_id=workspace_id)
    target_v_id = version_id or (dataset.versions[0].id if dataset.versions else None)
    if not target_v_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dataset has no active version")

    try:
        case = await eval_lab_service.create_case(
            session=session,
            dataset_version_id=target_v_id,
            case_in=case_in,
        )
        return EvaluationCaseResponse(
            id=case.id,
            dataset_version_id=case.dataset_version_id,
            case_key=case.case_key,
            name=case.name,
            input_data=case.input_data,
            expected_output=case.expected_output,
            expected_context=case.expected_context,
            expected_sources=case.expected_sources,
            assertions=case.assertions,
            metadata=case.case_metadata,
            created_at=case.created_at,
            updated_at=case.updated_at,
        )
    except (DatasetValidationError, DatasetVersionLockedError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/cases/{case_id}",
    response_model=EvaluationCaseResponse,
    summary="Get single evaluation case",
)
async def get_case(
    case_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    try:
        c = await eval_lab_service.get_case(session, case_id)
        return EvaluationCaseResponse(
            id=c.id,
            dataset_version_id=c.dataset_version_id,
            case_key=c.case_key,
            name=c.name,
            input_data=c.input_data,
            expected_output=c.expected_output,
            expected_context=c.expected_context,
            expected_sources=c.expected_sources,
            assertions=c.assertions,
            metadata=c.case_metadata,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
    except CaseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/cases/{case_id}",
    response_model=EvaluationCaseResponse,
    summary="Update evaluation case",
)
async def update_case(
    case_id: UUID,
    update_in: EvaluationCaseUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    try:
        c = await eval_lab_service.update_case(session, case_id, update_in)
        return EvaluationCaseResponse(
            id=c.id,
            dataset_version_id=c.dataset_version_id,
            case_key=c.case_key,
            name=c.name,
            input_data=c.input_data,
            expected_output=c.expected_output,
            expected_context=c.expected_context,
            expected_sources=c.expected_sources,
            assertions=c.assertions,
            metadata=c.case_metadata,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
    except CaseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (DatasetValidationError, DatasetVersionLockedError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/cases/{case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete evaluation case",
)
async def delete_case(
    case_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    try:
        await eval_lab_service.delete_case(session, case_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except CaseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DatasetVersionLockedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ---------------------------------------------------------------------------
# Experiment Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/experiments",
    response_model=EvaluationExperimentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create evaluation experiment",
)
async def create_experiment(
    exp_in: EvaluationExperimentCreate,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    workspace_id = _resolve_workspace_id(user, header_ws_id=x_workspace_id)
    try:
        exp = await eval_lab_service.create_experiment(
            session=session,
            workspace_id=workspace_id,
            exp_in=exp_in,
            created_by=user.id,
        )
        return EvaluationExperimentResponse(
            id=exp.id,
            workspace_id=exp.workspace_id,
            project_id=exp.project_id,
            dataset_version_id=exp.dataset_version_id,
            target_type=exp.target_type,
            target_configuration=exp.target_configuration,
            name=exp.name,
            description=exp.description,
            status=exp.status,
            created_by=exp.created_by,
            started_at=exp.started_at,
            completed_at=exp.completed_at,
            created_at=exp.created_at,
        )
    except DatasetVersionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/experiments",
    response_model=EvaluationExperimentListResponse,
    summary="List evaluation experiments",
)
async def list_experiments(
    status_filter: Optional[str] = Query(None, alias="status"),
    target_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    workspace_id = _resolve_workspace_id(user, header_ws_id=x_workspace_id)
    exps, total = await eval_lab_service.list_experiments(
        session=session,
        workspace_id=workspace_id,
        status=status_filter,
        target_type=target_type,
        limit=limit,
        offset=offset,
    )
    items = []
    for exp in exps:
        items.append(
            EvaluationExperimentResponse(
                id=exp.id,
                workspace_id=exp.workspace_id,
                project_id=exp.project_id,
                dataset_version_id=exp.dataset_version_id,
                target_type=exp.target_type,
                target_configuration=exp.target_configuration,
                name=exp.name,
                description=exp.description,
                status=exp.status,
                created_by=exp.created_by,
                started_at=exp.started_at,
                completed_at=exp.completed_at,
                created_at=exp.created_at,
            )
        )
    return EvaluationExperimentListResponse(items=items, total=total)


@router.get(
    "/experiments/{experiment_id}",
    response_model=EvaluationExperimentResponse,
    summary="Get evaluation experiment details",
)
async def get_experiment(
    experiment_id: UUID,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    workspace_id = _resolve_workspace_id(user, header_ws_id=x_workspace_id)
    try:
        exp = await eval_lab_service.get_experiment(
            session=session, experiment_id=experiment_id, workspace_id=workspace_id
        )
        return EvaluationExperimentResponse(
            id=exp.id,
            workspace_id=exp.workspace_id,
            project_id=exp.project_id,
            dataset_version_id=exp.dataset_version_id,
            target_type=exp.target_type,
            target_configuration=exp.target_configuration,
            name=exp.name,
            description=exp.description,
            status=exp.status,
            created_by=exp.created_by,
            started_at=exp.started_at,
            completed_at=exp.completed_at,
            created_at=exp.created_at,
        )
    except ExperimentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/experiments/{experiment_id}/run",
    response_model=EvaluationExperimentResponse,
    summary="Execute evaluation experiment",
)
async def run_experiment(
    experiment_id: UUID,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    workspace_id = _resolve_workspace_id(user, header_ws_id=x_workspace_id)
    try:
        exp = await eval_lab_service.run_experiment(
            session=session, experiment_id=experiment_id, workspace_id=workspace_id
        )
        return EvaluationExperimentResponse(
            id=exp.id,
            workspace_id=exp.workspace_id,
            project_id=exp.project_id,
            dataset_version_id=exp.dataset_version_id,
            target_type=exp.target_type,
            target_configuration=exp.target_configuration,
            name=exp.name,
            description=exp.description,
            status=exp.status,
            created_by=exp.created_by,
            started_at=exp.started_at,
            completed_at=exp.completed_at,
            created_at=exp.created_at,
        )
    except ExperimentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ExperimentStateError, DatasetValidationError, SideEffectBlockedError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/experiments/{experiment_id}/cancel",
    response_model=EvaluationExperimentResponse,
    summary="Cancel in-flight evaluation experiment",
)
async def cancel_experiment(
    experiment_id: UUID,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    workspace_id = _resolve_workspace_id(user, header_ws_id=x_workspace_id)
    try:
        exp = await eval_lab_service.cancel_experiment(
            session=session, experiment_id=experiment_id, workspace_id=workspace_id
        )
        return EvaluationExperimentResponse(
            id=exp.id,
            workspace_id=exp.workspace_id,
            project_id=exp.project_id,
            dataset_version_id=exp.dataset_version_id,
            target_type=exp.target_type,
            target_configuration=exp.target_configuration,
            name=exp.name,
            description=exp.description,
            status=exp.status,
            created_by=exp.created_by,
            started_at=exp.started_at,
            completed_at=exp.completed_at,
            created_at=exp.created_at,
        )
    except ExperimentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ExperimentStateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/experiments/{experiment_id}/results",
    summary="Get evaluation experiment results and case runs",
)
async def get_experiment_results(
    experiment_id: UUID,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    workspace_id = _resolve_workspace_id(user, header_ws_id=x_workspace_id)
    try:
        return await eval_lab_service.get_experiment_results(
            session=session, experiment_id=experiment_id, workspace_id=workspace_id
        )
    except ExperimentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/experiments/{experiment_id}/trace",
    summary="Get execution trace events for an experiment",
)
async def get_experiment_trace(
    experiment_id: UUID,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    workspace_id = _resolve_workspace_id(user, header_ws_id=x_workspace_id)
    # Validate experiment exists and workspace matches
    await eval_lab_service.get_experiment(session, experiment_id, workspace_id=workspace_id)
    events = await eval_lab_service.get_experiment_trace(session, experiment_id)
    return [
        {
            "id": str(ev.id),
            "event_type": ev.event_type,
            "status": ev.status,
            "operation": ev.operation,
            "duration_ms": ev.duration_ms,
            "metadata": ev.safe_metadata,
            "created_at": ev.created_at.isoformat() if ev.created_at else None,
        }
        for ev in events
    ]


# ---------------------------------------------------------------------------
# Comparison & Regression Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/compare",
    response_model=EvaluationComparisonResponse,
    summary="Compare two evaluation experiments factually",
)
async def compare_experiments(
    req: EvaluationComparisonRequest,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    workspace_id = _resolve_workspace_id(user, header_ws_id=x_workspace_id)
    try:
        return await eval_lab_service.compare_experiments(
            session=session,
            experiment_a_id=req.experiment_a,
            experiment_b_id=req.experiment_b,
            workspace_id=workspace_id,
        )
    except ExperimentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/regressions/check",
    response_model=RegressionCheckResponse,
    summary="Detect deterministic regressions between baseline and candidate experiments",
)
async def detect_regressions(
    req: RegressionCheckRequest,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    workspace_id = _resolve_workspace_id(user, header_ws_id=x_workspace_id)
    try:
        return await eval_lab_service.detect_regressions(
            session=session,
            baseline_experiment_id=req.baseline_experiment,
            candidate_experiment_id=req.candidate_experiment,
            workspace_id=workspace_id,
        )
    except ExperimentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
