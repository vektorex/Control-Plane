"""
Marketplace Domain Exceptions.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
from typing import Any, Dict, List, Optional


class MarketplaceException(Exception):
    """Base exception for all marketplace errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        code: str = "marketplace_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}


class PackageNotFoundError(MarketplaceException):
    def __init__(self, identifier: str):
        super().__init__(
            f"Marketplace package '{identifier}' was not found.",
            status_code=404,
            code="package_not_found",
        )


class PackageVersionNotFoundError(MarketplaceException):
    def __init__(self, package_id: str, version: str):
        super().__init__(
            f"Package version '{version}' for package '{package_id}' was not found.",
            status_code=404,
            code="package_version_not_found",
        )


class PackageValidationError(MarketplaceException):
    def __init__(self, message: str, validation_errors: Optional[List[str]] = None):
        super().__init__(
            message,
            status_code=422,
            code="package_validation_error",
            details={"errors": validation_errors or []},
        )


class PackageSecurityBlockedError(MarketplaceException):
    def __init__(self, message: str, findings: Optional[List[str]] = None):
        super().__init__(
            message,
            status_code=403,
            code="package_security_blocked",
            details={"findings": findings or []},
        )


class PackageIncompatibleError(MarketplaceException):
    def __init__(self, message: str, missing_capabilities: Optional[List[str]] = None):
        super().__init__(
            message,
            status_code=422,
            code="package_incompatible",
            details={"missing_capabilities": missing_capabilities or []},
        )


class DependencyResolutionError(MarketplaceException):
    def __init__(self, message: str, cycle: Optional[List[str]] = None):
        super().__init__(
            message,
            status_code=422,
            code="dependency_resolution_error",
            details={"cycle": cycle or []},
        )


class PackageAlreadyInstalledError(MarketplaceException):
    def __init__(self, package_id: str, scope_id: str):
        super().__init__(
            f"Package '{package_id}' is already installed in target scope '{scope_id}'.",
            status_code=409,
            code="package_already_installed",
        )


class PackageInstallationNotFoundError(MarketplaceException):
    def __init__(self, installation_id: str):
        super().__init__(
            f"Package installation '{installation_id}' was not found.",
            status_code=404,
            code="installation_not_found",
        )


class RollbackNotAllowedError(MarketplaceException):
    def __init__(self, message: str, reason: str = ""):
        super().__init__(
            f"Rollback not permitted: {message}",
            status_code=400,
            code="rollback_disallowed",
            details={"reason": reason},
        )


class PackageRevokedError(MarketplaceException):
    def __init__(self, package_id: str, version: str):
        super().__init__(
            f"Package '{package_id}' version '{version}' has been revoked for security or policy violations.",
            status_code=403,
            code="package_revoked",
        )


class MarketplaceGovernanceDeniedError(MarketplaceException):
    def __init__(self, message: str, policy_name: Optional[str] = None):
        super().__init__(
            f"Governance evaluation denied marketplace operation: {message}",
            status_code=403,
            code="marketplace_governance_denied",
            details={"policy_name": policy_name},
        )
