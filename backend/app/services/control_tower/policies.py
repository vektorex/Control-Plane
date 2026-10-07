"""
Security policies for Step 45: Control Tower.
Detects unauthorized access patterns, cross-tenant queries, and metadata leakage.
"""
from backend.app.core.logging import logger


class ControlTowerPolicies:
    """Enforces security policies for Control Tower."""

    @staticmethod
    def validate_workspace_access(user_workspace_ids: list, requested_workspace_id: str) -> bool:
        """User may only access workspaces they belong to."""
        return requested_workspace_id in user_workspace_ids

    @staticmethod
    def validate_search_query(query: str) -> tuple[bool, str]:
        """
        Basic search query validation.
        Prevents SQL injection via parameterized queries in search_svc.
        """
        if not query or not query.strip():
            return False, "Search query cannot be empty"
        if len(query) > 500:
            return False, "Search query too long (max 500 characters)"
        return True, ""

    @staticmethod
    def validate_briefing_access(user_scopes: list) -> bool:
        """AI briefing requires explicit permission."""
        return "control_tower:briefing" in user_scopes or "admin" in user_scopes

    @staticmethod
    def validate_no_cross_tenant_data(
        result_workspace_id: str, user_workspace_id: str, result_type: str
    ) -> bool:
        """Verify search/attention results belong to the user's workspace."""
        if result_workspace_id != user_workspace_id:
            logger.warning(
                f"[CTPolicy] Cross-tenant data leak attempt detected: "
                f"result_type={result_type} result_ws={result_workspace_id} user_ws={user_workspace_id}"
            )
            return False
        return True

    @staticmethod
    def validate_count_exposure(
        section_key: str,
        user_scopes: list,
    ) -> bool:
        """
        Ensure counts don't leak restricted resource existence.
        Data Governance: restricted resources must not leak through count aggregation.
        """
        restricted_sections = {"security", "data_governance", "governance"}
        if section_key in restricted_sections:
            required = f"{section_key}:read"
            return required in user_scopes or "admin" in user_scopes
        return True
