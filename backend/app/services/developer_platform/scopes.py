"""
Permission Scopes and Scope Mapping for Developer Platform.
Step 37: Public API, Developer Platform & SDK Layer.
"""
from typing import Dict, List, Set

# Fixed permission scope registry
VALID_API_SCOPES: Set[str] = {
    "tasks:read",
    "tasks:run",
    "runs:read",
    "workflows:read",
    "workflows:run",
    "artifacts:read",
    "artifacts:create",
    "documents:read",
    "memory:read",
    "memory:write",
    "knowledge:read",
    "prompts:read",
    "evaluations:read",
    "replays:read",
    "connectors:read",
    "models:read",
    "events:read",
    "usage:read",
    "webhooks:manage",
    "applications:manage",
    "marketplace:read",
    "marketplace:install",
    "marketplace:manage",
    "collaboration:read",
    "collaboration:write",
    "collaboration:execute",
    "agents:read",
    "agents:write",
    "agents:execute",
    "agent_teams:read",
    "agent_teams:write",
    "agent_teams:execute",
    "simulations:read",
    "simulations:write",
    "simulations:execute",
}
PUBLIC_SCOPES = VALID_API_SCOPES

# Mapping from public API scopes to internal access control permissions
SCOPE_TO_PERMISSION_MAP: Dict[str, str] = {
    "tasks:read": "task.read",
    "tasks:run": "task.run",
    "runs:read": "task.read",
    "workflows:read": "workflow.read",
    "workflows:run": "workflow.run",
    "artifacts:read": "artifact.read",
    "artifacts:create": "artifact.create",
    "documents:read": "document.read",
    "memory:read": "memory.read",
    "memory:write": "memory.create",
    "knowledge:read": "graph.read",
    "prompts:read": "prompt.read",
    "evaluations:read": "evaluation.read",
    "replays:read": "replay.read",
    "connectors:read": "connector.read",
    "models:read": "task.read",
    "events:read": "event.read",
    "usage:read": "analytics.read",
    "webhooks:manage": "webhook.configure",
    "applications:manage": "developer.manage",
    "marketplace:read": "marketplace.read",
    "marketplace:install": "marketplace.install",
    "marketplace:manage": "marketplace.manage",
    "collaboration:read": "collaboration.session_read",
    "collaboration:write": "collaboration.comment",
    "collaboration:execute": "collaboration.execute",
    "agents:read": "agent.read",
    "agents:write": "agent.create",
    "agents:execute": "agent.run",
    "agent_teams:read": "agent_team.read",
    "agent_teams:write": "agent_team.create",
    "agent_teams:execute": "agent_team.run",
    "simulations:read": "simulation.read",
    "simulations:write": "simulation.create",
    "simulations:execute": "simulation.run",
}

# Sensitive scopes that require explicit organization admin privileges
SENSITIVE_SCOPES: Set[str] = {
    "tasks:run",
    "workflows:run",
    "artifacts:create",
    "marketplace:install",
    "marketplace:manage",
    "collaboration:execute",
    "memory:write",
    "webhooks:manage",
    "applications:manage",
    "agents:write",
    "agents:execute",
    "agent_teams:write",
    "agent_teams:execute",
}


class ScopeRegistry:
    """Validates scopes, translates scopes to permissions, and prevents privilege escalation."""

    @classmethod
    def is_valid_scope(cls, scope: str) -> bool:
        return scope in VALID_API_SCOPES

    @classmethod
    def validate_scopes(cls, scopes: List[str]) -> List[str]:
        """Returns list of invalid scopes if any."""
        return [s for s in scopes if s not in VALID_API_SCOPES]

    @classmethod
    def get_all_scopes(cls) -> Set[str]:
        return set(VALID_API_SCOPES)

    @classmethod
    def to_internal_permission(cls, scope: str) -> str:
        return SCOPE_TO_PERMISSION_MAP.get(scope, "")

    @classmethod
    def check_privilege_escalation(
        cls,
        requested_scopes: List[str],
        creator_permissions: Set[str],
        is_org_admin: bool = False,
    ) -> List[str]:
        """
        Ensures a creator cannot assign scopes that exceed their own permissions,
        and ensures sensitive scopes require organization admin permission.
        Returns list of disallowed scopes.
        """
        disallowed: List[str] = []
        for scope in requested_scopes:
            if scope in SENSITIVE_SCOPES and not is_org_admin:
                disallowed.append(f"{scope} (requires organization administrator)")
                continue

            required_perm = cls.to_internal_permission(scope)
            if required_perm and required_perm not in creator_permissions and not is_org_admin:
                disallowed.append(f"{scope} (missing {required_perm})")

        return disallowed
