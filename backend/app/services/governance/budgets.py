"""
BudgetService: cost governance — budget reservations, settlement, soft/hard thresholds.
Integrates with existing cost tracking from Step 14 Observability. Step 32.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.governance.constants import (
    GovernanceDecisionType,
    MAX_BUDGET_RESERVATION_SECONDS,
)
from backend.app.services.governance.errors import (
    GovernanceBudgetExceededError,
    GovernanceReservationError,
)
from backend.app.services.governance.models import BudgetPolicy, BudgetReservation
from backend.app.services.governance.repository import GovernancePolicyRepository
from backend.app.services.governance.schemas import BudgetPolicyCreate, BudgetReservationCreate


class BudgetService:
    """
    Manages workspace/project budget policies and budget reservations.
    Never invents cost values for unknown providers.
    """

    def __init__(self, repo: GovernancePolicyRepository):
        self.repo = repo

    async def upsert_budget_policy(
        self,
        organization_id: uuid.UUID,
        created_by: uuid.UUID,
        data: BudgetPolicyCreate,
    ) -> BudgetPolicy:
        return await self.repo.upsert_budget_policy(organization_id, created_by, data)

    async def get_budget_policy(
        self,
        organization_id: uuid.UUID,
        workspace_id: Optional[uuid.UUID],
        project_id: Optional[uuid.UUID],
    ) -> Optional[BudgetPolicy]:
        # Project-level first, then workspace, then org
        if project_id:
            p = await self.repo.get_budget_policy(organization_id, workspace_id, project_id)
            if p:
                return p
        if workspace_id:
            p = await self.repo.get_budget_policy(organization_id, workspace_id, None)
            if p:
                return p
        return await self.repo.get_budget_policy(organization_id, None, None)

    async def check_cost(
        self,
        organization_id: uuid.UUID,
        workspace_id: Optional[uuid.UUID],
        project_id: Optional[uuid.UUID],
        estimated_cost_usd: Optional[float],
    ) -> Tuple[GovernanceDecisionType, list]:
        """
        Returns (decision, reasons) for estimated cost against budget policy.
        If cost is None/unknown, returns ALLOW (never fabricate costs).
        """
        if estimated_cost_usd is None:
            return GovernanceDecisionType.ALLOW, []

        policy = await self.get_budget_policy(organization_id, workspace_id, project_id)
        if not policy:
            return GovernanceDecisionType.ALLOW, []

        reasons = []

        # Check per-run limit
        if policy.per_run_limit_usd and estimated_cost_usd > policy.per_run_limit_usd:
            action = policy.on_hard_breach
            if action == "deny":
                return GovernanceDecisionType.DENY, [
                    f"Estimated cost ${estimated_cost_usd:.4f} exceeds per-run limit ${policy.per_run_limit_usd:.4f}"
                ]
            elif action == "require_approval":
                return GovernanceDecisionType.REQUIRE_APPROVAL, [
                    f"Estimated cost ${estimated_cost_usd:.4f} exceeds per-run limit; approval required"
                ]

        # Check active reservations vs daily limit
        if workspace_id and policy.daily_limit_usd:
            active_reservations = await self.repo.get_active_reservations_total(workspace_id)
            projected = active_reservations + estimated_cost_usd
            soft_limit = policy.daily_limit_usd * policy.soft_threshold_pct
            hard_limit = policy.daily_limit_usd * policy.hard_threshold_pct

            if projected >= hard_limit:
                action = policy.on_hard_breach
                if action == "deny":
                    return GovernanceDecisionType.DENY, [
                        f"Projected daily usage ${projected:.4f} would exceed daily limit ${policy.daily_limit_usd:.4f}"
                    ]
                elif action == "require_approval":
                    return GovernanceDecisionType.REQUIRE_APPROVAL, [
                        f"Projected daily usage would exceed hard threshold; approval required"
                    ]
            elif projected >= soft_limit:
                reasons.append(
                    f"Projected daily usage ${projected:.4f} approaching daily limit ${policy.daily_limit_usd:.4f}"
                )
                return GovernanceDecisionType.ALLOW_WITH_CONSTRAINTS, reasons

        return GovernanceDecisionType.ALLOW, reasons

    async def reserve(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        user_id: Optional[uuid.UUID],
        estimated_cost_usd: float,
        run_id: Optional[uuid.UUID] = None,
        job_id: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None,
    ) -> Optional[uuid.UUID]:
        """
        Creates a budget reservation before execution.
        Returns reservation_id or None if no budget policy is configured.
        """
        policy = await self.get_budget_policy(organization_id, workspace_id, project_id)
        if not policy:
            return None

        try:
            reservation = await self.repo.create_reservation(
                organization_id=organization_id,
                user_id=user_id,
                data=BudgetReservationCreate(
                    workspace_id=workspace_id,
                    project_id=project_id,
                    user_id=user_id,
                    run_id=run_id,
                    job_id=job_id,
                    reserved_amount_usd=estimated_cost_usd,
                ),
            )
            return reservation.id
        except Exception as exc:
            logger.warning("Budget: failed to create reservation: %s", exc)
            return None

    async def settle(self, reservation_id: uuid.UUID, actual_cost_usd: float) -> None:
        await self.repo.settle_reservation(reservation_id, actual_cost_usd)

    async def release(self, reservation_id: uuid.UUID) -> None:
        await self.repo.release_reservation(reservation_id)
