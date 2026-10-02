"""
Centralized Event Registry for Step 26: Unified Event Bus.
Maintains metadata for registered system events and permits extension
without modifying core infrastructure.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from backend.app.services.events.constants import AggregateType, SystemEventType


@dataclass
class EventTypeDefinition:
    event_type: str
    aggregate_type: str
    description: str
    is_auditable: bool = False


class EventRegistry:
    """
    Catalog of all approved system events.
    """

    def __init__(self):
        self._registry: Dict[str, EventTypeDefinition] = {}
        self._register_defaults()

    def register(
        self,
        event_type: str,
        aggregate_type: str,
        description: str,
        is_auditable: bool = False,
    ) -> None:
        self._registry[event_type] = EventTypeDefinition(
            event_type=event_type,
            aggregate_type=aggregate_type,
            description=description,
            is_auditable=is_auditable,
        )

    def get(self, event_type: str) -> Optional[EventTypeDefinition]:
        return self._registry.get(event_type)

    def is_registered(self, event_type: str) -> bool:
        return event_type in self._registry

    def list_all(self) -> List[EventTypeDefinition]:
        return list(self._registry.values())

    def _register_defaults(self):
        # 1. Job events
        self.register(SystemEventType.JOB_CREATED.value, AggregateType.JOB.value, "Background job created in durable store")
        self.register(SystemEventType.JOB_QUEUED.value, AggregateType.JOB.value, "Job enqueued for worker claiming")
        self.register(SystemEventType.JOB_STARTED.value, AggregateType.JOB.value, "Job claimed by worker and began execution")
        self.register(SystemEventType.JOB_PROGRESS.value, AggregateType.JOB.value, "Job updated percentage or progress stage")
        self.register(SystemEventType.JOB_RETRYING.value, AggregateType.JOB.value, "Job encountered transient error and will retry")
        self.register(SystemEventType.JOB_CANCEL_REQUESTED.value, AggregateType.JOB.value, "Cancellation requested for running job")
        self.register(SystemEventType.JOB_CANCELLED.value, AggregateType.JOB.value, "Job cancelled successfully")
        self.register(SystemEventType.JOB_COMPLETED.value, AggregateType.JOB.value, "Job execution completed successfully")
        self.register(SystemEventType.JOB_FAILED.value, AggregateType.JOB.value, "Job reached permanent failure state")
        self.register(SystemEventType.JOB_RECOVERED.value, AggregateType.JOB.value, "Job recovered from expired worker lease")

        # 2. Workflow events
        self.register(SystemEventType.WORKFLOW_STARTED.value, AggregateType.WORKFLOW.value, "Workflow execution initiated", is_auditable=True)
        self.register(SystemEventType.WORKFLOW_STEP_STARTED.value, AggregateType.WORKFLOW.value, "Workflow step execution started")
        self.register(SystemEventType.WORKFLOW_STEP_COMPLETED.value, AggregateType.WORKFLOW.value, "Workflow step execution finished")
        self.register(SystemEventType.WORKFLOW_WAITING_FOR_APPROVAL.value, AggregateType.WORKFLOW.value, "Workflow paused pending human review")
        self.register(SystemEventType.WORKFLOW_RESUMED.value, AggregateType.WORKFLOW.value, "Workflow resumed after human intervention")
        self.register(SystemEventType.WORKFLOW_COMPLETED.value, AggregateType.WORKFLOW.value, "Workflow execution completed successfully", is_auditable=True)
        self.register(SystemEventType.WORKFLOW_FAILED.value, AggregateType.WORKFLOW.value, "Workflow execution failed", is_auditable=True)

        # 3. Trigger events
        self.register(SystemEventType.TRIGGER_CREATED.value, AggregateType.TRIGGER.value, "Trigger configured for workflow", is_auditable=True)
        self.register(SystemEventType.TRIGGER_UPDATED.value, AggregateType.TRIGGER.value, "Trigger configuration updated", is_auditable=True)
        self.register(SystemEventType.TRIGGER_PAUSED.value, AggregateType.TRIGGER.value, "Trigger temporarily paused", is_auditable=True)
        self.register(SystemEventType.TRIGGER_RESUMED.value, AggregateType.TRIGGER.value, "Trigger resumed active schedule/webhook", is_auditable=True)
        self.register(SystemEventType.TRIGGER_FIRED.value, AggregateType.TRIGGER.value, "Trigger evaluated positive and fired")
        self.register(SystemEventType.TRIGGER_COMPLETED.value, AggregateType.TRIGGER.value, "Trigger evaluation completed")
        self.register(SystemEventType.TRIGGER_FAILED.value, AggregateType.TRIGGER.value, "Trigger evaluation failed with error")

        # 4. Document processing events
        self.register(SystemEventType.DOCUMENT_PROCESSING_STARTED.value, AggregateType.DOCUMENT.value, "Document parsing initiated")
        self.register(SystemEventType.DOCUMENT_PROCESSING_PROGRESS.value, AggregateType.DOCUMENT.value, "Document chunking/embedding progress")
        self.register(SystemEventType.DOCUMENT_PROCESSING_COMPLETED.value, AggregateType.DOCUMENT.value, "Document indexed into vector store")
        self.register(SystemEventType.DOCUMENT_PROCESSING_FAILED.value, AggregateType.DOCUMENT.value, "Document extraction failed")

        # 5. Evaluation events
        self.register(SystemEventType.EVALUATION_STARTED.value, AggregateType.EVALUATION.value, "Evaluation benchmark run started")
        self.register(SystemEventType.EVALUATION_COMPLETED.value, AggregateType.EVALUATION.value, "Evaluation experiment completed")
        self.register(SystemEventType.EVALUATION_REGRESSION_DETECTED.value, AggregateType.EVALUATION.value, "Evaluation regression metric detected")
        self.register(SystemEventType.EVALUATION_FAILED.value, AggregateType.EVALUATION.value, "Evaluation run failed")

        # 6. Replay events
        self.register(SystemEventType.REPLAY_STARTED.value, AggregateType.REPLAY.value, "Execution replay started")
        self.register(SystemEventType.REPLAY_PROGRESS.value, AggregateType.REPLAY.value, "Execution replay step progress")
        self.register(SystemEventType.REPLAY_COMPLETED.value, AggregateType.REPLAY.value, "Execution replay completed")
        self.register(SystemEventType.REPLAY_FAILED.value, AggregateType.REPLAY.value, "Execution replay encountered divergence or failure")

        # 7. Connector events
        self.register(SystemEventType.CONNECTOR_STARTED.value, AggregateType.CONNECTOR.value, "External connector sync started")
        self.register(SystemEventType.CONNECTOR_COMPLETED.value, AggregateType.CONNECTOR.value, "External connector sync completed")
        self.register(SystemEventType.CONNECTOR_FAILED.value, AggregateType.CONNECTOR.value, "External connector sync failed")

        # 8. HITL events
        self.register(SystemEventType.APPROVAL_REQUESTED.value, AggregateType.APPROVAL.value, "Human review requested")
        self.register(SystemEventType.APPROVAL_APPROVED.value, AggregateType.APPROVAL.value, "Intervention request approved by user", is_auditable=True)
        self.register(SystemEventType.APPROVAL_REJECTED.value, AggregateType.APPROVAL.value, "Intervention request rejected by user", is_auditable=True)
        self.register(SystemEventType.APPROVAL_EXPIRED.value, AggregateType.APPROVAL.value, "Intervention request timed out")

        # 9. Notification events
        self.register(SystemEventType.NOTIFICATION_CREATED.value, AggregateType.NOTIFICATION.value, "In-app notification created")
        self.register(SystemEventType.NOTIFICATION_DELIVERY_STARTED.value, AggregateType.NOTIFICATION.value, "External delivery transmission started")
        self.register(SystemEventType.NOTIFICATION_DELIVERY_COMPLETED.value, AggregateType.NOTIFICATION.value, "External delivery delivered successfully")
        self.register(SystemEventType.NOTIFICATION_DELIVERY_FAILED.value, AggregateType.NOTIFICATION.value, "External delivery failed")

        # 10. System events
        self.register(SystemEventType.SYSTEM_WARNING.value, AggregateType.SYSTEM.value, "System alert or capacity threshold warning", is_auditable=True)
        self.register(SystemEventType.SYSTEM_ERROR.value, AggregateType.SYSTEM.value, "Critical system error", is_auditable=True)


# Global singleton registry
event_registry = EventRegistry()
