"""
API Versioning and Version Resolution for Public API.
Step 37: Public API, Developer Platform & SDK Layer.
"""
from typing import Dict, List


SUPPORTED_VERSIONS: List[str] = ["v1"]
CURRENT_VERSION: str = "v1"


class APIVersionResolver:
    """Resolves and validates public API version contracts."""

    @classmethod
    def get_supported_versions(cls) -> List[str]:
        return list(SUPPORTED_VERSIONS)

    @classmethod
    def is_supported(cls, version: str) -> bool:
        return version in SUPPORTED_VERSIONS

    @classmethod
    def get_version_metadata(cls) -> Dict[str, str]:
        return {
            "current_version": CURRENT_VERSION,
            "supported_versions": ",".join(SUPPORTED_VERSIONS),
            "status": "stable",
        }
