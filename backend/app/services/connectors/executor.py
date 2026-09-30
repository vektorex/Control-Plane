from __future__ import annotations
import time
import uuid
from typing import Any, Dict, Optional, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession




if TYPE_CHECKING:
    from backend.app.services.observability.tracer import ExecutionTracer

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.db.database import async_session_factory
from backend.app.db.models.user import User

from backend.app.services.connectors.credentials import CredentialStore, get_credential_store
from backend.app.services.connectors.errors import (
    ConnectorAuthError,
    ConnectorError,
    ConnectorNotFoundError,
    ConnectorOperationNotFoundError,
    ConnectorPermissionError,
    ConnectorTimeoutError,
    ConnectorValidationError,
)
from backend.app.services.connectors.permissions import ConnectorPermissionService, get_connector_permission_service
from backend.app.services.connectors.registry import ConnectorRegistry, get_connector_registry
from backend.app.services.connectors.sanitization import sanitize_connector_result
from backend.app.services.connectors.schemas import ConnectorResult
from backend.app.services.observability.events import TraceEventStatus, TraceEventType



class ConnectorExecutor:
    """
    Executes connector operations safely within workspace security boundaries.
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

    async def execute(
        self,
        connector_name: str,
        operation: str,
        arguments: Dict[str, Any],
        workspace_id: uuid.UUID,
        user: Optional[User] = None,
        session: Optional[AsyncSession] = None,
        tracer: Optional[ExecutionTracer] = None,
        **kwargs: Any,
    ) -> ConnectorResult:
        """
        Executes a connector operation with full authorization, sanitization, and telemetry.
        """
        start_time = time.perf_counter()

        if tracer:
            tracer.record_event(
                TraceEventType.CONNECTOR_STARTED if hasattr(TraceEventType, "CONNECTOR_STARTED") else TraceEventType.TOOL_STARTED,
                step_type="connector",
                status=TraceEventStatus.STARTED,
                metadata={
                    "connector": connector_name,
                    "operation": operation,
                    "workspace_id": str(workspace_id),
                },
            )

        try:
            # 1. Resolve Connector
            connector = self.registry.get(connector_name)
            if not connector:
                raise ConnectorNotFoundError(connector_name)

            op_meta = connector.get_operation(operation)
            if not op_meta:
                raise ConnectorOperationNotFoundError(connector_name, operation)

            # 2. Permission Check (Workspace Scoped)
            # Use session if provided, or open a context session
            if session is not None:
                has_perm = await self.permission_service.check_permission(
                    session=session,
                    workspace_id=workspace_id,
                    connector_name=connector_name,
                    operation=operation,
                    permission_level=op_meta.permission_level.value,
                )
                if not has_perm:
                    raise ConnectorPermissionError(
                        f"Workspace '{workspace_id}' is not authorized to execute '{connector_name}.{operation}'."
                    )

                # 2b. HITL Approval Check (Step 18)
                from backend.app.services.hitl.policies import ApprovalPolicyEngine
                op_capability = op_meta.permission_level.value if hasattr(op_meta, "permission_level") else "read"
                if any(k in operation.lower() for k in ApprovalPolicyEngine.DESTRUCTIVE_KEYWORDS):
                    op_capability = "destructive"
                elif any(k in operation.lower() for k in ApprovalPolicyEngine.WRITE_KEYWORDS):
                    if op_capability == "read":
                        op_capability = "write"

                risk = ApprovalPolicyEngine.classify_risk(
                    target_type="connector",
                    operation=f"{connector_name}.{operation}",
                    capability=op_capability,
                    arguments=arguments,
                )

                if risk.is_destructive and not kwargs.get("approval_granted", False):
                    raise ConnectorPermissionError(
                        f"Operation '{connector_name}.{operation}' is DESTRUCTIVE and strictly requires human approval."
                    )

                # 3. Retrieve Decrypted Credential Secret
                cred = await self.credential_store.get(
                    session=session,
                    workspace_id=workspace_id,
                    connector_name=connector_name,
                    user_id=user.id if user else None,
                )
            else:
                async with async_session_factory() as ctx_session:
                    has_perm = await self.permission_service.check_permission(

                        session=ctx_session,
                        workspace_id=workspace_id,
                        connector_name=connector_name,
                        operation=operation,
                        permission_level=op_meta.permission_level.value,
                    )
                    if not has_perm:
                        raise ConnectorPermissionError(
                            f"Workspace '{workspace_id}' is not authorized to execute '{connector_name}.{operation}'."
                        )

                    # 2b. HITL Approval Check (Step 18)
                    from backend.app.services.hitl.policies import ApprovalPolicyEngine
                    op_capability = op_meta.permission_level.value if hasattr(op_meta, "permission_level") else "read"
                    if any(k in operation.lower() for k in ApprovalPolicyEngine.DESTRUCTIVE_KEYWORDS):
                        op_capability = "destructive"
                    elif any(k in operation.lower() for k in ApprovalPolicyEngine.WRITE_KEYWORDS):
                        if op_capability == "read":
                            op_capability = "write"

                    risk = ApprovalPolicyEngine.classify_risk(
                        target_type="connector",
                        operation=f"{connector_name}.{operation}",
                        capability=op_capability,
                        arguments=arguments,
                    )

                    if risk.is_destructive and not kwargs.get("approval_granted", False):
                        raise ConnectorPermissionError(
                            f"Operation '{connector_name}.{operation}' is DESTRUCTIVE and strictly requires human approval."
                        )

                    cred = await self.credential_store.get(
                        session=ctx_session,
                        workspace_id=workspace_id,
                        connector_name=connector_name,
                        user_id=user.id if user else None,
                    )

            if not cred or not cred.secret:
                raise ConnectorAuthError(
                    f"No active credentials found for connector '{connector_name}' in workspace '{workspace_id}'."
                )

            # 4. Execute Connector Operation with Credentials
            raw_result = await connector.execute_operation(
                operation=operation,
                arguments=arguments or {},
                credentials=cred.secret,
                metadata=cred.metadata,
            )

            # 5. Sanitize Result (Scrub secrets, enforce max response bytes, mark untrusted)
            max_bytes = getattr(settings, "MAX_CONNECTOR_RESPONSE_BYTES", 1000000)
            sanitized_data = sanitize_connector_result(raw_result.data, max_bytes=max_bytes)
            sanitized_items = sanitize_connector_result(raw_result.items, max_bytes=max_bytes) or []
            
            # Enforce max results per call limit
            max_results = getattr(settings, "MAX_CONNECTOR_RESULTS_PER_CALL", 100)
            if isinstance(sanitized_items, list) and len(sanitized_items) > max_results:
                sanitized_items = sanitized_items[:max_results]

            # Attach untrusted trust level to all items
            for item in sanitized_items:
                if isinstance(item, dict):
                    item["trust_level"] = "external_untrusted"
                    item["connector"] = connector_name
                    item["operation"] = operation

            duration_ms = int((time.perf_counter() - start_time) * 1000)

            final_result = ConnectorResult(
                success=True,
                connector=connector_name,
                operation=operation,
                data=sanitized_data,
                items=sanitized_items,
                metadata={
                    **(raw_result.metadata or {}),
                    "duration_ms": duration_ms,
                    "result_count": len(sanitized_items),
                    "trust_level": "external_untrusted",
                },
                source=raw_result.source,
            )

            if tracer:
                tracer.record_event(
                    TraceEventType.CONNECTOR_COMPLETED if hasattr(TraceEventType, "CONNECTOR_COMPLETED") else TraceEventType.TOOL_COMPLETED,
                    step_type="connector",
                    status=TraceEventStatus.COMPLETED,
                    duration_ms=duration_ms,
                    metadata={
                        "connector": connector_name,
                        "operation": operation,
                        "result_count": len(sanitized_items),
                    },
                )

            logger.info(
                f"[ConnectorExecutor] Executed '{connector_name}.{operation}' successfully in {duration_ms}ms"
            )
            return final_result

        except ConnectorError as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.warning(f"[ConnectorExecutor] Connector error in '{connector_name}.{operation}': {e.message}")
            if tracer:
                tracer.record_event(
                    TraceEventType.CONNECTOR_FAILED if hasattr(TraceEventType, "CONNECTOR_FAILED") else TraceEventType.TOOL_COMPLETED,
                    step_type="connector",
                    status=TraceEventStatus.FAILED,
                    duration_ms=duration_ms,
                    error_code=e.code,
                    metadata={"connector": connector_name, "operation": operation, "error": e.message},
                )
            return ConnectorResult(
                success=False,
                connector=connector_name,
                operation=operation,
                data=None,
                items=[],
                metadata={"duration_ms": duration_ms},
                error_code=e.code,
                error_message=e.message,
            )

        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"[ConnectorExecutor] Unexpected error in '{connector_name}.{operation}': {str(e)}", exc_info=True)
            if tracer:
                tracer.record_event(
                    TraceEventType.CONNECTOR_FAILED if hasattr(TraceEventType, "CONNECTOR_FAILED") else TraceEventType.TOOL_COMPLETED,
                    step_type="connector",
                    status=TraceEventStatus.FAILED,
                    duration_ms=duration_ms,
                    error_code="CONNECTOR_EXECUTION_ERROR",
                    metadata={"connector": connector_name, "operation": operation, "error": str(e)},
                )
            return ConnectorResult(
                success=False,
                connector=connector_name,
                operation=operation,
                data=None,
                items=[],
                metadata={"duration_ms": duration_ms},
                error_code="CONNECTOR_EXECUTION_ERROR",
                error_message=f"Execution failed: {str(e)}",
            )


_default_connector_executor: Optional[ConnectorExecutor] = None


def get_connector_executor() -> ConnectorExecutor:
    global _default_connector_executor
    if _default_connector_executor is None:
        _default_connector_executor = ConnectorExecutor()
    return _default_connector_executor
