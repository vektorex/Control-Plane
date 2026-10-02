"""
Exception types for Step 24: Durable Background Job System.
"""
from fastapi import status
from backend.app.core.errors import AppError


class JobError(AppError):
    """Base exception for durable job failures."""
    code = "JOB_ERROR"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class JobNotFoundError(JobError):
    code = "JOB_NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND


class JobValidationError(JobError):
    code = "JOB_VALIDATION_ERROR"
    status_code = status.HTTP_400_BAD_REQUEST


class JobStateError(JobError):
    code = "JOB_STATE_ERROR"
    status_code = status.HTTP_409_CONFLICT


class JobCancellationError(JobError):
    code = "JOB_CANCELLED"
    status_code = status.HTTP_400_BAD_REQUEST


class JobConcurrencyError(JobError):
    code = "JOB_CONCURRENCY_EXCEEDED"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS


class JobHandlerNotFoundError(JobError):
    code = "JOB_HANDLER_NOT_FOUND"
    status_code = status.HTTP_400_BAD_REQUEST


class JobLeaseExpiredError(JobError):
    code = "JOB_LEASE_EXPIRED"
    status_code = status.HTTP_409_CONFLICT


class JobPermissionDeniedError(JobError):
    code = "JOB_PERMISSION_DENIED"
    status_code = status.HTTP_403_FORBIDDEN
