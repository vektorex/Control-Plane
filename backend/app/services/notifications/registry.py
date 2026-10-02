"""
Notification Event Registry for Step 25: Unified Notification & External Delivery Layer.
Allows registering and inspecting supported notification event types safely.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional

from backend.app.services.notifications.constants import (
    DEFAULT_EVENT_SEVERITY,
    MANDATORY_IN_APP_EVENTS,
    NotificationEventType,
    NotificationSeverity,
)


@dataclass
class EventTypeMetadata:
    """Metadata describing a registered notification event type."""
    event_type: str
    label: str
    description: str
    default_severity: str
    default_title_template: str
    default_body_template: str
    mandatory_in_app: bool = False


class NotificationRegistry:
    """
    Registry for notification event types, their default severities,
    default templates, and constraints.
    """

    def __init__(self):
        self._events: Dict[str, EventTypeMetadata] = {}
        self._register_defaults()

    def _register_defaults(self):
        # 1. Workflows
        self.register(
            event_type=NotificationEventType.WORKFLOW_COMPLETED.value,
            label="Workflow Completed",
            description="Triggered when a workflow execution completes successfully.",
            default_severity=NotificationSeverity.SUCCESS.value,
            default_title_template="Workflow '{{workflow.name}}' Completed",
            default_body_template="Workflow '{{workflow.name}}' finished successfully (run ID: {{source.id}}).",
        )
        self.register(
            event_type=NotificationEventType.WORKFLOW_FAILED.value,
            label="Workflow Failed",
            description="Triggered when a workflow execution fails or errors.",
            default_severity=NotificationSeverity.ERROR.value,
            default_title_template="Workflow '{{workflow.name}}' Failed",
            default_body_template="Workflow '{{workflow.name}}' execution encountered an error (run ID: {{source.id}}).",
        )
        self.register(
            event_type=NotificationEventType.WORKFLOW_WAITING_APPROVAL.value,
            label="Approval Required",
            description="Triggered when a workflow run pauses for human-in-the-loop review.",
            default_severity=NotificationSeverity.WARNING.value,
            default_title_template="Approval Required: Workflow '{{workflow.name}}'",
            default_body_template="A human approval checkpoint requires your action to proceed (run ID: {{source.id}}).",
            mandatory_in_app=True,
        )

        # 2. Triggers
        self.register(
            event_type=NotificationEventType.TRIGGER_COMPLETED.value,
            label="Trigger Completed",
            description="Triggered when an automated schedule or webhook trigger executes.",
            default_severity=NotificationSeverity.INFO.value,
            default_title_template="Trigger Executed",
            default_body_template="Automation trigger '{{source.id}}' executed successfully.",
        )
        self.register(
            event_type=NotificationEventType.TRIGGER_FAILED.value,
            label="Trigger Failed",
            description="Triggered when an automated trigger fails to invoke.",
            default_severity=NotificationSeverity.ERROR.value,
            default_title_template="Trigger Execution Failed",
            default_body_template="Automation trigger '{{source.id}}' encountered a failure.",
        )

        # 3. Background Jobs
        self.register(
            event_type=NotificationEventType.JOB_COMPLETED.value,
            label="Job Completed",
            description="Triggered when a background job finishes successfully.",
            default_severity=NotificationSeverity.INFO.value,
            default_title_template="Background Job Completed",
            default_body_template="Job '{{source.id}}' finished execution.",
        )
        self.register(
            event_type=NotificationEventType.JOB_FAILED.value,
            label="Job Failed",
            description="Triggered when a background job fails permanently.",
            default_severity=NotificationSeverity.ERROR.value,
            default_title_template="Background Job Failed",
            default_body_template="Job '{{source.id}}' failed after exhausting retries.",
        )
        self.register(
            event_type=NotificationEventType.JOB_RETRYING.value,
            label="Job Retrying",
            description="Triggered when a background job encounters a transient error and retries.",
            default_severity=NotificationSeverity.WARNING.value,
            default_title_template="Background Job Retrying",
            default_body_template="Job '{{source.id}}' encountered a transient error and is retrying.",
        )

        # 4. Document Processing
        self.register(
            event_type=NotificationEventType.DOCUMENT_COMPLETED.value,
            label="Document Processed",
            description="Triggered when document ingestion and indexing finishes.",
            default_severity=NotificationSeverity.SUCCESS.value,
            default_title_template="Document Processing Completed",
            default_body_template="Document '{{source.id}}' has been parsed and indexed.",
        )
        self.register(
            event_type=NotificationEventType.DOCUMENT_FAILED.value,
            label="Document Processing Failed",
            description="Triggered when document parsing or indexing fails.",
            default_severity=NotificationSeverity.ERROR.value,
            default_title_template="Document Processing Failed",
            default_body_template="Failed to process document '{{source.id}}'.",
        )

        # 5. Evaluation Lab
        self.register(
            event_type=NotificationEventType.EVALUATION_COMPLETED.value,
            label="Evaluation Completed",
            description="Triggered when an evaluation experiment run completes.",
            default_severity=NotificationSeverity.INFO.value,
            default_title_template="Evaluation Run Completed",
            default_body_template="Evaluation experiment '{{source.id}}' completed successfully.",
        )
        self.register(
            event_type=NotificationEventType.EVALUATION_REGRESSION.value,
            label="Evaluation Regression Detected",
            description="Triggered when evaluation lab detects a performance or accuracy drop.",
            default_severity=NotificationSeverity.ERROR.value,
            default_title_template="Regression Detected in Evaluation Run",
            default_body_template="Evaluation experiment '{{source.id}}' detected a benchmark metric regression.",
        )

        # 6. Replay & Debugging
        self.register(
            event_type=NotificationEventType.REPLAY_COMPLETED.value,
            label="Replay Completed",
            description="Triggered when a session replay execution finishes.",
            default_severity=NotificationSeverity.INFO.value,
            default_title_template="Session Replay Completed",
            default_body_template="Replay run '{{source.id}}' completed execution.",
        )
        self.register(
            event_type=NotificationEventType.REPLAY_FAILED.value,
            label="Replay Failed",
            description="Triggered when a session replay execution errors.",
            default_severity=NotificationSeverity.ERROR.value,
            default_title_template="Session Replay Failed",
            default_body_template="Replay run '{{source.id}}' encountered an error during re-execution.",
        )

        # 7. Connectors
        self.register(
            event_type=NotificationEventType.CONNECTOR_COMPLETED.value,
            label="Connector Operation Completed",
            description="Triggered when an external connector sync or action completes.",
            default_severity=NotificationSeverity.INFO.value,
            default_title_template="Connector Operation Succeeded",
            default_body_template="Connector operation '{{source.id}}' finished successfully.",
        )
        self.register(
            event_type=NotificationEventType.CONNECTOR_FAILED.value,
            label="Connector Operation Failed",
            description="Triggered when an external connector sync or action fails.",
            default_severity=NotificationSeverity.ERROR.value,
            default_title_template="Connector Operation Failed",
            default_body_template="Connector operation '{{source.id}}' encountered a failure.",
        )

        # 8. System Warning
        self.register(
            event_type=NotificationEventType.SYSTEM_WARNING.value,
            label="System Warning",
            description="Critical system notices, policy warnings, or resource threshold alerts.",
            default_severity=NotificationSeverity.WARNING.value,
            default_title_template="System Notice",
            default_body_template="{{notification.body}}",
            mandatory_in_app=True,
        )

    def register(
        self,
        event_type: str,
        label: str,
        description: str,
        default_severity: str,
        default_title_template: str,
        default_body_template: str,
        mandatory_in_app: bool = False,
    ) -> None:
        """Register a new event type into the registry."""
        is_mandatory = mandatory_in_app or (event_type in MANDATORY_IN_APP_EVENTS)
        self._events[event_type] = EventTypeMetadata(
            event_type=event_type,
            label=label,
            description=description,
            default_severity=default_severity,
            default_title_template=default_title_template,
            default_body_template=default_body_template,
            mandatory_in_app=is_mandatory,
        )

    def get(self, event_type: str) -> Optional[EventTypeMetadata]:
        return self._events.get(event_type)

    def is_valid_event_type(self, event_type: str) -> bool:
        return event_type in self._events

    def list_events(self) -> List[Dict]:
        return [
            {
                "event_type": item.event_type,
                "label": item.label,
                "description": item.description,
                "default_severity": item.default_severity,
                "default_title_template": item.default_title_template,
                "default_body_template": item.default_body_template,
                "mandatory_in_app": item.mandatory_in_app,
            }
            for item in self._events.values()
        ]


# Singleton instance
notification_registry = NotificationRegistry()
