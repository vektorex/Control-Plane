"""
GovernanceService: unified facade for all governance operations.
Entry point for policy CRUD, evaluation, simulation, budgets, and data classification. Step 32.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.governance.audit import GovernanceAuditService
from backend.app.services.governance.budgets import BudgetService
from backend.app.services.governance.constants import (
    GovernanceDecisionType,
    PolicyVersionStatus,
)
from backend.app.services.governance.data_policy import DataClassificationService
from backend.app.services.governance.errors import (
    GovernancePolicyMalformedError,
    GovernancePolicyNotFoundError,
)
from backend.app.services.governance.evaluator import PolicyEvaluator
from backend.app.services.governance.models import (
    BudgetPolicy,
    GovernancePolicy,
    GovernancePolicyVersion,
)
from backend.app.services.governance.policy_engine import GovernancePolicyEngine
from backend.app.services.governance.repository import GovernancePolicyRepository
from backend.app.services.governance.schemas import (
    BudgetPolicyCreate,
    BudgetPolicyResponse,
    DataClassificationRequest,
    DataClassificationResponse,
    GovernanceDecision,
    GovernanceEvaluationRequest,
    GovernancePolicyCreate,
    GovernancePolicyResponse,
    GovernancePolicyUpdate,
    GovernancePreviewRequest,
    GovernancePreviewResponse,
    GovernanceSimulateRequest,
    GovernanceSimulateResponse,
    GovernanceStatsResponse,
    PolicyVersionCreate,
    PolicyVersionResponse,
)


class GovernanceService:
    """
    Unified governance service facade.
    All governance operations route through this service.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = GovernancePolicyRepository(session)
        self.engine = GovernancePolicyEngine(self.repo)
        self.budget_service = BudgetService(self.repo)

    # ------------------------------------------------------------------
    # Policy CRUD
    # ------------------------------------------------------------------

    async def create_policy(
        self,
        organization_id: uuid.UUID,
        created_by: uuid.UUID,
        data: GovernancePolicyCreate,
    ) -> GovernancePolicyResponse:
        policy = await self.repo.create_policy(organization_id, created_by, data)
        await self.session.commit()
        await GovernanceAuditService.emit(
            "policy_created",
            organization_id=organization_id,
            workspace_id=data.workspace_id,
            actor_id=created_by,
            metadata={"policy_id": str(policy.id), "name": policy.name},
        )
        return GovernancePolicyResponse.model_validate(policy)

    async def get_policy(self, policy_id: uuid.UUID) -> GovernancePolicyResponse:
        policy = await self.repo.require_policy(policy_id)
        return GovernancePolicyResponse.model_validate(policy)

    async def list_policies(
        self,
        organization_id: uuid.UUID,
        workspace_id: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None,
        scope: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[GovernancePolicyResponse]:
        policies = await self.repo.list_policies(
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            scope=scope,
            status=status,
        )
        return [GovernancePolicyResponse.model_validate(p) for p in policies]

    async def update_policy(
        self,
        policy_id: uuid.UUID,
        actor_id: uuid.UUID,
        data: GovernancePolicyUpdate,
    ) -> GovernancePolicyResponse:
        policy = await self.repo.update_policy(policy_id, data)
        await self.session.commit()
        await GovernanceAuditService.emit(
            "policy_updated",
            organization_id=policy.organization_id,
            workspace_id=policy.workspace_id,
            actor_id=actor_id,
            metadata={"policy_id": str(policy_id)},
        )
        return GovernancePolicyResponse.model_validate(policy)

    async def delete_policy(
        self, policy_id: uuid.UUID, actor_id: uuid.UUID, organization_id: uuid.UUID
    ) -> None:
        await self.repo.delete_policy(policy_id)
        await self.session.commit()
        await GovernanceAuditService.emit(
            "policy_deactivated",
            organization_id=organization_id,
            workspace_id=None,
            actor_id=actor_id,
            metadata={"policy_id": str(policy_id)},
        )

    # ------------------------------------------------------------------
    # Policy Versions
    # ------------------------------------------------------------------

    async def create_version(
        self,
        policy_id: uuid.UUID,
        created_by: uuid.UUID,
        organization_id: uuid.UUID,
        data: PolicyVersionCreate,
    ) -> PolicyVersionResponse:
        # Validate rules before accepting
        errors = PolicyEvaluator.validate_rules(data.rules)
        if errors:
            raise GovernancePolicyMalformedError("; ".join(errors))

        version = await self.repo.create_version(policy_id, created_by, data)
        await self.session.commit()
        return PolicyVersionResponse.model_validate(version)

    async def list_versions(self, policy_id: uuid.UUID) -> List[PolicyVersionResponse]:
        versions = await self.repo.list_versions(policy_id)
        return [PolicyVersionResponse.model_validate(v) for v in versions]

    async def activate_version(
        self,
        policy_id: uuid.UUID,
        version_id: uuid.UUID,
        actor_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> PolicyVersionResponse:
        version = await self.repo.activate_version(policy_id, version_id)
        await self.session.commit()
        await GovernanceAuditService.emit(
            "policy_activated",
            organization_id=organization_id,
            workspace_id=None,
            actor_id=actor_id,
            metadata={
                "policy_id": str(policy_id),
                "version_id": str(version_id),
                "version_number": version.version_number,
            },
        )
        return PolicyVersionResponse.model_validate(version)

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    async def evaluate(
        self,
        request: GovernanceEvaluationRequest,
    ) -> GovernanceDecision:
        return await self.engine.evaluate_and_log(request, user_id=request.user_id)

    async def simulate(
        self, request: GovernanceSimulateRequest
    ) -> GovernanceSimulateResponse:
        """
        Dry-run simulation. Never executes the operation.
        """
        decision = await self.engine.evaluate(request.evaluation)
        await GovernanceAuditService.emit(
            "policy_simulated",
            organization_id=request.evaluation.organization_id,
            workspace_id=request.evaluation.workspace_id,
            actor_id=request.evaluation.user_id,
            metadata={"decision": decision.decision.value},
        )
        return GovernanceSimulateResponse(
            decision=decision.decision,
            matched_policies=decision.matched_policies,
            constraints=decision.constraints,
            required_approvals=decision.required_approvals,
            required_verifications=decision.required_verifications,
            reasons=decision.reasons,
        )

    async def preview(
        self, request: GovernancePreviewRequest
    ) -> GovernancePreviewResponse:
        """
        Test a hypothetical policy configuration. Never mutates production state.
        """
        errors = PolicyEvaluator.validate_rules(request.hypothetical_rules)
        if errors:
            raise GovernancePolicyMalformedError("; ".join(errors))

        decision_type, reasons, constraints, approvals, verifications = PolicyEvaluator.evaluate(
            rules=request.hypothetical_rules,
            request=request.evaluation,
        )

        matched_rules = [
            r.model_dump() for r in request.hypothetical_rules
        ]

        return GovernancePreviewResponse(
            decision=decision_type,
            matched_rules=matched_rules,
            constraints=constraints,
            reasons=reasons,
        )

    # ------------------------------------------------------------------
    # Budget
    # ------------------------------------------------------------------

    async def upsert_budget_policy(
        self,
        organization_id: uuid.UUID,
        created_by: uuid.UUID,
        data: BudgetPolicyCreate,
    ) -> BudgetPolicyResponse:
        budget = await self.budget_service.upsert_budget_policy(organization_id, created_by, data)
        await self.session.commit()
        return BudgetPolicyResponse.model_validate(budget)

    async def get_budget_policy(
        self,
        organization_id: uuid.UUID,
        workspace_id: Optional[uuid.UUID],
        project_id: Optional[uuid.UUID],
    ) -> Optional[BudgetPolicyResponse]:
        budget = await self.budget_service.get_budget_policy(
            organization_id, workspace_id, project_id
        )
        if not budget:
            return None
        return BudgetPolicyResponse.model_validate(budget)

    # ------------------------------------------------------------------
    # Data Classification
    # ------------------------------------------------------------------

    def classify(self, request: DataClassificationRequest) -> DataClassificationResponse:
        return DataClassificationService.assign(request)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    async def get_stats(
        self,
        organization_id: uuid.UUID,
        workspace_id: Optional[uuid.UUID],
    ) -> GovernanceStatsResponse:
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        since_24h = now - timedelta(hours=24)
        since_7d = now - timedelta(days=7)

        active_policies = await self.repo.list_policies(
            organization_id=organization_id,
            workspace_id=workspace_id,
            status="active",
        )

        blocked_24h = 0
        approval_24h = 0
        verification_24h = 0
        policy_changes_7d = 0

        if workspace_id:
            blocked_24h = await self.repo.count_decisions_since(
                workspace_id, GovernanceDecisionType.DENY.value, since_24h
            )
            approval_24h = await self.repo.count_decisions_since(
                workspace_id, GovernanceDecisionType.REQUIRE_APPROVAL.value, since_24h
            )
            verification_24h = await self.repo.count_decisions_since(
                workspace_id, GovernanceDecisionType.REQUIRE_VERIFICATION.value, since_24h
            )

        budget_policy = await self.budget_service.get_budget_policy(
            organization_id, workspace_id, None
        )

        recent_logs = []
        if workspace_id:
            logs = await self.repo.list_decision_logs(workspace_id, limit=5)
            recent_logs = [
                {
                    "enforcement_point": l.enforcement_point,
                    "decision": l.decision,
                    "reasons": l.reasons[:2],
                    "created_at": l.created_at.isoformat(),
                }
                for l in logs
            ]

        return GovernanceStatsResponse(
            active_policies=len(active_policies),
            blocked_operations_24h=blocked_24h,
            approval_required_24h=approval_24h,
            verification_required_24h=verification_24h,
            budget_usage_daily_usd=0.0,
            budget_limit_daily_usd=budget_policy.daily_limit_usd if budget_policy else None,
            policy_changes_7d=policy_changes_7d,
            recent_enforcement_events=recent_logs,
        )
