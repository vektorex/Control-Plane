"""
Domain-specific exceptions for Step 40: Governed AI Agent Runtime and Multi-Agent Teams.
"""
from typing import Optional


class AgentError(Exception):
    """Base exception for all agent domain errors."""

    def __init__(self, message: str, code: str = "AGENT_ERROR", details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class AgentNotFoundError(AgentError):
    """Raised when an agent is not found."""

    def __init__(self, agent_id: str):
        super().__init__(f"Agent '{agent_id}' not found.", code="AGENT_NOT_FOUND", details={"agent_id": agent_id})


class AgentVersionNotFoundError(AgentError):
    """Raised when an agent version is not found."""

    def __init__(self, agent_id: str, version: Optional[int] = None, version_id: Optional[str] = None):
        super().__init__(
            f"Agent version for agent '{agent_id}' (version={version}, id={version_id}) not found.",
            code="AGENT_VERSION_NOT_FOUND",
            details={"agent_id": agent_id, "version": version, "version_id": version_id},
        )


class AgentVersionImmutableError(AgentError):
    """Raised when attempting to modify an immutable published agent version."""

    def __init__(self, version_id: str):
        super().__init__(
            f"Agent version '{version_id}' is published and immutable. Create a new draft version to edit.",
            code="AGENT_VERSION_IMMUTABLE",
            details={"version_id": version_id},
        )


class AgentLifecycleError(AgentError):
    """Raised on invalid lifecycle state transition."""

    def __init__(self, current_status: str, target_status: str, reason: str):
        super().__init__(
            f"Cannot transition agent from '{current_status}' to '{target_status}': {reason}",
            code="INVALID_AGENT_LIFECYCLE_TRANSITION",
            details={"current_status": current_status, "target_status": target_status, "reason": reason},
        )


class CapabilityNotGrantedError(AgentError):
    """Raised when an agent attempts an action without having the required declarative capability."""

    def __init__(self, capability: str, agent_id: str):
        super().__init__(
            f"Agent '{agent_id}' does not have capability '{capability}' granted by its policy.",
            code="CAPABILITY_NOT_GRANTED",
            details={"capability": capability, "agent_id": agent_id},
        )


class DelegationDepthExceededError(AgentError):
    """Raised when delegation depth exceeds maximum allowed depth."""

    def __init__(self, current_depth: int, max_depth: int):
        super().__init__(
            f"Delegation depth {current_depth} exceeds maximum permitted depth {max_depth}.",
            code="DELEGATION_DEPTH_EXCEEDED",
            details={"current_depth": current_depth, "max_depth": max_depth},
        )


class DelegationCycleDetectedError(AgentError):
    """Raised when circular delegation is detected."""

    def __init__(self, agent_id: str, cycle_path: list):
        super().__init__(
            f"Circular delegation detected involving agent '{agent_id}'. Path: {' -> '.join(cycle_path)}",
            code="DELEGATION_CYCLE_DETECTED",
            details={"agent_id": agent_id, "cycle_path": cycle_path},
        )


class DelegationBudgetExceededError(AgentError):
    """Raised when child delegation budget exceeds parent budget."""

    def __init__(self, requested_budget: float, available_parent_budget: float):
        super().__init__(
            f"Requested delegation budget ${requested_budget:.4f} exceeds available parent allocation ${available_parent_budget:.4f}.",
            code="DELEGATION_BUDGET_EXCEEDED",
            details={"requested": requested_budget, "available": available_parent_budget},
        )


class AgentBudgetExhaustedError(AgentError):
    """Raised when an agent execution exhausts its budget reservation."""

    def __init__(self, run_id: str, budget_limit: float, current_spend: float):
        super().__init__(
            f"Agent run '{run_id}' has exhausted allocated budget ${budget_limit:.4f} (spent ${current_spend:.4f}).",
            code="AGENT_BUDGET_EXHAUSTED",
            details={"run_id": run_id, "budget_limit": budget_limit, "current_spend": current_spend},
        )


class AgentExecutionLimitExceededError(AgentError):
    """Raised when execution limits (steps, tokens, calls, time) are breached."""

    def __init__(self, limit_type: str, limit_value: float, current_value: float):
        super().__init__(
            f"Agent execution limit exceeded for '{limit_type}': limit={limit_value}, actual={current_value}.",
            code="AGENT_EXECUTION_LIMIT_EXCEEDED",
            details={"limit_type": limit_type, "limit_value": limit_value, "current_value": current_value},
        )


class AgentTeamNotFoundError(AgentError):
    """Raised when a multi-agent team is not found."""

    def __init__(self, team_id: str):
        super().__init__(f"Agent team '{team_id}' not found.", code="AGENT_TEAM_NOT_FOUND", details={"team_id": team_id})


class AgentTeamVersionNotFoundError(AgentError):
    """Raised when a team version is not found."""

    def __init__(self, team_id: str, version: Optional[int] = None, version_id: Optional[str] = None):
        super().__init__(
            f"Agent team version for team '{team_id}' (version={version}, id={version_id}) not found.",
            code="AGENT_TEAM_VERSION_NOT_FOUND",
            details={"team_id": team_id, "version": version, "version_id": version_id},
        )


class AgentTeamRunNotFoundError(AgentError):
    """Raised when an agent team run is not found."""

    def __init__(self, run_id: str):
        super().__init__(f"Agent team run '{run_id}' not found.", code="AGENT_TEAM_RUN_NOT_FOUND", details={"run_id": run_id})


class AgentRunNotFoundError(AgentError):
    """Raised when an agent run is not found."""

    def __init__(self, run_id: str):
        super().__init__(f"Agent run '{run_id}' not found.", code="AGENT_RUN_NOT_FOUND", details={"run_id": run_id})


class AgentGovernanceDeniedError(AgentError):
    """Raised when a governance policy check denies agent execution."""

    def __init__(self, policy_id: str, reason: str):
        super().__init__(
            f"Agent execution denied by governance policy '{policy_id}': {reason}",
            code="AGENT_GOVERNANCE_DENIED",
            details={"policy_id": policy_id, "reason": reason},
        )


class AgentSelfApprovalBlockedError(AgentError):
    """Raised when an agent attempts to approve its own privileged action."""

    def __init__(self, agent_id: str, action: str):
        super().__init__(
            f"Security violation: Agent '{agent_id}' cannot approve its own action '{action}'.",
            code="AGENT_SELF_APPROVAL_BLOCKED",
            details={"agent_id": agent_id, "action": action},
        )
