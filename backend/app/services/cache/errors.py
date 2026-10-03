"""
Exception hierarchy for Step 31: Semantic Cache and Intelligent Reuse Layer.
"""
from backend.app.core.errors import AppError


class CacheError(AppError):
    """Base exception for all semantic cache errors."""
    pass


class CacheLookupError(CacheError):
    """Raised when cache query or retrieval encounters an unrecoverable failure."""
    pass


class CacheAdmissionError(CacheError):
    """Raised when an entry fails validation during cache admission."""
    pass


class CacheInvalidationError(CacheError):
    """Raised when an invalidation directive fails."""
    pass


class CachePolicyViolationError(CacheError):
    """Raised when a cache operation violates workspace or tenant policy."""
    pass


class CacheSecurityError(CacheError):
    """Raised when a cross-tenant, cross-user, or unauthorized cache access is attempted."""
    pass


class CacheStorageLimitExceededError(CacheError):
    """Raised when the workspace cache storage limit is exceeded."""
    pass
