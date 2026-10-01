"""Errors and exceptions for the AI Evaluation Lab."""

class EvaluationLabError(Exception):
    """Base error for all Evaluation Lab operations."""
    pass


class DatasetNotFoundError(EvaluationLabError):
    """Raised when an evaluation dataset is not found or not accessible."""
    pass


class DatasetVersionNotFoundError(EvaluationLabError):
    """Raised when an evaluation dataset version is not found."""
    pass


class DatasetVersionLockedError(EvaluationLabError):
    """Raised when attempting to modify a dataset version that is locked by completed experiments."""
    pass


class CaseNotFoundError(EvaluationLabError):
    """Raised when an evaluation case is not found."""
    pass


class ExperimentNotFoundError(EvaluationLabError):
    """Raised when an evaluation experiment is not found or not accessible."""
    pass


class ExperimentRunNotFoundError(EvaluationLabError):
    """Raised when an evaluation experiment run record is not found."""
    pass


class ExperimentStateError(EvaluationLabError):
    """Raised when an experiment operation is invalid for its current lifecycle state."""
    pass


class InvalidTargetError(EvaluationLabError):
    """Raised when an evaluation target (task, workflow, model, prompt) is invalid or unavailable."""
    pass


class AssertionExecutionError(EvaluationLabError):
    """Raised when an evaluation assertion cannot be evaluated or is malformed."""
    pass


class DatasetValidationError(EvaluationLabError):
    """Raised when dataset cases fail validation checks."""
    pass


class DatasetImportError(EvaluationLabError):
    """Raised when importing dataset cases fails due to format or payload limits."""
    pass


class SideEffectBlockedError(EvaluationLabError):
    """Raised when an evaluation target attempts a destructive or write side-effect without authorization."""
    pass
