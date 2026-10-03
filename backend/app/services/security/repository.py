"""
Security Repository and Aggregation Queries for Step 34.
Generates factual operational metrics without subjective security scores.
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.security.models import (
    ContainmentAction,
    SecurityIncident,
    SecurityIndicator,
    SecurityPlaybook,
    SecuritySignal,
)
from backend.app.services.security.schemas import (
    SecurityOverviewResponse,
    SecurityStatisticsResponse,
)


class SecurityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_overview(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
    ) -> SecurityOverviewResponse:
        """
        Calculates operational security overview metrics.
        Never computes a subjective 'security score'.
        """
        now = datetime.now(timezone.utc)
        recent_window = now - timedelta(hours=24)

        # 1. Open incidents count
        q_open = select(func.count(SecurityIncident.id)).where(
            SecurityIncident.organization_id == organization_id,
            SecurityIncident.status.in_(["open", "investigating"]),
        )
        if workspace_id:
            q_open = q_open.where(SecurityIncident.workspace_id == workspace_id)
        open_incidents = (await self.session.execute(q_open)).scalar() or 0

        # 2. Critical & High signals count (last 24h)
        q_crit = select(func.count(SecuritySignal.id)).where(
            SecuritySignal.organization_id == organization_id,
            SecuritySignal.severity == "critical",
            SecuritySignal.timestamp >= recent_window,
        )
        if workspace_id:
            q_crit = q_crit.where(SecuritySignal.workspace_id == workspace_id)
        crit_signals = (await self.session.execute(q_crit)).scalar() or 0

        q_high = select(func.count(SecuritySignal.id)).where(
            SecuritySignal.organization_id == organization_id,
            SecuritySignal.severity == "high",
            SecuritySignal.timestamp >= recent_window,
        )
        if workspace_id:
            q_high = q_high.where(SecuritySignal.workspace_id == workspace_id)
        high_signals = (await self.session.execute(q_high)).scalar() or 0

        # 3. Total recent signals (last 24h)
        q_recent = select(func.count(SecuritySignal.id)).where(
            SecuritySignal.organization_id == organization_id,
            SecuritySignal.timestamp >= recent_window,
        )
        if workspace_id:
            q_recent = q_recent.where(SecuritySignal.workspace_id == workspace_id)
        recent_signals = (await self.session.execute(q_recent)).scalar() or 0

        # 4. Active indicators count
        q_ind = select(func.count(SecurityIndicator.id)).where(
            SecurityIndicator.organization_id == organization_id,
            SecurityIndicator.status == "active",
        )
        active_indicators = (await self.session.execute(q_ind)).scalar() or 0

        # 5. Active playbooks
        q_pb = select(func.count(SecurityPlaybook.id)).where(
            (SecurityPlaybook.organization_id == organization_id)
            | (SecurityPlaybook.organization_id.is_(None)),
            SecurityPlaybook.enabled.is_(True),
        )
        active_playbooks = (await self.session.execute(q_pb)).scalar() or 0

        # 6. Pending containments
        q_cont = (
            select(func.count(ContainmentAction.id))
            .join(SecurityIncident, ContainmentAction.incident_id == SecurityIncident.id)
            .where(
                SecurityIncident.organization_id == organization_id,
                ContainmentAction.status.in_(["requested", "awaiting_approval", "executing"]),
            )
        )
        pending_containments = (await self.session.execute(q_cont)).scalar() or 0

        # 7. Breakdown by severity and category
        q_by_sev = (
            select(SecurityIncident.severity, func.count(SecurityIncident.id))
            .where(SecurityIncident.organization_id == organization_id)
            .group_by(SecurityIncident.severity)
        )
        incidents_by_severity = dict((await self.session.execute(q_by_sev)).all())

        q_by_sig_cat = (
            select(SecuritySignal.source_type, func.count(SecuritySignal.id))
            .where(
                SecuritySignal.organization_id == organization_id,
                SecuritySignal.timestamp >= recent_window,
            )
            .group_by(SecuritySignal.source_type)
        )
        signals_by_category = dict((await self.session.execute(q_by_sig_cat)).all())

        return SecurityOverviewResponse(
            open_incidents_count=open_incidents,
            critical_signals_count=crit_signals,
            high_signals_count=high_signals,
            recent_signals_count=recent_signals,
            active_indicators_count=active_indicators,
            active_playbooks_count=active_playbooks,
            pending_containments_count=pending_containments,
            signals_by_category=signals_by_category,
            incidents_by_severity=incidents_by_severity,
        )

    async def get_statistics(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
    ) -> SecurityStatisticsResponse:
        """
        Compiles aggregate historical security statistics.
        """
        q_tot_sig = select(func.count(SecuritySignal.id)).where(
            SecuritySignal.organization_id == organization_id
        )
        if workspace_id:
            q_tot_sig = q_tot_sig.where(SecuritySignal.workspace_id == workspace_id)
        total_signals = (await self.session.execute(q_tot_sig)).scalar() or 0

        q_tot_inc = select(func.count(SecurityIncident.id)).where(
            SecurityIncident.organization_id == organization_id
        )
        if workspace_id:
            q_tot_inc = q_tot_inc.where(SecurityIncident.workspace_id == workspace_id)
        total_incidents = (await self.session.execute(q_tot_inc)).scalar() or 0

        q_contained = select(func.count(SecurityIncident.id)).where(
            SecurityIncident.organization_id == organization_id,
            SecurityIncident.status == "contained",
        )
        contained_incidents = (await self.session.execute(q_contained)).scalar() or 0

        q_resolved = select(func.count(SecurityIncident.id)).where(
            SecurityIncident.organization_id == organization_id,
            SecurityIncident.status == "resolved",
        )
        resolved_incidents = (await self.session.execute(q_resolved)).scalar() or 0

        # Actions by type
        q_act_type = (
            select(ContainmentAction.action_type, func.count(ContainmentAction.id))
            .join(SecurityIncident, ContainmentAction.incident_id == SecurityIncident.id)
            .where(SecurityIncident.organization_id == organization_id)
            .group_by(ContainmentAction.action_type)
        )
        containment_by_type = dict((await self.session.execute(q_act_type)).all())

        # Signals by detector/source
        q_det = (
            select(SecuritySignal.signal_type, func.count(SecuritySignal.id))
            .where(SecuritySignal.organization_id == organization_id)
            .group_by(SecuritySignal.signal_type)
        )
        detector_counts = dict((await self.session.execute(q_det)).all())

        return SecurityStatisticsResponse(
            total_signals=total_signals,
            total_incidents=total_incidents,
            contained_incidents=contained_incidents,
            resolved_incidents=resolved_incidents,
            avg_resolution_time_seconds=None,
            containment_actions_by_type=containment_by_type,
            detectors_trigger_counts=detector_counts,
        )
