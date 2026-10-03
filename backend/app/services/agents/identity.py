"""
Controlled AgentIdentity abstraction for Step 40.
Ensures every agent execution has a verifiable, stable identity
that distinguishes Human, AI Agent, AI Agent acting under another agent, and System.
Never allows an agent to impersonate a human.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class AgentIdentity:
    """Stable, immutable identity representation for an active agent execution."""

    agent_id: str
    workspace_id: str
    agent_version_id: str
    execution_id: str
    project_id: Optional[str] = None
    parent_agent_id: Optional[str] = None
    delegated_by: Optional[str] = None  # Parent run ID or delegation initiator
    human_initiator_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_delegated(self) -> bool:
        """Returns True if this agent execution was spawned via delegation."""
        return self.parent_agent_id is not None or self.delegated_by is not None

    @property
    def principal_type(self) -> str:
        """Returns the distinct principal classification."""
        if self.parent_agent_id:
            return "ai_agent_delegated"
        return "ai_agent"

    def to_dict(self) -> Dict[str, Any]:
        """Serializes identity for event metadata, audit logs, and telemetry."""
        return {
            "principal_type": self.principal_type,
            "agent_id": self.agent_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "agent_version_id": self.agent_version_id,
            "execution_id": self.execution_id,
            "parent_agent_id": self.parent_agent_id,
            "delegated_by": self.delegated_by,
            "human_initiator_id": self.human_initiator_id,
            "is_agent": True,
            "is_human": False,  # Strict invariant: agents can never claim to be human
        }

    def to_audit_context(self) -> Dict[str, Any]:
        """Returns sanitized context for audit trail and security logging."""
        ctx = self.to_dict()
        ctx["actor_type"] = "agent"
        return ctx

    def to_headers(self) -> Dict[str, str]:
        """Generates internal propagation headers for inter-service communication."""
        headers = {
            "X-Agent-ID": self.agent_id,
            "X-Agent-Version-ID": self.agent_version_id,
            "X-Agent-Execution-ID": self.execution_id,
            "X-Workspace-ID": self.workspace_id,
            "X-Principal-Type": self.principal_type,
        }
        if self.project_id:
            headers["X-Project-ID"] = self.project_id
        if self.parent_agent_id:
            headers["X-Parent-Agent-ID"] = self.parent_agent_id
        if self.human_initiator_id:
            headers["X-Human-Initiator-ID"] = self.human_initiator_id
        return headers
