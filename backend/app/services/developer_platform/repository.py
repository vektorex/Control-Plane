"""
Developer Platform Database Repository.
Step 37: Public API, Developer Platform & SDK Layer.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.services.developer_platform.models import (
    APICredential,
    APIEnvironmentConfig,
    APIQuota,
    APIUsageRecord,
    ApplicationApproval,
    DeveloperApplication,
    WebhookSubscription,
)


class DeveloperPlatformRepository:
    """Repository handling database queries for developer applications, credentials, and telemetry."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # -----------------------------------------------------------------------
    # Overview & Metrics
    # -----------------------------------------------------------------------
    async def get_overview(self, organization_id: str) -> Dict[str, Any]:
        """Calculates factual operational metrics for the developer platform dashboard."""
        now = datetime.now(timezone.utc)
        recent_24h = now - timedelta(hours=24)

        # 1. Total applications
        q_apps = select(func.count(DeveloperApplication.id)).where(
            DeveloperApplication.organization_id == organization_id
        )
        total_apps = (await self.session.execute(q_apps)).scalar() or 0

        # 2. Active credentials
        q_creds = (
            select(func.count(APICredential.id))
            .join(DeveloperApplication, APICredential.application_id == DeveloperApplication.id)
            .where(
                DeveloperApplication.organization_id == organization_id,
                APICredential.status == "active",
            )
        )
        active_creds = (await self.session.execute(q_creds)).scalar() or 0

        # 3. Active webhooks
        q_webhooks = select(func.count(WebhookSubscription.id)).where(
            WebhookSubscription.organization_id == organization_id,
            WebhookSubscription.status == "active",
        )
        active_webhooks = (await self.session.execute(q_webhooks)).scalar() or 0

        # 4. Usage in last 24h
        q_usage = select(APIUsageRecord).where(
            APIUsageRecord.organization_id == organization_id,
            APIUsageRecord.timestamp >= recent_24h,
        )
        usage_records = list((await self.session.execute(q_usage)).scalars().all())

        total_reqs = len(usage_records)
        error_count = sum(1 for r in usage_records if r.status_code >= 400)
        error_rate = (error_count / total_reqs) if total_reqs > 0 else 0.0
        avg_latency = (sum(r.latency_ms for r in usage_records) / total_reqs) if total_reqs > 0 else 0.0

        # 5. Active environments
        q_envs = (
            select(DeveloperApplication.environment)
            .where(DeveloperApplication.organization_id == organization_id)
            .distinct()
        )
        envs = list((await self.session.execute(q_envs)).scalars().all())

        # 6. Recent activity (last 10 usage records)
        recent_records = sorted(usage_records, key=lambda x: x.timestamp, reverse=True)[:10]
        recent_activity = [
            {
                "id": r.id,
                "endpoint": r.endpoint,
                "method": r.method,
                "status_code": r.status_code,
                "latency_ms": r.latency_ms,
                "timestamp": r.timestamp.isoformat(),
                "request_id": r.request_id,
            }
            for r in recent_records
        ]

        return {
            "total_applications": total_apps,
            "active_credentials": active_creds,
            "active_webhooks": active_webhooks,
            "total_requests_24h": total_reqs,
            "error_rate_24h": round(error_rate, 4),
            "average_latency_ms": round(avg_latency, 2),
            "active_environments": envs or ["development"],
            "recent_activity": recent_activity,
        }

    # -----------------------------------------------------------------------
    # Quotas
    # -----------------------------------------------------------------------
    async def list_quotas(self, application_id: str) -> List[APIQuota]:
        query = select(APIQuota).where(APIQuota.application_id == application_id)
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def create_quota(self, application_id: str, resource_type: str, limit: int, period: str) -> APIQuota:
        quota = APIQuota(
            application_id=application_id,
            resource_type=resource_type,
            limit=limit,
            period=period,
            enabled=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.session.add(quota)
        await self.session.commit()
        return quota

    # -----------------------------------------------------------------------
    # Approvals
    # -----------------------------------------------------------------------
    async def list_approvals(self, organization_id: str, status: Optional[str] = None) -> List[ApplicationApproval]:
        query = select(ApplicationApproval).where(ApplicationApproval.organization_id == organization_id)
        if status:
            query = query.where(ApplicationApproval.status == status)
        query = query.order_by(ApplicationApproval.created_at.desc())
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def review_approval(
        self,
        approval_id: str,
        organization_id: str,
        reviewer_id: str,
        decision: str,
        notes: Optional[str] = None,
    ) -> ApplicationApproval:
        query = select(ApplicationApproval).where(
            ApplicationApproval.id == approval_id,
            ApplicationApproval.organization_id == organization_id,
        )
        res = await self.session.execute(query)
        approval = res.scalars().first()
        if not approval:
            raise ValueError(f"Approval '{approval_id}' not found.")

        approval.status = decision
        approval.reviewed_by = reviewer_id
        approval.reviewed_at = datetime.now(timezone.utc)
        approval.notes = notes

        # If approved, activate application
        if decision == "approved":
            app_q = select(DeveloperApplication).where(DeveloperApplication.id == approval.application_id)
            app = (await self.session.execute(app_q)).scalars().first()
            if app:
                app.status = "active"

        await self.session.commit()
        return approval
