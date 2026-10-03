"""
Safety and policy validators for Step 36: Disaster Recovery & Business Continuity.
"""
from typing import Any, Dict, List, Optional
import re

from backend.app.services.disaster_recovery.exceptions import (
    CrossTenantRestoreBlockedError,
    ElevatedAuthorizationRequiredError,
    ReplaceExistingNotPermittedError,
    ProductionExerciseBlockedError,
    DeletedDataResurrectionBlockedError,
    LegalHoldConflictError,
    DisasterRecoveryError,
)

SECRET_KEY_PATTERNS = [
    re.compile(r"api[-_]?key", re.IGNORECASE),
    re.compile(r"secret[-_]?key", re.IGNORECASE),
    re.compile(r"access[-_]?token", re.IGNORECASE),
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"private[-_]?key", re.IGNORECASE),
    re.compile(r"credentials?", re.IGNORECASE),
]


def validate_tenant_restore_boundary(
    backup_org_id: str,
    target_org_id: str,
    target_environment: str = "sandbox",
) -> None:
    """
    Ensure backup from organization A cannot be restored into organization B.
    Cross-organization restore is strictly prohibited.
    """
    if backup_org_id != target_org_id:
        raise CrossTenantRestoreBlockedError(
            f"Cross-tenant restore is strictly prohibited: Backup belongs to organization '{backup_org_id}', "
            f"cannot restore into '{target_org_id}'."
        )


def validate_no_secrets_in_backup_payload(data: Any, path: str = "root") -> None:
    """
    Recursively check that raw credentials or secret values are not stored in plaintext inside backup payloads.
    """
    if isinstance(data, dict):
        for k, v in data.items():
            current_path = f"{path}.{k}"
            for pattern in SECRET_KEY_PATTERNS:
                if pattern.search(str(k)):
                    if isinstance(v, str) and len(v) > 0 and not v.startswith("ref://") and not v.startswith("vault://") and not v.startswith("[REDACTED"):
                        raise DisasterRecoveryError(
                            f"Plaintext secret detected in backup payload at '{current_path}'. "
                            f"Use secure secret reference or encryption abstraction instead."
                        )
            validate_no_secrets_in_backup_payload(v, current_path)
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            validate_no_secrets_in_backup_payload(item, f"{path}[{idx}]")


def validate_replace_existing_conflict_policy(
    conflict_policy: str,
    user_role: str = "member",
    has_hitl_approval: bool = False,
) -> None:
    """
    Enforce that 'replace_existing' requires elevated administrative privileges and explicit HITL approval.
    """
    if conflict_policy == "replace_existing":
        if user_role not in ["admin", "owner", "superadmin"]:
            raise ElevatedAuthorizationRequiredError(
                "Conflict policy 'replace_existing' requires administrative privileges (admin or owner)."
            )
        if not has_hitl_approval:
            raise ReplaceExistingNotPermittedError(
                "Conflict policy 'replace_existing' overwrites production data and requires explicit Step 18 HITL approval."
            )


def validate_production_exercise_safety(
    environment: str,
    has_governance_approval: bool = False,
    has_hitl_approval: bool = False,
) -> None:
    """
    Enforce that disaster recovery exercises in production are disabled by default
    and require both Step 32 Governance and Step 18 HITL authorization.
    """
    if environment == "production":
        if not (has_governance_approval and has_hitl_approval):
            raise ProductionExerciseBlockedError(
                "Disaster recovery exercises against production are disabled by default and require "
                "both Step 32 Governance clearance and Step 18 HITL approval."
            )


def validate_restore_data_lifecycle(
    resource_id: str,
    is_legally_deleted: bool = False,
    is_under_legal_hold: bool = False,
    mode: str = "sandbox",
) -> None:
    """
    Prevent silent resurrection of legally deleted data (Step 33) and respect active legal holds.
    """
    if is_legally_deleted:
        raise DeletedDataResurrectionBlockedError(
            f"Resource '{resource_id}' was legally deleted under Step 33 Data Governance. "
            f"Silent resurrection is prohibited."
        )
    if is_under_legal_hold and mode != "sandbox":
        raise LegalHoldConflictError(
            f"Resource '{resource_id}' is subject to an active Legal Hold. Modifications during restore are restricted."
        )
