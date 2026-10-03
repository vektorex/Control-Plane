"""
Domain exceptions for Step 36: Disaster Recovery, Backup & Business Continuity Layer.
"""


class DisasterRecoveryError(Exception):
    """Base exception for all disaster recovery operations."""
    pass


class BackupNotFoundError(DisasterRecoveryError):
    """Raised when a referenced backup run or snapshot cannot be found."""
    pass


class BackupIntegrityError(DisasterRecoveryError):
    """Raised when backup content hash, manifest hash, or signature check fails."""
    pass


class ManifestTamperedError(DisasterRecoveryError):
    """Raised when a manifest cryptographic signature or hash does not match content."""
    pass


class RestorePreconditionFailedError(DisasterRecoveryError):
    """Raised when pre-flight restore checks fail (e.g. unverified backup, policy veto)."""
    pass


class CrossTenantRestoreBlockedError(DisasterRecoveryError):
    """Raised when an attempt is made to restore a backup into a different tenant/organization."""
    pass


class ElevatedAuthorizationRequiredError(DisasterRecoveryError):
    """Raised when replace-existing or production restore lacks elevated administrative privileges."""
    pass


class ReplaceExistingNotPermittedError(DisasterRecoveryError):
    """Raised when replace_existing conflict policy is invoked without explicit HITL approval."""
    pass


class LegalHoldConflictError(DisasterRecoveryError):
    """Raised when attempting to expire/delete a backup containing active legal-held assets,
    or attempting to overwrite an asset under legal hold during restore."""
    pass


class DeletedDataResurrectionBlockedError(DisasterRecoveryError):
    """Raised when a restore attempt would silently resurrect data that was legally deleted under Step 33."""
    pass


class GovernanceDowngradeBlockedError(DisasterRecoveryError):
    """Raised when attempting to restore a historical governance policy that weakens current security."""
    pass


class ProductionExerciseBlockedError(DisasterRecoveryError):
    """Raised when a disaster recovery exercise targets production without explicit Governance + HITL authorization."""
    pass


class StorageProviderError(DisasterRecoveryError):
    """Raised when physical or logical backup storage operations fail."""
    pass


class BackupEncryptionError(DisasterRecoveryError):
    """Raised when backup encryption or decryption fails."""
    pass


class InvalidRestorePlanError(DisasterRecoveryError):
    """Raised when a restore plan definition is invalid or unexecutable."""
    pass


class RecoveryObjectiveNotFoundError(DisasterRecoveryError):
    """Raised when a requested recovery objective does not exist."""
    pass


class StaleBackupWarning(DisasterRecoveryError):
    """Raised/logged when a backup exceeds its configured RPO window."""
    pass
