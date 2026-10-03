"""
Marketplace Package Builder.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
import hashlib
import json
from typing import Any, Dict, List, Optional
from backend.app.services.marketplace.validator import PackageValidator


class MarketplacePackageBuilder:
    """Helper to assemble, inspect, and hash package manifests and components."""

    @staticmethod
    def compute_content_hash(components: List[Dict[str, Any]]) -> str:
        """Computes deterministic SHA-256 hash of all package components."""
        # Sort components by ID for determinism
        sorted_comps = sorted(components, key=lambda c: str(c.get("id", "")))
        serialized = json.dumps(sorted_comps, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def compute_manifest_hash(manifest: Dict[str, Any]) -> str:
        """Computes deterministic SHA-256 hash of the complete manifest."""
        serialized = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def preview_package(cls, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts high-level preview of package requirements for installer inspection:
        components, permissions, data access, external actions, dependencies, and configuration.
        """
        PackageValidator.validate_manifest(manifest)

        components = manifest.get("components", [])
        permissions = manifest.get("permissions", [])
        dependencies = manifest.get("dependencies", [])
        configuration = manifest.get("configuration", {})

        # Summarize requested permissions and data access
        all_perms = []
        for p in permissions:
            if isinstance(p, dict):
                if p.get("permissions") and isinstance(p["permissions"], list):
                    all_perms.extend(p["permissions"])
                elif p.get("scope"):
                    all_perms.append(p["scope"])

        data_access = [p for p in all_perms if "read" in p or "documents" in p or "artifacts" in p or "memory" in p or "knowledge" in p]
        external_actions = [p for p in all_perms if "connectors" in p or "webhooks" in p or "run" in p]

        from backend.app.services.marketplace.security_scanner import MarketplaceSecurityScanner
        sec_status, findings = MarketplaceSecurityScanner.scan_manifest(manifest)

        return {
            "name": manifest.get("package", {}).get("name"),
            "version": manifest.get("package", {}).get("version"),
            "type": manifest.get("package", {}).get("type"),
            "component_count": len(components),
            "components": [{"id": c.get("id") or c.get("identifier"), "name": c.get("name"), "type": c.get("type")} for c in components],
            "requested_permissions": all_perms,
            "data_access": data_access,
            "external_actions": external_actions,
            "dependencies": dependencies,
            "variables": list(configuration.get("variables", {}).keys()) if isinstance(configuration, dict) else [],
            "content_hash": cls.compute_content_hash(components),
            "manifest_hash": cls.compute_manifest_hash(manifest),
            "security_status": sec_status.value if hasattr(sec_status, "value") else str(sec_status),
            "security_findings": findings,
        }

