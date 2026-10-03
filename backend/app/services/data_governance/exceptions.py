"""
Domain exceptions for Step 33: Data Governance, Privacy & Compliance Evidence Layer.
"""
from typing import Optional


class DataGovernanceError(Exception):
    """Base exception for all data governance errors."""

    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.detail = detail or message


class DataAssetNotFoundError(DataGovernanceError):
    """Raised when a requested data asset cannot be found."""
    pass


class LegalHoldActiveError(DataGovernanceError):
    """Raised when an operation is blocked due to an active legal hold."""
    pass


class DeletionBlockedError(DataGovernanceError):
    """Raised when an asset deletion is blocked by policy, dependencies, or holds."""
    pass


class UnauthorizedClassificationDowngradeError(DataGovernanceError):
    """Raised when attempting an unauthorized downgrade of sensitive/confidential/restricted classification."""
    pass


class InvalidLineageError(DataGovernanceError):
    """Raised when lineage cycle or malformed relationship is detected."""
    pass


class PrivacyRequestError(DataGovernanceError):
    """Raised when a privacy workflow request fails validation or state transition."""
    pass


class ExportSanitizationError(DataGovernanceError):
    """Raised when data export sanitization fails or unauthorized secrets are encountered."""
    pass


class EvidenceVerificationError(DataGovernanceError):
    """Raised when cryptographic evidence chain verification fails."""
    pass


class RetentionPolicyConflictError(DataGovernanceError):
    """Raised when retention policy resolution encounters irreconcilable conflicts."""
    pass
