"""
GovernancePolicyRepository: database persistence for policies, versions, budgets, reservations,
and decision logs. Step 32.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.governance.constants import (
    BudgetReservationStatus,
    GovernanceDecisionType,
    MAX_BUDGET_RESERVATION_SECONDS,
    PolicyScope,
    PolicyStatus,
    PolicyVersionStatus,
)
from backend.app.services.governance.errors import (
    GovernanceConflictError,
    GovernancePolicyNotFoundError,
    GovernancePolicyVersionError,
    GovernanceReservationError,
)
from backend.app.services.governance.models import (
    BudgetPolicy,
    BudgetReservation,
    GovernanceDecisionLog,
    GovernancePolicy,
    GovernancePolicyVersion,
)
from backend.app.services.governance.schemas import (
    BudgetPolicyCreate,
    BudgetReservationCreate,
    GovernanceDecision,
    GovernancePolicyCreate,
    GovernancePolicyUpdate,
    PolicyVersionCreate,
)


class GovernancePolicyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ------------------------------------------------------------------
    # Policy CRUD
    # ------------------------------------------------------------------

    async def create_policy(
        self,
        organization_id: uuid.UUID,
        created_by: uuid.UUID,
        data: GovernancePolicyCreate,
    ) -> GovernancePolicy:
        policy = GovernancePolicy(
            organization_id=organization_id,
            workspace_id=data.workspace_id,
            project_id=data.project_id,
            name=data.name,
            description=data.description,
            scope=data.scope.value,
            priority=data.priority,
            created_by=created_by,
        )
        self.session.add(policy)
        await self.session.flush()
        return policy

    async def get_policy(self, policy_id: uuid.UUID) -> Optional[GovernancePolicy]:
        result = await self.session.execute(
            select(GovernancePolicy).where(GovernancePolicy.id == policy_id)
        )
        return result.scalar_one_or_none()

    async def require_policy(self, policy_id: uuid.UUID) -> GovernancePolicy:
        policy = await self.get_policy(policy_id)
        if not policy:
            raise GovernancePolicyNotFoundError(f"Policy {policy_id} not found")
        return policy

    async def list_policies(
        self,
        organization_id: uuid.UUID,
        workspace_id: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None,
        scope: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[GovernancePolicy]:
        q = select(GovernancePolicy).where(GovernancePolicy.organization_id == organization_id)
        if workspace_id is not None:
            q = q.where(GovernancePolicy.workspace_id == workspace_id)
        if project_id is not None:
            q = q.where(GovernancePolicy.project_id == project_id)
        if scope:
            q = q.where(GovernancePolicy.scope == scope)
        if status:
            q = q.where(GovernancePolicy.status == status)
        q = q.order_by(GovernancePolicy.priority.asc(), GovernancePolicy.created_at.asc())
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def update_policy(
        self,
        policy_id: uuid.UUID,
        data: GovernancePolicyUpdate,
    ) -> GovernancePolicy:
        policy = await self.require_policy(policy_id)
        if data.name is not None:
            policy.name = data.name
        if data.description is not None:
            policy.description = data.description
        if data.priority is not None:
            policy.priority = data.priority
        if data.status is not None:
            policy.status = data.status.value
        await self.session.flush()
        return policy

    async def delete_policy(self, policy_id: uuid.UUID) -> None:
        policy = await self.require_policy(policy_id)
        policy.status = PolicyStatus.ARCHIVED.value
        await self.session.flush()

    # ------------------------------------------------------------------
    # Policy Versions
    # ------------------------------------------------------------------

    async def create_version(
        self,
        policy_id: uuid.UUID,
        created_by: uuid.UUID,
        data: PolicyVersionCreate,
    ) -> GovernancePolicyVersion:
        # Compute next version number atomically
        result = await self.session.execute(
            select(sa_func.coalesce(sa_func.max(GovernancePolicyVersion.version_number), 0)).where(
                GovernancePolicyVersion.policy_id == policy_id
            )
        )
        max_ver = result.scalar_one() or 0
        version = GovernancePolicyVersion(
            policy_id=policy_id,
            version_number=max_ver + 1,
            rules=[r.model_dump() for r in data.rules],
            change_summary=data.change_summary,
            created_by=created_by,
            status=PolicyVersionStatus.DRAFT.value,
        )
        self.session.add(version)
        await self.session.flush()
        return version

    async def get_version(self, version_id: uuid.UUID) -> Optional[GovernancePolicyVersion]:
        result = await self.session.execute(
            select(GovernancePolicyVersion).where(GovernancePolicyVersion.id == version_id)
        )
        return result.scalar_one_or_none()

    async def list_versions(self, policy_id: uuid.UUID) -> List[GovernancePolicyVersion]:
        result = await self.session.execute(
            select(GovernancePolicyVersion)
            .where(GovernancePolicyVersion.policy_id == policy_id)
            .order_by(GovernancePolicyVersion.version_number.desc())
        )
        return list(result.scalars().all())

    async def activate_version(
        self,
        policy_id: uuid.UUID,
        version_id: uuid.UUID,
    ) -> GovernancePolicyVersion:
        """Atomically activate a draft version and deactivate the previously active version."""
        version = await self.get_version(version_id)
        if not version or version.policy_id != policy_id:
            raise GovernancePolicyVersionError(f"Version {version_id} not found for policy {policy_id}")
        if version.status != PolicyVersionStatus.DRAFT.value:
            raise GovernanceConflictError(f"Only draft versions can be activated; version is '{version.status}'")

        # Deactivate currently active version
        result = await self.session.execute(
            select(GovernancePolicyVersion).where(
                GovernancePolicyVersion.policy_id == policy_id,
                GovernancePolicyVersion.status == PolicyVersionStatus.ACTIVE.value,
            )
        )
        current_active = result.scalar_one_or_none()
        if current_active:
            current_active.status = PolicyVersionStatus.DEPRECATED.value
            current_active.deactivated_at = datetime.now(timezone.utc)

        # Activate new version
        version.status = PolicyVersionStatus.ACTIVE.value
        version.activated_at = datetime.now(timezone.utc)

        # Update policy pointer
        policy = await self.require_policy(policy_id)
        policy.active_version_id = version.id
        policy.status = PolicyStatus.ACTIVE.value

        await self.session.flush()
        return version

    async def get_active_version(self, policy_id: uuid.UUID) -> Optional[GovernancePolicyVersion]:
        result = await self.session.execute(
            select(GovernancePolicyVersion).where(
                GovernancePolicyVersion.policy_id == policy_id,
                GovernancePolicyVersion.status == PolicyVersionStatus.ACTIVE.value,
            )
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Budget Policies
    # ------------------------------------------------------------------

    async def upsert_budget_policy(
        self,
        organization_id: uuid.UUID,
        created_by: uuid.UUID,
        data: BudgetPolicyCreate,
    ) -> BudgetPolicy:
        # Deactivate any existing budget policy for the same scope
        existing_q = select(BudgetPolicy).where(
            BudgetPolicy.organization_id == organization_id,
            BudgetPolicy.workspace_id == data.workspace_id,
            BudgetPolicy.project_id == data.project_id,
            BudgetPolicy.is_active == True,
        )
        existing = (await self.session.execute(existing_q)).scalar_one_or_none()
        if existing:
            existing.is_active = False

        budget = BudgetPolicy(
            organization_id=organization_id,
            workspace_id=data.workspace_id,
            project_id=data.project_id,
            daily_limit_usd=data.daily_limit_usd,
            monthly_limit_usd=data.monthly_limit_usd,
            per_run_limit_usd=data.per_run_limit_usd,
            per_user_daily_limit_usd=data.per_user_daily_limit_usd,
            soft_threshold_pct=data.soft_threshold_pct,
            hard_threshold_pct=data.hard_threshold_pct,
            on_soft_breach=data.on_soft_breach,
            on_hard_breach=data.on_hard_breach,
            created_by=created_by,
        )
        self.session.add(budget)
        await self.session.flush()
        return budget

    async def get_budget_policy(
        self,
        organization_id: uuid.UUID,
        workspace_id: Optional[uuid.UUID],
        project_id: Optional[uuid.UUID],
    ) -> Optional[BudgetPolicy]:
        q = select(BudgetPolicy).where(
            BudgetPolicy.organization_id == organization_id,
            BudgetPolicy.workspace_id == workspace_id,
            BudgetPolicy.project_id == project_id,
            BudgetPolicy.is_active == True,
        )
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Budget Reservations
    # ------------------------------------------------------------------

    async def create_reservation(
        self,
        organization_id: uuid.UUID,
        user_id: Optional[uuid.UUID],
        data: BudgetReservationCreate,
    ) -> BudgetReservation:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=MAX_BUDGET_RESERVATION_SECONDS)
        reservation = BudgetReservation(
            organization_id=organization_id,
            workspace_id=data.workspace_id,
            project_id=data.project_id,
            user_id=user_id,
            run_id=data.run_id,
            job_id=data.job_id,
            reserved_amount_usd=data.reserved_amount_usd,
            status=BudgetReservationStatus.ACTIVE.value,
            expires_at=expires_at,
        )
        self.session.add(reservation)
        await self.session.flush()
        return reservation

    async def settle_reservation(
        self,
        reservation_id: uuid.UUID,
        actual_amount_usd: float,
    ) -> None:
        result = await self.session.execute(
            select(BudgetReservation).where(BudgetReservation.id == reservation_id)
        )
        r = result.scalar_one_or_none()
        if r:
            r.actual_amount_usd = actual_amount_usd
            r.status = BudgetReservationStatus.SETTLED.value
            r.settled_at = datetime.now(timezone.utc)
        await self.session.flush()

    async def release_reservation(self, reservation_id: uuid.UUID) -> None:
        result = await self.session.execute(
            select(BudgetReservation).where(BudgetReservation.id == reservation_id)
        )
        r = result.scalar_one_or_none()
        if r:
            r.status = BudgetReservationStatus.RELEASED.value
            r.settled_at = datetime.now(timezone.utc)
        await self.session.flush()

    async def get_active_reservations_total(
        self,
        workspace_id: uuid.UUID,
    ) -> float:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(sa_func.coalesce(sa_func.sum(BudgetReservation.reserved_amount_usd), 0.0)).where(
                BudgetReservation.workspace_id == workspace_id,
                BudgetReservation.status == BudgetReservationStatus.ACTIVE.value,
                BudgetReservation.expires_at > now,
            )
        )
        return float(result.scalar_one() or 0.0)

    # ------------------------------------------------------------------
    # Decision Log
    # ------------------------------------------------------------------

    async def log_decision(
        self,
        decision: GovernanceDecision,
        organization_id: uuid.UUID,
        workspace_id: Optional[uuid.UUID],
        project_id: Optional[uuid.UUID],
        user_id: Optional[uuid.UUID],
        enforcement_point: str,
        latency_ms: Optional[int] = None,
    ) -> GovernanceDecisionLog:
        log = GovernanceDecisionLog(
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            user_id=user_id,
            enforcement_point=enforcement_point,
            decision=decision.decision.value,
            reasons=decision.reasons,
            matched_policy_ids=decision.matched_policies,
            policy_version=decision.policy_version,
            constraints=decision.constraints,
            required_approvals=decision.required_approvals,
            required_verifications=decision.required_verifications,
            evaluation_latency_ms=latency_ms,
            expires_at=decision.expires_at,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def list_decision_logs(
        self,
        workspace_id: uuid.UUID,
        enforcement_point: Optional[str] = None,
        decision: Optional[str] = None,
        limit: int = 100,
    ) -> List[GovernanceDecisionLog]:
        q = select(GovernanceDecisionLog).where(
            GovernanceDecisionLog.workspace_id == workspace_id
        )
        if enforcement_point:
            q = q.where(GovernanceDecisionLog.enforcement_point == enforcement_point)
        if decision:
            q = q.where(GovernanceDecisionLog.decision == decision)
        q = q.order_by(GovernanceDecisionLog.created_at.desc()).limit(limit)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def count_decisions_since(
        self,
        workspace_id: uuid.UUID,
        decision_type: str,
        since: datetime,
    ) -> int:
        result = await self.session.execute(
            select(sa_func.count()).where(
                GovernanceDecisionLog.workspace_id == workspace_id,
                GovernanceDecisionLog.decision == decision_type,
                GovernanceDecisionLog.created_at >= since,
            )
        )
        return result.scalar_one() or 0
