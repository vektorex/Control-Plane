"""
Exceptions hierarchy for Step 39: Multi-User Collaboration, Shared AI Workspaces & Real-Time Co-Execution.
"""
from typing import Any, Dict, Optional
from fastapi import status


class CollaborationException(Exception):
    """Base exception for all collaboration domain errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class SessionNotFoundError(CollaborationException):
    def __init__(self, session_id: str):
        super().__init__(
            f"Collaboration session '{session_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"session_id": session_id},
        )


class ParticipantNotFoundError(CollaborationException):
    def __init__(self, user_id: str, session_id: str):
        super().__init__(
            f"User '{user_id}' is not a participant in collaboration session '{session_id}'.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"user_id": user_id, "session_id": session_id},
        )


class UnauthorizedSessionAccessError(CollaborationException):
    def __init__(self, message: str = "Access to collaboration session denied."):
        super().__init__(
            message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ConflictError(CollaborationException):
    """Optimistic concurrency conflict error (HTTP 409)."""

    def __init__(
        self,
        resource_id: str,
        current_version: int,
        expected_version: int,
        message: Optional[str] = None,
    ):
        msg = (
            message
            or f"Resource '{resource_id}' version conflict. Current: {current_version}, expected: {expected_version}."
        )
        super().__init__(
            msg,
            status_code=status.HTTP_409_CONFLICT,
            details={
                "resource_id": resource_id,
                "current_version": current_version,
                "expected_version": expected_version,
            },
        )
        self.resource_id = resource_id
        self.current_version = current_version
        self.expected_version = expected_version


class LockConflictError(CollaborationException):
    def __init__(self, resource_id: str, owner_id: str):
        super().__init__(
            f"Resource '{resource_id}' is currently locked by user '{owner_id}'.",
            status_code=status.HTTP_423_LOCKED,
            details={"resource_id": resource_id, "owner_id": owner_id},
        )
        self.resource_id = resource_id
        self.owner_id = owner_id


class CommentNotFoundError(CollaborationException):
    def __init__(self, comment_id: str):
        super().__init__(
            f"Comment '{comment_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"comment_id": comment_id},
        )


class AssignmentNotFoundError(CollaborationException):
    def __init__(self, assignment_id: str):
        super().__init__(
            f"Assignment '{assignment_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"assignment_id": assignment_id},
        )


class AnnotationNotFoundError(CollaborationException):
    def __init__(self, annotation_id: str):
        super().__init__(
            f"Annotation '{annotation_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"annotation_id": annotation_id},
        )


class CoExecutionError(CollaborationException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details or {},
        )


class InvalidSessionStateError(CollaborationException):
    def __init__(self, message: str):
        super().__init__(
            message,
            status_code=status.HTTP_409_CONFLICT,
        )
