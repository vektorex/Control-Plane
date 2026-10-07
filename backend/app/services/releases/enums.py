from enum import Enum

class ReleaseType(str, Enum):
    configuration_change = "configuration_change"
    agent_release = "agent_release"
    workflow_release = "workflow_release"
    solution_release = "solution_release"
    prompt_release = "prompt_release"
    model_configuration_change = "model_configuration_change"
    connector_configuration_change = "connector_configuration_change"
    catalog_release = "catalog_release"
    marketplace_package_change = "marketplace_package_change"
    policy_change = "policy_change"
    knowledge_release = "knowledge_release"
    evaluation_configuration_change = "evaluation_configuration_change"
    other = "other"

class ReleaseStatus(str, Enum):
    draft = "draft"
    planning = "planning"
    validation_required = "validation_required"
    approval_required = "approval_required"
    ready = "ready"
    scheduled = "scheduled"
    in_progress = "in_progress"
    verifying = "verifying"
    observing = "observing"
    completed = "completed"
    blocked = "blocked"
    failed = "failed"
    rollback_required = "rollback_required"
    rolling_back = "rolling_back"
    rolled_back = "rolled_back"
    cancelled = "cancelled"

class CandidateStatus(str, Enum):
    pending = "pending"
    validated = "validated"
    blocked = "blocked"
    approved = "approved"
    released = "released"
    failed = "failed"
    rolled_back = "rolled_back"\n