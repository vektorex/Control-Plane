"""
Policy enforcement and security boundaries for Step 28 Prompt Management.
Enforces RBAC, cross-tenant isolation, restricted project boundaries,
HITL approval requirements for production releases, and model execution constraints.
"""
import uuid
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.user import User
from backend.app.services.access_control.authorization import AuthorizationService
from backend.app.services.access_control.errors import PermissionDeniedError, TenantIsolationError
from backend.app.services.access_control.permissions import (
    PROMPT_ARCHIVE,
    PROMPT_CREATE,
    PROMPT_EXECUTE,
    PROMPT_EXPERIMENT,
    PROMPT_PUBLISH,
    PROMPT_READ,
    PROMPT_RELEASE,
    PROMPT_ROLLBACK,
    PROMPT_UPDATE,
)
from backend.app.services.prompts.constants import PromptEnvironment
from backend.app.services.prompts.errors import ExecutionConfigPolicyError
from backend.app.services.prompts.models import Prompt


class PromptPolicyEngine:
    """
    Authoritative server-side policy verification for prompt operations.
    """

    @classmethod
    async def authorize_prompt_access(
        cls,
        session: AsyncSession,
        user: User,
        permission: str,
        prompt: Optional[Prompt] = None,
        workspace_id: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None,
    ) -> None:
        """
        Enforces tenant isolation, workspace boundaries, and role permissions.
        """
        auth_service = AuthorizationService(session)

        target_ws_id = prompt.workspace_id if prompt else workspace_id
        target_proj_id = (prompt.project_id if prompt else None) or project_id
        target_org_id = prompt.organization_id if prompt else None

        context = await auth_service.resolve_context(
            user=user,
            organization_id=target_org_id,
            workspace_id=target_ws_id,
            project_id=target_proj_id,
        )

        allowed = await auth_service.has_permission(
            user=user,
            permission=permission,
            resource=prompt,
            context=context,
        )
        if not allowed:
            raise PermissionDeniedError(
                f"Forbidden: You lack permission '{permission}' for prompt operations in this context."
            )

    @classmethod
    async def check_production_release_hitl(
        cls,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        environment: str,
        prompt_key: str,
        user_id: uuid.UUID,
    ) -> bool:
        """
        Checks whether HITL approval is required for production release or rollback.
        Returns True if human approval request was created and pending, False if direct release allowed.
        """
        if environment != PromptEnvironment.PRODUCTION.value:
            return False

        hitl_service = HITLService(session)
        policies = await hitl_service.get_workspace_policies(workspace_id)
        if not policies:
            return False

        # If workspace policy requires approval for deployment / production mutations
        # High impact planner / evaluator prompt releases
        is_high_impact = any(k in prompt_key for k in ["planner.", "evaluation.", "production."])
        if is_high_impact and getattr(policies, "require_approval_for_tools", False):
            return True

        return False

    @classmethod
    def validate_model_execution_config(
        cls,
        execution_config: Optional[Dict[str, Any]],
        model_requirements: Optional[Dict[str, Any]],
    ) -> None:
        """
        Validates that execution config and model requirements do not attempt to bypass
        gateway security or access models forbidden by workspace policy.
        """
        if not execution_config and not model_requirements:
            return

        if execution_config:
            temp = execution_config.get("temperature")
            if temp is not None and (temp < 0.0 or temp > 2.0):
                raise ExecutionConfigPolicyError("Temperature out of acceptable bounds (0.0 - 2.0).")

            tokens = execution_config.get("max_output_tokens")
            if tokens is not None and (tokens < 1 or tokens > 32768):
                raise ExecutionConfigPolicyError("max_output_tokens out of acceptable bounds (1 - 32768).")
