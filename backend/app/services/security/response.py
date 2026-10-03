"""
Security Incident Response Orchestrator for Step 34.
Evaluates enabled playbooks, triggers automated responses, and manages containment execution.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.security.containment import SecurityContainmentService
from backend.app.services.security.evidence import SecurityEvidenceRecorder
from backend.app.services.security.models import SecurityIncident, SecuritySignal
from backend.app.services.security.playbooks import SecurityPlaybookService
from backend.app.services.security.policies import SecurityPolicyEngineBridge
from backend.app.services.security.schemas import ContainmentActionCreate


class SecurityResponseOrchestrator:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.playbook_service = SecurityPlaybookService(session)
        self.containment_service = SecurityContainmentService(session)
        self.evidence_recorder = SecurityEvidenceRecorder(session)
        self.policy_bridge = SecurityPolicyEngineBridge(session)

    async def evaluate_and_respond(
        self,
        incident: SecurityIncident,
        trigger_signal: Optional[SecuritySignal] = None,
    ) -> List[Dict[str, Any]]:
        """
        Evaluates active playbooks matching the incident category and severity.
        Executes allowlisted automated actions where pre-authorized.
        """
        playbooks = await self.playbook_service.list_playbooks(
            organization_id=incident.organization_id,
            enabled_only=True,
        )

        executed_actions: List[Dict[str, Any]] = []

        for pb in playbooks:
            conds = pb.trigger_conditions or {}
            # Check match on category or signal_type
            cat_match = conds.get("category") in {None, incident.category}
            sev_match = True
            if "min_severity" in conds:
                sev_order = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
                inc_rank = sev_order.get(incident.severity, 0)
                req_rank = sev_order.get(conds["min_severity"], 0)
                sev_match = inc_rank >= req_rank

            if cat_match and sev_match:
                for act in pb.actions:
                    action_name = act.get("action")
                    target_type = act.get("target_type", "incident")
                    target_id = act.get("target_id", incident.id)

                    req_hitl = await self.policy_bridge.does_containment_require_approval(
                        organization_id=incident.organization_id,
                        workspace_id=incident.workspace_id,
                        action_type=action_name,
                        target_type=target_type,
                    )

                    try:
                        containment = await self.containment_service.request_containment(
                            incident_id=incident.id,
                            organization_id=incident.organization_id,
                            requested_by=f"playbook:{pb.name}",
                            actor_type="system",
                            data=ContainmentActionCreate(
                                action_type=action_name,
                                target_type=target_type,
                                target_id=str(target_id),
                                reason=f"Automated execution by playbook '{pb.name}'",
                            ),
                            requires_hitl=req_hitl,
                        )
                        executed_actions.append({
                            "playbook_id": pb.id,
                            "playbook_name": pb.name,
                            "action_type": action_name,
                            "status": containment.status,
                        })
                    except Exception as exc:
                        executed_actions.append({
                            "playbook_id": pb.id,
                            "playbook_name": pb.name,
                            "action_type": action_name,
                            "error": str(exc),
                        })

        return executed_actions
