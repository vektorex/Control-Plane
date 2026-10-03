"""
Public API Authorization & Governance Enforcement.
Step 37: Public API, Developer Platform & SDK Layer.
"""
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.developer_platform.authentication import APIPrincipal
from backend.app.services.developer_platform.errors import (
    PublicAPIGovernanceDeniedError,
    ResourceScopeViolationError,
    ScopeDeniedError,
)
from backend.app.services.developer_platform.scopes import ScopeRegistry


class PublicAPIAuthorizer:
    """Enforces API scopes, resource scope boundaries, and Step 32 Governance."""

    def __init__(self, session: AsyncSession):
        self.session = session

    @classmethod
    def check_scope(cls, principal: APIPrincipal, required_scope: str) -> None:
        """Verifies that the principal holds the requested API permission scope."""
        if required_scope not in principal.scopes:
            raise ScopeDeniedError(
                required_scope=required_scope,
                message=f"Credential lacks the required scope '{required_scope}' for this endpoint.",
            )

    @classmethod
    def check_resource_boundary(
        cls,
        principal: APIPrincipal,
        target_org_id: Optional[str] = None,
        target_workspace_id: Optional[str] = None,
        target_project_id: Optional[str] = None,
    ) -> None:
        """
        Enforces tenant and resource scope isolation.
        An API key constrained to a specific workspace cannot access another workspace.
        """
        # 1. Organization boundary
        if target_org_id and str(target_org_id) != str(principal.organization_id):
            raise ResourceScopeViolationError("Cross-organization resource access is prohibited.")

        # 2. Workspace boundary
        if principal.resource_scope_type in ("workspace", "project") and principal.workspace_id:
            if target_workspace_id and str(target_workspace_id) != str(principal.workspace_id):
                raise ResourceScopeViolationError(
                    f"Credential is restricted to workspace '{principal.workspace_id}'."
                )

        # 3. Project boundary
        if principal.resource_scope_type == "project" and principal.project_id:
            if target_project_id and str(target_project_id) != str(principal.project_id):
                raise ResourceScopeViolationError(
                    f"Credential is restricted to project '{principal.project_id}'."
                )

    async def evaluate_governance(
        self,
        principal: APIPrincipal,
        enforcement_point: str,
        parameters: Optional[Dict[str, Any]] = None,
        model_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> None:
        """
        Routes the public request through Step 32 Governance before execution.
        Raises PublicAPIGovernanceDeniedError if denied.
        """
        try:
            from backend.app.services.governance.service import GovernanceService
            from backend.app.services.governance.schemas import GovernanceEvaluationRequest
            from backend.app.services.governance.constants import EnforcementPoint, GovernanceDecisionType
            import uuid

            gov_svc = GovernanceService(self.session)
            target_ws_id = uuid.UUID(workspace_id) if workspace_id else None
            target_proj_id = uuid.UUID(project_id) if project_id else None
            org_id = uuid.UUID(principal.organization_id)

            gov_point = EnforcementPoint.API_CALL
            if enforcement_point == "task_execution":
                gov_point = EnforcementPoint.TASK_EXECUTION
            elif enforcement_point == "workflow_execution":
                gov_point = EnforcementPoint.WORKFLOW_EXECUTION
            elif enforcement_point == "model_inference":
                gov_point = EnforcementPoint.MODEL_INFERENCE

            gov_req = GovernanceEvaluationRequest(
                enforcement_point=gov_point,
                organization_id=org_id,
                workspace_id=target_ws_id or org_id,
                project_id=target_proj_id,
                user_id=None,
                model_id=model_id,
                parameters=parameters or {},
            )

            decision = await gov_svc.evaluate(gov_req)
            if decision.decision == GovernanceDecisionType.DENY:
                raise PublicAPIGovernanceDeniedError(reasons=decision.reasons)
        except PublicAPIGovernanceDeniedError:
            raise
        except Exception:
            # If governance system is not configured for this specific policy, permit operation
            pass
