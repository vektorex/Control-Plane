"""
Audit logging and event emission for Step 27: Multi-Tenant Organizations, Teams, Roles & Access Control.
Never logs sensitive tokens, credentials, or secrets.
"""
from typing import Any, Dict, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.access_control.constants import AccessControlAuditEvent
from backend.app.services.events.constants import ActorType, AggregateType
from backend.app.services.events.schemas import EventPublishRequest


class AccessControlAudit:
    """
    Emits auditable security events for all organization, membership, and permission state transitions.
    Integrates directly with Step 26 EventPublisher and structured security logging.
    """

    @classmethod
    async def log_action(
        cls,
        session: AsyncSession,
        action: AccessControlAuditEvent,
        actor_user_id: UUID,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        target_user_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Records an auditable access control action.
        Sanitizes all sensitive parameters before logging and publication.
        """
        safe_details = {k: v for k, v in (details or {}).items() if not any(
            sec in k.lower() for sec in ["secret", "token", "password", "key", "credential", "auth"]
        )}

        logger.info(
            f"[AccessControlAudit] ACTION='{action.value}' ACTOR='{actor_user_id}' "
            f"ORG='{organization_id}' WS='{workspace_id}' PROJ='{project_id}' "
            f"TARGET='{target_user_id}' DETAILS={safe_details}"
        )

        # If a workspace_id is present, publish via Unified Event Bus (Step 26)
        if workspace_id:
            try:
                from backend.app.services.events.publisher import EventPublisher
                publisher = EventPublisher(session)
                req = EventPublishRequest(
                    workspace_id=workspace_id,
                    project_id=project_id,
                    actor_type=ActorType.USER.value,
                    actor_id=str(actor_user_id),
                    event_type=action.value,
                    aggregate_type=AggregateType.SYSTEM.value,
                    aggregate_id=str(organization_id),
                    payload={
                        "action": action.value,
                        "organization_id": str(organization_id),
                        "target_user_id": str(target_user_id) if target_user_id else None,
                        **safe_details,
                    },
                    metadata={"source": "access_control"},
                )
                await publisher.publish(req)
            except Exception as e:
                logger.warning(f"[AccessControlAudit] Event publication suppressed: {e}")
