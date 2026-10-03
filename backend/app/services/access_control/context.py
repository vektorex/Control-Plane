"""
AuthorizationContext for Step 27: Multi-Tenant Organizations, Teams, Roles & Access Control.
Encapsulates server-side resolved authorization state for the current request.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set
from uuid import UUID
from backend.app.services.access_control.constants import OrganizationRole


@dataclass
class AuthorizationContext:
    """
    Resolved server-side authorization context for an authenticated user.
    Never accepts role or permission information from client request bodies.
    """
    user_id: UUID
    organization_id: UUID
    organization_role: str
    workspace_id: Optional[UUID] = None
    workspace_role: Optional[str] = None
    project_id: Optional[UUID] = None
    project_access: Optional[str] = None  # e.g., 'workspace' or 'restricted'
    project_role: Optional[str] = None    # e.g., 'editor' or 'viewer'
    permissions: Set[str] = field(default_factory=set)

    @property
    def is_owner(self) -> bool:
        return self.organization_role == OrganizationRole.OWNER.value

    @property
    def is_admin(self) -> bool:
        return self.organization_role in {OrganizationRole.OWNER.value, OrganizationRole.ADMIN.value}

    @property
    def is_viewer(self) -> bool:
        return self.organization_role == OrganizationRole.VIEWER.value

    def has_permission(self, permission: str) -> bool:
        """Checks if the context grants a specific permission."""
        return permission in self.permissions

    def has_any_permission(self, *permissions: str) -> bool:
        """Checks if the context grants at least one of the specified permissions."""
        return any(p in self.permissions for p in permissions)

    def has_all_permissions(self, *permissions: str) -> bool:
        """Checks if the context grants all of the specified permissions."""
        return all(p in self.permissions for p in permissions)

    def get_capabilities(self) -> Dict[str, bool]:
        """
        Generates standard UI hints for frontend rendering.
        Note: These are UI hints only; server-side authorization remains mandatory.
        """
        return {
            "can_read": self.has_permission("workspace.read"),
            "can_update": self.has_permission("workspace.update"),
            "can_delete": self.has_permission("workspace.delete"),
            "can_run": self.has_permission("workflow.run") or self.has_permission("task.run"),
            "can_manage_members": self.has_permission("member.update") or self.has_permission("member.invite"),
            "can_invite": self.has_permission("member.invite"),
            "can_create_project": self.has_permission("project.create"),
            "can_create_workflow": self.has_permission("workflow.create"),
            "can_configure_connector": self.has_permission("connector.configure"),
            "can_execute_connector": self.has_permission("connector.execute"),
            "is_owner": self.is_owner,
            "is_admin": self.is_admin,
            "is_viewer": self.is_viewer,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": str(self.user_id),
            "organization_id": str(self.organization_id),
            "organization_role": self.organization_role,
            "workspace_id": str(self.workspace_id) if self.workspace_id else None,
            "workspace_role": self.workspace_role,
            "project_id": str(self.project_id) if self.project_id else None,
            "project_access": self.project_access,
            "project_role": self.project_role,
            "permissions": sorted(list(self.permissions)),
            "capabilities": self.get_capabilities(),
        }
