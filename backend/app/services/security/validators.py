"""
Security validators for Step 34.
Enforces containment allowlists, prevents AI self-authorization, and validates tenant boundaries.
"""
import re
from typing import Any, Dict, List
from backend.app.services.security.exceptions import (
    AISelfAuthorizationBlockedError,
    InvalidPlaybookActionError,
    TenantIsolationSecurityError,
    UnauthorizedContainmentError,
)

CONTAINMENT_ALLOWLIST = {
    "pause_workflow",
    "pause_trigger",
    "cancel_job",
    "disable_connector_credential",
    "revoke_session",
    "quarantine_artifact",
    "invalidate_cache",
    "require_approval",
    "increase_logging",
    "notify_admin",
    "create_privacy_request",
    "create_governance_review",
}

DISALLOWED_PATTERNS = [
    re.compile(r"exec\s*\(", re.IGNORECASE),
    re.compile(r"eval\s*\(", re.IGNORECASE),
    re.compile(r"subprocess", re.IGNORECASE),
    re.compile(r"bash|sh|cmd\.exe|powershell", re.IGNORECASE),
    re.compile(r"curl|wget|fetch|requests\.", re.IGNORECASE),
]


def validate_containment_action(action_type: str) -> None:
    """
    Validates that a requested containment action is on the strict allowlist.
    Prevents arbitrary code execution, shell commands, and untrusted HTTP requests.
    """
    if action_type not in CONTAINMENT_ALLOWLIST:
        raise InvalidPlaybookActionError(
            f"Action '{action_type}' is not on the strict containment allowlist. "
            f"Allowed actions: {', '.join(sorted(CONTAINMENT_ALLOWLIST))}"
        )


def validate_playbook_actions(actions: List[Dict[str, Any]]) -> None:
    """
    Validates all actions declared in a playbook against allowlist and safety patterns.
    """
    for act in actions:
        action_name = act.get("action") or act.get("type")
        if not action_name:
            raise InvalidPlaybookActionError("Playbook action missing 'action' or 'type' field.")
        validate_containment_action(action_name)

        # Check for arbitrary commands or shell snippets in parameters
        params_str = str(act.get("parameters") or {})
        for pat in DISALLOWED_PATTERNS:
            if pat.search(params_str):
                raise InvalidPlaybookActionError(
                    f"Playbook action parameter contains disallowed command pattern: {pat.pattern}"
                )


def validate_not_ai_self_authorizing(actor_type: str, action_name: str) -> None:
    """
    Ensures that an AI model or autonomous agent cannot self-authorize containment,
    grant itself elevated permissions, or override security policies.
    """
    normalized_actor = (actor_type or "").lower().strip()
    if normalized_actor in {"ai", "model", "agent", "llm", "ai_system", "bot"}:
        raise AISelfAuthorizationBlockedError(
            f"AI model/agent '{actor_type}' cannot self-authorize security action '{action_name}'. "
            "Deterministic policies, RBAC, or human approval are strictly required."
        )


def validate_tenant_boundaries(
    target_org_id: str,
    subject_org_id: str,
    operation: str = "security_operation",
) -> None:
    """
    Strictly prevents cross-organization access or correlation across disparate tenants.
    """
    if not target_org_id or not subject_org_id or str(target_org_id) != str(subject_org_id):
        raise TenantIsolationSecurityError(
            f"Tenant isolation violation in {operation}: target tenant {target_org_id} does not match {subject_org_id}."
        )
