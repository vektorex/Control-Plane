"""
Marketplace Compatibility Checker.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
from typing import Any, Dict, List, Tuple
from backend.app.services.marketplace.exceptions import PackageIncompatibleError

CURRENT_PLATFORM_VERSION = "1.0.0"

SUPPORTED_MODEL_CAPABILITIES = {
    "vision",
    "structured_output",
    "streaming",
    "large_context",
    "audio_input",
    "multimodal_input",
}


class CompatibilityChecker:
    """Evaluates package compatibility against platform version and supported capabilities."""

    @classmethod
    def check_compatibility(
        cls,
        compatibility_manifest: Dict[str, Any],
        available_capabilities: List[str] = None,
    ) -> Tuple[str, List[str]]:
        """
        Returns (status, reasons).
        status is one of: 'compatible', 'compatible_with_warnings', 'incompatible'.
        """
        if not compatibility_manifest:
            return "compatible", []

        reasons: List[str] = []
        is_incompatible = False
        avail_caps = set(available_capabilities or SUPPORTED_MODEL_CAPABILITIES)

        # 1. Platform version check
        min_ver = compatibility_manifest.get("platform_min_version")
        if min_ver:
            if min_ver > CURRENT_PLATFORM_VERSION:
                reasons.append(f"Platform version {CURRENT_PLATFORM_VERSION} is lower than required {min_ver}.")
                is_incompatible = True

        # 2. Required model capabilities
        req_caps = compatibility_manifest.get("required_capabilities") or compatibility_manifest.get("model_capabilities") or []
        missing = [cap for cap in req_caps if cap not in avail_caps]
        if missing:
            reasons.append(f"Missing required model/platform capabilities: {', '.join(missing)}.")
            is_incompatible = True

        if is_incompatible:
            return "incompatible", reasons
        elif reasons:
            return "compatible_with_warnings", reasons
        return "compatible", []
