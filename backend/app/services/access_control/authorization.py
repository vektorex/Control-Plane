"""
Centralized Server-Side Authorization Service for Step 27:
Multi-Tenant Organizations, Teams, Roles & Access Control.
Every protected resource and API endpoint evaluates permissions here.
"""
from typing import Any, Optional, Set
from uuid import UUID
from fastapi import Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from backend.app.db.database import get_db
from backend.app.db.models.user import User

_bearer_scheme = HTTPBearer(auto_error=False)
from backend.app.services.access_control.constants import (
    OrganizationRole,
    WorkspaceRole,
    ProjectRole,
    ProjectAccessMode,
)
from backend.app.services.access_control.context import AuthorizationContext
from backend.app.services.access_control.errors import (
    PermissionDeniedError,
    TenantIsolationError,
)
from backend.app.services.access_control.policies import PolicyEngine
from backend.app.services.access_control.repository import AccessControlRepository


class AuthorizationService:
    """
    Core authorization engine performing strict server-side permission validation.
    Never trusts client role claims or frontend state.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = AccessControlRepository(session)

    async def resolve_context(
        self,
        user: User,
        organization_id: Optional[UUID] = None,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
    ) -> AuthorizationContext:
        """
        Derives the AuthorizationContext from database membership and roles.
        """
        (
            resolved_org_id,
            org_role,
            resolved_ws_id,
            ws_role,
            resolved_proj_id,
            proj_role,
            proj_access_mode,
        ) = await self.repository.resolve_authorization_chain(
            user_id=user.id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
        )

        if not resolved_org_id or not org_role:
            # User has no active membership in the target organization
            return AuthorizationContext(
                user_id=user.id,
                organization_id=organization_id or UUID("00000000-0000-0000-0000-000000000000"),
                organization_role="none",
                workspace_id=resolved_ws_id,
                workspace_role=ws_role,
                project_id=resolved_proj_id,
                project_access=proj_access_mode,
                project_role=proj_role,
                permissions=set(),
            )

        # Resolve effective intersected permissions
        effective_permissions = PolicyEngine.resolve_effective_permissions(
            organization_role=org_role,
            workspace_role=ws_role,
            project_role=proj_role,
            project_access_mode=proj_access_mode,
        )

        return AuthorizationContext(
            user_id=user.id,
            organization_id=resolved_org_id,
            organization_role=org_role,
            workspace_id=resolved_ws_id,
            workspace_role=ws_role,
            project_id=resolved_proj_id,
            project_access=proj_access_mode,
            project_role=proj_role,
            permissions=effective_permissions,
        )

    async def has_permission(
        self,
        user: User,
        permission: str,
        resource: Optional[Any] = None,
        context: Optional[AuthorizationContext] = None,
        organization_id: Optional[UUID] = None,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
    ) -> bool:
        """
        Checks whether the user possesses the required permission on the resource/context.
        """
        if context is None:
            context = await self.resolve_context(
                user=user,
                organization_id=organization_id,
                workspace_id=workspace_id,
                project_id=project_id,
            )

        if not context.organization_role or context.organization_role == "none":
            return False

        return PolicyEngine.can_access_resource(
            user_id=user.id,
            permission=permission,
            effective_permissions=context.permissions,
            resource=resource,
            organization_role=context.organization_role,
        )

    async def authorize(
        self,
        user: User,
        permission: str,
        resource: Optional[Any] = None,
        context: Optional[AuthorizationContext] = None,
        organization_id: Optional[UUID] = None,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
    ) -> AuthorizationContext:
        """
        Enforces authorization. Raises PermissionDeniedError if unauthorized.
        Returns the resolved AuthorizationContext on success.
        """
        if context is None:
            context = await self.resolve_context(
                user=user,
                organization_id=organization_id,
                workspace_id=workspace_id,
                project_id=project_id,
            )

        allowed = await self.has_permission(
            user=user,
            permission=permission,
            resource=resource,
            context=context,
        )
        if not allowed:
            raise PermissionDeniedError(
                f"Forbidden: You lack permission '{permission}' for this resource."
            )

        return context


# -----------------------------------------------------------------------------
# FastAPI Dependency Helpers
# -----------------------------------------------------------------------------

async def get_authorization_context(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    session: AsyncSession = Depends(get_db),
    x_org_id: Optional[str] = Header(None, alias="X-Organization-Id"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    org_id_query: Optional[UUID] = Query(None, alias="organization_id"),
    ws_id_query: Optional[UUID] = Query(None, alias="workspace_id"),
) -> AuthorizationContext:
    """
    FastAPI dependency that resolves the AuthorizationContext for the current request.
    Validates server-side against authenticated database records.
    """
    from backend.app.core.auth import get_current_user

    user = await get_current_user(credentials=credentials, session=session)

    parsed_org_id = org_id_query
    if not parsed_org_id and x_org_id:
        try:
            parsed_org_id = UUID(x_org_id)
        except ValueError:
            pass

    parsed_ws_id = ws_id_query
    if not parsed_ws_id and x_workspace_id:
        try:
            parsed_ws_id = UUID(x_workspace_id)
        except ValueError:
            pass

    service = AuthorizationService(session)
    return await service.resolve_context(
        user=user,
        organization_id=parsed_org_id,
        workspace_id=parsed_ws_id,
    )
