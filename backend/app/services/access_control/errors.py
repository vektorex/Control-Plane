"""
Custom exception hierarchy for Step 27: Multi-Tenant Organizations, Teams, Roles & Access Control.
"""
from typing import Any, Optional
from fastapi import status
from backend.app.core.errors import AppError


class AccessControlError(AppError):
    """Base exception for all access control, membership, and authorization errors."""
    code = "ACCESS_CONTROL_ERROR"
    status_code = status.HTTP_400_BAD_REQUEST


class PermissionDeniedError(AccessControlError):
    """Raised when an authenticated user lacks the required permission for an operation."""
    code = "PERMISSION_DENIED"
    status_code = status.HTTP_403_FORBIDDEN


class TenantIsolationError(AccessControlError):
    """Raised when a cross-tenant or unpermitted boundary access is attempted."""
    code = "TENANT_ACCESS_DENIED"
    status_code = status.HTTP_403_FORBIDDEN


class ResourceNotFoundError(AccessControlError):
    """Raised when a resource does not exist or is invisible due to tenancy scoping."""
    code = "NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND


class InvitationError(AccessControlError):
    """Raised when invitation creation, acceptance, or revocation fails."""
    code = "INVITATION_ERROR"
    status_code = status.HTTP_400_BAD_REQUEST


class OwnershipTransferError(AccessControlError):
    """Raised when organization ownership transfer validation fails."""
    code = "OWNERSHIP_TRANSFER_ERROR"
    status_code = status.HTTP_400_BAD_REQUEST


class QuotaExceededError(AccessControlError):
    """Raised when an organization, workspace, or project reaches membership safety limits."""
    code = "QUOTA_EXCEEDED"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
