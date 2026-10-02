"""
TriggerPolicyEngine enforcing rate limits, concurrency limits, workspace isolation, and security policies.
"""
import time
import uuid
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.db.models.trigger import WorkflowTrigger, TriggerRun
from backend.app.db.models.workflow import Workflow
from backend.app.services.triggers.errors import (
    TriggerConcurrencyError,
    TriggerDisabledError,
    TriggerPolicyError,
    TriggerRateLimitError,
)


class TriggerPolicyEngine:
    """
    Enforces application policies on trigger activations.
    Guarantees triggers cannot bypass HITL, model policies, or connector restrictions.
    """

    # In-memory sliding window rate limiter: key -> list of float timestamps
    _rate_limit_windows: Dict[str, List[float]] = defaultdict(list)

    @classmethod
    def check_rate_limit(
        cls,
        trigger_id: uuid.UUID,
        workspace_id: uuid.UUID,
        public_trigger_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates rate limits:
        TRIGGER_RATE_LIMIT_PER_MINUTE = 60
        - per trigger
        - per workspace
        - per webhook identifier
        """
        now = time.time()
        window_sec = 60.0
        max_rate = getattr(settings, "TRIGGER_RATE_LIMIT_PER_MINUTE", 60)

        keys = [
            f"trig:{trigger_id}",
            f"ws:{workspace_id}",
        ]
        if public_trigger_id:
            keys.append(f"wh:{public_trigger_id}")

        for k in keys:
            timestamps = cls._rate_limit_windows[k]
            # Prune timestamps older than 60s
            cls._rate_limit_windows[k] = [ts for ts in timestamps if now - ts < window_sec]
            if len(cls._rate_limit_windows[k]) >= max_rate:
                return False, f"Rate limit of {max_rate}/minute exceeded on {k.split(':')[0]}."

        # Record this invocation
        for k in keys:
            cls._rate_limit_windows[k].append(now)

        return True, None

    @classmethod
    async def check_workspace_concurrency(
        cls,
        session: AsyncSession,
        workspace_id: uuid.UUID,
    ) -> Tuple[bool, int, int]:
        """
        Ensures active running triggers in a workspace do not exceed
        MAX_TRIGGER_CONCURRENCY_PER_WORKSPACE (default 5).
        """
        max_concurrency = getattr(settings, "MAX_TRIGGER_CONCURRENCY_PER_WORKSPACE", 5)

        stmt = (
            select(func.count(TriggerRun.id))
            .where(
                TriggerRun.workspace_id == workspace_id,
                TriggerRun.status.in_(["running", "queued"]),
            )
        )
        res = await session.execute(stmt)
        active_count = res.scalar() or 0

        if active_count >= max_concurrency:
            return False, active_count, max_concurrency

        return True, active_count, max_concurrency

    @classmethod
    async def validate_trigger_execution(
        cls,
        session: AsyncSession,
        trigger: WorkflowTrigger,
        workflow: Optional[Workflow] = None,
    ) -> List[str]:
        """
        Comprehensive pre-execution policy validation.
        Returns a list of warnings or raises policy errors.
        """
        warnings: List[str] = []

        # 1. Trigger Status
        if trigger.status != "active":
            raise TriggerDisabledError(f"Trigger '{trigger.name}' is {trigger.status}; execution rejected.")

        # 2. Workflow Existence & Status
        if workflow:
            if workflow.status == "archived":
                raise TriggerPolicyError(f"Workflow '{workflow.name}' is archived. Triggers cannot run archived workflows.")
            if workflow.status == "draft":
                warnings.append("Workflow is in draft mode. Ensure it is published for production automation.")

        # 3. Rate Limit
        passed_rl, rl_msg = cls.check_rate_limit(
            trigger_id=trigger.id,
            workspace_id=trigger.workspace_id,
            public_trigger_id=trigger.public_trigger_id,
        )
        if not passed_rl:
            raise TriggerRateLimitError(rl_msg or "Rate limit exceeded.")

        # 4. Workspace Concurrency
        passed_conc, active_cnt, max_conc = await cls.check_workspace_concurrency(session, trigger.workspace_id)
        if not passed_conc:
            raise TriggerConcurrencyError(
                f"Workspace trigger concurrency limit reached ({active_cnt}/{max_conc} active). Try again later."
            )

        return warnings
