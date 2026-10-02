"""
Notification Event Bus & Dispatcher for Step 25: Notifications & External Delivery Layer.
Normalizes system events into notification events and delegates to NotificationService.
"""
import logging
from typing import Any, Dict, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.database import AsyncSessionLocal
from backend.app.services.notifications.constants import (
    DEFAULT_EVENT_SEVERITY,
    NotificationEventType,
    NotificationSeverity,
)
from backend.app.services.notifications.registry import notification_registry
from backend.app.services.notifications.service import NotificationService
from backend.app.services.notifications.templates import NotificationTemplateEngine

logger = logging.getLogger(__name__)


class NotificationEvent(BaseModel):
    """Normalized payload representing a system event eligible for notification."""
    workspace_id: UUID
    event_type: str
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    severity: Optional[str] = None
    project_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotificationEventBus:
    """
    Authoritative event bus receiving system events from WorkflowExecutor,
    TriggerService, JobWorker, HITL, Connectors, Evaluation, and Replay.
    Normalizes, resolves recipients, applies policies, and enqueues deliveries.
    """

    @classmethod
    async def publish(
        cls,
        event: Union[NotificationEvent, Dict[str, Any]],
        session: Optional[AsyncSession] = None,
    ) -> Optional[UUID]:
        """
        Publishes a system event to create a notification and trigger channel deliveries.
        Accepts either a NotificationEvent or a dictionary.
        Returns the created notification ID or None on failure.
        """
        if isinstance(event, dict):
            # Normalize dictionary into NotificationEvent
            ev_data = event.copy()
            # Handle aliases
            if "metadata_json" in ev_data and "metadata" not in ev_data:
                ev_data["metadata"] = ev_data.pop("metadata_json")
            if "data" in ev_data and "metadata" not in ev_data:
                ev_data["metadata"] = ev_data.pop("data")
            ev_obj = NotificationEvent.model_validate(ev_data)
        else:
            ev_obj = event

        # Resolve templates if title or body is missing
        event_meta = notification_registry.get(ev_obj.event_type)
        severity = ev_obj.severity or (
            event_meta.default_severity if event_meta else DEFAULT_EVENT_SEVERITY.get(ev_obj.event_type, NotificationSeverity.INFO.value)
        )

        template_ctx = {
            "source": {
                "type": ev_obj.source_type or "",
                "id": ev_obj.source_id or "",
            },
            "job": {
                "id": ev_obj.source_id or "",
                "status": ev_obj.metadata.get("status", ""),
            },
            "workflow": {
                "id": ev_obj.source_id or "",
                "name": ev_obj.metadata.get("workflow_name", ev_obj.metadata.get("name", "Workflow")),
            },
            "project": {
                "id": str(ev_obj.project_id or ""),
                "name": ev_obj.metadata.get("project_name", "Project"),
            },
            "data": ev_obj.metadata,
        }

        title = ev_obj.title
        if not title:
            title_tpl = event_meta.default_title_template if event_meta else f"Event: {ev_obj.event_type}"
            title = NotificationTemplateEngine.render(title_tpl, template_ctx)

        body = ev_obj.body
        if not body:
            body_tpl = event_meta.default_body_template if event_meta else f"Event {ev_obj.event_type} occurred."
            body = NotificationTemplateEngine.render(body_tpl, template_ctx)

        async def _dispatch_with_session(db_session: AsyncSession) -> Optional[UUID]:
            service = NotificationService(db_session)
            created = await service.create_notification(
                workspace_id=ev_obj.workspace_id,
                event_type=ev_obj.event_type,
                title=title,
                body=body,
                severity=severity,
                project_id=ev_obj.project_id,
                user_id=ev_obj.user_id,
                source_type=ev_obj.source_type,
                source_id=ev_obj.source_id,
                metadata_json=ev_obj.metadata,
            )
            return created.id

        try:
            if session:
                return await _dispatch_with_session(session)
            else:
                async with AsyncSessionLocal() as fresh_session:
                    res_id = await _dispatch_with_session(fresh_session)
                    await fresh_session.commit()
                    return res_id
        except Exception as exc:
            logger.error(f"[NotificationEventBus] Failed to publish event {ev_obj.event_type}: {exc}", exc_info=True)
            return None


# Helper instance
event_bus = NotificationEventBus()
