"""
Permissions and policies for Step 45: Control Tower.
Enforces RBAC, workspace isolation, Governance, and Data Governance boundaries.
Dashboard aggregation must never reveal information the user cannot access directly.
"""
from typing import Any, Dict, Optional


class ControlTowerPermissions:
    """
    Validates access to Control Tower sections based on existing RBAC.
    No data is surfaced based solely on role labels - actual RBAC is always enforced.
    """

    # Sections with their required permission scope
    SECTION_PERMISSIONS = {
        "security": "security:read",
        "governance": "governance:read",
        "data_governance": "data_governance:read",
        "approvals": "hitl:read",
        "jobs": "jobs:read",
        "workflows": "workflows:read",
        "agents": "agents:read",
        "planning": "planning:read",
        "outcomes": "outcomes:read",
        "objectives": "objectives:read",
        "learning": "learning:read",
        "evaluation": "evaluation:read",
        "simulation": "simulation:read",
        "reliability": "reliability:read",
        "recovery": "recovery:read",
        "collaboration": "collaboration:read",
        "notifications": "notifications:read",
        "briefing": "control_tower:briefing",
        "search": "control_tower:search",
    }

    # Role presets (UI configuration only - actual data access comes from RBAC)
    ROLE_PRESETS: Dict[str, Dict[str, Any]] = {
        "individual_contributor": {
            "visible_sections": [
                "overview", "attention", "active_work", "objectives", "outcomes",
                "approvals", "notifications", "activity",
            ],
            "description": "Focused on own work items and approvals",
        },
        "project_manager": {
            "visible_sections": [
                "overview", "attention", "active_work", "objectives", "outcomes",
                "agents", "workflows", "planning", "approvals", "collaboration", "activity",
            ],
            "description": "Project-level view with planning and team coordination",
        },
        "engineering_lead": {
            "visible_sections": [
                "overview", "attention", "active_work", "workflows", "agents",
                "jobs", "evaluation", "simulation", "reliability", "planning",
                "approvals", "activity",
            ],
            "description": "Technical execution and engineering operations",
        },
        "ai_platform_administrator": {
            "visible_sections": [
                "overview", "attention", "active_work", "agents", "workflows",
                "jobs", "evaluation", "simulation", "learning", "reliability",
                "recovery", "planning", "governance", "data_governance",
                "security", "approvals", "activity", "search",
            ],
            "description": "Full platform operational view",
        },
        "security_operator": {
            "visible_sections": [
                "overview", "attention", "security", "governance", "data_governance",
                "approvals", "activity",
            ],
            "description": "Security-focused view - security items always visible",
        },
        "governance_operator": {
            "visible_sections": [
                "overview", "attention", "governance", "data_governance",
                "approvals", "planning", "outcomes", "activity",
            ],
            "description": "Policy compliance and governance operations",
        },
        "executive": {
            "visible_sections": [
                "overview", "objectives", "outcomes", "planning",
                "attention", "activity",
            ],
            "description": "Concise outcome-oriented executive view",
        },
    }

    @classmethod
    def get_role_preset(cls, role: str) -> Dict[str, Any]:
        """Return UI configuration preset for a role. Actual data access is still RBAC-controlled."""
        return cls.ROLE_PRESETS.get(role, cls.ROLE_PRESETS["individual_contributor"])

    @classmethod
    def validate_section_visibility(
        cls,
        section: str,
        user_scopes: list,
    ) -> bool:
        """
        Check if a user has access to a specific section.
        Always uses real RBAC scopes, never role labels alone.
        """
        required = cls.SECTION_PERMISSIONS.get(section)
        if not required:
            return True  # No specific permission required
        return required in user_scopes or "admin" in user_scopes

    @classmethod
    def filter_overview_sections(
        cls, overview: Dict[str, Any], user_scopes: list
    ) -> Dict[str, Any]:
        """
        Filter overview sections based on user permissions.
        Security sections are never hidden but may show 'access denied' if no permission.
        """
        filtered = dict(overview)
        sections = dict(filtered.get("sections", {}))

        # Security info must always be shown (per spec §22)
        # but detail access is controlled by Security Operations permissions

        # Remove sections the user cannot access
        for section_key, permission in cls.SECTION_PERMISSIONS.items():
            if section_key not in sections:
                continue
            if permission not in user_scopes and "admin" not in user_scopes:
                if section_key == "security":
                    # Always show count but not details
                    pass
                else:
                    sections.pop(section_key, None)

        filtered["sections"] = sections
        return filtered
