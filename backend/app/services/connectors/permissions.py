"""
Permission checking and access control service for external connectors.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.db.models.connector import ConnectorPermission
from backend.app.services.connectors.errors import ConnectorPermissionError


class ConnectorPermissionService:
    """
    Manages operation-level permissions per workspace for connectors.
    Default policy: Read operations are permitted by default unless explicitly disabled.
    Write and Destructive operations require explicit permission grants.
    """

    async def check_permission(
        self,
        session: Optional[AsyncSession],
        workspace_id: uuid.UUID,
        connector_name: str,
        operation: str,
        permission_level: str = "read",
    ) -> bool:
        """
        Validates whether the workspace is authorized to execute the operation.
        """
        # Step 16 constraint: write and destructive operations are rejected by default
        if permission_level in ("write", "destructive"):
            # Check for explicit permission record enabling it
            if session is None:
                return False
            stmt = select(ConnectorPermission).where(
                ConnectorPermission.workspace_id == workspace_id,
                ConnectorPermission.connector_name == connector_name,
                ConnectorPermission.operation.in_([operation, "*"]),
            )
            result = await session.execute(stmt)
            perm = result.scalar_one_or_none()
            if not perm or not perm.enabled:
                return False
            return True

        # For read operations: allowed unless explicitly disabled in DB
        if session is not None:
            stmt = select(ConnectorPermission).where(
                ConnectorPermission.workspace_id == workspace_id,
                ConnectorPermission.connector_name == connector_name,
                ConnectorPermission.operation.in_([operation, "*"]),
            )
            result = await session.execute(stmt)
            perm = result.scalar_one_or_none()
            if perm is not None:
                return perm.enabled

        return True

    async def list_permissions(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        connector_name: str,
    ) -> List[ConnectorPermission]:
        """
        Lists all explicit permission configuration records for a connector in the workspace.
        """
        stmt = select(ConnectorPermission).where(
            ConnectorPermission.workspace_id == workspace_id,
            ConnectorPermission.connector_name == connector_name,
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def update_permission(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        connector_name: str,
        operation: str,
        enabled: bool,
        permission_level: str = "read",
    ) -> ConnectorPermission:
        """
        Upserts an operation permission override for a workspace.
        """
        stmt = select(ConnectorPermission).where(
            ConnectorPermission.workspace_id == workspace_id,
            ConnectorPermission.connector_name == connector_name,
            ConnectorPermission.operation == operation,
        )
        result = await session.execute(stmt)
        perm = result.scalar_one_or_none()

        if perm:
            perm.enabled = enabled
            perm.permission_level = permission_level
            perm.updated_at = datetime.now(timezone.utc)
        else:
            perm = ConnectorPermission(
                workspace_id=workspace_id,
                connector_name=connector_name,
                operation=operation,
                permission_level=permission_level,
                enabled=enabled,
            )
            session.add(perm)

        await session.flush()
        await session.refresh(perm)
        logger.info(
            f"[ConnectorPermissionService] Workspace '{workspace_id}' updated '{connector_name}.{operation}' -> enabled={enabled}"
        )
        return perm


_default_permission_service: Optional[ConnectorPermissionService] = None


def get_connector_permission_service() -> ConnectorPermissionService:
    global _default_permission_service
    if _default_permission_service is None:
        _default_permission_service = ConnectorPermissionService()
    return _default_permission_service
