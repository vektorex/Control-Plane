"""
Custom domain exceptions for Step 34: AI Security Operations, Threat Detection & Incident Response Layer.
"""
from typing import Optional


class SecurityError(Exception):
    """Base exception for all security operations domain errors."""
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.detail = detail or message


class SecuritySignalNotFoundError(SecurityError):
    """Raised when a requested security signal does not exist."""
    pass


class SecurityIncidentNotFoundError(SecurityError):
    """Raised when a requested security incident does not exist."""
    pass


class ContainmentActionBlockedError(SecurityError):
    """Raised when a containment action is blocked by governance, legal hold, or policy."""
    pass


class UnauthorizedContainmentError(SecurityError):
    """Raised when an actor lacks sufficient privileges to execute containment."""
    pass


class InvalidPlaybookActionError(SecurityError):
    """Raised when a playbook attempts to execute an action not on the strict allowlist."""
    pass


class AISelfAuthorizationBlockedError(SecurityError):
    """Raised when an automated AI agent or model attempts to self-authorize containment or security overrides."""
    pass


class TenantIsolationSecurityError(SecurityError):
    """Raised when a security operation violates organization or workspace boundaries."""
    pass
