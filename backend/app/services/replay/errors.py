from typing import Any, Optional
from fastapi import status
from backend.app.core.errors import AppError


class ReplayError(AppError):
    """Base exception for all replay and debugging studio operations."""
    code: str = "REPLAY_ERROR"
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR


class ReplayNotFoundError(ReplayError):
    """Raised when a requested ReplayRun or original Run/WorkflowRun is not found."""
    code: str = "REPLAY_NOT_FOUND"
    status_code: int = status.HTTP_404_NOT_FOUND


class ReplayPermissionDeniedError(ReplayError):
    """Raised when access to a replay or original run is denied across workspace boundaries."""
    code: str = "REPLAY_PERMISSION_DENIED"
    status_code: int = status.HTTP_403_FORBIDDEN


class ReplayEligibilityError(ReplayError):
    """Raised when an execution is ineligible for replay (e.g., missing model, deleted task)."""
    code: str = "REPLAY_INELIGIBLE"
    status_code: int = status.HTTP_400_BAD_REQUEST


class SnapshotSanitizationError(ReplayError):
    """Raised when execution snapshot sanitization fails or exceeds memory ceilings."""
    code: str = "SNAPSHOT_SANITIZATION_FAILED"
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR


class SideEffectBlockedError(ReplayError):
    """Raised when an unauthorized external write or destructive operation is blocked during replay."""
    code: str = "SIDE_EFFECT_BLOCKED"
    status_code: int = status.HTTP_400_BAD_REQUEST


class ReplayConflictError(ReplayError):
    """Raised when a duplicate replay is already actively running."""
    code: str = "REPLAY_CONFLICT"
    status_code: int = status.HTTP_409_CONFLICT
