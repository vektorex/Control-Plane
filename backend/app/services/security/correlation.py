"""
Deterministic Incident Signal Correlation Engine for Step 34.
Links security signals into cohesive security incidents based on shared context,
temporal proximity, and correlation/causation identifiers.
Never invents false causation.
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.security.models import (
    IncidentSignal,
    IncidentTimelineEvent,
    SecurityIncident,
    SecuritySignal,
)


class IncidentCorrelationEngine:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def correlate_signal(
        self,
        signal: SecuritySignal,
        time_window_minutes: int = 30,
    ) -> Optional[SecurityIncident]:
        """
        Attempts to correlate an incoming signal into an existing open incident
        matching the same organization, workspace, actor, resource, or correlation_id.
        If no matching incident is found and severity is high or critical, creates a new incident.
        """
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=time_window_minutes)

        # 1. Search for existing open incident matching correlation_id, causation_id, or actor/resource
        query = (
            select(SecurityIncident)
            .where(
                SecurityIncident.organization_id == signal.organization_id,
                SecurityIncident.status.in_(["open", "investigating"]),
                SecurityIncident.last_seen_at >= window_start,
            )
            .order_by(desc(SecurityIncident.last_seen_at))
        )

        if signal.workspace_id:
            query = query.where(
                (SecurityIncident.workspace_id == signal.workspace_id)
                | (SecurityIncident.workspace_id.is_(None))
            )

        res = await self.session.execute(query)
        candidates = list(res.scalars().all())

        matched_incident: Optional[SecurityIncident] = None
        rel_type = "related"

        for cand in candidates:
            cand_meta = cand.metadata_payload or {}
            # Match 1: explicit correlation_id or causation_id
            if signal.correlation_id and cand_meta.get("correlation_id") == signal.correlation_id:
                matched_incident = cand
                rel_type = "supporting"
                break
            if signal.causation_id and cand_meta.get("causation_id") == signal.causation_id:
                matched_incident = cand
                rel_type = "follow_up"
                break

            # Match 2: shared actor with matching category
            if signal.actor_id and cand_meta.get("primary_actor_id") == signal.actor_id:
                matched_incident = cand
                rel_type = "supporting"
                break

            # Match 3: shared resource
            if signal.resource_id and cand_meta.get("primary_resource_id") == signal.resource_id:
                matched_incident = cand
                rel_type = "related"
                break

        # If matched, bind signal to existing incident
        if matched_incident:
            link = IncidentSignal(
                incident_id=matched_incident.id,
                signal_id=signal.id,
                relationship=rel_type,
                created_at=now,
            )
            self.session.add(link)

            # Update incident timestamps and status
            matched_incident.last_seen_at = now
            if signal.severity in {"high", "critical"} and matched_incident.severity not in {"critical"}:
                matched_incident.severity = signal.severity

            # Add timeline event
            tl = IncidentTimelineEvent(
                incident_id=matched_incident.id,
                timestamp=signal.timestamp or now,
                event_type="signal_correlated",
                source_type=signal.source_type,
                source_id=signal.id,
                actor_type=signal.actor_type,
                actor_id=signal.actor_id,
                summary=f"Signal '{signal.signal_type}' ({signal.severity}) correlated with relationship '{rel_type}'",
                metadata_payload={"signal_type": signal.signal_type, "severity": signal.severity},
            )
            self.session.add(tl)
            signal.status = "correlated"
            await self.session.flush()
            return matched_incident

        # 2. If signal is high/critical, automatically spawn new incident
        if signal.severity in {"high", "critical"}:
            category = self._derive_category(signal.signal_type)
            inc = SecurityIncident(
                organization_id=signal.organization_id,
                workspace_id=signal.workspace_id,
                project_id=signal.project_id,
                title=f"Security Alert: {signal.signal_type.replace('_', ' ').title()}",
                description=f"Automated incident spawned by high-severity signal: {signal.signal_type}",
                category=category,
                severity=signal.severity,
                status="open",
                detected_at=now,
                first_seen_at=signal.timestamp or now,
                last_seen_at=signal.timestamp or now,
                metadata_payload={
                    "primary_actor_id": signal.actor_id,
                    "primary_resource_id": signal.resource_id,
                    "correlation_id": signal.correlation_id,
                    "causation_id": signal.causation_id,
                    "trigger_signal_type": signal.signal_type,
                },
                created_at=now,
            )
            self.session.add(inc)
            await self.session.flush()

            # Attach trigger link
            link = IncidentSignal(
                incident_id=inc.id,
                signal_id=signal.id,
                relationship="trigger",
                created_at=now,
            )
            self.session.add(link)

            # Timeline event
            tl = IncidentTimelineEvent(
                incident_id=inc.id,
                timestamp=signal.timestamp or now,
                event_type="incident_created",
                source_type=signal.source_type,
                source_id=signal.id,
                actor_type=signal.actor_type,
                actor_id=signal.actor_id,
                summary=f"Incident triggered by {signal.signal_type} ({signal.severity})",
                metadata_payload={"signal_type": signal.signal_type, "severity": signal.severity},
            )
            self.session.add(tl)
            signal.status = "correlated"
            await self.session.flush()
            return inc

        return None

    def _derive_category(self, signal_type: str) -> str:
        if "auth" in signal_type:
            return "authentication"
        if "authorization" in signal_type:
            return "authorization"
        if "injection" in signal_type:
            return "prompt_injection"
        if "secret" in signal_type or "pii" in signal_type:
            return "data_exposure"
        if "tool" in signal_type:
            return "tool_abuse"
        if "connector" in signal_type:
            return "connector_abuse"
        if "workflow" in signal_type:
            return "workflow_abuse"
        if "deletion" in signal_type or "hold" in signal_type:
            return "data_exposure"
        if "isolation" in signal_type:
            return "tenant_isolation"
        if "artifact" in signal_type:
            return "artifact_security"
        if "webhook" in signal_type:
            return "webhook_security"
        if "cost" in signal_type or "rate_limit" in signal_type:
            return "cost_abuse"
        return "unknown"
