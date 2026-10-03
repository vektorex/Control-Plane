"""
GovernanceAuditService: emits structured audit records to the EventPublisher for
all significant governance events. Never records secrets or raw sensitive inputs. Step 32.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from backend.app.core.logging import logger
from backend.app.services.governance.constants import GovernanceDecisionType
from backend.app.services.governance.sanitizer import GovernanceSanitizer


class GovernanceAuditService:
    """
    Records factual governance audit events.
    All payloads are sanitized before emission.
    """

    AUDIT_EVENTS = {
        "policy_created": "governance.policy_created",
        "policy_updated": "governance.policy_updated",
        "policy_activated": "governance.policy_activated",
        "policy_deactivated": "governance.policy_deactivated",
        "policy_simulated": "governance.policy_simulated",
        "decision_denied": "governance.decision_denied",
        "approval_required": "governance.approval_required",
        "verification_required": "governance.verification_required",
        "budget_blocked": "governance.budget_blocked",
    }

    @staticmethod
    async def emit(
        event_key: str,
        organization_id: uuid.UUID,
        workspace_id: Optional[uuid.UUID],
        actor_id: Optional[uuid.UUID],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Emits a governance audit event via the EventPublisher.
        Metadata is sanitized before emission.
        """
        event_type = GovernanceAuditService.AUDIT_EVENTS.get(event_key)
        if not event_type:
            logger.warning("GovernanceAudit: unknown event key '%s'", event_key)
            return

        safe_metadata = GovernanceSanitizer.sanitize_dict(metadata or {})

        try:
            # Import inside to avoid circular imports at module load time
            from backend.app.services.events.publisher import EventPublisher
            from backend.app.services.events.constants import AggregateType, ActorType

            await EventPublisher.publish(
                event_type=event_type,
                aggregate_type=AggregateType.SYSTEM.value,
                aggregate_id=str(organization_id),
                organization_id=str(organization_id),
                workspace_id=str(workspace_id) if workspace_id else None,
                actor_id=str(actor_id) if actor_id else None,
                actor_type=ActorType.SYSTEM.value,
                payload=safe_metadata,
            )
        except Exception as exc:
            logger.warning("GovernanceAudit: failed to emit event '%s': %s", event_type, exc)

    @staticmethod
    async def record_decision(
        decision: GovernanceDecisionType,
        enforcement_point: str,
        reasons: List[str],
        organization_id: uuid.UUID,
        workspace_id: Optional[uuid.UUID],
        actor_id: Optional[uuid.UUID],
    ) -> None:
        if decision == GovernanceDecisionType.DENY:
            await GovernanceAuditService.emit(
                "decision_denied",
                organization_id=organization_id,
                workspace_id=workspace_id,
                actor_id=actor_id,
                metadata={
                    "enforcement_point": enforcement_point,
                    "reasons": reasons[:5],
                },
            )
        elif decision == GovernanceDecisionType.REQUIRE_APPROVAL:
            await GovernanceAuditService.emit(
                "approval_required",
                organization_id=organization_id,
                workspace_id=workspace_id,
                actor_id=actor_id,
                metadata={"enforcement_point": enforcement_point},
            )
        elif decision == GovernanceDecisionType.REQUIRE_VERIFICATION:
            await GovernanceAuditService.emit(
                "verification_required",
                organization_id=organization_id,
                workspace_id=workspace_id,
                actor_id=actor_id,
                metadata={"enforcement_point": enforcement_point},
            )
