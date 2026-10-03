"""
Constants and Enums for Step 26: Unified Event Bus and Real-Time Execution Updates.
"""
from enum import Enum


class ActorType(str, Enum):
    USER = "user"
    SYSTEM = "system"
    WORKER = "worker"
    CONNECTOR = "connector"
    SCHEDULER = "scheduler"


class AggregateType(str, Enum):
    WORKFLOW = "workflow"
    JOB = "job"
    TRIGGER = "trigger"
    DOCUMENT = "document"
    EVALUATION = "evaluation"
    REPLAY = "replay"
    CONNECTOR = "connector"
    APPROVAL = "approval"
    NOTIFICATION = "notification"
    SYSTEM = "system"
    PROMPT = "prompt"
    PROMPT_EXPERIMENT = "prompt_experiment"
    GRAPH = "graph"
    ARTIFACT = "artifact"
    CACHE = "cache"
    GOVERNANCE = "governance"
    DATA_GOVERNANCE = "data_governance"
    SECURITY = "security"
    RELIABILITY = "reliability"
    RECOVERY = "recovery"
    DEVELOPER = "developer"
    MARKETPLACE = "marketplace"
    COLLABORATION = "collaboration"



class EventDeliveryStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    RETRYING = "retrying"
    FAILED = "failed"


class EventVisibility(str, Enum):
    WORKSPACE = "workspace"
    PROJECT = "project"
    USER = "user"
    SYSTEM = "system"


class SystemEventType(str, Enum):
    # Job events
    JOB_CREATED = "job.created"
    JOB_QUEUED = "job.queued"
    JOB_STARTED = "job.started"
    JOB_PROGRESS = "job.progress"
    JOB_RETRYING = "job.retrying"
    JOB_CANCEL_REQUESTED = "job.cancel_requested"
    JOB_CANCELLED = "job.cancelled"
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    JOB_RECOVERED = "job.recovered"

    # Workflow events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_STEP_STARTED = "workflow.step_started"
    WORKFLOW_STEP_COMPLETED = "workflow.step_completed"
    WORKFLOW_WAITING_FOR_APPROVAL = "workflow.waiting_for_approval"
    WORKFLOW_RESUMED = "workflow.resumed"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"

    # Trigger events
    TRIGGER_CREATED = "trigger.created"
    TRIGGER_UPDATED = "trigger.updated"
    TRIGGER_PAUSED = "trigger.paused"
    TRIGGER_RESUMED = "trigger.resumed"
    TRIGGER_FIRED = "trigger.fired"
    TRIGGER_COMPLETED = "trigger.completed"
    TRIGGER_FAILED = "trigger.failed"

    # Document events
    DOCUMENT_PROCESSING_STARTED = "document.processing_started"
    DOCUMENT_PROCESSING_PROGRESS = "document.processing_progress"
    DOCUMENT_PROCESSING_COMPLETED = "document.processing_completed"
    DOCUMENT_PROCESSING_FAILED = "document.processing_failed"

    # Evaluation events
    EVALUATION_STARTED = "evaluation.started"
    EVALUATION_COMPLETED = "evaluation.completed"
    EVALUATION_REGRESSION_DETECTED = "evaluation.regression_detected"
    EVALUATION_FAILED = "evaluation.failed"

    # Replay events
    REPLAY_STARTED = "replay.started"
    REPLAY_PROGRESS = "replay.progress"
    REPLAY_COMPLETED = "replay.completed"
    REPLAY_FAILED = "replay.failed"

    # Connector events
    CONNECTOR_STARTED = "connector.started"
    CONNECTOR_COMPLETED = "connector.completed"
    CONNECTOR_FAILED = "connector.failed"

    # HITL events
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_APPROVED = "approval.approved"
    APPROVAL_REJECTED = "approval.rejected"
    APPROVAL_EXPIRED = "approval.expired"

    # Notification events
    NOTIFICATION_CREATED = "notification.created"
    NOTIFICATION_DELIVERY_STARTED = "notification.delivery_started"
    NOTIFICATION_DELIVERY_COMPLETED = "notification.delivery_completed"
    NOTIFICATION_DELIVERY_FAILED = "notification.delivery_failed"

    # System events
    SYSTEM_WARNING = "system.warning"
    SYSTEM_ERROR = "system.error"

    # Step 27 Access Control & Organization events
    ORGANIZATION_CREATED = "organization.created"
    ORGANIZATION_UPDATED = "organization.updated"
    ORGANIZATION_ARCHIVED = "organization.archived"
    MEMBER_INVITED = "member.invited"
    MEMBER_JOINED = "member.joined"
    MEMBER_ROLE_CHANGED = "member.role_changed"
    MEMBER_SUSPENDED = "member.suspended"
    MEMBER_REMOVED = "member.removed"
    WORKSPACE_CREATED = "workspace.created"
    WORKSPACE_UPDATED = "workspace.updated"
    WORKSPACE_ARCHIVED = "workspace.archived"
    WORKSPACE_MEMBER_ADDED = "workspace.member_added"
    WORKSPACE_MEMBER_UPDATED = "workspace.member_updated"
    WORKSPACE_MEMBER_REMOVED = "workspace.member_removed"
    PROJECT_MEMBER_ADDED = "project.member_added"
    PROJECT_MEMBER_UPDATED = "project.member_updated"
    PROJECT_MEMBER_REMOVED = "project.member_removed"
    PROJECT_ACCESS_CHANGED = "project.access_changed"
    OWNERSHIP_TRANSFERRED = "ownership.transferred"

    # Step 28 Prompt Management & Experimentation events
    PROMPT_CREATED = "prompt.created"
    PROMPT_VERSION_CREATED = "prompt.version_created"
    PROMPT_VERSION_PUBLISHED = "prompt.version_published"
    PROMPT_RELEASE_CHANGED = "prompt.release_changed"
    PROMPT_ROLLED_BACK = "prompt.rolled_back"
    PROMPT_ARCHIVED = "prompt.archived"
    PROMPT_EXPERIMENT_STARTED = "prompt.experiment_started"
    PROMPT_EXPERIMENT_PAUSED = "prompt.experiment_paused"
    PROMPT_EXPERIMENT_COMPLETED = "prompt.experiment_completed"

    # Step 29 Knowledge Graph events
    GRAPH_ENTITY_CREATED = "graph.entity_created"
    GRAPH_ENTITY_UPDATED = "graph.entity_updated"
    GRAPH_ENTITY_ARCHIVED = "graph.entity_archived"
    GRAPH_RELATIONSHIP_CREATED = "graph.relationship_created"
    GRAPH_RELATIONSHIP_REMOVED = "graph.relationship_removed"
    GRAPH_PROPOSAL_CREATED = "graph.proposal_created"
    GRAPH_PROPOSAL_APPROVED = "graph.proposal_approved"
    GRAPH_PROPOSAL_REJECTED = "graph.proposal_rejected"
    GRAPH_CONFLICT_CREATED = "graph.conflict_created"
    GRAPH_CONFLICT_RESOLVED = "graph.conflict_resolved"

    # Step 30 Multimodal Artifact events
    ARTIFACT_PROCESSING_STARTED = "artifact.processing_started"
    ARTIFACT_PROCESSING_PROGRESS = "artifact.processing_progress"
    ARTIFACT_PROCESSING_COMPLETED = "artifact.processing_completed"
    ARTIFACT_PROCESSING_FAILED = "artifact.processing_failed"
    ARTIFACT_ANALYSIS_STARTED = "artifact.analysis_started"
    ARTIFACT_ANALYSIS_COMPLETED = "artifact.analysis_completed"
    ARTIFACT_ANALYSIS_FAILED = "artifact.analysis_failed"

    # Step 31 Semantic Cache events
    CACHE_ENTRY_CREATED = "cache.entry_created"
    CACHE_HIT = "cache.hit"
    CACHE_MISS = "cache.miss"
    CACHE_INVALIDATED = "cache.invalidated"
    CACHE_REFRESH_STARTED = "cache.refresh_started"
    CACHE_REFRESH_COMPLETED = "cache.refresh_completed"
    CACHE_REFRESH_FAILED = "cache.refresh_failed"

    # Step 32 Governance events
    GOVERNANCE_POLICY_CREATED = "governance.policy_created"
    GOVERNANCE_POLICY_UPDATED = "governance.policy_updated"
    GOVERNANCE_POLICY_ACTIVATED = "governance.policy_activated"
    GOVERNANCE_POLICY_DEACTIVATED = "governance.policy_deactivated"
    GOVERNANCE_POLICY_SIMULATED = "governance.policy_simulated"
    GOVERNANCE_DECISION_DENIED = "governance.decision_denied"
    GOVERNANCE_APPROVAL_REQUIRED = "governance.approval_required"
    GOVERNANCE_VERIFICATION_REQUIRED = "governance.verification_required"
    GOVERNANCE_BUDGET_BLOCKED = "governance.budget_blocked"
    GOVERNANCE_BUDGET_THRESHOLD_REACHED = "governance.budget_threshold_reached"

    # Step 33 Data Governance events
    DATA_ASSET_CREATED = "data.asset.created"
    DATA_ASSET_CLASSIFIED = "data.asset.classified"
    DATA_ASSET_ACCESSED = "data.asset.accessed"
    DATA_ASSET_UPDATED = "data.asset.updated"
    DATA_ASSET_RETENTION_DUE = "data.asset.retention_due"
    DATA_LIFECYCLE_STARTED = "data.lifecycle.started"
    DATA_LIFECYCLE_COMPLETED = "data.lifecycle.completed"
    DATA_LIFECYCLE_FAILED = "data.lifecycle.failed"
    DATA_DELETION_REQUESTED = "data.deletion.requested"
    DATA_DELETION_COMPLETED = "data.deletion.completed"
    DATA_DELETION_BLOCKED = "data.deletion.blocked"
    DATA_EXPORT_REQUESTED = "data.export.requested"
    DATA_EXPORT_COMPLETED = "data.export.completed"
    DATA_PRIVACY_REQUEST_CREATED = "data.privacy_request.created"
    DATA_PRIVACY_REQUEST_COMPLETED = "data.privacy_request.completed"
    DATA_LEGAL_HOLD_CREATED = "data.legal_hold.created"
    DATA_LEGAL_HOLD_RELEASED = "data.legal_hold.released"
    DATA_EVIDENCE_CREATED = "data.evidence.created"

    # Step 34 Security Operations events
    SECURITY_SIGNAL_CREATED = "security.signal.created"
    SECURITY_INCIDENT_CREATED = "security.incident.created"
    SECURITY_INCIDENT_UPDATED = "security.incident.updated"
    SECURITY_CONTAINMENT_REQUESTED = "security.containment.requested"
    SECURITY_CONTAINMENT_COMPLETED = "security.containment.completed"

    # Step 35 Reliability & Resilience events
    RELIABILITY_COMPONENT_DEGRADED = "reliability.component.degraded"
    RELIABILITY_COMPONENT_RECOVERED = "reliability.component.recovered"
    RELIABILITY_DEPENDENCY_FAILED = "reliability.dependency.failed"
    RELIABILITY_DEPENDENCY_RECOVERED = "reliability.dependency.recovered"
    RELIABILITY_JOB_RETRYING = "reliability.job.retrying"
    RELIABILITY_JOB_RECOVERED = "reliability.job.recovered"
    RELIABILITY_JOB_FAILED = "reliability.job.failed"
    RELIABILITY_WORKFLOW_PAUSED = "reliability.workflow.paused"
    RELIABILITY_WORKFLOW_RESUMED = "reliability.workflow.resumed"
    RELIABILITY_FALLBACK_USED = "reliability.fallback.used"
    RELIABILITY_DEGRADATION_APPLIED = "reliability.degradation.applied"
    RELIABILITY_CHECKPOINT_CREATED = "reliability.checkpoint.created"
    RELIABILITY_CHECKPOINT_INVALIDATED = "reliability.checkpoint.invalidated"
    RELIABILITY_RESUME_STARTED = "reliability.resume.started"
    RELIABILITY_RESUME_COMPLETED = "reliability.resume.completed"
    RELIABILITY_RESUME_FAILED = "reliability.resume.failed"
    RELIABILITY_CIRCUIT_OPENED = "reliability.circuit.opened"
    RELIABILITY_CIRCUIT_CLOSED = "reliability.circuit.closed"

    # Step 36 Disaster Recovery & Business Continuity events
    RECOVERY_BACKUP_STARTED = "recovery.backup.started"
    RECOVERY_BACKUP_COMPLETED = "recovery.backup.completed"
    RECOVERY_BACKUP_FAILED = "recovery.backup.failed"
    RECOVERY_BACKUP_VERIFIED = "recovery.backup.verified"
    RECOVERY_BACKUP_INVALID = "recovery.backup.invalid"
    RECOVERY_RESTORE_PLANNED = "recovery.restore.planned"
    RECOVERY_RESTORE_APPROVED = "recovery.restore.approved"
    RECOVERY_RESTORE_STARTED = "recovery.restore.started"
    RECOVERY_RESTORE_COMPLETED = "recovery.restore.completed"
    RECOVERY_RESTORE_FAILED = "recovery.restore.failed"
    RECOVERY_EXERCISE_STARTED = "recovery.exercise.started"
    RECOVERY_EXERCISE_COMPLETED = "recovery.exercise.completed"
    RECOVERY_EXERCISE_FAILED = "recovery.exercise.failed"
    RECOVERY_READINESS_CHANGED = "recovery.readiness.changed"

    # Step 37 Developer Platform & Public API events
    DEVELOPER_APPLICATION_CREATED = "developer.application.created"
    DEVELOPER_APPLICATION_UPDATED = "developer.application.updated"
    DEVELOPER_APPLICATION_SUSPENDED = "developer.application.suspended"
    DEVELOPER_CREDENTIAL_CREATED = "developer.credential.created"
    DEVELOPER_CREDENTIAL_ROTATED = "developer.credential.rotated"
    DEVELOPER_CREDENTIAL_REVOKED = "developer.credential.revoked"
    DEVELOPER_WEBHOOK_CREATED = "developer.webhook.created"
    DEVELOPER_WEBHOOK_FAILED = "developer.webhook.failed"
    DEVELOPER_API_RATE_LIMITED = "developer.api.rate_limited"
    DEVELOPER_API_POLICY_DENIED = "developer.api.policy_denied"

    # Step 38 Marketplace events
    MARKETPLACE_PACKAGE_CREATED = "marketplace.package.created"
    MARKETPLACE_PACKAGE_VERSION_CREATED = "marketplace.package.version.created"
    MARKETPLACE_PACKAGE_PUBLISHED = "marketplace.package.published"
    MARKETPLACE_PACKAGE_SUSPENDED = "marketplace.package.suspended"
    MARKETPLACE_PACKAGE_REVOKED = "marketplace.package.revoked"
    MARKETPLACE_PACKAGE_INSTALLED = "marketplace.package.installed"
    MARKETPLACE_PACKAGE_UPDATED = "marketplace.package.updated"
    MARKETPLACE_PACKAGE_ROLLED_BACK = "marketplace.package.rolled_back"
    MARKETPLACE_PACKAGE_FORKED = "marketplace.package.forked"
    MARKETPLACE_REVIEW_CREATED = "marketplace.review.created"
    MARKETPLACE_SECURITY_WARNING = "marketplace.security.warning"

    # Step 39 Multi-User Collaboration events
    COLLABORATION_SESSION_CREATED = "collaboration.session.created"
    COLLABORATION_PARTICIPANT_JOINED = "collaboration.participant.joined"
    COLLABORATION_PARTICIPANT_LEFT = "collaboration.participant.left"
    COLLABORATION_PRESENCE_UPDATED = "collaboration.presence.updated"
    COLLABORATION_COMMENT_CREATED = "collaboration.comment.created"
    COLLABORATION_COMMENT_UPDATED = "collaboration.comment.updated"
    COLLABORATION_COMMENT_DELETED = "collaboration.comment.deleted"
    COLLABORATION_MENTION_CREATED = "collaboration.mention.created"
    COLLABORATION_ASSIGNMENT_CREATED = "collaboration.assignment.created"
    COLLABORATION_ASSIGNMENT_UPDATED = "collaboration.assignment.updated"
    COLLABORATION_ANNOTATION_CREATED = "collaboration.annotation.created"
    COLLABORATION_ANNOTATION_UPDATED = "collaboration.annotation.updated"
    COLLABORATION_DECISION_CREATED = "collaboration.decision.created"
    COLLABORATION_RESOURCE_UPDATED = "collaboration.resource.updated"
    COLLABORATION_CONFLICT_DETECTED = "collaboration.conflict.detected"
    COLLABORATION_RUN_STARTED = "collaboration.run.started"
    COLLABORATION_RUN_UPDATED = "collaboration.run.updated"
    COLLABORATION_RUN_COMPLETED = "collaboration.run.completed"
    COLLABORATION_RUN_FAILED = "collaboration.run.failed"


# Auditable event types
AUDITABLE_EVENTS = {
    SystemEventType.COLLABORATION_DECISION_CREATED.value,
    SystemEventType.COLLABORATION_CONFLICT_DETECTED.value,

    SystemEventType.RELIABILITY_COMPONENT_DEGRADED.value,
    SystemEventType.RELIABILITY_COMPONENT_RECOVERED.value,
    SystemEventType.RELIABILITY_RESUME_COMPLETED.value,
    SystemEventType.RELIABILITY_CIRCUIT_OPENED.value,
    SystemEventType.APPROVAL_APPROVED.value,
    SystemEventType.APPROVAL_REJECTED.value,
    SystemEventType.GRAPH_PROPOSAL_APPROVED.value,
    SystemEventType.GRAPH_PROPOSAL_REJECTED.value,
    SystemEventType.GRAPH_CONFLICT_RESOLVED.value,
    SystemEventType.TRIGGER_UPDATED.value,
    SystemEventType.TRIGGER_PAUSED.value,
    SystemEventType.TRIGGER_RESUMED.value,
    SystemEventType.WORKFLOW_STARTED.value,
    SystemEventType.WORKFLOW_COMPLETED.value,
    SystemEventType.WORKFLOW_FAILED.value,
    SystemEventType.SYSTEM_WARNING.value,
    SystemEventType.SYSTEM_ERROR.value,
    SystemEventType.ORGANIZATION_CREATED.value,
    SystemEventType.ORGANIZATION_UPDATED.value,
    SystemEventType.ORGANIZATION_ARCHIVED.value,
    SystemEventType.MEMBER_INVITED.value,
    SystemEventType.MEMBER_JOINED.value,
    SystemEventType.MEMBER_ROLE_CHANGED.value,
    SystemEventType.MEMBER_SUSPENDED.value,
    SystemEventType.MEMBER_REMOVED.value,
    SystemEventType.WORKSPACE_CREATED.value,
    SystemEventType.WORKSPACE_UPDATED.value,
    SystemEventType.WORKSPACE_ARCHIVED.value,
    SystemEventType.WORKSPACE_MEMBER_ADDED.value,
    SystemEventType.WORKSPACE_MEMBER_UPDATED.value,
    SystemEventType.WORKSPACE_MEMBER_REMOVED.value,
    SystemEventType.PROJECT_MEMBER_ADDED.value,
    SystemEventType.PROJECT_MEMBER_UPDATED.value,
    SystemEventType.PROJECT_MEMBER_REMOVED.value,
    SystemEventType.PROJECT_ACCESS_CHANGED.value,
    SystemEventType.OWNERSHIP_TRANSFERRED.value,
    SystemEventType.PROMPT_CREATED.value,
    SystemEventType.PROMPT_VERSION_CREATED.value,
    SystemEventType.PROMPT_VERSION_PUBLISHED.value,
    SystemEventType.PROMPT_RELEASE_CHANGED.value,
    SystemEventType.PROMPT_ROLLED_BACK.value,
    SystemEventType.PROMPT_ARCHIVED.value,
    SystemEventType.PROMPT_EXPERIMENT_STARTED.value,
    SystemEventType.PROMPT_EXPERIMENT_COMPLETED.value,
    # Step 32 Governance auditable events
    SystemEventType.GOVERNANCE_POLICY_CREATED.value,
    SystemEventType.GOVERNANCE_POLICY_UPDATED.value,
    SystemEventType.GOVERNANCE_POLICY_ACTIVATED.value,
    SystemEventType.GOVERNANCE_POLICY_DEACTIVATED.value,
    SystemEventType.GOVERNANCE_DECISION_DENIED.value,
    SystemEventType.GOVERNANCE_APPROVAL_REQUIRED.value,
    SystemEventType.GOVERNANCE_VERIFICATION_REQUIRED.value,
    SystemEventType.GOVERNANCE_BUDGET_BLOCKED.value,
    # Step 33 Data Governance auditable events
    SystemEventType.DATA_ASSET_CLASSIFIED.value,
    SystemEventType.DATA_DELETION_REQUESTED.value,
    SystemEventType.DATA_DELETION_COMPLETED.value,
    SystemEventType.DATA_DELETION_BLOCKED.value,
    SystemEventType.DATA_EXPORT_REQUESTED.value,
    SystemEventType.DATA_EXPORT_COMPLETED.value,
    SystemEventType.DATA_PRIVACY_REQUEST_CREATED.value,
    SystemEventType.DATA_PRIVACY_REQUEST_COMPLETED.value,
    SystemEventType.DATA_LEGAL_HOLD_CREATED.value,
    SystemEventType.DATA_LEGAL_HOLD_RELEASED.value,
    SystemEventType.DATA_EVIDENCE_CREATED.value,
    # Step 34 Security Operations auditable events
    SystemEventType.SECURITY_SIGNAL_CREATED.value,
    SystemEventType.SECURITY_INCIDENT_CREATED.value,
    SystemEventType.SECURITY_INCIDENT_UPDATED.value,
    SystemEventType.SECURITY_CONTAINMENT_REQUESTED.value,
    SystemEventType.SECURITY_CONTAINMENT_COMPLETED.value,
}

# Sensitive keys scrubbed from all payloads
SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "secret",
    "secret_key",
    "password",
    "passwd",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "auth",
    "cookie",
    "cookies",
    "private_key",
    "credential",
    "credentials",
    "database_url",
    "connection_string",
    "prompt",
    "hidden_prompt",
    "system_prompt",
    "chain_of_thought",
    "internal_reasoning",
    "raw_thought",
}

SSE_HEARTBEAT_EVENT = "heartbeat"
SSE_HEADER_LAST_EVENT_ID = "last-event-id"
