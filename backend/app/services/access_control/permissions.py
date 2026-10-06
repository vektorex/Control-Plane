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

# Reliability, Resilience & Chaos permissions (Step 35)
RELIABILITY_READ = "reliability.read"
RELIABILITY_MANAGE = "reliability.manage"
RELIABILITY_RECOVER = "reliability.recover"
CHAOS_EXECUTE = "chaos.execute"
RELIABILITY_ADMIN = "reliability.admin"

# Disaster Recovery, Backup & Continuity permissions (Step 36)
RECOVERY_READ = "recovery.read"
RECOVERY_BACKUP = "recovery.backup"
RECOVERY_RESTORE = "recovery.restore"
RECOVERY_EXERCISE = "recovery.exercise"
RECOVERY_ADMIN = "recovery.admin"

# Developer Platform permissions (Step 37)
DEVELOPER_READ = "developer.read"
DEVELOPER_MANAGE = "developer.manage"
DEVELOPER_CREDENTIAL_CREATE = "developer.credential_create"
DEVELOPER_CREDENTIAL_REVOKE = "developer.credential_revoke"
DEVELOPER_ADMIN = "developer.admin"
# Marketplace & Extension Ecosystem permissions (Step 38)
MARKETPLACE_READ = "marketplace.read"
MARKETPLACE_INSTALL = "marketplace.install"
MARKETPLACE_PUBLISH = "marketplace.publish"
MARKETPLACE_MANAGE = "marketplace.manage"
MARKETPLACE_ADMIN = "marketplace.admin"

# Collaboration permissions (Step 39)
COLLABORATION_SESSION_READ = "collaboration.session_read"
COLLABORATION_SESSION_JOIN = "collaboration.session_join"
COLLABORATION_COMMENT = "collaboration.comment"
COLLABORATION_ANNOTATE = "collaboration.annotate"
COLLABORATION_ASSIGN = "collaboration.assign"
COLLABORATION_EDIT = "collaboration.edit"
COLLABORATION_APPROVE = "collaboration.approve"
COLLABORATION_EXECUTE = "collaboration.execute"
COLLABORATION_ADMIN = "collaboration.admin"

# Agent & Agent Team permissions (Step 40)
AGENT_READ = "agent.read"
AGENT_CREATE = "agent.create"
AGENT_UPDATE = "agent.update"
AGENT_DELETE = "agent.delete"
AGENT_PUBLISH = "agent.publish"
AGENT_ACTIVATE = "agent.activate"
AGENT_PAUSE = "agent.pause"
AGENT_RUN = "agent.run"
AGENT_DELEGATE = "agent.delegate"
AGENT_TEAM_READ = "agent_team.read"
AGENT_TEAM_CREATE = "agent_team.create"
AGENT_TEAM_UPDATE = "agent_team.update"
AGENT_TEAM_DELETE = "agent_team.delete"
AGENT_TEAM_RUN = "agent_team.run"

# Step 43: Outcome Intelligence permissions
OBJECTIVE_READ = "objective.read"
OBJECTIVE_CREATE = "objective.create"
OBJECTIVE_UPDATE = "objective.update"
OBJECTIVE_DELETE = "objective.delete"
OUTCOME_READ = "outcome.read"
OUTCOME_CREATE = "outcome.create"
OUTCOME_UPDATE = "outcome.update"
OUTCOME_DELETE = "outcome.delete"
OUTCOME_VERIFY = "outcome.verify"
OUTCOME_DISPUTE = "outcome.dispute"
DECISION_READ = "decision.read"
DECISION_CREATE = "decision.create"
DECISION_UPDATE = "decision.update"
DECISION_APPROVE = "decision.approve"
DECISION_REJECT = "decision.reject"

# Step 44: AI Work Planning permissions
PLAN_READ = "plan.read"
PLAN_CREATE = "plan.create"
PLAN_UPDATE = "plan.update"
PLAN_DELETE = "plan.delete"
PLAN_VALIDATE = "plan.validate"
PLAN_ACTIVATE = "plan.activate"
PLAN_PAUSE = "plan.pause"
RESOURCE_READ = "resource.read"
RESOURCE_CREATE = "resource.create"
RESOURCE_UPDATE = "resource.update"
CAPACITY_READ = "capacity.read"
CAPACITY_RESERVE = "capacity.reserve"
SCENARIO_RUN = "scenario.run"

# Set of all valid system permissions
ALL_PERMISSIONS = {
    PLAN_READ,
    PLAN_CREATE,
    PLAN_UPDATE,
    PLAN_DELETE,
    PLAN_VALIDATE,
    PLAN_ACTIVATE,
    PLAN_PAUSE,
    RESOURCE_READ,
    RESOURCE_CREATE,
    RESOURCE_UPDATE,
    CAPACITY_READ,
    CAPACITY_RESERVE,
    SCENARIO_RUN,
    OBJECTIVE_READ,
    OBJECTIVE_CREATE,
    OBJECTIVE_UPDATE,
    OBJECTIVE_DELETE,
    OUTCOME_READ,
    OUTCOME_CREATE,
    OUTCOME_UPDATE,
    OUTCOME_DELETE,
    OUTCOME_VERIFY,
    OUTCOME_DISPUTE,
    DECISION_READ,
    DECISION_CREATE,
    DECISION_UPDATE,
    DECISION_APPROVE,
    DECISION_REJECT,
    AGENT_READ,
    AGENT_CREATE,
    AGENT_UPDATE,
    AGENT_DELETE,
    AGENT_PUBLISH,
    AGENT_ACTIVATE,
    AGENT_PAUSE,
    AGENT_RUN,
    AGENT_DELEGATE,
    AGENT_TEAM_READ,
    AGENT_TEAM_CREATE,
    AGENT_TEAM_UPDATE,
    AGENT_TEAM_DELETE,
    AGENT_TEAM_RUN,
    COLLABORATION_SESSION_READ,
    COLLABORATION_SESSION_JOIN,
    COLLABORATION_COMMENT,
    COLLABORATION_ANNOTATE,
    COLLABORATION_ASSIGN,
    COLLABORATION_EDIT,
    COLLABORATION_APPROVE,
    COLLABORATION_EXECUTE,
    COLLABORATION_ADMIN,

    MARKETPLACE_READ,
    MARKETPLACE_INSTALL,
    MARKETPLACE_PUBLISH,
    MARKETPLACE_MANAGE,
    MARKETPLACE_ADMIN,
    DEVELOPER_READ,
    DEVELOPER_MANAGE,
    DEVELOPER_CREDENTIAL_CREATE,
    DEVELOPER_CREDENTIAL_REVOKE,
    DEVELOPER_ADMIN,
    RECOVERY_READ,
    RECOVERY_BACKUP,
    RECOVERY_RESTORE,
    RECOVERY_EXERCISE,
    RECOVERY_ADMIN,
    RELIABILITY_READ,
    RELIABILITY_MANAGE,
    RELIABILITY_RECOVER,
    CHAOS_EXECUTE,
    RELIABILITY_ADMIN,
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

