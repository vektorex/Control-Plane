"""
High-level management service for Connectors, credentials, and permissions.
"""
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.connectors.credentials import CredentialStore, get_credential_store
from backend.app.services.connectors.errors import ConnectorAuthError, ConnectorNotFoundError
from backend.app.services.connectors.permissions import ConnectorPermissionService, get_connector_permission_service
from backend.app.services.connectors.registry import ConnectorRegistry, get_connector_registry
from backend.app.services.connectors.schemas import (
    ConnectionStatus,
    ConnectorMetadataResponse,
    ConnectorOperationMetadata,
    ConnectorPermissionResponse,
    ConnectorStatusResponse,
    ConnectorTestResponse,
)


class ConnectorService:
    """
    Coordinates connector discovery, connection lifecycle, and workspace permissions.
    """

    def __init__(
        self,
        registry: Optional[ConnectorRegistry] = None,
        credential_store: Optional[CredentialStore] = None,
        permission_service: Optional[ConnectorPermissionService] = None,
    ) -> None:
        self.registry = registry or get_connector_registry()
        self.credential_store = credential_store or get_credential_store()
        self.permission_service = permission_service or get_connector_permission_service()

    async def list_connectors(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
    ) -> List[ConnectorMetadataResponse]:
        """
        Returns all registered connectors decorated with the current workspace's connection status.
        Never returns secrets.
        """
        connectors = self.registry.list()
        results: List[ConnectorMetadataResponse] = []

        for conn in connectors:
            meta = conn.get_metadata()
            status_resp = await self.get_status(session, workspace_id, conn.name)
            meta.status = status_resp.status
            meta.account = status_resp.account
            results.append(meta)

        return results

    async def get_connector(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        connector_name: str,
    ) -> ConnectorMetadataResponse:
        """
        Returns metadata for a specific connector with workspace status.
        """
        conn = self.registry.get_or_raise(connector_name)
        meta = conn.get_metadata()
        status_resp = await self.get_status(session, workspace_id, connector_name)
        meta.status = status_resp.status
        meta.account = status_resp.account
        return meta

    async def get_operations(
        self,
        connector_name: str,
    ) -> List[ConnectorOperationMetadata]:
        """
        Returns supported operations and parameter schemas for a connector.
        """
        conn = self.registry.get_or_raise(connector_name)
        return list(conn.supported_operations)

    async def get_status(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        connector_name: str,
    ) -> ConnectorStatusResponse:
        """
        Determines connection state (connected, disconnected, expired, invalid)
        and returns safe account info if connected.
        """
        conn = self.registry.get(connector_name)
        if not conn:
            return ConnectorStatusResponse(
                connector=connector_name,
                status=ConnectionStatus.UNAVAILABLE.value,
                has_credentials=False,
                message="Connector is not registered on this system.",
            )

        safe_record = await self.credential_store.get_safe_record(
            session=session,
            workspace_id=workspace_id,
            connector_name=connector_name,
        )

        if not safe_record:
            return ConnectorStatusResponse(
                connector=connector_name,
                status=ConnectionStatus.DISCONNECTED.value,
                has_credentials=False,
            )

        # Extract account info from safe metadata if available
        account_data = safe_record.metadata.get("account") if safe_record.metadata else None

        return ConnectorStatusResponse(
            connector=connector_name,
            status=ConnectionStatus.CONNECTED.value,
            has_credentials=True,
            account=account_data,
            last_verified_at=safe_record.updated_at,
        )

    async def connect(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        connector_name: str,
        credential: str,
        credential_type: str = "pat",
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> ConnectorStatusResponse:
        """
        Tests the credential, saves the encrypted secret, and returns the verified connection status.
        """
        conn = self.registry.get_or_raise(connector_name)

        # 1. Verify credentials against provider
        try:
            account_info = await conn.test_connection(credential, metadata)
        except Exception as e:
            logger.warning(f"[ConnectorService] Connection test failed for '{connector_name}': {e}")
            raise ConnectorAuthError(f"Connection test failed: {str(e)}")

        # 2. Prepare safe metadata including verified account info
        stored_meta = dict(metadata or {})
        stored_meta["account"] = account_info

        # 3. Persist encrypted in CredentialStore
        record = await self.credential_store.save(
            session=session,
            workspace_id=workspace_id,
            connector_name=connector_name,
            credential_type=credential_type,
            secret=credential,
            metadata=stored_meta,
            user_id=user_id,
        )

        return ConnectorStatusResponse(
            connector=connector_name,
            status=ConnectionStatus.CONNECTED.value,
            has_credentials=True,
            account=account_info,
            last_verified_at=record.updated_at,
            message="Connected and verified successfully.",
        )

    async def disconnect(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        connector_name: str,
        user_id: Optional[uuid.UUID] = None,
    ) -> bool:
        """
        Deletes stored credentials for the connector in the workspace.
        """
        self.registry.get_or_raise(connector_name)
        return await self.credential_store.delete(
            session=session,
            workspace_id=workspace_id,
            connector_name=connector_name,
            user_id=user_id,
        )

    async def test_connection(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        connector_name: str,
        user_id: Optional[uuid.UUID] = None,
    ) -> ConnectorTestResponse:
        """
        Tests stored credentials by verifying connectivity and account information.
        """
        conn = self.registry.get_or_raise(connector_name)
        cred = await self.credential_store.get(
            session=session,
            workspace_id=workspace_id,
            connector_name=connector_name,
            user_id=user_id,
        )

        if not cred or not cred.secret:
            return ConnectorTestResponse(
                success=False,
                connector=connector_name,
                status=ConnectionStatus.DISCONNECTED.value,
                message="No credentials configured for this connector.",
            )

        try:
            account_info = await conn.test_connection(cred.secret, cred.metadata)
            return ConnectorTestResponse(
                success=True,
                connector=connector_name,
                status=ConnectionStatus.CONNECTED.value,
                account=account_info,
                message="Connection test successful.",
            )
        except Exception as e:
            return ConnectorTestResponse(
                success=False,
                connector=connector_name,
                status=ConnectionStatus.INVALID.value,
                message=f"Connection test failed: {str(e)}",
            )

    async def list_permissions(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        connector_name: str,
    ) -> List[ConnectorPermissionResponse]:
        """
        Lists all operations and their current permission configuration for the workspace.
        """
        conn = self.registry.get_or_raise(connector_name)
        db_perms = await self.permission_service.list_permissions(
            session=session,
            workspace_id=workspace_id,
            connector_name=connector_name,
        )
        db_perm_map = {p.operation: p for p in db_perms}

        responses: List[ConnectorPermissionResponse] = []
        for op in conn.supported_operations:
            if op.name in db_perm_map:
                p = db_perm_map[op.name]
                responses.append(
                    ConnectorPermissionResponse(
                        id=p.id,
                        workspace_id=workspace_id,
                        connector_name=connector_name,
                        operation=op.name,
                        permission_level=p.permission_level,
                        enabled=p.enabled,
                        created_at=p.created_at,
                        updated_at=p.updated_at,
                    )
                )
            else:
                # Default permission
                responses.append(
                    ConnectorPermissionResponse(
                        id=None,
                        workspace_id=workspace_id,
                        connector_name=connector_name,
                        operation=op.name,
                        permission_level=op.permission_level.value,
                        enabled=True,
                    )
                )

        return responses

    async def update_permission(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        connector_name: str,
        operation: str,
        enabled: bool,
        permission_level: str = "read",
    ) -> ConnectorPermissionResponse:
        """
        Updates an operation permission setting.
        """
        conn = self.registry.get_or_raise(connector_name)
        if not conn.has_operation(operation) and operation != "*":
            raise ConnectorNotFoundError(f"Operation '{operation}' not recognized on connector '{connector_name}'.")

        p = await self.permission_service.update_permission(
            session=session,
            workspace_id=workspace_id,
            connector_name=connector_name,
            operation=operation,
            enabled=enabled,
            permission_level=permission_level,
        )

        return ConnectorPermissionResponse(
            id=p.id,
            workspace_id=p.workspace_id,
            connector_name=p.connector_name,
            operation=p.operation,
            permission_level=p.permission_level,
            enabled=p.enabled,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )


_default_connector_service: Optional[ConnectorService] = None


def get_connector_service() -> ConnectorService:
    global _default_connector_service
    if _default_connector_service is None:
        _default_connector_service = ConnectorService()
    return _default_connector_service
