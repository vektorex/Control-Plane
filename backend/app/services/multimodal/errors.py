"""
Custom error definitions for Step 30: Multimodal AI and Unified Artifact Intelligence.
"""
from typing import Any, Dict, Optional
from backend.app.core.errors import AppError


class MultimodalError(AppError):
    """Base error for all multimodal and artifact operations."""
    def __init__(self, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status_code)
        self.details = details or {}


class ArtifactNotFoundError(MultimodalError):
    def __init__(self, message: str = "Artifact not found."):
        super().__init__(message=message, status_code=404)


class UnsupportedMimeTypeError(MultimodalError):
    def __init__(self, message: str = "Unsupported MIME type or file format."):
        super().__init__(message=message, status_code=415)


class MimeSpoofingError(MultimodalError):
    def __init__(self, message: str = "File extension does not match true content signature."):
        super().__init__(message=message, status_code=400)


class FileLimitExceededError(MultimodalError):
    def __init__(self, message: str = "File size, duration, or dimensions exceed server limits."):
        super().__init__(message=message, status_code=413)


class ArtifactAccessDeniedError(MultimodalError):
    def __init__(self, message: str = "Access to artifact denied across tenant boundaries."):
        super().__init__(message=message, status_code=403)


class CapabilityUnavailableError(MultimodalError):
    def __init__(self, message: str = "Required multimodal capability is unavailable."):
        super().__init__(message=message, status_code=501)


class DecompressionBombError(MultimodalError):
    def __init__(self, message: str = "Oversized image or decompression bomb detected."):
        super().__init__(message=message, status_code=400)
