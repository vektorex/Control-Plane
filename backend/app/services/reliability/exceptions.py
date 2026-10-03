"""
Custom exceptions for Step 35: AI Reliability, Resilience & Chaos Engineering Layer.
"""
from typing import Any, Dict, Optional


class ReliabilityError(Exception):
    """Base exception for all reliability and resilience failures."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ComponentNotFoundError(ReliabilityError):
    """Raised when a specified reliability component is not registered."""
    pass


class DependencyHealthCheckFailed(ReliabilityError):
    """Raised when a dependency health check encounters an unhandled error."""
    pass


class CheckpointNotFoundError(ReliabilityError):
    """Raised when an execution checkpoint cannot be found."""
    pass


class CheckpointIntegrityError(ReliabilityError):
    """Raised when a checkpoint's cryptographic hash or payload fails integrity validation."""
    pass


class ResumePreconditionFailedError(ReliabilityError):
    """Raised when safety, governance, security, or tenant verification fails before resume."""
    pass


class CircuitOpenError(ReliabilityError):
    """Raised when a call is blocked because the target circuit breaker is currently open."""
    pass


class BulkheadCapacityExceededError(ReliabilityError):
    """Raised when bounded concurrency limit for a subsystem or provider is saturated."""
    pass


class ProductionChaosBlockedError(ReliabilityError):
    """Raised when an experiment attempts to execute in production without explicit authorization."""
    pass


class UnauthorizedChaosExecutionError(ReliabilityError):
    """Raised when an actor lacks permission to run or approve chaos experiments."""
    pass


class InvalidChaosActionError(ReliabilityError):
    """Raised when an experiment action is not present in the safety allowlist."""
    pass


class ChaosExperimentAbortedError(ReliabilityError):
    """Raised when an ongoing experiment triggers an abort condition or is cancelled."""
    pass
