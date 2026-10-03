"""
Policy resolution engine for Step 27: Multi-Tenant Organizations, Teams, Roles & Access Control.
Computes effective permission intersections and enforces security boundaries.
"""
from typing import Any, Optional, Set, Union
from uuid import UUID

from backend.app.services.access_control.constants import (
    OrganizationRole,
    WorkspaceRole,
    ProjectRole,
    ProjectAccessMode,
)
from backend.app.services.access_control.roles import (
    ORGANIZATION_ROLE_PERMISSIONS,
    WORKSPACE_ROLE_PERMISSIONS,
    PROJECT_ROLE_PERMISSIONS,
)
from backend.app.services.access_control.permissions import (
    WORKSPACE_READ,
    WORKSPACE_UPDATE,
    WORKSPACE_DELETE,
    PROJECT_CREATE,
    PROJECT_READ,
    PROJECT_UPDATE,
    PROJECT_DELETE,
    TASK_READ,
    TASK_CREATE,
    TASK_UPDATE,
    TASK_DELETE,
    TASK_RUN,
    WORKFLOW_READ,
    WORKFLOW_CREATE,
    WORKFLOW_UPDATE,
    WORKFLOW_DELETE,
    WORKFLOW_PUBLISH,
    WORKFLOW_RUN,
    TRIGGER_READ,
    TRIGGER_CREATE,
    TRIGGER_UPDATE,
    TRIGGER_DELETE,
    TRIGGER_RUN,
    JOB_READ,
    JOB_CANCEL,
    JOB_RETRY,
    CONNECTOR_READ,
    CONNECTOR_CONFIGURE,
    CONNECTOR_EXECUTE,
    MEMORY_READ,
    MEMORY_CREATE,
    MEMORY_UPDATE,
    MEMORY_DELETE,
    EVALUATION_READ,
    EVALUATION_CREATE,
    EVALUATION_RUN,
    REPLAY_READ,
    REPLAY_CREATE,
    NOTIFICATION_READ,
    NOTIFICATION_CONFIGURE,
    WEBHOOK_READ,
    WEBHOOK_CONFIGURE,
    APPROVAL_READ,
    APPROVAL_RESPOND,
    ANALYTICS_READ,
    EVENT_READ,
    AUDIT_READ,
    PROMPT_READ,
    PROMPT_CREATE,
    PROMPT_UPDATE,
    PROMPT_PUBLISH,
    PROMPT_RELEASE,
    PROMPT_ROLLBACK,
    PROMPT_EXECUTE,
    PROMPT_EXPERIMENT,
    PROMPT_ARCHIVE,
    GRAPH_READ,
    GRAPH_CREATE,
    GRAPH_UPDATE,
    GRAPH_DELETE,
    GRAPH_EXTRACT,
    GRAPH_MERGE,
    ARTIFACT_READ,
    ARTIFACT_CREATE,
    ARTIFACT_UPDATE,
    ARTIFACT_DELETE,
    ARTIFACT_PROCESS,
    ARTIFACT_ANALYZE,
)

# Workspace-scoped permissions (subject to workspace role restrictions)
WORKSPACE_SCOPED_PERMISSIONS: Set[str] = {
    WORKSPACE_READ,
    WORKSPACE_UPDATE,
    WORKSPACE_DELETE,
    PROJECT_CREATE,
    PROJECT_READ,
    PROJECT_UPDATE,
    PROJECT_DELETE,
    TASK_READ,
    TASK_CREATE,
    TASK_UPDATE,
    TASK_DELETE,
    TASK_RUN,
    WORKFLOW_READ,
    WORKFLOW_CREATE,
    WORKFLOW_UPDATE,
    WORKFLOW_DELETE,
    WORKFLOW_PUBLISH,
    WORKFLOW_RUN,
    TRIGGER_READ,
    TRIGGER_CREATE,
    TRIGGER_UPDATE,
    TRIGGER_DELETE,
    TRIGGER_RUN,
    JOB_READ,
    JOB_CANCEL,
    JOB_RETRY,
    CONNECTOR_READ,
    CONNECTOR_CONFIGURE,
    CONNECTOR_EXECUTE,
    MEMORY_READ,
    MEMORY_CREATE,
    MEMORY_UPDATE,
    MEMORY_DELETE,
    EVALUATION_READ,
    EVALUATION_CREATE,
    EVALUATION_RUN,
    REPLAY_READ,
    REPLAY_CREATE,
    NOTIFICATION_READ,
    NOTIFICATION_CONFIGURE,
    WEBHOOK_READ,
    WEBHOOK_CONFIGURE,
    APPROVAL_READ,
    APPROVAL_RESPOND,
    ANALYTICS_READ,
    EVENT_READ,
    AUDIT_READ,
    PROMPT_READ,
    PROMPT_CREATE,
    PROMPT_UPDATE,
    PROMPT_PUBLISH,
    PROMPT_RELEASE,
    PROMPT_ROLLBACK,
    PROMPT_EXECUTE,
    PROMPT_EXPERIMENT,
    PROMPT_ARCHIVE,
    GRAPH_READ,
    GRAPH_CREATE,
    GRAPH_UPDATE,
    GRAPH_DELETE,
    GRAPH_EXTRACT,
    GRAPH_MERGE,
    ARTIFACT_READ,
    ARTIFACT_CREATE,
    ARTIFACT_UPDATE,
    ARTIFACT_DELETE,
    ARTIFACT_PROCESS,
    ARTIFACT_ANALYZE,
}

# Project-scoped permissions (subject to project restrictions if restricted)
PROJECT_SCOPED_PERMISSIONS: Set[str] = {
    PROJECT_READ,
    PROJECT_UPDATE,
    PROJECT_DELETE,
    TASK_READ,
    TASK_CREATE,
    TASK_UPDATE,
    TASK_DELETE,
    TASK_RUN,
    WORKFLOW_READ,
    WORKFLOW_CREATE,
    WORKFLOW_UPDATE,
    WORKFLOW_DELETE,
    WORKFLOW_PUBLISH,
    WORKFLOW_RUN,
    TRIGGER_READ,
    TRIGGER_CREATE,
    TRIGGER_UPDATE,
    TRIGGER_DELETE,
    TRIGGER_RUN,
    JOB_READ,
    JOB_CANCEL,
    JOB_RETRY,
    CONNECTOR_READ,
    CONNECTOR_EXECUTE,
    MEMORY_READ,
    MEMORY_CREATE,
    MEMORY_UPDATE,
    MEMORY_DELETE,
    EVALUATION_READ,
    EVALUATION_CREATE,
    EVALUATION_RUN,
    REPLAY_READ,
    REPLAY_CREATE,
    APPROVAL_READ,
    APPROVAL_RESPOND,
    PROMPT_READ,
    PROMPT_CREATE,
    PROMPT_UPDATE,
    PROMPT_PUBLISH,
    PROMPT_RELEASE,
    PROMPT_ROLLBACK,
    PROMPT_EXECUTE,
    PROMPT_EXPERIMENT,
    PROMPT_ARCHIVE,
    GRAPH_READ,
    GRAPH_CREATE,
    GRAPH_UPDATE,
    GRAPH_DELETE,
    GRAPH_EXTRACT,
    GRAPH_MERGE,
    ARTIFACT_READ,
    ARTIFACT_CREATE,
    ARTIFACT_UPDATE,
    ARTIFACT_DELETE,
    ARTIFACT_PROCESS,
    ARTIFACT_ANALYZE,
}


class PolicyEngine:
    """
    Centralized server-side authorization policy engine.
    Computes effective permissions through strict intersection:
    Organization Role ∩ Workspace Role ∩ Project Role.
    A lower-level role CANNOT elevate a higher-level restriction.
    """

    @classmethod
    def resolve_effective_permissions(
        cls,
        organization_role: str,
        workspace_role: Optional[str] = None,
        project_role: Optional[str] = None,
        project_access_mode: str = ProjectAccessMode.WORKSPACE.value,
    ) -> Set[str]:
        # 1. Base permissions from Organization Role
        base_perms = set(ORGANIZATION_ROLE_PERMISSIONS.get(organization_role, set()))

        # 2. Workspace role restriction (if in workspace context)
        if workspace_role:
            ws_allowed = WORKSPACE_ROLE_PERMISSIONS.get(workspace_role, set())
            # For any workspace-scoped permission, require both org permission AND workspace permission
            # Lower-level role cannot elevate higher-level role
            effective = set()
            for p in base_perms:
                if p in WORKSPACE_SCOPED_PERMISSIONS:
                    if p in ws_allowed:
                        effective.add(p)
                else:
                    # Non-workspace scoped (org level, member management, etc.)
                    effective.add(p)
            base_perms = effective

        # 3. Project role restriction (if project is in restricted mode)
        if project_access_mode == ProjectAccessMode.RESTRICTED.value:
            # Org OWNER or org ADMIN or workspace ADMIN bypass restricted project member lists
            is_admin = organization_role in {OrganizationRole.OWNER.value, OrganizationRole.ADMIN.value} or (
                workspace_role == WorkspaceRole.ADMIN.value
            )
            if not is_admin:
                if project_role:
                    proj_allowed = PROJECT_ROLE_PERMISSIONS.get(project_role, set())
                    effective = set()
                    for p in base_perms:
                        if p in PROJECT_SCOPED_PERMISSIONS:
                            if p in proj_allowed:
                                effective.add(p)
                        else:
                            effective.add(p)
                    base_perms = effective
                else:
                    # Not an explicit member of the restricted project: strip all project-scoped access
                    base_perms = {p for p in base_perms if p not in PROJECT_SCOPED_PERMISSIONS}

        return base_perms

    @classmethod
    def can_access_resource(
        cls,
        user_id: UUID,
        permission: str,
        effective_permissions: Set[str],
        resource: Optional[Any] = None,
        organization_role: Optional[str] = None,
    ) -> bool:
        """
        Evaluates whether a user with effective_permissions may perform the action on the resource.
        Takes into account resource ownership and safety policies.
        """
        # 1. Base permission check
        if permission not in effective_permissions:
            return False

        # 2. Viewers can NEVER execute, run, or write, regardless of ownership
        if organization_role == OrganizationRole.VIEWER.value:
            if any(action in permission for action in ["run", "create", "update", "delete", "execute", "cancel", "retry", "publish", "configure", "release", "rollback", "experiment", "archive"]):
                return False

        # 3. Resource ownership rules (where applicable)
        if resource:
            owner_id = getattr(resource, "owner_user_id", None) or getattr(resource, "created_by", None)
            # If deleting or modifying a resource, members can edit/delete their own resources
            # But non-admins cannot edit/delete other members' resources if restricted
            is_admin = organization_role in {OrganizationRole.OWNER.value, OrganizationRole.ADMIN.value}
            if owner_id and owner_id != user_id and not is_admin:
                # Disallow modifying another user's private resources unless member has admin permission
                if permission in {TASK_DELETE, WORKFLOW_DELETE, TRIGGER_DELETE, PROMPT_ARCHIVE}:
                    return False

        return True

    @classmethod
    def derive_context(
        cls,
        user_id: UUID,
        organization_id: Optional[UUID] = None,
        organization_role: Optional[Union[str, OrganizationRole]] = None,
        workspace_id: Optional[UUID] = None,
        workspace_role: Optional[Union[str, WorkspaceRole]] = None,
        project_id: Optional[UUID] = None,
        project_role: Optional[Union[str, ProjectRole]] = None,
        project_access_mode: str = ProjectAccessMode.WORKSPACE.value,
    ):
        from backend.app.services.access_control.context import AuthorizationContext

        org_role_val = organization_role.value if isinstance(organization_role, OrganizationRole) else organization_role
        ws_role_val = workspace_role.value if isinstance(workspace_role, WorkspaceRole) else workspace_role
        proj_role_val = project_role.value if isinstance(project_role, ProjectRole) else project_role

        perms = cls.resolve_effective_permissions(
            organization_role=org_role_val or OrganizationRole.VIEWER.value,
            workspace_role=ws_role_val,
            project_role=proj_role_val,
            project_access_mode=project_access_mode,
        )
        return AuthorizationContext(
            user_id=user_id,
            organization_id=organization_id,
            organization_role=org_role_val,
            workspace_id=workspace_id,
            workspace_role=ws_role_val,
            project_id=project_id,
            project_access=project_access_mode,
            project_role=proj_role_val,
            permissions=perms,
        )

