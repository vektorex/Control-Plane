"""
Constants and Enums for Step 24: Durable Background Job System.
"""
from enum import Enum


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


PRIORITY_WEIGHTS = {
    JobPriority.HIGH.value: 1,
    JobPriority.NORMAL.value: 2,
    JobPriority.LOW.value: 3,
}


class JobType(str, Enum):
    WORKFLOW_RUN = "workflow_run"
    TRIGGER_RUN = "trigger_run"
    DOCUMENT_PROCESSING = "document_processing"
    EVALUATION_EXPERIMENT = "evaluation_experiment"
    REPLAY_RUN = "replay_run"
    CONNECTOR_OPERATION = "connector_operation"
    NOTIFICATION_DELIVERY = "notification_delivery"
    PROMPT_EXPERIMENT = "prompt_experiment"
    GRAPH_EXTRACTION = "graph_extraction"
    GRAPH_RECONCILIATION = "graph_reconciliation"
    GRAPH_REBUILD = "graph_rebuild"
    ARTIFACT_PROCESSING = "artifact_processing"
    IMAGE_PROCESSING = "image_processing"
    AUDIO_TRANSCRIPTION = "audio_transcription"
    VIDEO_PROCESSING = "video_processing"
    TABLE_PROCESSING = "table_processing"
    MULTIMODAL_EXTRACTION = "multimodal_extraction"
    CACHE_REFRESH = "cache_refresh"
    CACHE_CLEANUP = "cache_cleanup"
    GOVERNANCE_POLICY_RECHECK = "governance_policy_recheck"
    DATA_RETENTION_SCAN = "data_retention_scan"
    DATA_DELETION = "data_deletion"
    DATA_EXPORT = "data_export"
    DATA_ANONYMIZATION = "data_anonymization"
    DATA_ARCHIVE = "data_archive"
    PRIVACY_REQUEST = "privacy_request"
    SECURITY_SIGNAL_PROCESSING = "security_signal_processing"
    SECURITY_CORRELATION = "security_correlation"
    SECURITY_RETENTION = "security_retention"
    SECURITY_INDICATOR_CLEANUP = "security_indicator_cleanup"
    RELIABILITY_HEALTH_CHECK = "reliability_health_check"
    RELIABILITY_CHECKPOINT_CLEANUP = "reliability_checkpoint_cleanup"
    RELIABILITY_SLO_MONITORING = "reliability_slo_monitoring"
    RELIABILITY_CIRCUIT_RECONCILIATION = "reliability_circuit_reconciliation"
    RECOVERY_BACKUP_RUN = "recovery_backup_run"
    RECOVERY_BACKUP_RESOURCE_BATCH = "recovery_backup_resource_batch"
    RECOVERY_BACKUP_VERIFICATION = "recovery_backup_verification"
    RECOVERY_BACKUP_CLEANUP = "recovery_backup_cleanup"
    RECOVERY_RESTORE_RUN = "recovery_restore_run"
    RECOVERY_RESTORE_VERIFICATION = "recovery_restore_verification"
    RECOVERY_EXERCISE = "recovery_exercise"
    PUBLIC_WEBHOOK_DELIVERY = "public_webhook_delivery"
    MARKETPLACE_VALIDATION = "marketplace_validation"
    MARKETPLACE_SECURITY_SCAN = "marketplace_security_scan"
    MARKETPLACE_PUBLISH = "marketplace_publish"
    MARKETPLACE_INSTALL = "marketplace_install"
    MARKETPLACE_UPDATE = "marketplace_update"
    MARKETPLACE_ROLLBACK = "marketplace_rollback"
    MARKETPLACE_EVALUATION = "marketplace_evaluation"
    AGENT_RUN = "agent_run"
    AGENT_DELEGATION = "agent_delegation"
    AGENT_TEAM_RUN = "agent_team_run"
    AGENT_EVALUATION = "agent_evaluation"
    SIMULATION_RUN = "simulation_run"
    SIMULATION_SUITE_RUN = "simulation_suite_run"
    SIMULATION_SCENARIO_RUN = "simulation_scenario_run"
    # Step 43: Outcome Intelligence jobs
    OUTCOME_MEASUREMENT = "outcome_measurement"
    OUTCOME_VERIFICATION = "outcome_verification"
    OUTCOME_HEALTH_REFRESH = "outcome_health_refresh"
    OUTCOME_IMPACT_ANALYSIS = "outcome_impact_analysis"
    OUTCOME_RECOMMENDATION = "outcome_recommendation"
    OUTCOME_GRAPH_UPDATE = "outcome_graph_update"


class JobEventType(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    CLAIMED = "claimed"
    STARTED = "started"
    HEARTBEAT = "heartbeat"
    PROGRESS = "progress"
    RETRY_SCHEDULED = "retry_scheduled"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERED = "recovered"
