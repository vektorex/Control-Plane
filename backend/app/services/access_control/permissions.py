"""
Permission definitions for Step 27: Multi-Tenant Organizations, Teams, Roles & Access Control.
Centralized, explicit permission constants.
"""

# Organization permissions
ORGANIZATION_READ = "organization.read"
ORGANIZATION_UPDATE = "organization.update"
ORGANIZATION_DELETE = "organization.delete"

# Member permissions
MEMBER_READ = "member.read"
MEMBER_INVITE = "member.invite"
MEMBER_UPDATE = "member.update"
MEMBER_REMOVE = "member.remove"

# Workspace permissions
WORKSPACE_CREATE = "workspace.create"
WORKSPACE_READ = "workspace.read"
WORKSPACE_UPDATE = "workspace.update"
WORKSPACE_DELETE = "workspace.delete"

# Project permissions
PROJECT_CREATE = "project.create"
PROJECT_READ = "project.read"
PROJECT_UPDATE = "project.update"
PROJECT_DELETE = "project.delete"

# Task permissions
TASK_READ = "task.read"
TASK_CREATE = "task.create"
TASK_UPDATE = "task.update"
TASK_DELETE = "task.delete"
TASK_RUN = "task.run"

# Workflow permissions
WORKFLOW_READ = "workflow.read"
WORKFLOW_CREATE = "workflow.create"
WORKFLOW_UPDATE = "workflow.update"
WORKFLOW_DELETE = "workflow.delete"
WORKFLOW_PUBLISH = "workflow.publish"
WORKFLOW_RUN = "workflow.run"

# Trigger permissions
TRIGGER_READ = "trigger.read"
TRIGGER_CREATE = "trigger.create"
TRIGGER_UPDATE = "trigger.update"
TRIGGER_DELETE = "trigger.delete"
TRIGGER_RUN = "trigger.run"

# Job permissions
JOB_READ = "job.read"
JOB_CANCEL = "job.cancel"
JOB_RETRY = "job.retry"

# Connector permissions
CONNECTOR_READ = "connector.read"
CONNECTOR_CONFIGURE = "connector.configure"
CONNECTOR_EXECUTE = "connector.execute"

# Memory permissions
MEMORY_READ = "memory.read"
MEMORY_CREATE = "memory.create"
MEMORY_UPDATE = "memory.update"
MEMORY_DELETE = "memory.delete"

# Evaluation permissions
EVALUATION_READ = "evaluation.read"
EVALUATION_CREATE = "evaluation.create"
EVALUATION_RUN = "evaluation.run"

# Replay permissions
REPLAY_READ = "replay.read"
REPLAY_CREATE = "replay.create"

# Notification permissions
NOTIFICATION_READ = "notification.read"
NOTIFICATION_CONFIGURE = "notification.configure"

# Webhook permissions
WEBHOOK_READ = "webhook.read"
WEBHOOK_CONFIGURE = "webhook.configure"

# Approval permissions (HITL)
APPROVAL_READ = "approval.read"
APPROVAL_RESPOND = "approval.respond"

# Analytics permissions
ANALYTICS_READ = "analytics.read"

# Event permissions
EVENT_READ = "event.read"

# Audit permissions
AUDIT_READ = "audit.read"

# Prompt permissions (Step 28)
PROMPT_READ = "prompt.read"
PROMPT_CREATE = "prompt.create"
PROMPT_UPDATE = "prompt.update"
PROMPT_PUBLISH = "prompt.publish"
PROMPT_RELEASE = "prompt.release"
PROMPT_ROLLBACK = "prompt.rollback"
PROMPT_EXECUTE = "prompt.execute"
PROMPT_EXPERIMENT = "prompt.experiment"
PROMPT_ARCHIVE = "prompt.archive"

# Knowledge Graph permissions (Step 29)
GRAPH_READ = "graph.read"
GRAPH_CREATE = "graph.create"
GRAPH_UPDATE = "graph.update"
GRAPH_DELETE = "graph.delete"
GRAPH_EXTRACT = "graph.extract"
GRAPH_MERGE = "graph.merge"

# Artifact & Multimodal permissions (Step 30)
ARTIFACT_READ = "artifact.read"
ARTIFACT_CREATE = "artifact.create"
ARTIFACT_UPDATE = "artifact.update"
ARTIFACT_DELETE = "artifact.delete"
ARTIFACT_PROCESS = "artifact.process"
ARTIFACT_ANALYZE = "artifact.analyze"

# Cache permissions (Step 31)
CACHE_READ = "cache.read"
CACHE_CONFIGURE = "cache.configure"
CACHE_INVALIDATE = "cache.invalidate"
CACHE_DELETE = "cache.delete"

# Governance permissions (Step 32)
GOVERNANCE_READ = "governance.read"
GOVERNANCE_CONFIGURE = "governance.configure"
GOVERNANCE_SIMULATE = "governance.simulate"
GOVERNANCE_ACTIVATE = "governance.activate"
GOVERNANCE_AUDIT = "governance.audit"

# Data Governance permissions (Step 33)
DATA_GOVERNANCE_READ = "data_governance.read"
DATA_GOVERNANCE_MANAGE = "data_governance.manage"
DATA_GOVERNANCE_EXPORT = "data_governance.export"
DATA_GOVERNANCE_DELETE = "data_governance.delete"
DATA_GOVERNANCE_LEGAL_HOLD = "data_governance.legal_hold"
DATA_GOVERNANCE_AUDIT = "data_governance.audit"

# Security Operations permissions (Step 34)
SECURITY_READ = "security.read"
SECURITY_MANAGE = "security.manage"
SECURITY_CONTAIN = "security.contain"
SECURITY_INVESTIGATE = "security.investigate"
SECURITY_ADMIN = "security.admin"

# Set of all valid system permissions
ALL_PERMISSIONS = {
    CACHE_READ,
    CACHE_CONFIGURE,
    CACHE_INVALIDATE,
    CACHE_DELETE,
    GOVERNANCE_READ,
    GOVERNANCE_CONFIGURE,
    GOVERNANCE_SIMULATE,
    GOVERNANCE_ACTIVATE,
    GOVERNANCE_AUDIT,
    DATA_GOVERNANCE_READ,
    DATA_GOVERNANCE_MANAGE,
    DATA_GOVERNANCE_EXPORT,
    DATA_GOVERNANCE_DELETE,
    DATA_GOVERNANCE_LEGAL_HOLD,
    DATA_GOVERNANCE_AUDIT,
    SECURITY_READ,
    SECURITY_MANAGE,
    SECURITY_CONTAIN,
    SECURITY_INVESTIGATE,
    SECURITY_ADMIN,
    ORGANIZATION_READ,
    ORGANIZATION_UPDATE,
    ORGANIZATION_DELETE,
    MEMBER_READ,
    MEMBER_INVITE,
    MEMBER_UPDATE,
    MEMBER_REMOVE,
    WORKSPACE_CREATE,
    WORKSPACE_READ,
    WORKSPACE_UPDATE,
    WORKSPACE_DELETE,
    PROJECT_CREATE,
    PROJECT_READ,
    PROJECT_UPDATE,
    PROJECT_DELETE,
    TASK_READ,
    TASK_CREATE,
    TASK_UPDATE,
    TASK_DELETE,
    TASK_RUN,
    WORKFLOW_READ,
    WORKFLOW_CREATE,
    WORKFLOW_UPDATE,
    WORKFLOW_DELETE,
    WORKFLOW_PUBLISH,
    WORKFLOW_RUN,
    TRIGGER_READ,
    TRIGGER_CREATE,
    TRIGGER_UPDATE,
    TRIGGER_DELETE,
    TRIGGER_RUN,
    JOB_READ,
    JOB_CANCEL,
    JOB_RETRY,
    CONNECTOR_READ,
    CONNECTOR_CONFIGURE,
    CONNECTOR_EXECUTE,
    MEMORY_READ,
    MEMORY_CREATE,
    MEMORY_UPDATE,
    MEMORY_DELETE,
    EVALUATION_READ,
    EVALUATION_CREATE,
    EVALUATION_RUN,
    REPLAY_READ,
    REPLAY_CREATE,
    NOTIFICATION_READ,
    NOTIFICATION_CONFIGURE,
    WEBHOOK_READ,
    WEBHOOK_CONFIGURE,
    APPROVAL_READ,
    APPROVAL_RESPOND,
    ANALYTICS_READ,
    EVENT_READ,
    AUDIT_READ,
    PROMPT_READ,
    PROMPT_CREATE,
    PROMPT_UPDATE,
    PROMPT_PUBLISH,
    PROMPT_RELEASE,
    PROMPT_ROLLBACK,
    PROMPT_EXECUTE,
    PROMPT_EXPERIMENT,
    PROMPT_ARCHIVE,
    GRAPH_READ,
    GRAPH_CREATE,
    GRAPH_UPDATE,
    GRAPH_DELETE,
    GRAPH_EXTRACT,
    GRAPH_MERGE,
    ARTIFACT_READ,
    ARTIFACT_CREATE,
    ARTIFACT_UPDATE,
    ARTIFACT_DELETE,
    ARTIFACT_PROCESS,
    ARTIFACT_ANALYZE,
}

