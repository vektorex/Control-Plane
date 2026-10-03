"""
Environment Isolation and Environment Management for Developer Platform.
Step 37: Public API, Developer Platform & SDK Layer.
"""
from typing import Set
from backend.app.services.developer_platform.errors import EnvironmentMismatchError

VALID_ENVIRONMENTS: Set[str] = {"development", "staging", "production"}


class EnvironmentManager:
    """Enforces strict isolation between development, staging, and production environments."""

    @classmethod
    def validate_environment(cls, environment: str) -> bool:
        return (environment or "").lower() in VALID_ENVIRONMENTS

    @classmethod
    def enforce_isolation(cls, key_environment: str, target_environment: str) -> None:
        """
        Enforces that credentials cannot be used across environments.
        Development credentials -> development resources only.
        Staging credentials -> staging resources only.
        Production credentials -> production resources only.
        """
        key_env = (key_environment or "").lower()
        target_env = (target_environment or "").lower()

        if key_env != target_env:
            raise EnvironmentMismatchError(key_env=key_env, target_env=target_env)
