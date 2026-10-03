"""
API Usage Telemetry and Aggregated Reporting.
Step 37: Public API, Developer Platform & SDK Layer.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.developer_platform.models import APIUsageRecord
from backend.app.services.developer_platform.schemas import APIUsageAggregateResponse


class APIUsageService:
    """Records and aggregates API call metrics and latency telemetry."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_usage(
        self,
        organization_id: str,
        application_id: str,
        credential_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        latency_ms: float,
        request_bytes: int = 0,
        response_bytes: int = 0,
        tokens: Optional[int] = None,
        cost: Optional[float] = None,
        request_id: str = "",
        run_id: Optional[str] = None,
    ) -> APIUsageRecord:
        """Persists a sanitized telemetry record for an API request."""
        record = APIUsageRecord(
            organization_id=organization_id,
            application_id=application_id,
            credential_id=credential_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            request_bytes=request_bytes,
            response_bytes=response_bytes,
            latency_ms=latency_ms,
            tokens=tokens,
            cost=cost,
            timestamp=datetime.now(timezone.utc),
            request_id=request_id,
            run_id=run_id,
        )
        self.session.add(record)
        await self.session.commit()
        return record

    async def get_usage_summary(
        self,
        organization_id: str,
        application_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        period_hours: int = 24,
    ) -> APIUsageAggregateResponse:
        """Calculates aggregated metrics over the requested window."""
        window_start = datetime.now(timezone.utc) - timedelta(hours=period_hours)

        query = select(APIUsageRecord).where(
            APIUsageRecord.organization_id == organization_id,
            APIUsageRecord.timestamp >= window_start,
        )
        if application_id:
            query = query.where(APIUsageRecord.application_id == application_id)
        if endpoint:
            query = query.where(APIUsageRecord.endpoint == endpoint)

        result = await self.session.execute(query)
        records: List[APIUsageRecord] = list(result.scalars().all())

        total_requests = len(records)
        total_errors = sum(1 for r in records if r.status_code >= 400)
        error_rate = (total_errors / total_requests) if total_requests > 0 else 0.0
        avg_latency = (sum(r.latency_ms for r in records) / total_requests) if total_requests > 0 else 0.0
        total_tokens = sum(r.tokens or 0 for r in records)
        total_cost = sum(r.cost or 0.0 for r in records)

        task_runs = sum(1 for r in records if "/tasks/" in r.endpoint and r.method == "POST")
        workflow_runs = sum(1 for r in records if "/workflows/" in r.endpoint and r.method == "POST")

        by_endpoint: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        for r in records:
            by_endpoint[r.endpoint] = by_endpoint.get(r.endpoint, 0) + 1
            status_str = str(r.status_code)
            by_status[status_str] = by_status.get(status_str, 0) + 1

        return APIUsageAggregateResponse(
            total_requests=total_requests,
            total_errors=total_errors,
            error_rate=round(error_rate, 4),
            average_latency_ms=round(avg_latency, 2),
            total_tokens=total_tokens,
            total_cost=round(total_cost, 4),
            task_runs=task_runs,
            workflow_runs=workflow_runs,
            by_endpoint=by_endpoint,
            by_status=by_status,
        )
