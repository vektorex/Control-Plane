"""
Security and Safety Boundary Enforcer for Step 41: AI Agent Simulation.
Ensures simulation is an impenetrable security boundary with zero real external side effects.
"""
from typing import Any, Dict, List, Optional, Set
import re

from backend.app.core.logging import logger
from backend.app.services.events.constants import SENSITIVE_KEYS
from backend.app.services.simulation.errors import SideEffectSandboxViolationError, TenantIsolationError


# Explicit list of dangerous or potentially external actions that MUST be intercepted
INTERCEPTED_ACTIONS: Set[str] = {
    # GitHub / code repository
    "github_issue_create",
    "github_pr_create",
    "github_repo_modify",
    "github_commit_create",
    "github_write",
    "github_create_branch",
    # Communications
    "email_send",
    "notification_deliver",
    "slack_post_message",
    "teams_post_message",
    "webhook_send",
    "http_request_write",
    "external_api_write",
    # Platform entities
    "workflow_publish",
    "workflow_modify",
    "agent_permission_modify",
    "governance_policy_modify",
    "marketplace_publish",
    "marketplace_package_install",
    "credential_modify",
    "user_privilege_escalate",
    # Production storage mutations
    "production_memory_write",
    "production_knowledge_graph_write",
    "production_artifact_modify",
    "production_database_write",
}


class SimulationSafetyEnforcer:
    """
    Enforces security boundary invariants during simulation runs.
    """

    @staticmethod
    def assert_tenant_boundary(simulation_workspace_id: str, target_workspace_id: str) -> None:
        """Enforces that a simulation can never operate across workspace/tenant boundaries."""
        if str(simulation_workspace_id) != str(target_workspace_id):
            logger.warning(
                f"[SimulationSafety] Cross-tenant access blocked. Sim WS: {simulation_workspace_id}, Target WS: {target_workspace_id}"
            )
            raise TenantIsolationError(
                f"Cross-tenant access forbidden. Simulation in workspace '{simulation_workspace_id}' cannot target workspace '{target_workspace_id}'."
            )

    @staticmethod
    def is_intercepted_action(action_name: str) -> bool:
        """Checks if an action is classified as external or mutating side-effect."""
        act = action_name.lower().replace(".", "_").replace(":", "_").strip()
        if act in INTERCEPTED_ACTIONS:
            return True
        for intercepted in INTERCEPTED_ACTIONS:
            if intercepted in act:
                return True
        # Catch generic mutations and external transports
        if any(w in act for w in ["write", "create", "update", "delete", "publish", "send", "dispatch", "post", "email", "webhook"]):
            return True
        return False


    @staticmethod
    def sanitize_snapshot_data(data: Any) -> Any:
        """
        Sanitizes data copied from production into a simulation snapshot:
        strips API keys, passwords, bearer tokens, credentials, and sensitive metadata.
        """
        if isinstance(data, dict):
            sanitized = {}
            for k, v in data.items():
                k_lower = str(k).lower()
                if any(sk in k_lower for sk in SENSITIVE_KEYS):
                    sanitized[k] = "[REDACTED_SECRET]"
                else:
                    sanitized[k] = SimulationSafetyEnforcer.sanitize_snapshot_data(v)
            return sanitized
        elif isinstance(data, list):
            return [SimulationSafetyEnforcer.sanitize_snapshot_data(item) for item in data]
        elif isinstance(data, str):
            # Check for token patterns (e.g., Bearer, ghp_, etc.)
            if re.search(r"ghp_[a-zA-Z0-9]{36}|sk-[a-zA-Z0-9]{32,}|bearer\s+[a-zA-Z0-9_\-\.]{20,}", data, re.IGNORECASE):
                return "[REDACTED_SENSITIVE_CREDENTIAL]"
            return data
        return data

    @staticmethod
    def check_adversarial_patterns(user_input: str) -> List[Dict[str, str]]:
        """
        Detects common adversarial security patterns in input (e.g. Prompt Injection, Privilege Escalation).
        Returns findings marked as SIMULATION FINDING without throwing exceptions.
        """
        findings = []
        lower = user_input.lower()

        # Prompt injection checks
        if any(p in lower for p in ["ignore previous instructions", "disregard all instructions", "override system prompt", "bypass security policy"]):
            findings.append({
                "type": "prompt_injection_attempt",
                "severity": "high",
                "description": "Simulation input contains prompt injection instruction patterns.",
                "classification": "SIMULATION FINDING",
            })

        # Secret extraction checks
        if any(p in lower for p in ["print api_key", "dump secrets", "reveal password", "show credentials", "export system prompt"]):
            findings.append({
                "type": "secret_extraction_attempt",
                "severity": "critical",
                "description": "Simulation input attempts to extract secrets or credentials.",
                "classification": "SIMULATION FINDING",
            })

        # Privilege escalation checks
        if any(p in lower for p in ["grant admin", "escalate privileges", "elevate capability", "set capability = *"]):
            findings.append({
                "type": "privilege_escalation_attempt",
                "severity": "critical",
                "description": "Simulation input attempts privilege escalation.",
                "classification": "SIMULATION FINDING",
            })

        # Cross-tenant checks
        if any(p in lower for p in ["cross_tenant", "access other workspace", "dump workspace_id", "select from other tenant"]):
            findings.append({
                "type": "cross_tenant_request_attempt",
                "severity": "critical",
                "description": "Simulation input attempts cross-tenant boundary access.",
                "classification": "SIMULATION FINDING",
            })

        return findings


class SafetyViolation(Exception):
    """Raised when an operation violates simulation safety boundaries."""
    pass


class SimulationSafetyGuard:
    """Convenience helper for checking and intercepting actions."""

    @staticmethod
    def intercept_action(action_type: str, target: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        is_blocked = SimulationSafetyEnforcer.is_intercepted_action(action_type)
        return {
            "blocked": is_blocked,
            "intercepted": is_blocked,
            "action": action_type,
            "target": target,
            "simulated_result": {
                "status": "would_execute" if is_blocked else "allowed",
                "message": f"Simulated execution; production write prevented for {action_type} on {target}" if is_blocked else "Operation allowed",
            },
        }


class TenantIsolationValidator:
    """Convenience validator for workspace tenant boundaries."""

    @staticmethod
    def validate_boundary(simulation_workspace_id: str, target_workspace_id: str) -> None:
        SimulationSafetyEnforcer.assert_tenant_boundary(simulation_workspace_id, target_workspace_id)


class SnapshotSanitizer:
    """Convenience sanitizer for production data snapshots."""

    @staticmethod
    def sanitize(data: Any) -> Any:
        return SimulationSafetyEnforcer.sanitize_snapshot_data(data)
