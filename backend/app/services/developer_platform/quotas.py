"""
API Quota Management and Enforcement for Developer Platform.
Step 37: Public API, Developer Platform & SDK Layer.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.developer_platform.errors import QuotaExceededError
from backend.app.services.developer_platform.models import APIQuota, APIUsageRecord


class QuotaService:
    """Enforces volumetric resource quotas per developer application."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_quota(
        self,
        application_id: str,
        resource_type: str,
        requested_amount: int = 1,
    ) -> None:
        """
        Verifies if the requested resource consumption fits within the configured quota.
        Raises QuotaExceededError if limit is breached.
        """
        # Fetch enabled quota rule for this application & resource
        query = select(APIQuota).where(
            APIQuota.application_id == application_id,
            APIQuota.resource_type == resource_type,
            APIQuota.enabled.is_(True),
        )
        result = await self.session.execute(query)
        quota: Optional[APIQuota] = result.scalars().first()

        if not quota:
            return  # No quota configured; allow operation

        now = datetime.now(timezone.utc)
        period = quota.period.lower()

        if period == "minute":
            window_start = now - timedelta(minutes=1)
        elif period == "hour":
            window_start = now - timedelta(hours=1)
        elif period == "day":
            window_start = now - timedelta(days=1)
        elif period == "month":
            window_start = now - timedelta(days=30)
        else:
            window_start = now - timedelta(days=1)

        # Aggregate current usage within the active period
        if resource_type in ("requests", "task_runs", "workflow_runs"):
            count_query = select(func.count(APIUsageRecord.id)).where(
                APIUsageRecord.application_id == application_id,
                APIUsageRecord.timestamp >= window_start,
            )
            count_res = await self.session.execute(count_query)
            current_usage = count_res.scalar() or 0
        elif resource_type == "tokens":
            token_query = select(func.coalesce(func.sum(APIUsageRecord.tokens), 0)).where(
                APIUsageRecord.application_id == application_id,
                APIUsageRecord.timestamp >= window_start,
            )
            token_res = await self.session.execute(token_query)
            current_usage = token_res.scalar() or 0
        else:
            current_usage = 0

        if current_usage + requested_amount > quota.limit:
            raise QuotaExceededError(
                resource_type=resource_type,
                limit=quota.limit,
                period=quota.period,
            )

QuotaEnforcer = QuotaService
