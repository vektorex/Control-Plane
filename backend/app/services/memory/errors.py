"""
Domain exceptions for the Memory System.
"""
from typing import List, Optional
from backend.app.core.errors import AppError


class MemoryError(AppError):
    """Base exception for all memory operations."""
    def __init__(self, message: str = "Memory operation error occurred.", status_code: int = 400):
        super().__init__(message=message, status_code=status_code)


class MemoryNotFoundError(MemoryError):
    """Raised when a requested memory, suggestion, or conflict cannot be found."""
    def __init__(self, memory_id: str):
        super().__init__(message=f"Memory '{memory_id}' not found.", status_code=404)


class MemoryPermissionError(MemoryError):
    """Raised when unauthorized access to a scoped memory or foreign workspace is attempted."""
    def __init__(self, message: str = "Access to memory is denied due to scope or workspace isolation."):
        super().__init__(message=message, status_code=403)


class MemoryValidationError(MemoryError):
    """Raised when memory inputs violate schema or size constraints."""
    def __init__(self, message: str):
        super().__init__(message=message, status_code=422)


class MemorySecretDetectedError(MemoryError):
    """
    Raised when raw credentials, tokens, or private secrets are detected in candidate memory.
    The secret itself is NEVER echoed back to the caller.
    """
    def __init__(self, detected_categories: Optional[List[str]] = None):
        cats = ", ".join(detected_categories) if detected_categories else "sensitive credential patterns"
        message = (
            f"Memory persistence rejected: Potential secret or credential data detected ({cats}). "
            f"The platform prevents persistent storage of credentials, tokens, and private secrets."
        )
        super().__init__(message=message, status_code=400)


class MemoryConflictError(MemoryError):
    """Raised when memory conflict state or resolution is invalid."""
    def __init__(self, message: str = "Memory conflict operation failed."):
        super().__init__(message=message, status_code=409)


class MemoryScopeError(MemoryError):
    """Raised when scope rules (e.g. project missing project_id, user missing user_id) are violated."""
    def __init__(self, message: str = "Invalid memory scope specification."):
        super().__init__(message=message, status_code=422)
