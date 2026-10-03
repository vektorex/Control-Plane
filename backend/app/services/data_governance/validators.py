"""
Validators for Step 33: Data Governance, Privacy & Compliance Evidence Layer.
"""
from typing import List, Optional

from backend.app.services.data_governance.exceptions import (
    LegalHoldActiveError,
    UnauthorizedClassificationDowngradeError,
    ExportSanitizationError,
)

CLASSIFICATION_LEVELS = {
    "public": 1,
    "internal": 2,
    "confidential": 3,
    "restricted": 4,
}


def validate_classification_transition(
    current_classification: str,
    target_classification: str,
    detected_by: str,
    is_admin: bool = False,
) -> None:
    """
    Ensures that automated classification cannot silently downgrade
    confidential or restricted data. Only explicit authorized user review may reduce classification.
    """
    curr_lvl = CLASSIFICATION_LEVELS.get(current_classification.lower(), 2)
    target_lvl = CLASSIFICATION_LEVELS.get(target_classification.lower(), 2)

    if target_lvl < curr_lvl:
        # Downgrade attempt
        if curr_lvl >= CLASSIFICATION_LEVELS["confidential"]:
            if detected_by != "user_confirmed" or not is_admin:
                raise UnauthorizedClassificationDowngradeError(
                    f"Cannot downgrade classification from '{current_classification}' to '{target_classification}' "
                    f"via automated source '{detected_by}'. Explicit authorized administrator confirmation required."
                )


def validate_not_under_legal_hold(
    asset_id: str,
    active_holds_for_asset: List[str],
) -> None:
    """
    Validates that an asset is not associated with any active legal holds before destructive action.
    """
    if active_holds_for_asset:
        holds_str = ", ".join(active_holds_for_asset)
        raise LegalHoldActiveError(
            f"Asset '{asset_id}' is protected by active legal hold(s): {holds_str}. Destructive action blocked."
        )


def validate_export_scope(scope_type: str, scope_id: str) -> None:
    """
    Validates export scope parameters against directory traversal or injection attempts.
    """
    if ".." in scope_id or "/" in scope_id or "\\" in scope_id:
        raise ExportSanitizationError(f"Malformed or unsafe scope_id: '{scope_id}'.")
    valid_scopes = {"asset", "resource", "workspace", "project", "user", "organization"}
    if scope_type not in valid_scopes:
        raise ExportSanitizationError(f"Invalid export scope_type '{scope_type}'. Must be one of {valid_scopes}.")
