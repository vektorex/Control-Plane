"""
Security and tenant isolation policy engine for Knowledge Graph.
Enforces Organization, Workspace, and Project boundaries on graph queries and mutations.
"""
import uuid
from typing import List, Optional, Set
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.project import Project
from backend.app.db.models.user import User
from backend.app.services.access_control.constants import ProjectAccessMode
from backend.app.services.access_control.models import ProjectMember, WorkspaceMember
from backend.app.services.access_control.permissions import (
    GRAPH_CREATE,
    GRAPH_DELETE,
    GRAPH_EXTRACT,
    GRAPH_MERGE,
    GRAPH_READ,
    GRAPH_UPDATE,
)
from backend.app.services.access_control.policies import PolicyEngine
from backend.app.services.knowledge_graph.errors import (
    CrossTenantGraphError,
    UnauthorizedGraphAccessError,
)
from backend.app.services.knowledge_graph.models import Entity, Relationship


class GraphPolicyEngine:
    """
    Evaluates tenant boundaries and RBAC permissions for all Knowledge Graph interactions.
    """

    @classmethod
    async def authorize_graph_operation(
        cls,
        session: AsyncSession,
        user: User,
        permission: str,
        workspace_id: uuid.UUID,
        project_id: Optional[uuid.UUID] = None,
    ) -> None:
        """
        Validates that the user has the required graph permission within the workspace/project scope.
        """
        # Superuser bypass
        if getattr(user, "is_superuser", False):
            return

        # 1. Resolve workspace role
        ws_member_query = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
            WorkspaceMember.status == "active",
        )
        ws_res = await session.execute(ws_member_query)
        ws_member = ws_res.scalar_one_or_none()

        workspace_role = ws_member.role if ws_member else None
        org_role = getattr(user, "organization_role", "viewer")

        # 2. Resolve project role if project provided
        project_role = None
        if project_id:
            proj_member_query = select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user.id,
            )
            proj_res = await session.execute(proj_member_query)
            proj_member = proj_res.scalar_one_or_none()
            project_role = proj_member.role if proj_member else None

            # Check if project is restricted
            proj_obj = await session.get(Project, project_id)
            if proj_obj and getattr(proj_obj, "access_mode", None) == ProjectAccessMode.RESTRICTED.value:
                if not proj_member and workspace_role != "admin" and org_role not in ("owner", "admin"):
                    raise UnauthorizedGraphAccessError(
                        f"Access to restricted project {project_id} graph resources denied."
                    )

        # 3. Resolve effective permissions
        effective_perms = PolicyEngine.resolve_effective_permissions(
            organization_role=org_role,
            workspace_role=workspace_role,
            project_role=project_role,
        )

        if permission not in effective_perms:
            raise UnauthorizedGraphAccessError(
                f"User lacks required graph permission '{permission}' for workspace {workspace_id}."
            )

    @classmethod
    def verify_tenant_boundary(
        cls,
        user: User,
        organization_id: uuid.UUID,
    ) -> None:
        """
        Asserts that the graph asset belongs to the user's active organization.
        """
        if getattr(user, "is_superuser", False):
            return

        user_org_id = getattr(user, "organization_id", None)
        if user_org_id and user_org_id != organization_id:
            raise CrossTenantGraphError("Graph operation attempted across organization boundary.")

    @classmethod
    async def get_authorized_project_ids(
        cls,
        session: AsyncSession,
        user: User,
        workspace_id: uuid.UUID,
    ) -> Optional[Set[uuid.UUID]]:
        """
        Returns the set of project IDs the user can view within the workspace.
        If user is admin, returns None (all projects accessible).
        """
        if getattr(user, "is_superuser", False):
            return None

        # Check admin roles
        org_role = getattr(user, "organization_role", "viewer")
        if org_role in ("owner", "admin"):
            return None

        ws_member_query = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
            WorkspaceMember.status == "active",
        )
        ws_res = await session.execute(ws_member_query)
        ws_member = ws_res.scalar_one_or_none()
        if ws_member and ws_member.role == "admin":
            return None

        # Fetch non-restricted projects + projects where user is member
        query = select(Project.id).where(
            Project.workspace_id == workspace_id,
            (Project.access_mode != ProjectAccessMode.RESTRICTED.value) |
            (Project.id.in_(
                select(ProjectMember.project_id).where(ProjectMember.user_id == user.id)
            ))
        )
        res = await session.execute(query)
        return set(res.scalars().all())
