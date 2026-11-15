"""
REST API endpoints for the Connector System.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.logging import logger
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.connectors.errors import (
    ConnectorAuthError,
    ConnectorError,
    ConnectorNotFoundError,
    ConnectorOperationNotFoundError,
    ConnectorPermissionError,
    ConnectorRateLimitError,
    ConnectorTimeoutError,
    ConnectorUnavailableError,
    ConnectorValidationError,
)
from backend.app.services.connectors.executor import ConnectorExecutor, get_connector_executor
from backend.app.services.connectors.schemas import (
    ConnectorConnectRequest,
    ConnectorExecuteRequest,
    ConnectorMetadataResponse,
    ConnectorOperationMetadata,
    ConnectorPermissionResponse,
    ConnectorPermissionUpdateRequest,
    ConnectorResult,
    ConnectorStatusResponse,
    ConnectorTestResponse,
)
from backend.app.services.connectors.service import ConnectorService, get_connector_service

router = APIRouter(prefix="/connectors", tags=["Connectors"])


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


@router.get("", response_model=List[ConnectorMetadataResponse])
async def list_connectors(
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    service: ConnectorService = Depends(get_connector_service),
) -> List[ConnectorMetadataResponse]:
    """
    List all available connectors with active connection status for the workspace.
    """
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    return await service.list_connectors(session=session, workspace_id=ws_id)


@router.get("/{connector_name}", response_model=ConnectorMetadataResponse)
async def get_connector(
    connector_name: str,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    service: ConnectorService = Depends(get_connector_service),
) -> ConnectorMetadataResponse:
    """
    Retrieve connector details and workspace connection status.
    """
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    try:
        return await service.get_connector(session=session, workspace_id=ws_id, connector_name=connector_name)
    except ConnectorNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.get("/{connector_name}/operations", response_model=List[ConnectorOperationMetadata])
async def get_connector_operations(
    connector_name: str,
    user: User = Depends(get_current_user),
    service: ConnectorService = Depends(get_connector_service),
) -> List[ConnectorOperationMetadata]:
    """
    List supported operations and input schemas for a connector.
    """
    try:
        return await service.get_operations(connector_name=connector_name)
    except ConnectorNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.get("/{connector_name}/status", response_model=ConnectorStatusResponse)
async def get_connector_status(
    connector_name: str,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    service: ConnectorService = Depends(get_connector_service),
) -> ConnectorStatusResponse:
    """
    Get current connection status and safe account info for a connector.
    """
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    return await service.get_status(session=session, workspace_id=ws_id, connector_name=connector_name)


@router.post("/{connector_name}/connect", response_model=ConnectorStatusResponse)
async def connect_connector(
    connector_name: str,
    payload: ConnectorConnectRequest,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    service: ConnectorService = Depends(get_connector_service),
) -> ConnectorStatusResponse:
    """
    Verify credentials against remote provider and save encrypted in vault.
    Never returns secrets in response.
    """
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    try:
        res = await service.connect(
            session=session,
            workspace_id=ws_id,
            connector_name=connector_name,
            credential=payload.credential,
            credential_type=payload.credential_type,
            metadata=payload.metadata,
            user_id=user.id,
        )
        await session.commit()
        return res
    except ConnectorNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ConnectorAuthError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"[ConnectorAPI] Connect failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Connection failed: {str(e)}")


@router.delete("/{connector_name}/disconnect", status_code=status.HTTP_200_OK)
async def disconnect_connector(
    connector_name: str,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    service: ConnectorService = Depends(get_connector_service),
) -> dict:
    """
    Disconnect a connector and securely remove credentials for the workspace.
    """
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    try:
        deleted = await service.disconnect(
            session=session,
            workspace_id=ws_id,
            connector_name=connector_name,
            user_id=user.id,
        )
        await session.commit()
        return {"connector": connector_name, "disconnected": deleted, "status": "disconnected"}
    except ConnectorNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.post("/{connector_name}/test", response_model=ConnectorTestResponse)
async def test_connector(
    connector_name: str,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    service: ConnectorService = Depends(get_connector_service),
) -> ConnectorTestResponse:
    """
    Test connectivity using stored credentials without performing destructive actions.
    """
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    try:
        return await service.test_connection(
            session=session,
            workspace_id=ws_id,
            connector_name=connector_name,
            user_id=user.id,
        )
    except ConnectorNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.get("/{connector_name}/permissions", response_model=List[ConnectorPermissionResponse])
async def list_connector_permissions(
    connector_name: str,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    service: ConnectorService = Depends(get_connector_service),
) -> List[ConnectorPermissionResponse]:
    """
    List operation permission settings for the connector in the workspace.
    """
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    try:
        return await service.list_permissions(
            session=session,
            workspace_id=ws_id,
            connector_name=connector_name,
        )
    except ConnectorNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.patch("/{connector_name}/permissions", response_model=ConnectorPermissionResponse)
async def update_connector_permission(
    connector_name: str,
    payload: ConnectorPermissionUpdateRequest,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    service: ConnectorService = Depends(get_connector_service),
) -> ConnectorPermissionResponse:
    """
    Update permission level or toggle an operation for the workspace.
    """
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)
    try:
        perm = await service.update_permission(
            session=session,
            workspace_id=ws_id,
            connector_name=connector_name,
            operation=payload.operation,
            enabled=payload.enabled,
            permission_level=payload.permission_level or "read",
        )
        await session.commit()
        return perm
    except ConnectorNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.post("/{connector_name}/execute")
async def execute_connector_operation(
    connector_name: str,
    payload: ConnectorExecuteRequest,
    mode: Optional[str] = Query("sync", description="Execution mode: sync or async"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    workspace_id: Optional[UUID] = Query(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    executor: ConnectorExecutor = Depends(get_connector_executor),
):
    """
    Execute a connector operation directly in workspace context (sync or async background job).
    """
    ws_id = _resolve_workspace_id(user, x_workspace_id, workspace_id)

    if mode == "async":
        from fastapi.responses import JSONResponse
        from backend.app.services.jobs.service import JobService
        from backend.app.services.jobs.schemas import JobCreateRequest
        from backend.app.services.jobs.constants import JobType, JobPriority

        job_service = JobService(session)
        job_resp, _ = await job_service.create_job(
            workspace_id=ws_id,
            request=JobCreateRequest(
                job_type=JobType.CONNECTOR_OPERATION,
                priority=JobPriority.NORMAL,
                payload={
                    "request": {
                        "connector_name": connector_name,
                        "operation": payload.operation,
                        "arguments": payload.arguments,
                    },
                    "user_id": str(user.id),
                },
            ),
            user_id=user.id,
        )
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "job_id": str(job_resp.id),
                "status": job_resp.status,
                "job_type": job_resp.job_type,
                "created_at": job_resp.created_at.isoformat() if job_resp.created_at else None,
                "available_at": job_resp.available_at.isoformat() if job_resp.available_at else None,
                "poll_url": f"/api/jobs/{job_resp.id}",
                "cancel_url": f"/api/jobs/{job_resp.id}/cancel",
            },
        )
    res = await executor.execute(
        connector_name=connector_name,
        operation=payload.operation,
        arguments=payload.arguments,
        workspace_id=ws_id,
        user=user,
        session=session,
    )

    if not res.success:
        if res.error_code == "CONNECTOR_AUTH_FAILED":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=res.error_message)
        elif res.error_code == "CONNECTOR_PERMISSION_DENIED":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=res.error_message)
        elif res.error_code == "CONNECTOR_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res.error_message)
        elif res.error_code == "CONNECTOR_RATE_LIMITED":
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=res.error_message)
        elif res.error_code == "CONNECTOR_INVALID_ARGUMENTS":
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=res.error_message)
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=res.error_message)

    return res
