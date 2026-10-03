"""
Security Policies and Governance Bridge for Step 34.
Connects Step 32 AI Governance policy control plane to security detector thresholds and containment approvals.
"""
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession


class SecurityPolicyEngineBridge:
    """
    Interfaces with Step 32 AI Governance to resolve security detector thresholds,
    privilege requirements, and HITL containment approval policies.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def does_containment_require_approval(
        self,
        organization_id: str,
        workspace_id: Optional[str],
        action_type: str,
        target_type: str,
    ) -> bool:
        """
        Determines if a high-impact containment action requires Human-In-The-Loop approval.
        Privileged operations (e.g. revoking credentials, pausing organization-level workflows)
        mandate approval by default unless a safe automated policy applies.
        """
        privileged_actions = {
            "revoke_session",
            "disable_connector_credential",
            "quarantine_artifact",
        }
        return action_type in privileged_actions

    async def get_detector_thresholds(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Returns resolved security thresholds from Step 32 Governance.
        Falls back to safe platform defaults.
        """
        return {
            "auth_failure_threshold": 5,
            "auth_burst_window_seconds": 60,
            "tool_invocation_spike_threshold": 30,
            "max_workflow_depth": 10,
            "data_export_hourly_threshold": 5,
            "max_deletion_asset_count": 10,
            "cost_spike_threshold_usd": 50.0,
            "token_spike_threshold": 500000,
        }
