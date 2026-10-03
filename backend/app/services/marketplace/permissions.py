"""
Marketplace Permission Declarations and Verification.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
from typing import Any, Dict, List, Set, Tuple
from backend.app.services.developer_platform.scopes import VALID_API_SCOPES, SENSITIVE_SCOPES


class MarketplacePermissionManager:
    """Validates requested package permissions against standard platform scope registry."""

    @classmethod
    def validate_permissions(cls, permissions_manifest: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Validates that all requested permissions exist in the platform registry.
        Returns (is_valid, unknown_permissions).
        """
        valid, unknown = cls.validate_declared_permissions(permissions_manifest)
        return len(unknown) == 0, unknown

    @classmethod
    def validate_declared_permissions(cls, declared: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
        """Validates permission entries supporting scope string or permissions list."""
        valid: List[str] = []
        unknown: List[str] = []
        for entry in declared:
            if not isinstance(entry, dict):
                continue
            perms = entry.get("permissions")
            if perms and isinstance(perms, list):
                for p in perms:
                    if p in VALID_API_SCOPES:
                        valid.append(p)
                    else:
                        unknown.append(p)
            elif "scope" in entry:
                s = entry["scope"]
                if s in VALID_API_SCOPES:
                    valid.append(s)
                else:
                    unknown.append(s)
        return valid, unknown

    @classmethod
    def identify_sensitive_permissions(cls, permissions_manifest: List[Dict[str, Any]]) -> List[str]:
        """Identifies any sensitive scopes that require explicit elevated organization authorization."""
        sensitive: List[str] = []
        for entry in permissions_manifest:
            if not isinstance(entry, dict):
                continue
            perms = entry.get("permissions", [])
            if perms and isinstance(perms, list):
                for perm in perms:
                    if perm in SENSITIVE_SCOPES:
                        sensitive.append(perm)
            elif "scope" in entry:
                if entry["scope"] in SENSITIVE_SCOPES:
                    sensitive.append(entry["scope"])
        return sensitive
