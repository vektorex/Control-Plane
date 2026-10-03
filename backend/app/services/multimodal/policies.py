"""
Security Policies and Multi-Tenant Access Control for Step 30: Multimodal AI.
Enforces tenant boundaries, role permissions, path traversal protections, and safe references.
"""
import os
import re
import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.db.models.user import User
from backend.app.db.models.project import Project
from backend.app.services.access_control.models import ProjectMember, WorkspaceMember
from backend.app.services.access_control.constants import ProjectAccessMode
from backend.app.services.access_control.policies import PolicyEngine
from backend.app.services.multimodal.errors import (
    ArtifactAccessDeniedError,
    MultimodalError,
)
from backend.app.services.multimodal.models import Artifact


class ArtifactPolicyEngine:
    """
    Authorization and path-security engine for Multimodal Artifacts.
    """

    @classmethod
    def verify_tenant_boundary(cls, user: User, organization_id: uuid.UUID) -> None:
        """
        Enforces organization tenant boundaries.
        A user from Organization A cannot access or mutate artifacts of Organization B.
        """
        if getattr(user, "is_superuser", False):
            return

        user_org_id = getattr(user, "organization_id", None)
        if user_org_id and user_org_id != organization_id:
            logger.warning(
                f"[ArtifactPolicyEngine] Tenant boundary violation: User org '{user_org_id}' "
                f"attempted access to target org '{organization_id}'."
            )
            raise ArtifactAccessDeniedError("Cross-tenant artifact access is strictly forbidden.")

    @classmethod
    async def authorize_artifact_access(
        cls,
        session: AsyncSession,
        user: User,
        artifact: Artifact,
        permission: str,
    ) -> None:
        """
        Verifies organization boundary and checks workspace/project RBAC permission.
        """
        if getattr(user, "is_superuser", False):
            return

        # 1. Organization boundary
        cls.verify_tenant_boundary(user, artifact.organization_id)

        # 2. Resolve workspace role
        ws_member_query = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == artifact.workspace_id,
            WorkspaceMember.user_id == user.id,
            WorkspaceMember.status == "active",
        )
        ws_res = await session.execute(ws_member_query)
        ws_member = ws_res.scalar_one_or_none()
        workspace_role = ws_member.role if ws_member else None
        org_role = getattr(user, "organization_role", "viewer")

        # 3. Resolve project role if project provided
        project_role = None
        project_access_mode = ProjectAccessMode.WORKSPACE.value
        if artifact.project_id:
            proj_member_query = select(ProjectMember).where(
                ProjectMember.project_id == artifact.project_id,
                ProjectMember.user_id == user.id,
            )
            proj_res = await session.execute(proj_member_query)
            proj_member = proj_res.scalar_one_or_none()
            project_role = proj_member.role if proj_member else None

            proj_obj = await session.get(Project, artifact.project_id)
            if proj_obj:
                project_access_mode = getattr(proj_obj, "access_mode", ProjectAccessMode.WORKSPACE.value)
                if project_access_mode == ProjectAccessMode.RESTRICTED.value:
                    if not proj_member and workspace_role != "admin" and org_role not in ("owner", "admin"):
                        raise ArtifactAccessDeniedError(
                            f"Access to restricted project {artifact.project_id} artifact resources denied."
                        )

        # 4. Resolve effective permissions
        effective_perms = PolicyEngine.resolve_effective_permissions(
            organization_role=org_role,
            workspace_role=workspace_role,
            project_role=project_role,
            project_access_mode=project_access_mode,
        )

        if permission not in effective_perms:
            logger.warning(
                f"[ArtifactPolicyEngine] RBAC authorization failed for user '{user.id}', "
                f"permission '{permission}', artifact '{artifact.id}'"
            )
            raise ArtifactAccessDeniedError(f"Insufficient permissions for artifact operation: lacks '{permission}'")

    @classmethod
    def validate_storage_reference(cls, storage_reference: str) -> None:
        """
        Protects against path traversal, directory breakouts, and malicious URL references.
        """
        if not storage_reference or not isinstance(storage_reference, str):
            raise MultimodalError("Invalid empty storage reference.")

        # Guard against directory traversal
        if ".." in storage_reference or storage_reference.startswith("/") or "\\" in storage_reference:
            raise MultimodalError("Path traversal or absolute filesystem references are forbidden.")

        # Guard against remote URL injection as local storage references
        if re.match(r"^(https?|ftp|file)://", storage_reference, re.IGNORECASE):
            raise MultimodalError("Arbitrary remote URLs cannot be used as local storage references.")

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitizes client-supplied filename, stripping path components and hazardous characters.
        """
        if not filename:
            return "unnamed_artifact"
        # Take basename only
        base = os.path.basename(filename).strip()
        # Remove null bytes, slashes, backslashes, control characters
        cleaned = re.sub(r"[\x00-\x1f/\\:\*\?\"<>\|]", "", base)
        # Avoid hidden dotfiles or empty
        cleaned = cleaned.lstrip(".")
        return cleaned[:255] if cleaned else "artifact"
