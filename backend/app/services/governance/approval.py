"""
GovernanceApprovalService: creates HITL approval requests for governance decisions.
Strictly reuses existing Step 18 HITL system; creates no new approval mechanism. Step 32.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from backend.app.core.logging import logger
from backend.app.services.governance.constants import GovernanceDecisionType


class GovernanceApprovalService:
    """
    Bridges governance REQUIRE_APPROVAL decisions to the existing HITL system.
    Approval cannot modify the original governance decision.
    After approval, the governance policy is re-evaluated if staleness window has passed.
    """

    @staticmethod
    def should_create_hitl_request(decision: GovernanceDecisionType) -> bool:
        return decision == GovernanceDecisionType.REQUIRE_APPROVAL

    @staticmethod
    def build_hitl_payload(
        enforcement_point: str,
        reasons: list[str],
        required_approvals: list[str],
        organization_id: uuid.UUID,
        workspace_id: Optional[uuid.UUID],
        project_id: Optional[uuid.UUID],
        user_id: Optional[uuid.UUID],
    ) -> dict:
        """
        Builds a minimal, sanitized payload for creating a HumanInterventionRequest.
        Returns a dict matching the HITL service's create request schema.
        Secrets and internal policy logic are never included.
        """
        return {
            "reason": "; ".join(reasons[:5]) or "Governance approval required",
            "context": {
                "enforcement_point": enforcement_point,
                "required_approvals": required_approvals[:10],
                "source": "governance",
            },
            "timeout_hours": 24,
        }

    @staticmethod
    def build_verification_payload(
        enforcement_point: str,
        required_verifications: list[str],
    ) -> dict:
        """
        Builds a verification request payload to route into the Evaluation Lab.
        Never exposes internal security logic.
        """
        return {
            "enforcement_point": enforcement_point,
            "required_verifications": required_verifications,
            "source": "governance",
        }
