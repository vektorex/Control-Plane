"""
Integration bridge connecting Reliability signals to Step 34 SecurityIncident when security implications exist.
Never creates a duplicate incident store.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.security.models import SecurityIncident, SecuritySignal


class ReliabilityIncidentBridge:
    """Links high-severity reliability failures having security impact to Step 34 incidents."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def link_to_security_incident_if_warranted(
        self,
        organization_id: str,
        failure_type: str,
        target_resource: str,
        details: Dict[str, Any],
        is_security_implicated: bool = False,
    ) -> Optional[SecurityIncident]:
        """
        Evaluates whether a reliability outage has security implications
        (e.g., repeated authentication failure bursts, tenant isolation violation during recovery,
        legal hold bypass during purge). If so, links/creates a Step 34 incident.
        """
        if not is_security_implicated and failure_type not in {
            "tenant_isolation_failure",
            "legal_hold_bypass",
            "unauthorized_resume_attempt",
            "malicious_chaos_injection",
        }:
            # Standard operational failure; does not warrant security incident
            return None

        incident = SecurityIncident(
            organization_id=organization_id,
            title=f"Security-Implicated Reliability Event: {failure_type} on {target_resource}",
            description=f"Reliability failure with potential security impact: {details.get('reason', failure_type)}",
            category="availability",
            severity="high" if "isolation" in failure_type or "legal_hold" in failure_type else "medium",
            status="open",
            first_seen_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc),
            metadata_payload={
                "source": "reliability_layer",
                "failure_type": failure_type,
                "target_resource": target_resource,
                "details": details,
            },
        )
        self.session.add(incident)
        await self.session.commit()
        await self.session.refresh(incident)
        return incident
