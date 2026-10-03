"""
Domain errors for Step 28: Prompt Management, Versioning, Release, and Experimentation.
"""
from typing import Any, Optional
from fastapi import status
from backend.app.core.errors import AppError


class PromptError(AppError):
    """Base exception for all prompt management domain errors."""
    code = "PROMPT_ERROR"
    status_code = status.HTTP_400_BAD_REQUEST


class PromptNotFoundError(PromptError):
    """Raised when a prompt entity cannot be found."""
    code = "PROMPT_NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND


class PromptVersionNotFoundError(PromptError):
    """Raised when a requested prompt version is not found."""
    code = "PROMPT_VERSION_NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND


class PromptReleaseNotFoundError(PromptError):
    """Raised when a prompt release cannot be found."""
    code = "PROMPT_RELEASE_NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND


class PromptExperimentNotFoundError(PromptError):
    """Raised when a prompt experiment is not found."""
    code = "PROMPT_EXPERIMENT_NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND


class PromptExperimentVariantNotFoundError(PromptError):
    """Raised when an experiment variant is not found."""
    code = "PROMPT_EXPERIMENT_VARIANT_NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND


class DuplicatePromptKeyError(PromptError):
    """Raised when a prompt key already exists within the workspace/project scope."""
    code = "DUPLICATE_PROMPT_KEY"
    status_code = status.HTTP_409_CONFLICT


class ImmutableVersionError(PromptError):
    """Raised when attempting to edit or delete a published, immutable prompt version."""
    code = "IMMUTABLE_VERSION_ERROR"
    status_code = status.HTTP_409_CONFLICT


class VariableValidationError(PromptError):
    """Raised when provided variables do not satisfy the prompt's variable schema."""
    code = "VARIABLE_VALIDATION_ERROR"
    status_code = 422


class TemplateInjectionError(PromptError):
    """Raised when potentially malicious template injection or syntax violation is detected."""
    code = "TEMPLATE_INJECTION_ERROR"
    status_code = status.HTTP_400_BAD_REQUEST


class SecretDetectedError(PromptError):
    """Raised when prompt content contains suspected credentials, tokens, or private keys."""
    code = "SECRET_DETECTED_ERROR"
    status_code = 422


class PromotionNotAllowedError(PromptError):
    """Raised when a version does not satisfy environment promotion requirements."""
    code = "PROMOTION_NOT_ALLOWED"
    status_code = status.HTTP_400_BAD_REQUEST


class RollbackNotAllowedError(PromptError):
    """Raised when rollback cannot be completed to the specified version."""
    code = "ROLLBACK_NOT_ALLOWED"
    status_code = status.HTTP_400_BAD_REQUEST


class ExecutionConfigPolicyError(PromptError):
    """Raised when model requirements or execution config violate workspace/org policy."""
    code = "EXECUTION_CONFIG_POLICY_ERROR"
    status_code = status.HTTP_403_FORBIDDEN


class ExperimentAllocationError(PromptError):
    """Raised when deterministic experiment variant assignment fails."""
    code = "EXPERIMENT_ALLOCATION_ERROR"
    status_code = status.HTTP_400_BAD_REQUEST


class PromptResolutionError(PromptError):
    """Raised when a prompt reference cannot be safely resolved."""
    code = "PROMPT_RESOLUTION_ERROR"
    status_code = status.HTTP_404_NOT_FOUND
