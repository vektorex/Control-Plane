"""
Central Security Operations Service Facade for Step 34.
Coordinates signals, deterministic detection, correlation, incidents, investigation, containment, and playbooks.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.security.containment import SecurityContainmentService
from backend.app.services.security.correlation import IncidentCorrelationEngine
from backend.app.services.security.evidence import SecurityEvidenceRecorder
from backend.app.services.security.incidents import SecurityIncidentService
from backend.app.services.security.indicators import SecurityIndicatorService
from backend.app.services.security.investigation import IncidentInvestigationService
from backend.app.services.security.playbooks import SecurityPlaybookService
from backend.app.services.security.policies import SecurityPolicyEngineBridge
from backend.app.services.security.repository import SecurityRepository
from backend.app.services.security.response import SecurityResponseOrchestrator
from backend.app.services.security.schemas import (
    IncidentInvestigationResponse,
    SecurityEventNormalized,
    SecurityOverviewResponse,
    SecurityStatisticsResponse,
)
from backend.app.services.security.signals import SecuritySignalService


class SecurityService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.signals = SecuritySignalService(session)
        self.incidents = SecurityIncidentService(session)
        self.investigation = IncidentInvestigationService(session)
        self.containment = SecurityContainmentService(session)
        self.indicators = SecurityIndicatorService(session)
        self.playbooks = SecurityPlaybookService(session)
        self.correlation = IncidentCorrelationEngine(session)
        self.response = SecurityResponseOrchestrator(session)
        self.evidence = SecurityEvidenceRecorder(session)
        self.policy_bridge = SecurityPolicyEngineBridge(session)
        self.repo = SecurityRepository(session)

    async def process_security_event(self, event: SecurityEventNormalized) -> Dict[str, Any]:
        """
        Processes an operational event end-to-end:
        1. Runs 16 deterministic detectors to produce SecuritySignals
        2. Correlates signals with existing or new SecurityIncidents
        3. Evaluates active response playbooks and executes pre-authorized containment
        """
        emitted_signals = await self.signals.ingest_event(event)
        correlated_incidents = []

        for sig in emitted_signals:
            inc = await self.correlation.correlate_signal(sig)
            if inc and inc.id not in [ci.id for ci in correlated_incidents]:
                correlated_incidents.append(inc)
                # Evaluate playbooks for newly triggered/escalated incident
                await self.response.evaluate_and_respond(inc, trigger_signal=sig)

        return {
            "signals_detected": len(emitted_signals),
            "incidents_affected": len(correlated_incidents),
            "signal_ids": [s.id for s in emitted_signals],
            "incident_ids": [i.id for i in correlated_incidents],
        }

    async def get_overview(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
    ) -> SecurityOverviewResponse:
        return await self.repo.get_overview(organization_id, workspace_id)

    async def get_statistics(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
    ) -> SecurityStatisticsResponse:
        return await self.repo.get_statistics(organization_id, workspace_id)
