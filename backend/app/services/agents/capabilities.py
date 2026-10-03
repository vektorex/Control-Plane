"""
Declarative Agent Capabilities for Step 40.
Capabilities are explicit, granular permissions assigned to agent versions.
No capability automatically grants another capability.
"""
from enum import Enum
from typing import List, Set


class AgentCapability(str, Enum):
    TASK_EXECUTE = "task_execute"
    WORKFLOW_RUN = "workflow_run"
    WORKFLOW_CREATE_DRAFT = "workflow_create_draft"
    WORKFLOW_EDIT_DRAFT = "workflow_edit_draft"
    RETRIEVE = "retrieve"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    KNOWLEDGE_READ = "knowledge_read"
    DOCUMENT_READ = "document_read"
    ARTIFACT_READ = "artifact_read"
    ARTIFACT_CREATE = "artifact_create"
    TOOL_USE = "tool_use"
    CONNECTOR_READ = "connector_read"
    PROMPT_USE = "prompt_use"
    EVALUATION_RUN = "evaluation_run"
    REPLAY_RUN = "replay_run"
    COLLABORATION_COMMENT = "collaboration_comment"
    COLLABORATION_ASSIGN = "collaboration_assign"
    COLLABORATION_ANNOTATE = "collaboration_annotate"
    AGENT_DELEGATE = "agent_delegate"


ALL_CAPABILITIES: Set[str] = {c.value for c in AgentCapability}

# Sensitive capabilities that require extra scrutiny / verification
PRIVILEGED_CAPABILITIES: Set[str] = {
    AgentCapability.MEMORY_WRITE.value,
    AgentCapability.ARTIFACT_CREATE.value,
    AgentCapability.WORKFLOW_RUN.value,
    AgentCapability.AGENT_DELEGATE.value,
    AgentCapability.COLLABORATION_ASSIGN.value,
}


def validate_capabilities(capabilities: List[str]) -> List[str]:
    """Validates a list of capabilities against the known declarative set."""
    invalid = [c for c in capabilities if c not in ALL_CAPABILITIES]
    return invalid


def has_capability(granted_capabilities: List[str], required_capability: str) -> bool:
    """Checks if a required capability is explicitly present in granted list."""
    return required_capability in granted_capabilities
